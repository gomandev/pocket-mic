"""
STORAGE MANAGEMENT
==================
Upload and manage audio files in Supabase Storage.

Handles uploading vocals to public storage so they can be accessed
by external APIs like Suno for processing.
"""

import os
import uuid
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_vocal_to_storage(local_path: str, verbose: bool = False) -> str:
    """
    Upload vocal file to Supabase Storage and return public URL.
    
    This enables external APIs (like Suno) to access the vocal file
    for processing.
    
    Args:
        local_path: Path to local vocal audio file
        verbose: Enable logging
    
    Returns:
        Public HTTPS URL to uploaded file
    
    Raises:
        Exception: If upload fails
    """
    try:
        # Generate unique filename
        file_ext = Path(local_path).suffix
        filename = f"vocals/{uuid.uuid4()}{file_ext}"
        
        if verbose:
            print(f"\n📤 UPLOADING VOCAL TO STORAGE...")
            print(f"   File: {Path(local_path).name}")
            print(f"   Target: {filename}")
        
        # Read file content
        with open(local_path, 'rb') as f:
            file_content = f.read()
        
        # Upload to Supabase Storage
        response = supabase.storage.from_('audio-production').upload(
            filename,
            file_content,
            {
                "content-type": f"audio/{file_ext[1:]}",  # audio/wav, audio/mp3
                "x-upsert": "false"  # Don't overwrite existing files
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_('audio-production').get_public_url(filename)
        
        if verbose:
            print(f"   ✓ Upload complete!")
            print(f"   └─ URL: {public_url[:60]}...")
        
        return public_url
    
    except Exception as e:
        raise Exception(f"Failed to upload vocal to storage: {str(e)}")


def delete_vocal_from_storage(public_url: str, verbose: bool = False):
    """
    Delete vocal file from storage after processing.
    
    Args:
        public_url: Public URL to uploaded file
        verbose: Enable logging
    """
    try:
        # Extract filename from URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/audio-production/vocals/{uuid}.wav
        filename = public_url.split('/audio-production/')[-1]
        
        if verbose:
            print(f"   └─ Deleting: {filename}")
        
        supabase.storage.from_('audio-production').remove([filename])
        
        if verbose:
            print(f"   ✓ Deleted from storage")
    
    except Exception as e:
        if verbose:
            print(f"   ⚠ Cleanup warning: {e}")

