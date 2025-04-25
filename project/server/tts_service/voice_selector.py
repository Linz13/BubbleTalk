from cosyvoice.utils.file_utils import load_wav
from ..config import EMOTION_AUDIO_MAP, VOICE_SAMPLE_MAP

class VoiceSelector:
    """Manager for selecting appropriate voice samples"""
    
    def __init__(self):
        self.emotion_map = EMOTION_AUDIO_MAP
        self.voice_sample_map = VOICE_SAMPLE_MAP
    
    def get_emotion_audio(self, emotion):
        """Get reference audio for detected emotion"""
        emotion_lower = emotion.lower()
        path = self.emotion_map.get(emotion_lower, self.emotion_map["neutral"])
        return load_wav(path, 16000)
    
    def get_voice_sample(self, voice_type):
        """Get reference audio for selected voice type"""
        voice_lower = voice_type.lower() if voice_type else "default"
        path = self.voice_sample_map.get(voice_lower, self.voice_sample_map["default"])
        return load_wav(path, 16000)
    
    def select_voice(self, session_memory, detected_emotion):
        """Select appropriate voice based on preference or emotion"""
        # Preference takes precedence over detected emotion
        voice_preference = session_memory.get("voice_preference")
        
        if voice_preference:
            return self.get_voice_sample(voice_preference)
        else:
            return self.get_emotion_audio(detected_emotion)