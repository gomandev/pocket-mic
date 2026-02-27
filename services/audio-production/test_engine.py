import os
from engine import advanced_mix_vocal_and_beat, advanced_master_track

# We'll use the files from the last successful pipeline run if possible,
# or just dummy test
VOCAL_PATH = "generated_beat_replicate.wav" # Using a beat as a dummy vocal for testing
BEAT_PATH = "generated_beat_replicate.wav"
MIXED_PATH = "test_mixed.wav"
MASTERED_PATH = "test_mastered.wav"

def main():
    if not os.path.exists(VOCAL_PATH):
        print("❌ Test files not found. Creating a dummy file...")
        from pydub import AudioSegment
        dummy = AudioSegment.silent(duration=5000)
        dummy.export(VOCAL_PATH, format="wav")
        
    print("--- Testing Advanced Mixing ---")
    advanced_mix_vocal_and_beat(VOCAL_PATH, BEAT_PATH, MIXED_PATH)
    
    print("\n--- Testing Advanced Mastering (Radio Ready) ---")
    advanced_master_track(MIXED_PATH, MASTERED_PATH, style="Radio Ready", punch=80)
    
    if os.path.exists(MASTERED_PATH):
        print("\n✅ Test successful! Mastered file created.")
    else:
        print("\n❌ Test failed.")

if __name__ == "__main__":
    main()
