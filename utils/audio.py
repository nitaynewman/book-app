import os
import asyncio
import tempfile
import edge_tts
import pdfplumber
from uuid import uuid4
from pydub import AudioSegment
import logging
import math
import gc
from typing import Optional, Callable

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
        """Extract text from PDF file with better memory management"""
        try:
            logger.info(f"Extracting text from: {file_path}")
            pages_text = []
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    if i % 10 == 0:  # Log progress every 10 pages
                        logger.info(f"Processing page {i+1}/{total_pages}")
                    
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            # Clean and normalize text
                            cleaned_text = ' '.join(text.split())
                            pages_text.append(cleaned_text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {i+1}: {e}")
                        continue
                
                full_text = "\n".join(pages_text).strip()
                logger.info(f"Extracted {len(full_text)} characters from {len(pages_text)} pages")
                
                # Clean up memory
                pages_text.clear()
                gc.collect()
                
                return full_text
                
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    def split_text_into_segments(self, text: str, max_chars_per_segment: int = 12000) -> list:
        """Split text into segments optimized for chunked processing"""
        # Clean text first
        text = ' '.join(text.split())
        
        # If text is small enough, return as single segment
        if len(text) <= max_chars_per_segment:
            return [text]
        
        # Split into sentences to avoid cutting mid-sentence
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed the limit, start a new segment
            if len(current_segment) + len(sentence) + 2 > max_chars_per_segment and current_segment:
                segments.append(current_segment.strip())
                current_segment = sentence + ". "
            else:
                current_segment += sentence + ". "
        
        # Add the last segment
        if current_segment.strip():
            segments.append(current_segment.strip())
        
        logger.info(f"Split text into {len(segments)} segments (avg {len(text)//len(segments)} chars each)")
        return segments

    async def convert_segment_to_audio(self, segment_text: str, voice: str, output_path: str, segment_index: int = 0):
        """Convert a text segment to audio with better error handling"""
        try:
            # Further split segment into TTS-friendly chunks if needed
            max_chars = 2500  # Smaller chunks for more reliable TTS
            if len(segment_text) <= max_chars:
                chunks = [segment_text]
            else:
                # Split by sentences first, then by length if needed
                sentences = segment_text.split('. ')
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_chars:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            
            combined = AudioSegment.empty()
            temp_files = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{uuid4().hex[:8]}"
                temp_path = os.path.join(tempfile.gettempdir(), f"temp_seg{segment_index}_chunk_{chunk_id}.mp3")
                temp_files.append(temp_path)

                try:
                    # Generate audio for this chunk with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            communicate = edge_tts.Communicate(chunk, voice)
                            await communicate.save(temp_path)
                            
                            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                                break
                            else:
                                logger.warning(f"Attempt {attempt + 1} failed for chunk {i + 1} in segment {segment_index}")
                                
                        except Exception as e:
                            logger.warning(f"TTS attempt {attempt + 1} failed: {e}")
                            if attempt == max_retries - 1:
                                raise e
                            await asyncio.sleep(1)  # Wait before retry

                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        segment = AudioSegment.from_file(temp_path, format="mp3")
                        combined += segment
                        # Add a small pause between chunks
                        if i < len(chunks) - 1:
                            pause = AudioSegment.silent(duration=200)  # 200ms pause
                            combined += pause
                    else:
                        logger.error(f"Failed to generate audio for chunk {i + 1} in segment {segment_index}")
                        
                except Exception as e:
                    logger.error(f"Error processing chunk {i + 1} in segment {segment_index}: {e}")
                    continue

            # Save the combined segment
            if len(combined) > 0:
                combined.export(output_path, format="mp3", bitrate="64k")  # Use lower bitrate to save space
                duration_seconds = len(combined) / 1000.0
                logger.info(f"Segment {segment_index} saved: {output_path} ({duration_seconds:.1f}s)")
            else:
                logger.error(f"No audio generated for segment {segment_index}")

            # Clean up temp files immediately
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_file}: {e}")

            # Force garbage collection
            del combined
            gc.collect()

        except Exception as e:
            logger.error(f"Error converting segment {segment_index} to audio: {e}")
            raise

    async def convert_with_voice_chunked(self, pdf_path: str, voice: str, job_id: str, 
                                       progress_callback: Optional[Callable[[int], None]] = None):
        """Convert PDF to MP3 with chunked output and progress tracking"""
        logger.info(f"Starting chunked conversion with voice '{voice}' for: {pdf_path}")
        
        if voice not in self.voices:
            raise ValueError(f"Invalid voice '{voice}'. Available: {list(self.voices.keys())}")
        
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"File {pdf_path} not found")

        try:
            # Extract text
            if progress_callback:
                progress_callback(50)
            
            text = self.extract_text(pdf_path)
            if not text:
                raise ValueError(f"No text found in {pdf_path}")

            # Create chunks directory
            safe_name = os.path.splitext(os.path.basename(pdf_path))[0]
            chunks_dir = os.path.join(self.output_dir, f"{job_id}_chunks")
            os.makedirs(chunks_dir, exist_ok=True)

            # Split text into segments (each will become a chunk)
            segments = self.split_text_into_segments(text, max_chars_per_segment=10000)  # Smaller segments
            selected_voice = self.voices[voice]

            logger.info(f"Converting {len(segments)} segments to audio chunks")

            if progress_callback:
                progress_callback(60)

            # Process each segment
            for i, segment in enumerate(segments):
                logger.info(f"Processing segment {i + 1}/{len(segments)}")
                
                chunk_filename = f"chunk_{i:03d}.mp3"
                chunk_path = os.path.join(chunks_dir, chunk_filename)
                
                try:
                    await self.convert_segment_to_audio(segment, selected_voice, chunk_path, i)
                    
                    # Update progress
                    if progress_callback:
                        segment_progress = 60 + ((i + 1) / len(segments)) * 35  # 60-95%
                        progress_callback(int(segment_progress))
                    
                    # Verify chunk was created
                    if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                        logger.error(f"Failed to create valid chunk {i}")
                        # Try once more
                        try:
                            await self.convert_segment_to_audio(segment, selected_voice, chunk_path, i)
                        except:
                            logger.error(f"Retry failed for chunk {i}, skipping")
                            continue
                
                except Exception as e:
                    logger.error(f"Error processing segment {i}: {e}")
                    continue

            # Verify chunks were created
            chunk_files = [f for f in os.listdir(chunks_dir) 
                          if f.startswith("chunk_") and f.endswith(".mp3") 
                          and os.path.getsize(os.path.join(chunks_dir, f)) > 0]
            
            if not chunk_files:
                raise ValueError("No valid audio chunks were generated")

            # Sort chunks to ensure proper order
            chunk_files.sort()

            total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
            logger.info(f"✅ Chunked audio conversion completed!")
            logger.info(f"   Chunks directory: {chunks_dir}")
            logger.info(f"   Total chunks: {len(chunk_files)}")
            logger.info(f"   Total size: {total_size / (1024*1024):.2f} MB")

            if progress_callback:
                progress_callback(95)

            return chunks_dir

        except Exception as e:
            logger.error(f"Error in chunked conversion: {e}")
            # Clean up partial chunks directory if it exists
            if 'chunks_dir' in locals() and os.path.exists(chunks_dir):
                try:
                    import shutil
                    shutil.rmtree(chunks_dir)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up failed conversion directory: {cleanup_error}")
            raise

    async def convert_with_voice(self, pdf_path: str, voice: str):
        """Convert PDF to MP3 with specified voice (original method for backward compatibility)"""
        logger.info(f"Starting conversion with voice '{voice}' for: {pdf_path}")
        
        if voice not in self.voices:
            raise ValueError(f"Invalid voice '{voice}'. Available: {list(self.voices.keys())}")
        
        await self.convert_async(pdf_path, voice)

    async def convert_async(self, file_path: str, voice: str = "male"):
        """Convert PDF to MP3 asynchronously (original method with improvements)"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        logger.info(f"Starting conversion of: {file_path}")
        
        try:
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

            # Split text into smaller chunks for better reliability
            max_chars = 2500
            chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
            logger.info(
