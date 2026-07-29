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

async def process_user_batch(jobs_data: List[dict], api_key: Optional[str]):
    chunk_size = 5
    for i in range(0, len(jobs_data), chunk_size):
        chunk = jobs_data[i:i+chunk_size]
        
        # Filter out jobs that were cancelled by the user
        active_chunk = [job for job in chunk if jobs_store.get(job["job_id"], {}).get("status") != "cancelled"]
        if not active_chunk:
            continue
            
        try:
            for job in active_chunk:
                jobs_store[job["job_id"]]["status"] = "processing"
            
            ai_results = await analyze_product_images(active_chunk, api_key)
            
            for idx, ai_result in enumerate(ai_results):
                job_id = active_chunk[idx]["job_id"]
                if "error" in ai_result:
                    jobs_store[job_id]["status"] = "failed"
                    jobs_store[job_id]["result"] = ai_result
                else:
                    final_result = validate_and_correct(ai_result)
                    jobs_store[job_id]["status"] = "completed"
                    jobs_store[job_id]["result"] = final_result
            
            # The API call itself takes ~2 seconds. Reducing sleep to 0.5s as requested by user.
            # WARNING: This pushes throughput to ~24 RPM, which may exceed Gemini's 15 RPM Free Tier limit.
            await asyncio.sleep(0.5)
                    
        except Exception as e:
            for job in chunk:
                job_id = job["job_id"]
                jobs_store[job_id]["status"] = "failed"
                jobs_store[job_id]["result"] = {"error": str(e)}

@app.post("/api/analyze")
async def analyze_product(
    background_tasks: BackgroundTasks,
    image1: UploadFile = File(...)
):
    try:
        img1_bytes = await image1.read()
        
        job_id = str(uuid.uuid4())
        
        jobs_store[job_id] = {
            "status": "queued",
            "result": None,
            "filename": image1.filename
        }
        
        jobs_data = [{"job_id": job_id, "data": img1_bytes, "is_url": False, "custom_prompt": None}]
        background_tasks.add_task(process_user_batch, jobs_data, None)
        return {"job_id": job_id, "status": "queued", "message": "Job added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-url")
async def analyze_urls(payload: UrlAnalyzeRequest, background_tasks: BackgroundTasks):
    try:
        urls = payload.urls
        if not urls:
            raise HTTPException(status_code=400, detail="No URLs provided")
            
        job_id = str(uuid.uuid4())
        url1 = urls[0]
        
        filename = url1.split("/")[-1][:30] if "/" in url1 else url1[:30]
        if not filename: filename = "URL Image"
            
        jobs_store[job_id] = {
            "status": "queued",
            "result": None,
            "filename": filename
        }
        
        jobs_data = [{"job_id": job_id, "data": url1, "is_url": True, "custom_prompt": payload.custom_prompt}]
        background_tasks.add_task(process_user_batch, jobs_data, None)
        return {"job_id": job_id, "status": "queued", "message": "Job added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            jobs_data.append({"job_id": job_id, "data": url, "is_url": True, "custom_prompt": payload.custom_prompt})
            results.append({"job_id": job_id, "url": url, "filename": filename})
            
        keys_list = [k.strip() for k in x_user_api_key.split(",") if k.strip()] if x_user_api_key else []
        if not keys_list:
            keys_list = [None]
            
        num_keys = len(keys_list)
        segment_size = max(1, len(jobs_data) // num_keys + (1 if len(jobs_data) % num_keys > 0 else 0))
        
        for i in range(num_keys):
            segment = jobs_data[i * segment_size : (i + 1) * segment_size]
            if segment:
                background_tasks.add_task(process_user_batch, segment, keys_list[i])
                
        return {"jobs": results, "message": f"{len(urls)} jobs added to queue distributed across {len(keys_list)} keys"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/jobs-status")
async def get_jobs_status(payload: BulkStatusRequest):
    return {job_id: jobs_store.get(job_id) for job_id in payload.job_ids if job_id in jobs_store}

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
