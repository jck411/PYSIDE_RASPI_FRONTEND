#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from pydub import AudioSegment

def convert_mp3_to_raw_pcm(mp3_file_path):
    """
    Convert an MP3 file to raw PCM format with 24kHz sample rate, mono, 16-bit signed integer
    """
    try:
        # Get the output filename (same name but with .raw extension)
        output_file_path = mp3_file_path.with_suffix('.raw')
        
        # Load the MP3 file
        sound = AudioSegment.from_mp3(str(mp3_file_path))
        
        # Convert to mono if it's stereo
        if sound.channels > 1:
            sound = sound.set_channels(1)
        
        # Set the sample rate to 24kHz
        sound = sound.set_frame_rate(24000)
        
        # Set the sample width to 2 bytes (16-bit)
        sound = sound.set_sample_width(2)
        
        # Export as raw PCM data (no header)
        sound.export(
            str(output_file_path),
            format="raw",
            bitrate="384k"  # Ensure high quality
        )
        
        print(f"Converted {mp3_file_path.name} to {output_file_path.name}")
        return True
    except Exception as e:
        print(f"Error converting {mp3_file_path.name}: {e}")
        return False

def main():
    # Get the sounds directory
    sounds_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Find all MP3 files in the directory
    mp3_files = list(sounds_dir.glob("*.mp3"))
    
    if not mp3_files:
        print(f"No MP3 files found in {sounds_dir}")
        return
    
    print(f"Found {len(mp3_files)} MP3 file(s) to convert")
    
    # Convert each MP3 file
    success_count = 0
    for mp3_file in mp3_files:
        if convert_mp3_to_raw_pcm(mp3_file):
            success_count += 1
    
    print(f"Successfully converted {success_count} of {len(mp3_files)} files")

if __name__ == "__main__":
    main() 