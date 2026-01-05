"""Whisper audio transcription service"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperService:
    """Service for audio transcription using OpenAI Whisper"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        base_url: Optional[str] = None
    ):
        """
        Initialize Whisper service
        
        Args:
            api_key: OpenAI API key
            model: Whisper model to use (default: whisper-1)
            base_url: Optional base URL for API (for local Whisper servers)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"Whisper service initialized with model: {model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
    
    async def transcribe(
        self,
        audio_file,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_file: File-like object with audio data
            language: Optional language code (e.g., 'ru', 'en')
            prompt: Optional prompt to guide transcription
            
        Returns:
            Transcribed text
        """
        try:
            logger.info(f"Starting audio transcription with model {self.model}")
            
            # Prepare transcription parameters
            params = {
                "model": self.model,
                "file": audio_file,
            }
            
            if language:
                params["language"] = language
            
            if prompt:
                params["prompt"] = prompt
            
            # Call Whisper API
            response = await self.client.audio.transcriptions.create(**params)
            
            transcribed_text = response.text
            logger.info(f"Transcription successful: {len(transcribed_text)} characters")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise
    
    async def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Filename for the audio (important for format detection)
            language: Optional language code
            prompt: Optional prompt to guide transcription
            
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
                # Open and transcribe
                with open(temp_path, 'rb') as audio_file:
                    result = await self.transcribe(
                        audio_file=audio_file,
                        language=language,
                        prompt=prompt
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
_whisper_service: Optional[WhisperService] = None


def get_whisper_service() -> WhisperService:
    """Get or create Whisper service instance"""
    global _whisper_service
    
    if _whisper_service is None:
        from config import settings
        
        _whisper_service = WhisperService(
            api_key=settings.whisper_api_key or settings.llm_api_key,
            model=settings.whisper_model,
            base_url=settings.whisper_base_url
        )
    
    return _whisper_service
