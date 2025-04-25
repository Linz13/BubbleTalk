import os
import argparse
import asyncio
from flask import Flask, send_file
from flask_cors import CORS
from hypercorn.asyncio import serve
from hypercorn.config import Config
import logging
import sys
print(sys.path)

# Import services
# from llm_service.llm_manager import LLMManager
from server.llm_service.llm_manager import LLMManager
from server.tts_service.tts_manager import TTSManager
from server.tts_service.voice_selector import VoiceSelector
from server.whisper_service.whisper_manager import WhisperManager
from server.llm_service.memory import MemoryManager

# Import API endpoints
from server.api.llm_api import LLMEndpoints
from server.api.memory_api import MemoryEndpoints
from server.api.whisper_api import WhisperEndpoints

# Import configuration
from server.config import (
    LLM_API_HOST, LLM_API_PORT, 
    WHISPER_API_HOST, WHISPER_API_PORT,
    DEFAULT_OUTPUT_DIR, DEFAULT_SYSTEM_PROMPT,
    COSYVOICE_MODEL_PATH, WHISPER_MODEL_SIZE
)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    @app.route("/transcribe")
    def transcribe():
        result = some_function()
        logging.info(f"Response type: {type(result)}")
        return result

    @app.route('/audio/<path:filename>')
    def serve_audio(filename):
        """Serve audio files"""
        # Find audio file in output directory
        for root, dirs, files in os.walk(DEFAULT_OUTPUT_DIR):
            for file in files:
                if file == filename:
                    return send_file(os.path.join(root, file))
        
        return jsonify({'error': f'Audio file {filename} not found'}), 404
    
    return app

async def main(args):
    """Main function to run the server"""
    # Create Flask app
    app = create_app()
    
    # Initialize core services
    llm_manager = LLMManager(args.llm)
    tts_manager = TTSManager(args.model_path, args.ref_text)
    voice_selector = VoiceSelector()
    memory_manager = MemoryManager(args.output_folder, args.max_history_turns)
    
    # Register LLM API endpoints
    LLMEndpoints(app, llm_manager, memory_manager, tts_manager, voice_selector, args.output_folder)
    
    # Register Memory API endpoints
    MemoryEndpoints(app, memory_manager)
    
    # Configure server
    config = Config()
    config.bind = [f"{args.host}:{args.port}"]
    
    # Start server
    print(f"Starting server on {args.host}:{args.port}", file=sys.stderr)
    await serve(app, config)

def start_whisper_server(args):
    """Start the Whisper server as a separate process"""
    # Create Flask app for Whisper
    whisper_app = Flask("whisper_api")
    CORS(whisper_app)
    
    # Initialize Whisper service
    whisper_manager = WhisperManager(args.whisper_model)
    
    # Register Whisper API endpoints
    WhisperEndpoints(whisper_app, whisper_manager)
    
    # Start Whisper server
    print(f"Starting Whisper server on {args.whisper_host}:{args.whisper_port}", file=sys.stderr)
    whisper_app.run(host=args.whisper_host, port=args.whisper_port)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Conversational AI with TTS and Voice Recognition')
    
    # LLM-TTS server arguments
    parser.add_argument('--model-path', type=str, default=COSYVOICE_MODEL_PATH,
                        help='CosyVoice2 model path')
    parser.add_argument('--ref-text', type=str,
                        default='请说一段经典的相声，题材可以是关于医生和病人的趣事。',
                        help='Reference text for TTS')
    parser.add_argument('--system-prompt', type=str,
                        default=DEFAULT_SYSTEM_PROMPT,
                        help='System prompt for LLM')
    parser.add_argument('--output-folder', type=str,
                        default=DEFAULT_OUTPUT_DIR,
                        help='Output folder for audio files')
    parser.add_argument('--llm', type=str, default='deepseek', choices=['gpt', 'deepseek'],
                        help='LLM model to use (gpt or deepseek)')
    parser.add_argument('--host', type=str, default=LLM_API_HOST,
                        help='LLM-TTS server host')
    parser.add_argument('--port', type=int, default=LLM_API_PORT,
                        help='LLM-TTS server port')
    parser.add_argument('--max-history-turns', type=int, default=3,
                        help='Maximum conversation turns to keep in history')
    
    # Whisper server arguments
    parser.add_argument('--whisper-model', type=str, default=WHISPER_MODEL_SIZE,
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size')
    parser.add_argument('--whisper-host', type=str, default=WHISPER_API_HOST,
                        help='Whisper server host')
    parser.add_argument('--whisper-port', type=int, default=WHISPER_API_PORT,
                        help='Whisper server port')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Start Whisper server in a separate process
    import multiprocessing
    whisper_process = multiprocessing.Process(target=start_whisper_server, args=(args,))
    whisper_process.start()
    
    # Start LLM-TTS server
    asyncio.run(main(args))