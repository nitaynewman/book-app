import PyPDF2
import os
import edge_tts
import pdfplumber
import asyncio
import subprocess
import sys


class PDFToMP3Converter:
    def __init__(self):
        # Get the absolute path of the project's root directory (be/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.output_dir = os.path.join(project_root, "be-api/mp3")

        # Create the mp3 directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

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
        temp_script = os.path.join(self.output_dir, "_temp_tts_script.py")
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            # Run the script in a subprocess
            print("Running text-to-speech conversion in subprocess...")
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                print("✅ Subprocess completed successfully")
                return True
            else:
                print(f"❌ Subprocess failed:")
                print(f"  stdout: {result.stdout}")
                print(f"  stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Subprocess timed out after 30 minutes")
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

    def convert(self, pdf_path):
        """Convert PDF to MP3 using pyttsx3 in a subprocess for stability."""
        if not os.path.isfile(pdf_path):
            print(f"File {pdf_path} not found.")
            return
        
        try:
            print("Extracting text from PDF...")
            pdfreader = PyPDF2.PdfReader(open(pdf_path, 'rb'))
            full_text = ""

            total_pages = len(pdfreader.pages)
            print(f"Processing {total_pages} pages...")

            for num in range(total_pages):
                text = pdfreader.pages[num].extract_text()
                clean_txt = text.strip().replace('\n', ' ')
                full_text += clean_txt + " "
                
                if (num + 1) % 10 == 0:
                    print(f"  Processed {num + 1}/{total_pages} pages...")

            print(f"Extracted {len(full_text)} characters")

            # Generate the output MP3 filename
            mp3_filename = os.path.join(
                self.output_dir, 
                os.path.splitext(os.path.basename(pdf_path))[0] + '.mp3'
            )
            
            print(f"Generating audio file: {mp3_filename}")
            print("This may take 10-20 minutes for a full book...")
            
            # Run pyttsx3 in subprocess
            success = self._run_pyttsx3_subprocess(full_text, mp3_filename)
            
            if success and os.path.exists(mp3_filename):
                print(f"✅ MP3 file has been created successfully: {mp3_filename}")
            else:
                print(f"❌ Failed to create MP3 file")
                raise Exception("MP3 conversion failed")
            
        except Exception as e:
            print(f"❌ An error occurred during conversion: {e}")
            raise

    def extract_text(self, file: str) -> str:
        """ Extract text from a PDF file using pdfplumber. """
        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            if not text.strip():
                print(f"Warning: No text extracted from {file}.")
            return text.strip()
        except Exception as e:
            print(f"Error reading {file}: {e}")
            return ""

    async def convert_async(self, file: str, voice: str = "male"):
        """ Convert extracted text to an MP3 file asynchronously using edge-tts. """
        if not os.path.isfile(file):
            print(f"Error: File {file} not found.")
            return

        text = self.extract_text(file)
        if not text:
            print(f"Error: No text found in {file}.")
            return

        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file))[0]
        mp3_filename = os.path.join(self.output_dir, f"{safe_name}.mp3")

        try:
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(mp3_filename)
            print(f"MP3 file created: {mp3_filename}")
        except Exception as e:
            print(f"Error generating MP3: {e}")

    async def convert_with_voice(self, file: str, voice: str = "male"):
        """ Use edge-tts for non-male voices. """
        await self.convert_async(file, voice)