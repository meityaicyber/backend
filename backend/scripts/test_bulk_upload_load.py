import asyncio
import time
import uuid
import io
import httpx
from PyPDF2 import PdfWriter

# Configurations
API_BASE = "http://localhost:8000/api/bulk-upload"
AUTH_TOKEN = "your_admin_jwt_token_here" # Replace with valid token for local execution
NUM_FILES = 500
CHUNK_SIZE = 20

def create_dummy_pdf(index: int) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # Adding some metadata to make it slightly unique
    writer.add_metadata({"/Title": f"Dummy Report {index}"})
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

async def upload_chunk(client: httpx.AsyncClient, job_id: str, chunk_index: int, start_idx: int, end_idx: int):
    files = []
    for i in range(start_idx, end_idx):
        pdf_bytes = create_dummy_pdf(i)
        files.append(
            ("files", (f"report_{i}.pdf", pdf_bytes, "application/pdf"))
        )
        
    print(f"Uploading chunk {chunk_index} (files {start_idx} to {end_idx-1})...")
    
    start_time = time.time()
    resp = await client.post(f"{API_BASE}/jobs/{job_id}/files", files=files)
    resp.raise_for_status()
    end_time = time.time()
    
    print(f"Chunk {chunk_index} uploaded in {end_time - start_time:.2f}s")
    
async def run_load_test():
    print(f"--- Starting Bulk Upload Load Test ({NUM_FILES} files) ---")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    async with httpx.AsyncClient(timeout=120.0, headers=headers) as client:
        # 1. Create Job
        print("Creating bulk upload job...")
        resp = await client.post(f"{API_BASE}/jobs", json={"total_files": NUM_FILES})
        if resp.status_code != 201:
            print("Failed to create job. Are you authenticated?", resp.text)
            return
            
        job_id = resp.json()["id"]
        print(f"Job created: {job_id}")
        
        # 2. Upload in chunks concurrently (or sequentially to simulate real UI)
        # The UI uploads sequentially to avoid hammering the disk/network simultaneously
        upload_start = time.time()
        
        for i in range(0, NUM_FILES, CHUNK_SIZE):
            end_idx = min(i + CHUNK_SIZE, NUM_FILES)
            await upload_chunk(client, job_id, i // CHUNK_SIZE, i, end_idx)
            
        upload_end = time.time()
        print(f"All files uploaded in {upload_end - upload_start:.2f}s")
        
        # 3. Start Job
        print("Starting job processing...")
        resp = await client.post(f"{API_BASE}/jobs/{job_id}/start")
        resp.raise_for_status()
        
        # 4. Poll until complete
        process_start = time.time()
        while True:
            resp = await client.get(f"{API_BASE}/jobs/{job_id}")
            data = resp.json()
            
            status = data["status"]
            completed = data["completed_files"]
            failed = data["failed_files"]
            queued = data["queued_files"]
            processing = data["processing_files"]
            
            print(f"Status: {status} | Queued: {queued} | Processing: {processing} | Completed: {completed} | Failed: {failed}")
            
            if status in ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "CANCELLED"]:
                break
                
            await asyncio.sleep(5)
            
        process_end = time.time()
        
        print("\n--- Load Test Results ---")
        print(f"Total files processed: {NUM_FILES}")
        print(f"Total time (Upload): {upload_end - upload_start:.2f}s")
        print(f"Total time (Processing): {process_end - process_start:.2f}s")
        print(f"Average processing time per file: {(process_end - process_start) / NUM_FILES:.2f}s")
        print(f"Final Job Status: {status}")

if __name__ == "__main__":
    asyncio.run(run_load_test())
