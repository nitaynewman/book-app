import os
import asyncio
import tempfile
import edge_tts
import pdfplumber
from uuid import uuid4
from pydub import AudioSegment
import logging
import math

logger = logging.getLogger(__name__)

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
        """Extract text from PDF file"""
        try:
            logger.info(f"Extracting text from: {file_path}")
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                total_pages = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    if i % 10 == 0:  # Log progress every 10 pages
                        logger.info(f"Processing page {i+1}/{total_pages}")
                    
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                
                full_text = "\n".join(pages_text).strip()
                logger.info(f"Extracted {len(full_text)} characters from {len(pages_text)} pages")
                return full_text
                
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    def split_text_into_segments(self, text: str, max_chars_per_segment: int = 15000) -> list:
        """Split text into larger segments for chunked processing"""
        # Clean text first
        text = ' '.join(text.split())
        
        # Split into sentences to avoid cutting mid-sentence
        sentences = text.split('. ')
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed the limit, start a new segment
            if len(current_segment) + len(sentence) + 2 > max_chars_per_segment and current_segment:
                segments.append(current_segment.strip())
                current_segment = sentence + ". "
            else:
                current_segment += sentence + ". "
        
        # Add the last segment
        if current_segment.strip():
            segments.append(current_segment.strip())
        
        logger.info(f"Split text into {len(segments)} segments")
        return segments

    async def convert_segment_to_audio(self, segment_text: str, voice: str, output_path: str):
        """Convert a text segment to audio"""
        try:
            # Further split segment into TTS-friendly chunks
            max_chars = 3000
            chunks = [segment_text[i:i + max_chars] for i in range(0, len(segment_text), max_chars)]
            
            combined = AudioSegment.empty()
            temp_files = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{uuid4().hex[:8]}"
                temp_path = os.path.join(tempfile.gettempdir(), f"temp_chunk_{chunk_id}.mp3")
                temp_files.append(temp_path)

                try:
                    # Generate audio for this chunk
                    communicate = edge_tts.Communicate(chunk, voice)
                    await communicate.save(temp_path)

                    if os.path.exists(temp_path):
                        segment = AudioSegment.from_file(temp_path, format="mp3")
                        combined += segment
                except Exception as e:
                    logger.error(f"Error processing chunk {i + 1} in segment: {e}")
                    continue

            # Save the combined segment
            if len(combined) > 0:
                combined.export(output_path, format="mp3")
                logger.info(f"Segment saved: {output_path} ({len(combined)/1000:.1f}s)")
            else:
                logger.error(f"No audio generated for segment: {output_path}")

            # Clean up temp files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_file}: {e}")

        except Exception as e:
            logger.error(f"Error converting segment to audio: {e}")

    async def convert_with_voice_chunked(self, pdf_path: str, voice: str, job_id: str):
        """Convert PDF to MP3 with chunked output"""
        logger.info(f"Starting chunked conversion with voice '{voice}' for: {pdf_path}")
        
        if voice not in self.voices:
            raise ValueError(f"Invalid voice '{voice}'. Available: {list(self.voices.keys())}")
        
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"File {pdf_path} not found")

        # Extract text
        text = self.extract_text(pdf_path)
        if not text:
            raise ValueError(f"No text found in {pdf_path}")

        # Create chunks directory
        safe_name = os.path.splitext(os.path.basename(pdf_path))[0]
        chunks_dir = os.path.join(self.output_dir, f"{job_id}_chunks")
        os.makedirs(chunks_dir, exist_ok=True)

        # Split text into segments (each will become a chunk)
        segments = self.split_text_into_segments(text, max_chars_per_segment=15000)
        selected_voice = self.voices[voice]

        logger.info(f"Converting {len(segments)} segments to audio chunks")

        # Process each segment
        for i, segment in enumerate(segments):
            logger.info(f"Processing segment {i + 1}/{len(segments)}")
            
            chunk_filename = f"chunk_{i:03d}.mp3"
            chunk_path = os.path.join(chunks_dir, chunk_filename)
            
            await self.convert_segment_to_audio(segment, selected_voice, chunk_path)
            
            # Verify chunk was created
            if not os.path.exists(chunk_path):
                logger.error(f"Failed to create chunk {i}")
                continue

        # Verify chunks were created
        chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".mp3")]
        if not chunk_files:
            raise ValueError("No audio chunks were generated")

        total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
        logger.info(f"✅ Chunked audio conversion completed!")
        logger.info(f"   Chunks directory: {chunks_dir}")
        logger.info(f"   Total chunks: {len(chunk_files)}")
        logger.info(f"   Total size: {total_size / (1024*1024):.2f} MB")

        return chunks_dir

    async def convert_with_voice(self, pdf_path: str, voice: str):
        """Convert PDF to MP3 with specified voice (original method for backward compatibility)"""
        logger.info(f"Starting conversion with voice '{voice}' for: {pdf_path}")
        
        if voice not in self.voices:
            raise ValueError(f"Invalid voice '{voice}'. Available: {list(self.voices.keys())}")
        
        await self.convert_async(pdf_path, voice)

    async def convert_async(self, file_path: str, voice: str = "male"):
        """Convert PDF to MP3 asynchronously (original method)"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        logger.info(f"Starting conversion of: {file_path}")
        
        # Extract text
        text = self.extract_text(file_path)
        if not text:
            raise ValueError(f"No text found in {file_path}")

        # Clean text (remove excessive whitespace, etc.)
        text = ' '.join(text.split())
        logger.info(f"Cleaned text length: {len(text)} characters")

        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file_path))[0]
        final_output_path = os.path.join(self.output_dir, f"{safe_name}.mp3")

        # Remove existing file if it exists
        if os.path.exists(final_output_path):
            os.remove(final_output_path)

        # Split text into chunks
        max_chars = 3000
        chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
        logger.info(f"Split into {len(chunks)} chunks for processing")

        combined = AudioSegment.empty()
        temp_files = []

        try:
            # Process chunks with progress logging
            for i, chunk in enumerate(chunks):
                if i % 5 == 0:  # Log progress every 5 chunks
                    logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
                
                chunk_id = f"{uuid4().hex[:8]}"
                temp_path = os.path.join(tempfile.gettempdir(), f"{safe_name}_{chunk_id}.mp3")
                temp_files.append(temp_path)

                try:
                    # Generate audio for this chunk
                    communicate = edge_tts.Communicate(chunk, selected_voice)
                    await communicate.save(temp_path)

                    if not os.path.exists(temp_path):
                        logger.warning(f"Chunk {i + 1} not generated, skipping")
                        continue

                    # Load and combine audio
                    segment = AudioSegment.from_file(temp_path, format="mp3")
                    combined += segment

                except Exception as e:
                    logger.error(f"Error processing chunk {i + 1}: {e}")
                    continue

            if len(combined) == 0:
                raise ValueError("No audio was generated from any chunks")

            # Export final audio
            logger.info(f"Exporting final audio to: {final_output_path}")
            combined.export(final_output_path, format="mp3")
            
            # Verify the file was created and has content
            if not os.path.exists(final_output_path):
                raise ValueError("Final MP3 file was not created")
                
            file_size = os.path.getsize(final_output_path)
            if file_size == 0:
                raise ValueError("Final MP3 file is empty")
                
            duration_seconds = len(combined) / 1000.0
            logger.info(f"✅ Audio conversion completed successfully!")
            logger.info(f"   File: {final_output_path}")
            logger.info(f"   Size: {file_size / (1024*1024):.2f} MB")
            logger.info(f"   Duration: {duration_seconds / 60:.1f} minutes")

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_file}: {e}")
