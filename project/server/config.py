import os
import time

# Path configurations
REF_AUDIO_DIR = "/mnt/data6t/zhiyu/NLP/test/ref_audio"
SAMPLE_AUDIO_DIR = "/mnt/data6t/zhiyu/NLP/test/sample_audio"
DEFAULT_OUTPUT_DIR = f"/mnt/data6t/zhiyu/NLP/test/audio_gen/{time.strftime('%Y%m%d-%H%M%S')}"

# Model configurations
COSYVOICE_MODEL_PATH = "/mnt/data6t/zhiyu/NLP/test/pretrained_models/CosyVoice2-0.5B"
WHISPER_MODEL_SIZE = "small"

# API configurations
LLM_API_HOST = "127.0.0.1"
LLM_API_PORT = 5001
WHISPER_API_HOST = "127.0.0.1"
WHISPER_API_PORT = 5000

# LLM configurations
OPENAI_API_KEY = "sk-wkjhRLLsrokTbAKuA0TF8Z0EBZvxbBk6vpSPxknC5VDiFtzn"
OPENAI_API_BASE = "https://xiaoai.plus/v1"
DEEPSEEK_API_KEY = "sk-d7f3c72d43d847138787a493df4c68c0"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v3"

# Default system prompt
DEFAULT_SYSTEM_PROMPT = (
    "【儿童互动模式】你是一个7岁中国小朋友,名字叫小智\n"
    "请和儿童交流，不加动作：\n"
    "1. 句子简短（不超过10字）\n"
    "2. 用比喻解释知识：如'月亮是天空的夜灯'\n"
    "3. 主动提问互动：如'猜猜熊猫为什么黑眼圈？'\n"
    "注意：禁用复杂词汇，保持像二年级小学生的语言能力！"
)

# Voice configurations
EMOTION_AUDIO_MAP = {
    "happy": os.path.join(REF_AUDIO_DIR, "cheerful.mp3"),
    "cheerful": os.path.join(REF_AUDIO_DIR, "cheerful.mp3"),
    "excited": os.path.join(REF_AUDIO_DIR, "cheerful.mp3"),
    "sad": os.path.join(REF_AUDIO_DIR, "sad.mp3"),
    "anxious": os.path.join(REF_AUDIO_DIR, "sad.mp3"),
    "comforting": os.path.join(REF_AUDIO_DIR, "comforting.mp3"),
    "neutral": os.path.join(REF_AUDIO_DIR, "audio_0.mp3"),
    "curious": os.path.join(REF_AUDIO_DIR, "audio_0.mp3"),
    "serious": os.path.join(REF_AUDIO_DIR, "serious.mp3")
}

VOICE_SAMPLE_MAP = {
    "default": os.path.join(SAMPLE_AUDIO_DIR, "default.mp3"),
    "cheerful": os.path.join(SAMPLE_AUDIO_DIR, "cheerful.mp3"),
    "sad": os.path.join(SAMPLE_AUDIO_DIR, "sad.mp3"),
    "comforting": os.path.join(SAMPLE_AUDIO_DIR, "comforting.mp3"),
    "serious": os.path.join(SAMPLE_AUDIO_DIR, "serious.mp3")
}

# Memory configurations
MAX_HISTORY_TURNS = 3