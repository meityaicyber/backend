import asyncio
import time
import httpx

# In a real environment, this might point to a hosted container
# For local testing, we assume the AI pipeline is on port 8001
AI_PIPELINE_URL = "http://localhost:8001/run"

async def fetch_objective1(client: httpx.AsyncClient, index: int, file_bytes: bytes):
    try:
        start = time.time()
        response = await client.post(
            AI_PIPELINE_URL,
            data={"report_id": f"test-report-{index}"},
            files={"file": (f"test_{index}.pdf", file_bytes, "application/pdf")},
        )
        response.raise_for_status()
        end = time.time()
        return {"index": index, "status": "success", "time": end - start}
    except Exception as e:
        return {"index": index, "status": "failed", "error": str(e)}

async def run_concurrency_test(num_concurrent: int):
    print(f"Starting concurrency test with {num_concurrent} simultaneous requests to Objective 1...")
    
    # We create a dummy PDF file (or just some bytes)
    dummy_pdf_bytes = b"%PDF-1.4\n%EOF\n"
    
    # Using limits to see if the server chokes or if it handles them gracefully
    limits = httpx.Limits(max_connections=num_concurrent, max_keepalive_connections=num_concurrent)
    
    start_total = time.time()
    
    async with httpx.AsyncClient(timeout=120.0, limits=limits) as client:
        tasks = [fetch_objective1(client, i, dummy_pdf_bytes) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
    end_total = time.time()
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\n--- Concurrency Test Results ({num_concurrent} requests) ---")
    print(f"Total time elapsed: {end_total - start_total:.2f} seconds")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    if success_count > 0:
        avg_time = sum(r.get('time', 0) for r in results if r['status'] == 'success') / success_count
        print(f"Average response time: {avg_time:.2f} seconds")
        
    if fail_count > 0:
        print("\nErrors:")
        for r in results:
            if r['status'] == 'failed':
                print(f"Request {r['index']} failed: {r['error']}")
                
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Objective 1 Concurrency")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    args = parser.parse_args()
    
    asyncio.run(run_concurrency_test(args.concurrency))
