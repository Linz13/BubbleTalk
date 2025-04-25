import json
import time
import os
import sys

class MemoryManager:
    """Manager for conversation memory and context"""
    
    def __init__(self, output_folder, max_history_turns=3):
        self.output_folder = output_folder
        self.max_history_turns = max_history_turns
        self.memory_store = {}  # session_id -> memory content
        self.conversation_history = {}  # session_id -> conversation history
        
        # Create memory directory
        self.memory_dir = os.path.join(output_folder, "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
    
    def load_memory(self, session_id):
        """Load memory for a specific session"""
        if session_id in self.memory_store:
            return self.memory_store[session_id]
            
        memory_file = os.path.join(self.memory_dir, f"{session_id}_memory.json")
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {str(e)}", file=sys.stderr)
        
        # Create new memory structure if not found
        return {
            "facts": [], 
            "preferences": {}, 
            "current_emotion": "neutral",
            "voice_preference": None,
            "last_updated": time.time()
        }
    
    def save_memory(self, session_id, memory_data):
        """Save memory for a specific session"""
        memory_file = os.path.join(self.memory_dir, f"{session_id}_memory.json")
        
        try:
            memory_data["last_updated"] = time.time()
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
            # Update in-memory store
            self.memory_store[session_id] = memory_data
        except Exception as e:
            print(f"Error saving memory: {str(e)}", file=sys.stderr)
    
    def load_history(self, session_id):
        """Load conversation history for a specific session"""
        if session_id in self.conversation_history:
            return self.conversation_history[session_id]
            
        history_file = os.path.join(self.memory_dir, f"{session_id}_history.json")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {str(e)}", file=sys.stderr)
        
        return []
    
    def save_history(self, session_id, history):
        """Save conversation history for a specific session"""
        history_file = os.path.join(self.memory_dir, f"{session_id}_history.json")
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
            # Update in-memory store
            self.conversation_history[session_id] = history
        except Exception as e:
            print(f"Error saving history: {str(e)}", file=sys.stderr)
    
    def update_history(self, session_id, user_input, assistant_response):
        """Add a conversation turn to history"""
        history = self.load_history(session_id)
        
        # Add new turn
        history.append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": time.time()
        })
        
        # Limit history length
        if len(history) > self.max_history_turns * 2:
            history = history[-self.max_history_turns * 2:]
        
        # Save updated history
        self.save_history(session_id, history)
        
    def reset_memory(self, session_id):
        """Reset memory for a specific session"""
        empty_memory = {
            "facts": [], 
            "preferences": {}, 
            "current_emotion": "neutral",
            "voice_preference": None,
            "last_updated": time.time()
        }
        
        self.memory_store[session_id] = empty_memory
        self.save_memory(session_id, empty_memory)
        
    async def extract_and_update_memory(self, llm_manager, user_input, llm_response, session_id):
        """Extract important information from conversation and update memory"""
        # Load current memory
        current_memory = self.load_memory(session_id)
        
        # Enhanced prompt for better extraction with categories
        memory_extraction_prompt = f"""
        分析以下对话并提取重要信息:
        
        用户: {user_input}
        助手: {llm_response}
        
        请提取以下分类的信息:
        1. 基本信息 - 儿童的姓名、年龄、性别、学校等
        2. 家庭信息 - 父母、兄弟姐妹、家庭结构等
        3. 兴趣爱好 - 喜欢的活动、游戏、书籍等
        4. 情感状态 - 当前情绪、担忧、期待等
        5. 学习情况 - 学科喜好、困难、成就等
        6. 重要事件 - 过去经历或即将发生的事件
        
        以JSON格式返回，不要包含任何其他内容:
        ```json
        {{
            "new_facts": [], // 所有新的事实信息，每项是包含分类的对象 {"category": "类别", "fact": "具体事实"}
            "preferences": {{}}, // 提取的偏好，key是偏好类型，value是偏好内容
            "emotional_state": "" // 分析儿童当前的情绪状态: "happy", "sad", "neutral", "curious", "anxious", "excited" 等
        }}
        ```
        只提取对话中直接提及或强烈暗示的信息，不要推测。如果没有提取到新信息，则返回空数组和空对象。
        """
        
        try:
            # Request LLM for memory extraction
            extraction_response = await llm_manager.model.ainvoke([
                {"role": "system", "content": "你是一个精确提取信息的助手。只返回JSON格式，不要添加任何额外说明。"},
                {"role": "user", "content": memory_extraction_prompt}
            ])
            
            # Parse JSON response
            extraction_text = extraction_response.content
            
            # Clean up response if needed
            if "```json" in extraction_text:
                extraction_text = extraction_text.split("```json")[1].split("```")[0].strip()
            elif "```" in extraction_text:
                extraction_text = extraction_text.split("```")[1].split("```")[0].strip()
                
            extracted_data = json.loads(extraction_text)
            
            # Update memory with categorized facts
            if "new_facts" in extracted_data and extracted_data["new_facts"]:
                for fact_obj in extracted_data["new_facts"]:
                    # Convert to string format with category prefix
                    fact_str = f"[{fact_obj['category']}] {fact_obj['fact']}"
                    if fact_str not in current_memory["facts"]:
                        current_memory["facts"].append(fact_str)

            if "preferences" in extracted_data and extracted_data["preferences"]:
                # Update preferences
                current_memory["preferences"].update(extracted_data["preferences"])
            
            # Store emotional state if available
            if "emotional_state" in extracted_data and extracted_data["emotional_state"]:
                current_memory["current_emotion"] = extracted_data["emotional_state"]
            
            # Save updated memory
            self.save_memory(session_id, current_memory)
            print(f"Memory updated: {json.dumps(current_memory, ensure_ascii=False)}", file=sys.stderr)
            
            return extracted_data.get("emotional_state", "neutral")
        
        except Exception as e:
            print(f"Error extracting or updating memory: {str(e)}", file=sys.stderr)
            return "neutral"