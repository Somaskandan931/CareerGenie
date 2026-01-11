"""
Test the API endpoint step-by-step to find where it fails
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("  API Endpoint Diagnostic")
print("=" * 70)

# Test 1: Health check
print("\n1️⃣ Testing Health Endpoint...")
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"✅ Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 2: Check stats before
print("\n2️⃣ Checking Stats (Before)...")
try:
    r = requests.get(f"{BASE_URL}/rag/stats")
    stats = r.json()
    print(f"✅ Stats: {json.dumps(stats, indent=2)}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: Simple RAG request with minimal data
print("\n3️⃣ Testing RAG Endpoint (Minimal Request)...")
payload = {
    "resume_text": "Python engineer",
    "job_query": "engineer",
    "location": "India",
    "num_jobs": 5,
    "top_k": 3,
    "use_cache": False
}

print(f"Request payload:")
print(json.dumps(payload, indent=2))

try:
    print("\n⏳ Sending request...")
    r = requests.post(
        f"{BASE_URL}/rag/match-realtime",
        json=payload,
        timeout=30
    )

    print(f"\nResponse Status: {r.status_code}")
    print(f"Response Headers: {dict(r.headers)}")

    if r.status_code == 200:
        data = r.json()
        print(f"\n✅ Success! Response:")
        print(json.dumps(data, indent=2))

        # Analyze the response
        print(f"\n📊 Analysis:")
        print(f"  Jobs Fetched: {data.get('jobs_fetched', 'N/A')}")
        print(f"  Total Matches: {data.get('total_matches', 'N/A')}")
        print(f"  Cache Used: {data.get('cache_used', 'N/A')}")
        print(f"  Matched Jobs Count: {len(data.get('matched_jobs', []))}")

        if data.get('jobs_fetched', 0) == 0:
            print("\n⚠️ WARNING: 0 jobs fetched!")
            print("This means the scraper is not working in the API context.")
            print("\nPossible causes:")
            print("  1. Import error in the API router")
            print("  2. Scraper initialization failing")
            print("  3. API key not accessible in server context")
            print("\nCheck your server logs for errors!")

    elif r.status_code == 500:
        print(f"\n❌ Server Error!")
        try:
            error = r.json()
            print(f"Error details: {json.dumps(error, indent=2)}")
        except:
            print(f"Raw response: {r.text}")
    else:
        print(f"\n❌ Unexpected status: {r.status_code}")
        print(f"Response: {r.text}")

except requests.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check if scraper can be imported in server context
print("\n4️⃣ Testing Direct Scraper Import...")
print("Note: This tests if the scraper works when imported the same way the server does")

try:
    # Import the same way the server does
    import sys
    import os

    # Add current directory to path (simulating server context)
    backend_path = os.path.dirname(os.path.abspath(__file__))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    print(f"Python path: {sys.path[0]}")

    try:
        from rag.job_scraper import get_scraper
        print("✅ Import successful (rag.job_scraper)")

        scraper = get_scraper()
        print("✅ Scraper initialized")

        # Try fetching
        jobs = scraper.fetch_jobs("engineer", "India", 3)
        print(f"✅ Fetched {len(jobs)} jobs directly")

        if jobs:
            print(f"   Sample: {jobs[0].get('title')} at {jobs[0].get('company')}")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nThis is likely why the API is returning 0 jobs!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("  Diagnostic Complete")
print("=" * 70)

print("\n💡 Next Steps:")
print("1. Check your server terminal for ERROR messages")
print("2. Look for import errors or initialization failures")
print("3. The server logs will show the exact error")
print("\nServer logs format:")
print("  INFO:     ... (normal messages)")
print("  ERROR:    ... (← Look for these!)")
print("  WARNING:  ... (potential issues)")