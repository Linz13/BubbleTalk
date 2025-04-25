import sys
import os
import time
import asyncio
import torchaudio
from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav
from ..config import COSYVOICE_MODEL_PATH

class TTSManager:
    """Manager for CosyVoice2 TTS model"""
    
    def __init__(self, model_path=COSYVOICE_MODEL_PATH, ref_text=None):
        self.model_path = model_path
        self.ref_text = ref_text or "请说一段经典的相声，题材可以是关于医生和病人的趣事。"
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize CosyVoice2 model"""
        print(f"Initializing CosyVoice2 model: {self.model_path}", file=sys.stderr)
        try:
            self.model = CosyVoice2(
                self.model_path,
                load_jit=False,
                load_trt=False,
                fp16=False,
                use_flow_cache=True
            )
            print("CosyVoice2 model initialized", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing CosyVoice2 model: {str(e)}", file=sys.stderr)
            raise
    
    async def generate_speech(self, text, ref_audio, output_dir, filename_prefix="tts"):
        """Generate speech for given text using reference audio"""
        if self.model is None:
            raise ValueError("TTS model not initialized")
        
        os.makedirs(output_dir, exist_ok=True)
        output_paths = []
        
        def tts_run():
            for i, result in enumerate(self.model.inference_zero_shot(
                text,
                self.ref_text,
                ref_audio,
                stream=True
            )):
                # Save to file
                file_path = os.path.join(output_dir, f"{filename_prefix}_part_{i}.wav")
                torchaudio.save(file_path, result["tts_speech"], self.model.sample_rate)
                output_paths.append(file_path)
        
        # Run TTS in thread pool to avoid blocking async loop
        await asyncio.to_thread(tts_run)
        
        # Return path to the last file (complete speech)
        return output_paths[-1] if output_paths else None