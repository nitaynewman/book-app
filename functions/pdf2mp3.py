import PyPDF2
import os
import edge_tts
import pdfplumber
import asyncio
import subprocess
import sys
import platform
import tempfile
from pydub import AudioSegment


class PDFToMP3Converter:
    def __init__(self, progress_callback=None):
        # Get the absolute path of the project's root directory (be/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.output_dir = os.path.join(project_root, "book-app/mp3")

        # Create the mp3 directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Progress callback for real-time updates
        self.progress_callback = progress_callback

        # Voice mappings
        self.voices = {
            "male": "en-US-GuyNeural",
            "female": "en-US-JennyNeural",
            "British-male": "en-GB-RyanNeural",
            "British-female": "en-GB-SoniaNeural",
            "Australian-male": "en-AU-WilliamNeural",
            "Australian-female": "en-AU-NatashaNeural",
            "Indian-male": "en-IN-PrabhatNeural",
            "Indian-female": "en-IN-NeerjaNeural"
        }
        
        # Voices that should use pyttsx3 (only basic male/female)
        self.pyttsx3_voices = ["male", "female"]
        
        # Check if pyttsx3 is available
        self.pyttsx3_available = self._check_pyttsx3_availability()
        
        # Check if ffmpeg is available for merging
        self.ffmpeg_available = self._check_ffmpeg_availability()

    def _update_progress(self, status: str, progress: int):
        """Update progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(status, progress)
        print(f"[Progress] {status}: {progress}%")

    def _check_ffmpeg_availability(self):
        """Check if ffmpeg is available for audio merging."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ ffmpeg is available")
                return True
            return False
        except Exception as e:
            print(f"⚠️ ffmpeg not available: {e}")
            print("   Will use pydub for audio merging")
            return False

    def _check_pyttsx3_availability(self):
        """Check if pyttsx3 is available and working on this system."""
        try:
            import pyttsx3
            # Try to initialize it
            engine = pyttsx3.init()
            engine.stop()
            print("✅ pyttsx3 is available")
            return True
        except Exception as e:
            print(f"⚠️ pyttsx3 not available: {e}")
            print("   Will use edge-tts for all voices")
            return False

    def _install_espeak_if_needed(self):
        """On Linux, ensure espeak is installed for pyttsx3."""
        if platform.system() != "Linux":
            return True
        
        try:
            # Check if espeak is installed
            result = subprocess.run(
                ["which", "espeak"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ espeak is installed")
                return True
            
            print("⚠️ espeak not found. Attempting to install...")
            
            # Try to install espeak
            install_result = subprocess.run(
                ["sudo", "apt-get", "update"],
                capture_output=True,
                text=True
            )
            
            install_result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "espeak"],
                capture_output=True,
                text=True
            )
            
            if install_result.returncode == 0:
                print("✅ espeak installed successfully")
                return True
            else:
                print(f"❌ Failed to install espeak: {install_result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking/installing espeak: {e}")
            return False

    def extract_text(self, file: str) -> str:
        """Extract text from a PDF file using pdfplumber with progress updates."""
        try:
            print(f"Extracting text from: {file}")
            self._update_progress("extracting", 12)
            
            with pdfplumber.open(file) as pdf:
                text_parts = []
                total_pages = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Update progress during extraction (12% -> 25%)
                    if (i + 1) % 10 == 0 or i == total_pages - 1:
                        progress = 12 + int((i + 1) / total_pages * 13)
                        self._update_progress("extracting", progress)
                        print(f"  Processed {i + 1}/{total_pages} pages...")
                
                text = "\n".join(text_parts)
            
            if not text.strip():
                print(f"Warning: No text extracted from {file}.")
            else:
                print(f"✅ Extracted {len(text)} characters from {total_pages} pages")
            
            self._update_progress("extracting", 25)
            return text.strip()
        except Exception as e:
            print(f"Error reading {file}: {e}")
            raise

    def _merge_audio_files_ffmpeg(self, temp_files: list, output_file: str):
        """Merge audio files using ffmpeg (faster and more reliable)."""
        try:
            # Create a temporary file list for ffmpeg
            list_file = os.path.join(self.output_dir, "_concat_list.txt")
            with open(list_file, 'w') as f:
                for temp_file in temp_files:
                    # Escape single quotes in file paths
                    escaped_path = temp_file.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Use ffmpeg to concatenate
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    output_file,
                    "-y"  # Overwrite output file
                ],
                capture_output=True,
                text=True
            )
            
            # Clean up list file
            os.remove(list_file)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr}")
            
            print("✅ Files merged successfully with ffmpeg")
            
        except Exception as e:
            print(f"❌ ffmpeg merge failed: {e}")
            raise

    def _merge_audio_files_pydub(self, temp_files: list, output_file: str):
        """Merge audio files using pydub (fallback method)."""
        try:
            print("Merging audio files with pydub...")
            combined = AudioSegment.empty()
            
            for idx, temp_file in enumerate(temp_files):
                audio_chunk = AudioSegment.from_mp3(temp_file)
                combined += audio_chunk
                
                # Update progress during merge
                progress = 88 + int((idx + 1) / len(temp_files) * 7)
                self._update_progress("merging", progress)
            
            combined.export(output_file, format="mp3")
            print("✅ Files merged successfully with pydub")
            
        except Exception as e:
            print(f"❌ pydub merge failed: {e}")
            raise

    async def convert_async_chunked(self, file: str, voice: str = "male"):
        """Convert text to MP3 using edge-tts with ~1 hour chunks."""
        if not os.path.isfile(file):
            print(f"Error: File {file} not found.")
            raise FileNotFoundError(f"File {file} not found")

        text = self.extract_text(file)
        if not text:
            print(f"Error: No text found in {file}.")
            raise ValueError(f"No text found in {file}")

        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file))[0]
        mp3_filename = os.path.join(self.output_dir, f"{safe_name}.mp3")

        try:
            self._update_progress("converting", 30)
            print(f"Converting to MP3 using edge-tts with voice: {selected_voice}")
            
            # Calculate chunk size for ~1 hour chunks
            # Assuming ~150 words per minute reading speed, ~5 chars per word
            # 1 hour = 60 minutes * 150 words * 5 chars = 45,000 chars
            chunk_size = 45000
            text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            total_chunks = len(text_chunks)
            
            print(f"Processing {total_chunks} chunks (~1 hour each)...")
            
            # Process chunks and save to temporary files
            temp_files = []
            for idx, chunk in enumerate(text_chunks):
                chunk_file = os.path.join(self.output_dir, f"{safe_name}_chunk_{idx}.mp3")
                
                communicate = edge_tts.Communicate(chunk, selected_voice)
                await communicate.save(chunk_file)
                temp_files.append(chunk_file)
                
                # Update progress (30% -> 85%)
                progress = 30 + int((idx + 1) / total_chunks * 55)
                self._update_progress("converting", progress)
                print(f"  Processed chunk {idx + 1}/{total_chunks}")
            
            self._update_progress("merging", 88)
            print("Merging audio chunks into single file...")
            
            # Merge files using ffmpeg or pydub
            if self.ffmpeg_available:
                self._merge_audio_files_ffmpeg(temp_files, mp3_filename)
            else:
                self._merge_audio_files_pydub(temp_files, mp3_filename)
            
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_file}: {e}")
            
            self._update_progress("merging", 95)
            print(f"✅ MP3 file created: {mp3_filename}")
            
        except Exception as e:
            print(f"❌ Error generating MP3: {e}")
            raise

    def convert_sync_pyttsx3_chunked(self, file: str):
        """Convert PDF to MP3 using pyttsx3 with ~1 hour chunks for Ubuntu."""
        if not os.path.isfile(file):
            print(f"File {file} not found.")
            raise FileNotFoundError(f"File {file} not found")
        
        # Ensure espeak is installed on Linux
        if not self._install_espeak_if_needed():
            raise Exception("Cannot use pyttsx3 without espeak on Linux")
        
        text = self.extract_text(file)
        if not text:
            raise ValueError(f"No text found in {file}")
        
        safe_name = os.path.splitext(os.path.basename(file))[0]
        mp3_filename = os.path.join(self.output_dir, f"{safe_name}.mp3")
        
        self._update_progress("converting", 30)
        print(f"Converting to MP3 using pyttsx3 on Ubuntu...")
        
        # Calculate chunk size for ~1 hour chunks
        # Assuming ~150 words per minute, ~5 chars per word
        # 1 hour = 60 * 150 * 5 = 45,000 chars
        chunk_size = 45000
        text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        total_chunks = len(text_chunks)
        
        print(f"Processing {total_chunks} chunks (~1 hour each)...")
        
        # Process each chunk
        temp_files = []
        for idx, chunk in enumerate(text_chunks):
            chunk_file = os.path.join(self.output_dir, f"{safe_name}_chunk_{idx}.mp3")
            
            success = self._run_pyttsx3_subprocess(chunk, chunk_file)
            
            if success and os.path.exists(chunk_file):
                temp_files.append(chunk_file)
                # Update progress (30% -> 85%)
                progress = 30 + int((idx + 1) / total_chunks * 55)
                self._update_progress("converting", progress)
                print(f"  Processed chunk {idx + 1}/{total_chunks}")
            else:
                raise Exception(f"Failed to create chunk {idx + 1}")
        
        self._update_progress("merging", 88)
        print("Merging audio chunks into single file...")
        
        # Merge files using ffmpeg or pydub
        if self.ffmpeg_available:
            self._merge_audio_files_ffmpeg(temp_files, mp3_filename)
        else:
            self._merge_audio_files_pydub(temp_files, mp3_filename)
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
        
        if os.path.exists(mp3_filename):
            self._update_progress("merging", 95)
            print(f"✅ MP3 file has been created successfully: {mp3_filename}")
        else:
            raise Exception("Failed to create final MP3 file")

    def _run_pyttsx3_subprocess(self, text: str, output_path: str):
        """Run pyttsx3 in a separate process to prevent main process crashes."""
        
        # Create a temporary Python script to run pyttsx3
        script_content = f'''
import pyttsx3
import sys

text = """
{text}
"""

output_path = r"{output_path}"

try:
    speaker = pyttsx3.init()
    speaker.setProperty('rate', 150)
    speaker.setProperty('volume', 0.9)
    speaker.save_to_file(text, output_path)
    speaker.runAndWait()
    speaker.stop()
    print("SUCCESS")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
'''
        
        # Write script to temp file
        temp_script = os.path.join(self.output_dir, f"_temp_tts_script_{os.getpid()}.py")
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            # Run the script in a subprocess with longer timeout for large chunks
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout per chunk
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return True
            else:
                print(f"❌ Subprocess failed:")
                print(f"  stdout: {result.stdout}")
                print(f"  stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Subprocess timed out after 1 hour")
            return False
        except Exception as e:
            print(f"❌ Subprocess error: {e}")
            return False
        finally:
            # Clean up temp script
            try:
                os.remove(temp_script)
            except:
                pass

    async def convert_with_voice(self, file: str, voice: str = "male"):
        """
        Convert PDF to MP3 with specified voice using ~1 hour chunks.
        Returns a single merged file.
        Uses pyttsx3 for basic male/female voices on Ubuntu.
        Uses edge-tts for all accent voices and as fallback.
        """
        print(f"\n{'='*60}")
        print(f"Starting conversion with voice: {voice}")
        print(f"System: {platform.system()}")
        print(f"{'='*60}\n")
        
        # For basic voices on Linux, try pyttsx3 first
        if voice in self.pyttsx3_voices and self.pyttsx3_available and platform.system() == "Linux":
            try:
                print(f"Attempting conversion with pyttsx3 for '{voice}' voice on Ubuntu...")
                self.convert_sync_pyttsx3_chunked(file)
                return
            except Exception as e:
                print(f"⚠️ pyttsx3 failed: {e}")
                print("Falling back to edge-tts...")
        
        # Use edge-tts for accent voices or as fallback
        print(f"Using edge-tts for '{voice}' voice...")
        await self.convert_async_chunked(file, voice)
        