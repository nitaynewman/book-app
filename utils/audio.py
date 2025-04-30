import os
import re
import pyttsx3
import PyPDF2
import pdfplumber
import edge_tts
import asyncio


class PDFToMP3Converter:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.output_dir = os.path.join(self.base_dir, "mp3")  # changed from test/mp3
        os.makedirs(self.output_dir, exist_ok=True)

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

    def convert(self, pdf_path):
        if not os.path.isfile(pdf_path):
            print(f"File {pdf_path} not found.")
            return

        try:
            pdfreader = PyPDF2.PdfReader(open(pdf_path, 'rb'))
            speaker = pyttsx3.init()
            full_text = ""

            for num in range(len(pdfreader.pages)):
                text = pdfreader.pages[num].extract_text()
                clean_txt = text.strip().replace('\n', ' ') if text else ''
                full_text += clean_txt + " "

            mp3_filename = os.path.join(self.output_dir, os.path.splitext(os.path.basename(pdf_path))[0] + '.mp3')
            speaker.save_to_file(full_text, mp3_filename)
            speaker.runAndWait()
            speaker.stop()

            print(f"MP3 created at: {mp3_filename}")
        except Exception as e:
            print(f"Error during MP3 generation: {e}")

    def extract_text(self, file: str) -> str:
        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            return text.strip()
        except Exception as e:
            print(f"Error reading {file}: {e}")
            return ""

    async def convert_async(self, file: str, voice: str = "male"):
        if not os.path.isfile(file):
            print(f"Error: File {file} not found.")
            return

        text = self.extract_text(file)
        print(f"Extracted text length: {len(text)}")

        if not text:
            print(f"Error: No text found in {file}.")
            return

        max_chars = 3000
        text = text[:max_chars]
        print(f"Trimmed text to {len(text)} characters")


        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file))[0]
        mp3_filename = os.path.join(self.output_dir, f"{safe_name}.mp3")
        print(f"Saving MP3 to: {mp3_filename} with voice: {selected_voice}")

        try:
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(mp3_filename)
            print(f"MP3 created asynchronously at: {mp3_filename}")
        except Exception as e:
            print(f"Error generating MP3: {e}")

    async def convert_with_voice(self, file: str, voice: str = "male"):
        if asyncio.get_event_loop().is_running():
            await self.convert_async(file, voice)
        else:
            asyncio.run(self.convert_async(file, voice))
