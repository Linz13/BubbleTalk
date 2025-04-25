from flask import request, jsonify, Response, stream_with_context
import json
import time
import asyncio
import sys

class LLMEndpoints:
    """API endpoints for LLM functionality"""
    
    def __init__(self, app, llm_manager, memory_manager, tts_manager, voice_selector, output_folder):
        self.app = app
        self.llm_manager = llm_manager
        self.memory_manager = memory_manager
        self.tts_manager = tts_manager
        self.voice_selector = voice_selector
        self.output_folder = output_folder
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all LLM API endpoints"""
        self.app.route('/process', methods=['POST'])(self.process_endpoint)
        self.app.route('/stream_response', methods=['POST'])(self.stream_response_endpoint)
    
    async def process_endpoint(self):
        """API endpoint for processing user input without streaming"""
        if not request.json or 'text' not in request.json:
            return jsonify({'error': 'Input text required'}), 400
        
        user_input = request.json['text']
        session_id = request.json.get('session_id', time.strftime('%Y%m%d-%H%M%S'))
        
        try:
            # Load memory and history
            memory = self.memory_manager.load_memory(session_id)
            history = self.memory_manager.load_history(session_id)
            
            # Build prompt with context
            system_prompt = self._build_system_prompt(memory, history)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Generate response
            llm_response = await self.llm_manager.generate_response(messages)
            
            # Update conversation history
            self.memory_manager.update_history(session_id, user_input, llm_response)
            
            # Extract memory and detect emotion
            emotion = await self.memory_manager.extract_and_update_memory(
                self.llm_manager, user_input, llm_response, session_id
            )
            
            # Select voice based on emotion or preference
            ref_audio = self.voice_selector.select_voice(memory, emotion)
            
            # Generate speech
            session_folder = f"{self.output_folder}/{session_id}"
            audio_path = await self.tts_manager.generate_speech(
                llm_response, 
                ref_audio,
                session_folder,
                f"response_{int(time.time())}"
            )
            
            return jsonify({
                'llm_response': llm_response,
                'audio_path': audio_path
            })
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg, file=sys.stderr)
            return jsonify({'error': error_msg}), 500
    
    async def stream_response_endpoint(self):
        """API endpoint for streaming LLM and TTS responses"""
        if not request.json or 'text' not in request.json:
            return jsonify({'error': 'Input text required'}), 400
        
        user_input = request.json['text']
        session_id = request.json.get('session_id', time.strftime('%Y%m%d-%H%M%S'))
        
        try:
            # Create streaming response generator
            async def generate_streaming_response():
                # Load memory and history
                memory = self.memory_manager.load_memory(session_id)
                history = self.memory_manager.load_history(session_id)
                
                # Build prompt with context
                system_prompt = self._build_system_prompt(memory, history)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
                
                sentence_index = 0
                full_response = ""
                current_emotion = memory.get("current_emotion", "neutral")
                
                # Stream text chunks and generate TTS
                async for sentence, current_full_response in self._produce_text_chunks(messages):
                    sentence_index += 1
                    full_response = current_full_response
                    
                    # Select voice based on emotion or preference
                    ref_audio = self.voice_selector.select_voice(memory, current_emotion)
                    
                    # Generate audio for this sentence
                    session_folder = f"{self.output_folder}/{session_id}"
                    audio_path = await self.tts_manager.generate_speech(
                        sentence, 
                        ref_audio,
                        session_folder,
                        f"sentence_{sentence_index}"
                    )
                    
                    # Create the chunk data
                    chunk_data = {
                        "type": "chunk",
                        "text": sentence,
                        "audio_path": audio_path,
                        "index": sentence_index
                    }
                    
                    # Yield the chunk as a server-sent event
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Update conversation history
                self.memory_manager.update_history(session_id, user_input, full_response)
                
                # Extract memory and update emotion
                await self.memory_manager.extract_and_update_memory(
                    self.llm_manager, user_input, full_response, session_id
                )
                
                # Send completion event
                completion_data = {
                    "type": "complete",
                    "full_text": full_response
                }
                
                yield f"data: {json.dumps(completion_data)}\n\n"
            
            # Return streaming response
            return Response(
                stream_with_context(generate_streaming_response()),
                mimetype='text/event-stream'
            )
            
        except Exception as e:
            error_msg = f"Error processing streaming request: {str(e)}"
            print(error_msg, file=sys.stderr)
            return jsonify({'error': error_msg}), 500
    
    def _build_system_prompt(self, memory, history):
        """Build system prompt with memory and history context"""
        from ..config import DEFAULT_SYSTEM_PROMPT
        
        # Build memory context
        memory_prompt = ""
        if memory["facts"]:
            memory_prompt += "【儿童信息】\n" + "\n".join([f"- {fact}" for fact in memory["facts"]]) + "\n\n"
        
        if memory["preferences"]:
            memory_prompt += "【儿童偏好】\n"
            for pref_type, pref_value in memory["preferences"].items():
                memory_prompt += f"- {pref_type}: {pref_value}\n"
            memory_prompt += "\n"
        
        # Build history context
        history_prompt = ""
        if history:
            history_prompt = "【最近对话】\n"
            for turn in history[-self.memory_manager.max_history_turns:]:
                history_prompt += f"儿童: {turn['user']}\n"
                history_prompt += f"小智: {turn['assistant']}\n"
            history_prompt += "\n"
        
        # Combine prompts
        return f"{DEFAULT_SYSTEM_PROMPT}\n\n{memory_prompt}{history_prompt}"
    
async def _produce_text_chunks(self, messages):
        """Stream text from LLM and yield complete sentences"""
        buffer_text = ""
        full_response = ""
        
        async for chunk in self.llm_manager.stream_response(messages):
            # Add new chunk to buffer
            buffer_text += chunk
            full_response += chunk
            
            # Check for sentence ending punctuation
            sentences = []
            tmp = []
            for c in buffer_text:
                tmp.append(c)
                if c in ["。", "！", "？", ".", "!", "?"]:
                    # Complete sentence found
                    sentences.append("".join(tmp))
                    tmp = []
                    
            # Process complete sentences
            if sentences:
                for s in sentences:
                    yield s, full_response
                
                # Put remaining text back in buffer
                buffer_text = "".join(tmp)
        
        # Process any remaining text at the end of the stream
        remainder = buffer_text.strip()
        if remainder:
            yield remainder, full_response