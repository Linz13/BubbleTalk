from flask import request, jsonify
import os
import tempfile
import sys

class WhisperEndpoints:
    """API endpoints for Whisper speech recognition"""
    
    def __init__(self, app, whisper_manager):
        self.app = app
        self.whisper_manager = whisper_manager
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all Whisper API endpoints"""
        self.app.route('/transcribe', methods=['POST'])(self.transcribe_endpoint)
    
    def transcribe_endpoint(self):
        """API endpoint to transcribe uploaded audio"""
        try:
            if 'audio' not in request.files:
                return jsonify({'error': 'Audio file required'}), 400
                
            audio_file = request.files['audio']
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp:
                temp_path = temp.name
                audio_file.save(temp_path)
            
            # Transcribe
            print(f"Transcribing uploaded audio: {temp_path}", file=sys.stderr)
            transcription = self.whisper_manager.transcribe(temp_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return jsonify({'transcription': transcription})
        except Exception as e:
            error_msg = f"Error processing audio: {str(e)}"
            print(error_msg, file=sys.stderr)
            return jsonify({'error': error_msg}), 500