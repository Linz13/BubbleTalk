from flask import request, jsonify

class MemoryEndpoints:
    """API endpoints for memory functionality"""
    
    def __init__(self, app, memory_manager):
        self.app = app
        self.memory_manager = memory_manager
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all memory API endpoints"""
        self.app.route('/memory/<session_id>', methods=['GET'])(self.get_memory_endpoint)
        self.app.route('/memory/<session_id>/reset', methods=['POST'])(self.reset_memory_endpoint)
        self.app.route('/history/<session_id>', methods=['GET'])(self.get_history_endpoint)
        self.app.route('/set_voice', methods=['POST'])(self.set_voice_endpoint)
    
    def get_memory_endpoint(self, session_id):
        """API endpoint to get memory for a session"""
        try:
            memory = self.memory_manager.load_memory(session_id)
            return jsonify(memory)
        except Exception as e:
            return jsonify({'error': f"Failed to get memory: {str(e)}"}), 500
    
    def reset_memory_endpoint(self, session_id):
        """API endpoint to reset memory for a session"""
        try:
            self.memory_manager.reset_memory(session_id)
            return jsonify({"success": True, "message": "Memory reset successfully"})
        except Exception as e:
            return jsonify({'error': f"Failed to reset memory: {str(e)}"}), 500
    
    def get_history_endpoint(self, session_id):
        """API endpoint to get conversation history for a session"""
        try:
            history = self.memory_manager.load_history(session_id)
            return jsonify(history)
        except Exception as e:
            return jsonify({'error': f"Failed to get history: {str(e)}"}), 500
    
    def set_voice_endpoint(self):
        """API endpoint to set voice preference for a session"""
        if not request.json or 'voice' not in request.json:
            return jsonify({'error': 'Voice type required'}), 400
        
        voice_type = request.json['voice']
        session_id = request.json.get('session_id', '')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
            
        try:
            # Load memory
            memory = self.memory_manager.load_memory(session_id)
            
            # Update voice preference
            memory['voice_preference'] = voice_type
            
            # Save updated memory
            self.memory_manager.save_memory(session_id, memory)
            
            return jsonify({
                'success': True, 
                'message': f'Voice set to: {voice_type}'
            })
        except Exception as e:
            return jsonify({'error': f"Failed to set voice: {str(e)}"}), 500