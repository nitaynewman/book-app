import os
import asyncio
import tempfile
import edge_tts
import pdfplumber
from uuid import uuid4
from pydub import AudioSegment


class PDFToMP3Converter:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.output_dir = os.path.join(self.base_dir, "mp3")
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

    def extract_text(self, file_path: str) -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_text = [page.extract_text() for page in pdf.pages if page.extract_text()]
            return "\n".join(pages_text).strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    async def convert_async(self, file_path: str, voice: str = "male"):
        if not os.path.isfile(file_path):
            print(f"Error: File {file_path} not found.")
            return

        text = self.extract_text(file_path)
        if not text:
            print(f"Error: No text found in {file_path}.")
            return

        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file_path))[0]
        final_output_path = os.path.join(self.output_dir, f"{safe_name}.mp3")

        max_chars = 3000
        chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
        print(f"Total chunks: {len(chunks)}")

        combined = AudioSegment.empty()

        for i, chunk in enumerate(chunks):
            chunk_id = f"{uuid4().hex[:6]}"
            temp_path = os.path.join(tempfile.gettempdir(), f"{safe_name}_chunk_{chunk_id}.mp3")
            print(f"[{i + 1}/{len(chunks)}] Generating chunk to: {temp_path}")

            try:
                communicate = edge_tts.Communicate(chunk, selected_voice)
                await communicate.save(temp_path)

                if not os.path.exists(temp_path):
                    raise FileNotFoundError(f"Chunk not found after generation: {temp_path}")

                segment = AudioSegment.from_file(temp_path, format="mp3")
                combined += segment

            except Exception as e:
                print(f"Error generating or loading MP3 chunk {i + 1}: {e}")
                continue

        combined.export(final_output_path, format="mp3")
        print(f"✅ Final MP3 created at: {final_output_path}")

    async def convert_with_voice(self, pdf_path: str, voice: str):
        print(f"[convert_with_voice] Starting conversion of: {pdf_path}")
        if asyncio.get_event_loop().is_running():
            await self.convert_async(pdf_path, voice)
        else:
            asyncio.run(self.convert_async(pdf_path, voice))
