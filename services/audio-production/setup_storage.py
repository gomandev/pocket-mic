"""
Setup script to create required Supabase Storage buckets
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def setup_audio_production_bucket():
    """Create audio-production bucket if it doesn't exist"""
    try:
        # Try to get bucket info
        buckets = supabase.storage.list_buckets()
        
        # Check if audio-production exists
        bucket_exists = any(b.name == 'audio-production' for b in buckets)
        
        if bucket_exists:
            print("✅ Bucket 'audio-production' already exists")
        else:
            # Create the bucket
            supabase.storage.create_bucket(
                'audio-production',
                options={'public': True}  # Make it public so Suno can access URLs
            )
            print("✅ Created bucket 'audio-production' (public)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error setting up bucket: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Setting up Supabase Storage...")
    success = setup_audio_production_bucket()
    
    if success:
        print("\n✅ Storage setup complete! You can now run productions with Suno.")
    else:
        print("\n❌ Storage setup failed. Please create the bucket manually in Supabase Dashboard.")
