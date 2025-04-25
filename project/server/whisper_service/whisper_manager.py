import whisper
import sys
from ..config import WHISPER_MODEL_SIZE

class WhisperManager:
    """Manager for Whisper speech recognition model"""
    
    def __init__(self, model_size=WHISPER_MODEL_SIZE):
        self.model_size = model_size
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Whisper model"""
        print(f"Loading Whisper {self.model_size} model...", file=sys.stderr)
        try:
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded successfully", file=sys.stderr)
        except Exception as e:
            print(f"Error loading Whisper model: {str(e)}", file=sys.stderr)
            raise
    
    def transcribe(self, audio_path):
        """Transcribe audio using Whisper model"""
        if self.model is None:
            raise ValueError("Whisper model not initialized")
            
        print(f"Transcribing audio: {audio_path}", file=sys.stderr)
        try:
            result = self.model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}", file=sys.stderr)
            raise