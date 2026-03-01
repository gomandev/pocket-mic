"""
FastAPI Service for Audio Production Pipeline
Handles job processing in background
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
import numpy as np  # For density calculations

from analyze import analyze_audio, download_audio
from generate_replicate import generate_beat_replicate

# LYRIA INTEGRATION (Primary beat generation)
from generate_lyria_realtime import generate_reactive_beat
from generate_lyria import generate_beat_lyria

# PRODUCER-FIRST ARCHITECTURE
from vocal_intel import extract_vocal_dna, load_audio_robust
from reactive_mixer import mix_vocal_and_beat
from reactive_mixer_stems import mix_vocal_and_stems  # Stem-based mixing
from stem_separator import separate_beat_stems  # AI stem separation (fallback)
from decision_master import master_track
from beat_adapter import validate_beat_alignment, should_regenerate_beat, create_audiocraft_constraints

load_dotenv()

app = FastAPI(title="PocketMic Audio Production Service")

# CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

class ProductionRequest(BaseModel):
    job_id: str
    audio_url: str
    blueprint: dict  # {genre, bpm, key, mood}

@app.get("/")
async def root():
    return {
        "service": "PocketMic Audio Production",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}

class AnalyzeRequest(BaseModel):
    audio_url: str

@app.post("/analyze-vocal")
async def analyze_vocal_dna(request: AnalyzeRequest):
    """
    Extract high-fidelity vocal DNA (Timing, Phrases, Energy)
    Used to condition the AI Agents.
    """
    try:
        local_path = await download_audio(request.audio_url)
        vocal_dna = extract_vocal_dna(local_path, verbose=False)
        return vocal_dna
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_production(
    request: ProductionRequest,
    background_tasks: BackgroundTasks
):
    """
    Queue audio production job
    Returns immediately, processes in background
    """
    # Add to background tasks
    background_tasks.add_task(
        process_audio_pipeline,
        request.job_id,
        request.audio_url,
        request.blueprint
    )
    
    return {
        "status": "queued",
        "job_id": request.job_id,
        "message": "Production started in background"
    }

class MasteringRequest(BaseModel):
    job_id: str
    style: str = "Balanced"
    punch: float = 50.0
    width: float = 50.0

@app.post("/master")
async def master_production(
    request: MasteringRequest,
    background_tasks: BackgroundTasks
):
    """
    Apply advanced mastering to an existing production
    """
    background_tasks.add_task(
        process_mastering_only,
        request.job_id,
        request.style,
        request.punch,
        request.width
    )
    
    return {
        "status": "queued",
        "job_id": request.job_id,
        "message": f"Mastering with style '{request.style}' started in background"
    }

async def process_mastering_only(
    job_id: str,
    style: str,
    punch: float,
    width: float
):
    try:
        # 1. Fetch job to get current audio
        job_res = supabase.table('jobs').select('*').eq('id', job_id).single().execute()
        job_data = job_res.data
        if not job_data or not job_data.get('result_plan', {}).get('processed_audio_url'):
            raise Exception("No production found for this job")
            
        current_url = job_data['result_plan']['processed_audio_url']
        
        # 2. Download current track
        print(f"📥 Downloading for mastering: {current_url}")
        local_path = await download_audio(current_url)
        
        # 3. Apply Advanced Mastering
        print(f"💎 Mastering style: {style}")
        mastered_path = os.path.join(os.path.dirname(local_path), f"remastered_{job_id}.wav")
        master_track(local_path, mastered_path, style=style, punch=punch, width=width, verbose=True)
        
        # 4. Upload as a new version
        remote_path = f"productions/{job_id}_mastered_{style.lower().replace(' ', '_')}.wav"
        with open(mastered_path, 'rb') as f:
            supabase.storage.from_('audio-assets').upload(
                path=remote_path,
                file=f,
                file_options={"content-type": "audio/wav", "x-upsert": "true"}
            )
            
        final_url = supabase.storage.from_('audio-assets').get_public_url(remote_path)
        
        # 5. Update job (optionally keep previous versions in metadata)
        supabase.table('jobs').update({
            'result_plan': {
                **job_data.get('result_plan', {}),
                'processed_audio_url': final_url,
                'last_master_style': style
            }
        }).eq('id', job_id).execute()
        
        print(f"✅ Remastering complete: {final_url}")
        
    except Exception as e:
        print(f"❌ Mastering failed: {e}")

async def process_audio_pipeline(
    job_id: str,
    audio_url: str,
    blueprint: dict
):
    """
    Complete audio production pipeline
    1. Download audio
    2. Analyze (verify BPM/key)
    3. Generate beat
    4. Mix (TODO)
    5. Master (TODO)
    6. Upload to Supabase
    7. Update job status
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 Starting production pipeline for job: {job_id}")
        print(f"{'='*60}\n")
        
        # Step 1: Download audio (0-10%)
        supabase.table('jobs').update({'status': 'ANALYZING', 'progress': 0}).eq('id', job_id).execute()
        print("📥 Step 1/6: Downloading vocal...")
        local_audio = await download_audio(audio_url)
        supabase.table('jobs').update({'progress': 10}).eq('id', job_id).execute()
        
        # Step 2: Extract Vocal DNA (10-25%)
        print("\n🔬 Step 2/6: Extracting Vocal DNA...")
        vocal_dna = extract_vocal_dna(local_audio, verbose=True)
        supabase.table('jobs').update({'progress': 25}).eq('id', job_id).execute()
        
        # Step 3: Generate beat (25-60%) - DESIGNING phase
        supabase.table('jobs').update({'status': 'DESIGNING'}).eq('id', job_id).execute()
        
        # === LYRIA-FIRST BEAT GENERATION ===
        # Priority: Lyria RealTime (reactive) → Lyria 3 (static) → Stable Audio (legacy)
        beat_path = None
        
        # PRIMARY: Lyria RealTime - generates beat that breathes with the vocal
        try:
            print("\n🎹 Step 3/6: Generating vocal-reactive beat with Lyria RealTime...")
            beat_path = await generate_reactive_beat(
                vocal_path=local_audio,
                genre=blueprint.get("genre", "Alt-R&B"),
                bpm=vocal_dna['bpm'],
                key=blueprint.get("key", "D minor"),
                mood=blueprint.get("mood", "introspective"),
                duration_s=30.0,
                vocal_dna=vocal_dna,
                output_path=os.path.join(os.path.dirname(local_audio), f"beat_{job_id}_lyria_rt.wav"),
                verbose=True
            )
            print("   ✅ Lyria RealTime: Vocal-reactive beat generated")
        except Exception as lyria_rt_err:
            print(f"   ⚠️ Lyria RealTime failed: {lyria_rt_err}")
        
        # FALLBACK 1: Lyria 3 text-to-music
        if not beat_path:
            try:
                print("\n🎹 Step 3/6 (Fallback): Generating beat with Lyria 3...")
                beat_path = generate_beat_lyria(
                    genre=blueprint.get("genre", "Alt-R&B"),
                    bpm=vocal_dna['bpm'],
                    key=blueprint.get("key", "D minor"),
                    mood=blueprint.get("mood", "introspective"),
                    density_hints={
                        'breath_gap_count': len(vocal_dna.get('breath_gaps', [])),
                        'avg_presence': 1.0 - np.mean(vocal_dna.get('density_envelope', [0.5]))
                    },
                    vocal_dna=vocal_dna,
                    output_path=os.path.join(os.path.dirname(local_audio), f"beat_{job_id}_lyria3.wav"),
                    verbose=True
                )
                print("   ✅ Lyria 3: Beat generated")
            except Exception as lyria3_err:
                print(f"   ⚠️ Lyria 3 failed: {lyria3_err}")
        
        # FALLBACK 2: Stable Audio via Replicate (legacy)
        if not beat_path:
            print("\n🎹 Step 3/6 (Legacy Fallback): Generating beat with Stable Audio...")
            beat_path = generate_beat_replicate(
                genre=blueprint.get("genre", "Alt-R&B"),
                bpm=vocal_dna['bpm'],
                key=blueprint.get("key", "D minor"),
                mood=blueprint.get("mood", "introspective"),
                duration=30,
                density_hints={
                    'breath_gap_count': len(vocal_dna.get('breath_gaps', [])),
                    'avg_presence': 1.0 - np.mean(vocal_dna.get('density_envelope', [0.5]))
                },
                vocal_dna=vocal_dna
            )
        
        supabase.table('jobs').update({'progress': 60}).eq('id', job_id).execute()
        
        # Step 3.5: Optional stem separation (60-65%)
        # Lyria RealTime already generates density-aware beats, so Demucs is optional
        supabase.table('jobs').update({'status': 'ARRANGING'}).eq('id', job_id).execute()
        stems = None
        try:
            print("\n🔬 Step 3.5/6: Separating beat into stems with Demucs AI...")
            stems = separate_beat_stems(beat_path, verbose=True)
            supabase.table('jobs').update({'progress': 65}).eq('id', job_id).execute()
        except Exception as stem_err:
            print(f"   ⚠️ Stem separation skipped: {stem_err}")
            print("   → Using full beat mix (Lyria's density already handles arrangement)")
            supabase.table('jobs').update({'progress': 65}).eq('id', job_id).execute()
        
        # Step 4: Validate alignment (65-70%)
        print("\n🔍 Step 4/6: Validating beat alignment...")
        is_aligned, drift = validate_beat_alignment(
            local_audio, beat_path, 
            tolerance_ms=200.0,  # Lyria has BPM lock, so drift should be minimal
            verbose=True
        )
        
        if not is_aligned:
            print(f"   ⚠️ Drift {drift:.1f}ms detected, but continuing (Lyria BPM-locked)")
        
        supabase.table('jobs').update({'progress': 70}).eq('id', job_id).execute()
        
        # Step 5: Mixing (70-85%)
        print("\n🎚️ Step 5/6: Intelligent mixing...")
        
        if stems:
            # Stem-based mixing for maximum quality
            mixed_path = mix_vocal_and_stems(
                local_audio,
                stems,
                vocal_dna=vocal_dna,
                verbose=True
            )
        else:
            # Reactive mixer with vocal DNA (when stems unavailable)
            mixed_path = mix_vocal_and_beat(
                vocal_path=local_audio,
                beat_path=beat_path,
                output_path=os.path.join(os.path.dirname(local_audio), f"mixed_{job_id}.wav"),
                vocal_dna=vocal_dna,
                nudge_ms=drift if not is_aligned else 0.0,
                verbose=True
            )
        
        supabase.table('jobs').update({'progress': 85}).eq('id', job_id).execute()
        
        # Step 6: Decision-based mastering (80-90%)
        print("\n💎 Step 6/6: Mastering...")
        final_path = os.path.join(os.path.dirname(local_audio), f"final_{job_id}.wav")
        master_track(mixed_path, final_path, style="Balanced", verbose=True)
        supabase.table('jobs').update({'progress': 90}).eq('id', job_id).execute()
        
        # Step 6: Upload to Supabase Storage
        print("\nUploading to Supabase...")
        remote_path = f"productions/{job_id}_final.wav"
        with open(final_path, 'rb') as f:
            upload_result = supabase.storage.from_('audio-assets').upload(
                path=remote_path,
                file=f,
                file_options={"content-type": "audio/wav", "x-upsert": "true"}
            )
        
        # Get public URL
        final_url = supabase.storage.from_('audio-assets').get_public_url(
            f"productions/{job_id}_final.wav"
        )
        
        # Step 7: Update job in database
        print("Updating job status...")
        supabase.table('jobs').update({
            'status': 'COMPLETED',
            'progress': 100,
            'result_plan': {
                'processed_audio_url': final_url,
                'message': 'Production finished successfully'
            }
        }).eq('id', job_id).execute()
        
        print(f"\n✅ Production complete! Final URL: {final_url}\n")
        
    except Exception as e:
        print(f"\n❌ Error in pipeline: {e}\n")
        # Update job as failed
        supabase.table('jobs').update({
            'status': 'FAILED',
            'error': str(e)
        }).eq('id', job_id).execute()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

