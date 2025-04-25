import asyncio

async def produce_text_chunks(llm_manager, messages):
    """Stream text from LLM and yield complete sentences as they are generated"""
    buffer_text = ""
    full_response = ""
    
    async for chunk in llm_manager.model.astream(messages):
        # Add new chunk to buffer
        chunk_content = chunk.content
        buffer_text += chunk_content
        full_response += chunk_content
        
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