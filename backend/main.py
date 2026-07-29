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
RATE_LIMIT_DELAY = 0.0 
queue = asyncio.Queue()

class UrlAnalyzeRequest(BaseModel):
    urls: List[str]
    custom_prompt: Optional[str] = None

class BulkStatusRequest(BaseModel):
    job_ids: List[str]

async def process_queue():
    while True:
        # Get first job
        job1 = await queue.get()
        jobs_to_process = [job1]
        
        # Batch up to 2 images per API request to maximize accuracy
        while len(jobs_to_process) < 2:
            try:
                job_next = queue.get_nowait()
                jobs_to_process.append(job_next)
            except asyncio.QueueEmpty:
                break
                
        try:
            tasks_for_api = []
            for j in jobs_to_process:
                if len(j) == 6:
                    job_id, url1, url2, is_url, custom_prompt, api_key = j
                elif len(j) == 5:
                    job_id, url1, url2, is_url, custom_prompt = j
                    api_key = None
                else:
                    job_id, url1, url2, is_url = j
                    custom_prompt = None
                    api_key = None
                    
                jobs_store[job_id]["status"] = "processing"
                tasks_for_api.append({"job_id": job_id, "data": url1, "is_url": is_url, "custom_prompt": custom_prompt})
            
            # Use the api_key from the first job in the batch
            batch_api_key = jobs_to_process[0][-1] if len(jobs_to_process[0]) == 6 else None
            
            # Send batch to Gemini
            ai_results = await analyze_product_images(tasks_for_api, batch_api_key)
            
            # Process results
            for idx, ai_result in enumerate(ai_results):
                job_id = jobs_to_process[idx][0]
                
                if "error" in ai_result:
                    jobs_store[job_id]["status"] = "failed"
                    jobs_store[job_id]["result"] = ai_result
                else:
                    final_result = validate_and_correct(ai_result)
                    jobs_store[job_id]["status"] = "completed"
                    jobs_store[job_id]["result"] = final_result
                    
        except Exception as e:
            for j in jobs_to_process:
                job_id = j[0]
                jobs_store[job_id]["status"] = "failed"
                jobs_store[job_id]["result"] = {"error": str(e)}
        finally:
            for _ in jobs_to_process:
                queue.task_done()
            # Enforce Rate Limiter (wait ~4.5 seconds per request to stay under 14 req/min)
            await asyncio.sleep(RATE_LIMIT_DELAY)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_queue())

@app.post("/api/analyze")
async def analyze_product(
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
        
        await queue.put((job_id, img1_bytes, None, False))
        return {"job_id": job_id, "status": "queued", "message": "Job added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-url")
async def analyze_urls(request: UrlAnalyzeRequest):
    try:
        urls = request.urls
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
        
        await queue.put((job_id, url1, None, True))
        return {"job_id": job_id, "status": "queued", "message": "Job added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-bulk")
async def analyze_bulk(request: UrlAnalyzeRequest, x_user_api_key: Optional[str] = Header(None)):
    try:
        urls = request.urls
        if not urls:
            raise HTTPException(status_code=400, detail="No URLs provided")
            
        results = []
        for url in urls:
            job_id = str(uuid.uuid4())
            filename = url.split("/")[-1][:30] if "/" in url else url[:30]
            if not filename: filename = "URL Image"
            
            jobs_store[job_id] = {
                "status": "queued",
                "result": None,
                "filename": filename
            }
            await queue.put((job_id, url, None, True, request.custom_prompt, x_user_api_key))
            results.append({"job_id": job_id, "url": url, "filename": filename})
            
        return {"jobs": results, "message": f"{len(urls)} jobs added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_store[job_id]

@app.post("/api/jobs-status")
async def get_jobs_status(request: BulkStatusRequest):
    return {job_id: jobs_store.get(job_id) for job_id in request.job_ids if job_id in jobs_store}

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, x_user_api_key: Optional[str] = Header(None)):
    try:
        result = await handle_chat_message(request.message, request.history, x_user_api_key)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queue-status")
async def get_queue_status():
    return {
        "queue_size": queue.qsize(),
        "total_jobs": len(jobs_store)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
