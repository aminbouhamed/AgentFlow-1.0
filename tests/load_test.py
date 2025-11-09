import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict

async def send_request(session: aiohttp.ClientSession, email_text: str) -> Dict:
    """Send single request to API"""
    
    url = "http://localhost:8000/process"
    payload = {
        "email_text": email_text,
        "priority": "normal"
    }
    
    start_time = time.time()
    
    try:
        async with session.post(url, json=payload, timeout=60) as response:
            latency = time.time() - start_time
            
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "latency": latency,
                    "decision": data.get("decision"),
                    "confidence": data.get("confidence")
                }
            else:
                return {
                    "success": False,
                    "latency": latency,
                    "error": await response.text()
                }
    
    except Exception as e:
        return {
            "success": False,
            "latency": time.time() - start_time,
            "error": str(e)
        }

async def load_test(num_requests: int = 10, concurrency: int = 5):
    """Run load test"""
    
    test_email = """Subject: AI Solution Inquiry

Hello,

We're interested in implementing AI for our business operations.
Can you provide more information about your services?

Best regards,
Test User
TestCompany GmbH"""
    
    print(f"\n{'='*80}")
    print(f" LOAD TEST")
    print(f"{'='*80}")
    print(f"Total Requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"{'='*80}\n")
    
    # limiting concurency
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_request(session):
        async with semaphore:
            return await send_request(session, test_email)
    
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_request(session) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    latencies = [r["latency"] for r in successful]
    
    print(f"\n{'='*80}")
    print(f" RESULTS")
    print(f"{'='*80}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {num_requests/total_time:.2f} req/s")
    print(f"\nSuccess Rate: {len(successful)}/{num_requests} ({len(successful)/num_requests*100:.1f}%)")
    print(f"Failed: {len(failed)}")
    
    if latencies:
        print(f"\n Latency Statistics:")
        print(f"   Min: {min(latencies):.2f}s")
        print(f"   Max: {max(latencies):.2f}s")
        print(f"   Mean: {statistics.mean(latencies):.2f}s")
        print(f"   Median: {statistics.median(latencies):.2f}s")
        print(f"   P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}s")
        print(f"   P99: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}s")
    
    if successful:
        decisions = {}
        for r in successful:
            decision = r.get("decision", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1
        
        print(f"\n Decision Breakdown:")
        for decision, count in decisions.items():
            print(f"   {decision}: {count} ({count/len(successful)*100:.1f}%)")
    
    if failed:
        print(f"\n❌ Failures:")
        for r in failed[:5]:  
            print(f"   Error: {r.get('error', 'Unknown')[:100]}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    num_requests = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    asyncio.run(load_test(num_requests, concurrency))