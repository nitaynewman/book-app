import pyttsx3
import PyPDF2
import os
import edge_tts
import pdfplumber
import asyncio


class PDFToMP3Converter:
    def __init__(self):
        # Get the absolute path of the project's root directory (be/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.output_dir = os.path.join(project_root, "be/mp3")

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
                clean_txt = text.strip().replace('\n', ' ')
                full_text += clean_txt + " "

            # Generate the output MP3 filename in the correct directory
            mp3_filename = os.path.join(self.output_dir, os.path.splitext(os.path.basename(pdf_path))[0] + '.mp3')
            speaker.save_to_file(full_text, mp3_filename)
            speaker.runAndWait()
            speaker.stop()

            print(f"MP3 file has been created successfully: {mp3_filename}")
        except Exception as e:
            print(f"An error occurred: {e}")


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
        """ Convert extracted text to an MP3 file asynchronously. """
        if not os.path.isfile(file):
            print(f"Error: File {file} not found.")
            return

        text = self.extract_text(file)
        if not text:
            print(f"Error: No text found in {file}.")
            return

        # Get selected voice (default: male)
        selected_voice = self.voices.get(voice, "en-US-GuyNeural")

        # Generate MP3 output filename
        safe_name = os.path.splitext(os.path.basename(file))[0]
        mp3_filename = os.path.join(self.output_dir, f"{safe_name}.mp3")

        try:
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(mp3_filename)
            print(f"MP3 file created: {mp3_filename}")
        except Exception as e:
            print(f"Error generating MP3: {e}")

    async def convert_with_voice(self, file: str, voice: str = "male"):
        """ Call `convert_async()` properly depending on whether an event loop is running. """
        if asyncio.get_event_loop().is_running():
            await self.convert_async(file, voice)
        else:
            asyncio.run(self.convert_async(file, voice))
