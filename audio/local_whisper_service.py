"""Local Whisper service using faster-whisper library"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalWhisperService:
    """Service for audio transcription using local Whisper model"""
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize local Whisper service
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to use (cpu, cuda)
            compute_type: Compute type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
        logger.info(f"Initializing local Whisper service with model: {model_size}")
        
    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                
                logger.info(f"Loading Whisper model {self.model_size} on {self.device}...")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                logger.info("Whisper model loaded successfully")
                
            except ImportError:
                logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
                raise RuntimeError(
                    "faster-whisper not installed. "
                    "Install with: pip install faster-whisper"
                )
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
                raise
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'ru', 'en')
            
        Returns:
            Transcribed text
        """
        try:
            self._load_model()
            
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_file_path,
                language=language,
                beam_size=5,
                vad_filter=True  # Voice activity detection
            )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            logger.info(f"Transcription successful: {len(text)} characters, detected language: {info.language}")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise
    
    async def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Filename for the audio (important for format detection)
            language: Optional language code
            
        Returns:
            Transcribed text
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=Path(filename).suffix,
                delete=False
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Transcribe
                result = await self.transcribe(
                    audio_file_path=temp_path,
                    language=language
                )
                return result
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Transcription from bytes error: {e}", exc_info=True)
            raise


# Singleton instance
_local_whisper_service: Optional[LocalWhisperService] = None


def get_local_whisper_service() -> LocalWhisperService:
    """Get or create local Whisper service instance"""
    global _local_whisper_service
    
    if _local_whisper_service is None:
        from config import settings
        
        # Determine model size from config
        model_size = settings.whisper_model
        if model_size == "whisper-1":
            # Map OpenAI model name to local model size
            model_size = "base"  # or "small", "medium" depending on your needs
        
        _local_whisper_service = LocalWhisperService(
            model_size=model_size,
            device="cpu",  # Change to "cuda" if you have GPU
            compute_type="int8"  # Fast on CPU
        )
    
    return _local_whisper_service
