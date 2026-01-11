"""
Test the job scraper directly (bypassing API)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("  Direct Job Scraper Test")
print("=" * 70)

# Test 1: Check environment
print("\n1️⃣ Checking Environment Variables...")
searchapi_key = os.getenv("SEARCHAPI_KEY") or os.getenv("SERPAPI_KEY")
if searchapi_key:
    print(f"✅ API Key: {searchapi_key[:15]}...{searchapi_key[-5:]}")
else:
    print("❌ No API key found!")
    exit(1)

# Test 2: Import scraper
print("\n2️⃣ Importing Job Scraper...")
try:
    from backend.rag.job_scraper import RealTimeJobScraper
    print("✅ Job scraper imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nTrying alternative import...")
    try:
        from rag.job_scraper import RealTimeJobScraper
        print("✅ Job scraper imported successfully (alternative path)")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        exit(1)

# Test 3: Initialize scraper
print("\n3️⃣ Initializing Scraper...")
try:
    scraper = RealTimeJobScraper()
    print("✅ Scraper initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Fetch jobs
print("\n4️⃣ Fetching Jobs (Simple Query)...")
print("Query: 'engineer'")
print("Location: 'India'")
print("Number: 10")

try:
    jobs = scraper.fetch_jobs(
        query="engineer",
        location="India",
        num_results=10
    )

    print(f"\n✅ Fetched {len(jobs)} jobs!")

    if jobs:
        print("\n📋 Sample Job (First Result):")
        first_job = jobs[0]
        print(f"  Job ID: {first_job.get('job_id')}")
        print(f"  Title: {first_job.get('title')}")
        print(f"  Company: {first_job.get('company')}")
        print(f"  Location: {first_job.get('location')}")
        print(f"  Skills Required: {', '.join(first_job.get('skills_required', [])[:5])}")
        print(f"  Experience: {first_job.get('experience_required')}")
        print(f"  Apply Link: {first_job.get('apply_link', 'N/A')[:50]}...")

        print(f"\n📊 All {len(jobs)} Jobs:")
        for i, job in enumerate(jobs, 1):
            print(f"  {i}. {job.get('title')} at {job.get('company')}")
    else:
        print("\n⚠️ No jobs returned")
        print("\nPossible causes:")
        print("  - API key invalid or expired")
        print("  - Query returned no results")
        print("  - Response format changed")

except Exception as e:
    print(f"\n❌ Fetch failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Test different query
print("\n5️⃣ Testing Another Query (Python Developer)...")
try:
    jobs = scraper.fetch_jobs(
        query="python developer",
        location="India, IN",
        num_results=5
    )

    print(f"✅ Fetched {len(jobs)} jobs for 'python developer'")

    if jobs:
        for i, job in enumerate(jobs, 1):
            print(f"  {i}. {job.get('title')} at {job.get('company')}")

except Exception as e:
    print(f"❌ Second query failed: {e}")

print("\n" + "=" * 70)
print("  Test Complete!")
print("=" * 70)

if 'jobs' in locals() and jobs:
    print("\n✅ SUCCESS! Job scraper is working correctly")
    print(f"Total jobs fetched: {len(jobs)}")
    print("\nThe issue is likely in how the API endpoint uses the scraper.")
    print("Check your server logs for errors.")
else:
    print("\n❌ FAILED! Job scraper is not fetching jobs")
    print("\nNext steps:")
    print("  1. Verify API key at: https://www.searchapi.io/dashboard")
    print("  2. Check if you have remaining credits")
    print("  3. Try a different API key")