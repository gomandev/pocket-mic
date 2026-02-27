import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL: {url}")
print(f"Key length: {len(key) if key else 0}")

try:
    supabase = create_client(url, key)
    res = supabase.table("jobs").select("*").limit(1).execute()
    # Test Storage Upload
    print("\nTesting storage upload...")
    test_content = b"test audio content"
    storage_res = supabase.storage.from_("audio-assets").upload(
        path="test_upload.txt",
        file=test_content,
        file_options={"content-type": "text/plain", "x-upsert": "true"}
    )
    print("✅ Storage upload successful!")
    print(storage_res)
except Exception as e:
    print(f"❌ Operation failed: {e}")
