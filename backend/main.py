from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import re

from rules_engine import validate_and_correct
from gemini_service import analyze_product_images
from chat_service import handle_chat_message

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs_store = {}

class UrlAnalyzeRequest(BaseModel):
    urls: List[str]
    custom_prompt: Optional[str] = None

class BulkStatusRequest(BaseModel):
    job_ids: List[str]


# Global stats to track active bulk jobs
bulk_stats = {
    "total": 0,
    "completed": 0,
    "failed": 0,
    "exhausted_keys": [],
    "active_workers": 0
}

async def api_worker(queue: asyncio.Queue, api_key: str):
    chunk_size = 2
    try:
        while True:
            try:
                # Wait for jobs, but if queue is empty and we are done, break
                if queue.empty():
                    break
                    
                jobs_chunk = []
                # Try to get up to chunk_size jobs
                while len(jobs_chunk) < chunk_size and not queue.empty():
                    try:
                        job = queue.get_nowait()
                        if jobs_store.get(job["job_id"], {}).get("status") != "cancelled":
                            jobs_chunk.append(job)
                        else:
                            queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                        
                if not jobs_chunk:
                    break
                    
                for job in jobs_chunk:
                    jobs_store[job["job_id"]]["status"] = "processing"
                    
                print(f"Starting analysis for chunk of {len(jobs_chunk)} images on key ending in {api_key[-4:] if api_key else 'None'}...")
                ai_results = await analyze_product_images(jobs_chunk, api_key)
                
                # Check if it was a 429 Too Many Requests (Rate limit or Daily Quota)
                if ai_results and "error" in ai_results[0] and "429" in str(ai_results[0]["error"]):
                    print(f"API Key {api_key[-4:] if api_key else 'None'} got 429 Limit Exhausted! Putting jobs back in queue.")
                    # Put jobs back in queue
                    for job in jobs_chunk:
                        jobs_store[job["job_id"]]["status"] = "queued"
                        await queue.put(job)
                        queue.task_done() # we mark the original pulled ones as done, since we re-added them
                        
                    # Mark this key as exhausted and shut down this worker
                    if api_key not in bulk_stats["exhausted_keys"]:
                        bulk_stats["exhausted_keys"].append(api_key)
                    return # Exit worker

                # Success or other error
                for idx, ai_result in enumerate(ai_results):
                    job_id = jobs_chunk[idx]["job_id"]
                    if "error" in ai_result:
                        jobs_store[job_id]["status"] = "failed"
                        jobs_store[job_id]["result"] = ai_result
                        bulk_stats["failed"] += 1
                    else:
                        final_result = validate_and_correct(ai_result)
                        jobs_store[job_id]["status"] = "completed"
                        jobs_store[job_id]["result"] = final_result
                        bulk_stats["completed"] += 1
                    queue.task_done()
                    
                # Rate limit sleep for this specific worker/key (15 RPM max -> 1 req per 4s. 2.5s is safe)
                await asyncio.sleep(2.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker error: {e}")
                break
    finally:
        bulk_stats["active_workers"] -= 1

@app.post("/api/analyze-bulk")
async def analyze_bulk(payload: UrlAnalyzeRequest, background_tasks: BackgroundTasks, x_user_api_key: Optional[str] = Header(None)):
    try:
        urls = payload.urls
        if not urls:
            raise HTTPException(status_code=400, detail="No URLs provided")
            
        results = []
        jobs_data = []
        for url in urls:
            job_id = str(uuid.uuid4())
            filename = url.split("/")[-1][:30] if "/" in url else url[:30]
            if not filename: filename = "URL Image"
            
            jobs_store[job_id] = {
                "status": "queued",
                "result": None,
                "filename": filename
            }
            job_dict = {"job_id": job_id, "data": url, "is_url": True, "custom_prompt": payload.custom_prompt}
            jobs_data.append(job_dict)
            results.append({"job_id": job_id, "url": url, "filename": filename})
            
        keys_list = [k.strip() for k in x_user_api_key.split(",") if k.strip()] if x_user_api_key else []
        if not keys_list:
            keys_list = [None]
            
        # Reset stats for new bulk job
        bulk_stats["total"] = len(jobs_data)
        bulk_stats["completed"] = 0
        bulk_stats["failed"] = 0
        bulk_stats["exhausted_keys"] = []
        bulk_stats["active_workers"] = len(keys_list)
        
        # Populate Queue
        queue = asyncio.Queue()
        for job in jobs_data:
            queue.put_nowait(job)
            
        # Spawn Workers
        for key in keys_list:
            asyncio.create_task(api_worker(queue, key))
                
        return {"jobs": results, "message": f"{len(urls)} jobs added to shared queue distributed across {len(keys_list)} workers"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs-status")
async def get_jobs_status(payload: BulkStatusRequest):
    statuses = []
    pending_count = 0
    for job_id in payload.job_ids:
        job = jobs_store.get(job_id)
        if job:
            statuses.append({
                "job_id": job_id,
                "status": job["status"],
                "result": job.get("result")
            })
            if job["status"] in ["queued", "processing"]:
                pending_count += 1
                
    # Calculate ETA based on active workers (Chunk of 2 takes ~4.5 seconds per worker)
    active = max(1, bulk_stats["active_workers"])
    # Throughput: active workers * 2 images / 4.5 seconds
    images_per_second = (active * 2) / 4.5
    eta_seconds = int(pending_count / images_per_second) if images_per_second > 0 else 0
    
    return {
        "statuses": statuses,
        "exhausted_keys": len(bulk_stats["exhausted_keys"]),
        "active_workers": bulk_stats["active_workers"],
        "eta_seconds": eta_seconds,
        "pending_count": pending_count
    }

@app.post("/api/cancel-bulk")
async def cancel_bulk(payload: BulkStatusRequest):
    try:
        cancelled_count = 0
        for job_id in payload.job_ids:
            if job_id in jobs_store and jobs_store[job_id]["status"] in ["queued", "processing"]:
                jobs_store[job_id]["status"] = "cancelled"
                cancelled_count += 1
        return {"message": f"Cancelled {cancelled_count} jobs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_store[job_id]


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest, x_user_api_key: Optional[str] = Header(None)):
    try:
        keys_list = [k.strip() for k in x_user_api_key.split(",") if k.strip()] if x_user_api_key else []
        active_key = keys_list[0] if keys_list else None
        result = await handle_chat_message(payload.message, payload.history, active_key)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queue-status")
async def get_queue_status():
    return {
        "queue_size": 0, # Deprecated
        "total_jobs": len(jobs_store)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
