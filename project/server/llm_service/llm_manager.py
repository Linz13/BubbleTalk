import os
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from ..config import (
    OPENAI_API_KEY, OPENAI_API_BASE, 
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
)

class LLMManager:
    """Manager for LLM models (GPT or DeepSeek)"""
    
    def __init__(self, llm_type="deepseek"):
        self.llm_type = llm_type
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the selected LLM model"""
        if self.llm_type.lower() == "gpt":
            self._initialize_gpt()
        else:
            self._initialize_deepseek()
    
    def _initialize_gpt(self):
        """Initialize OpenAI GPT model"""
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE
        self.model = ChatOpenAI(model="gpt-4-1106-preview", temperature=1)
    
    def _initialize_deepseek(self):
        """Initialize DeepSeek model"""
        os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
        os.environ["DEEPSEEK_BASE_URL"] = DEEPSEEK_BASE_URL
        self.model = ChatDeepSeek(model="deepseek-chat", temperature=1)
    
    async def generate_response(self, messages):
        """Generate a complete response from the LLM"""
        if self.model is None:
            raise ValueError("LLM model not initialized")
        
        response = await self.model.ainvoke(messages)
        return response.content
    
    async def stream_response(self, messages):
        """Stream response from the LLM"""
        if self.model is None:
            raise ValueError("LLM model not initialized")
        
        async for chunk in self.model.astream(messages):
            yield chunk.content