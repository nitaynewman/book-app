import os
import asyncio
import tempfile
import edge_tts
import pdfplumber
from uuid import uuid4
from pydub import AudioSegment
import logging

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

    def clean_text(self, text: str) -> str:
        """Clean and prepare text for TTS conversion"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove problematic characters that might cause TTS issues
        # Keep basic punctuation for natural speech
        import re
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']+', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    async def convert_async(self, file_path: str, voice: str = "male"):
        """Convert PDF to MP3 asynchronously"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        logger.info(f"Starting conversion of: {file_path}")
        
        # Extract text
        text = self.extract_text(file_path)
        if not text:
            raise ValueError(f"No text found in {file_path}")

        # Clean text for better TTS processing
        text = self.clean_text(text)
        logger.info(f"Cleaned text length: {len(text)} characters")

        if len(text) < 100:
            raise ValueError(f"Text too short for conversion: {len(text)} characters")

        selected_voice = self.voices.get(voice, "en-US-GuyNeural")
        safe_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Sanitize filename
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_name:
            safe_name = f"audiobook_{uuid4().hex[:8]}"
            
        final_output_path = os.path.join(self.output_dir, f"{safe_name}.mp3")

        # Remove existing file if it exists
        if os.path.exists(final_output_path):
            try:
                os.remove(final_output_path)
                logger.info(f"Removed existing file: {final_output_path}")
            except Exception as e:
                logger.warning(f"Could not remove existing file: {e}")

        # Split text into manageable chunks
        max_chars = 2500  # Smaller chunks for better reliability
        chunks = []
        
        # Split by sentences first, then by character limit
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed limit, save current chunk
            if len(current_chunk + sentence) > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        logger.info(f"Split into {len(chunks)} chunks for processing")

        if not chunks:
            raise ValueError("No valid text chunks created")

        combined = AudioSegment.empty()
        temp_files = []
        successful_chunks = 0

        try:
            # Process chunks with progress logging
            for i, chunk in enumerate(chunks):
                try:
                    if i % 5 == 0:  # Log progress every 5 chunks
                        logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
                    
                    if not chunk.strip():
                        logger.warning(f"Skipping empty chunk {i + 1}")
                        continue
                    
                    chunk_id = f"{uuid4().hex[:8]}"
                    temp_path = os.path.join(tempfile.gettempdir(), f"{safe_name}_{chunk_id}.mp3")
                    temp_files.append(temp_path)

                    # Generate audio for this chunk with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            communicate = edge_tts.Communicate(chunk, selected_voice)
                            await communicate.save(temp_path)
                            break
                        except Exception as e:
                            logger.warning(f"Attempt {attempt + 1} failed for chunk {i + 1}: {e}")
                            if attempt == max_retries - 1:
                                raise e
                            await asyncio.sleep(1)  # Brief delay before retry

                    if not os.path.exists(temp_path):
                        logger.warning(f"Chunk {i + 1} not generated, skipping")
                        continue

                    # Verify file size
                    if os.path.getsize(temp_path) == 0:
                        logger.warning(f"Chunk {i + 1} is empty, skipping")
                        continue

                    # Load and combine audio
                    try:
                        segment = AudioSegment.from_file(temp_path, format="mp3")
                        if len(segment) > 0:  # Only add non-empty segments
                            combined += segment
                            successful_chunks += 1
                        else:
                            logger.warning(f"Chunk {i + 1} has no audio content")
                    except Exception as e:
                        logger.warning(f"Error loading chunk {i + 1}: {e}")
                        continue

                except Exception as e:
                    logger.error(f"Error processing chunk {i + 1}: {e}")
                    continue

            if len(combined) == 0:
                raise ValueError(f"No audio was generated from any chunks. Successful chunks: {successful_chunks}/{len(chunks)}")

            if successful_chunks < len(chunks) * 0.5:  # Less than 50% success rate
                logger.warning(f"Only {successful_chunks}/{len(chunks)} chunks processed successfully")

            # Export final audio
            logger.info(f"Exporting final audio to: {final_output_path}")
            combined.export(final_output_path, format="mp3", bitrate="64k")  # Lower bitrate for smaller files
            
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
            logger.info(f"   Successful chunks: {successful_chunks}/{len(chunks)}")

        except Exception as e:
            # Clean up partial file on error
            if os.path.exists(final_output_path):
                try:
                    os.remove(final_output_path)
                except:
                    pass
            raise e

        finally:
            # Clean up temporary files
            cleanup_count = 0
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        cleanup_count += 1
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_file}: {e}")
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} temporary files")

    async def convert_with_voice(self, pdf_path: str, voice: str):
        """Convert PDF to MP3 with specified voice"""
        logger.info(f"Starting conversion with voice '{voice}' for: {pdf_path}")
        
        if voice not in self.voices:
            raise ValueError(f"Invalid voice '{voice}'. Available: {list(self.voices.keys())}")
        
        await self.convert_async(pdf_path, voice)
