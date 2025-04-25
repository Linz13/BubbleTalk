// Message handling functions
function addMessage(message) {
    const messageContainer = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`;
    
    const senderName = message.role === 'user' ? '我' : '小智';
    const time = formatTime(message.timestamp);
    
    let audioControls = '';
    if (message.role === 'assistant' && message.audio) {
        audioControls = `
            <div class="audio-controls">
                <button class="play-button" data-audio="${message.audio}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 5v14l11-7z" fill="white"/>
                    </svg>
                </button>
                <span class="play-status">点击播放语音</span>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="sender-name">${senderName}</div>
        <div class="message-content">${message.content}</div>
        ${audioControls}
        <div class="message-time">${time}</div>
    `;
    
    messageContainer.appendChild(messageDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
    
    // Add event listener for audio playback
    if (message.role === 'assistant' && message.audio) {
        const playButton = messageDiv.querySelector('.play-button');
        const playStatus = messageDiv.querySelector('.play-status');
        
        playButton.addEventListener('click', () => {
            playAudio(message.audio, playStatus);
        });
    }
}

// Send message to server
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const messageContainer = document.getElementById('messageContainer');
    
    const text = userInput.value.trim();
    
    if (!text) return;
    
    // Add user message to UI
    addMessage({
        role: 'user',
        content: text,
        timestamp: new Date().toISOString()
    });
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Disable send button
    sendButton.disabled = true;
    
    // Use streaming or non-streaming based on user preference
    const useStreaming = true; // Could be a user setting
    
    if (useStreaming) {
        await sendStreamingMessage(text);
    } else {
        await sendRegularMessage(text);
    }
}

// Send message with streaming response
async function sendStreamingMessage(text) {
    const messageContainer = document.getElementById('messageContainer');
    const sendButton = document.getElementById('sendButton');
    
    // Close any existing SSE connection
    if (eventSource) {
        eventSource.close();
    }
    
    try {
        // Create container for streaming response
        const streamingContainer = document.createElement('div');
        streamingContainer.className = 'message assistant-message';
        streamingContainer.innerHTML = `
            <div class="sender-name">小智</div>
            <div class="message-content" id="streaming-content"></div>
            <div class="audio-controls" id="streaming-audio-controls"></div>
            <div class="message-time">${formatTime(new Date())}</div>
        `;
        messageContainer.appendChild(streamingContainer);
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        const streamingContent = document.getElementById('streaming-content');
        const streamingAudioControls = document.getElementById('streaming-audio-controls');
        
        // Text accumulator
        let accumulatedText = '';
        
        // Connect to SSE endpoint
        const queryParams = new URLSearchParams({ session_id: sessionId }).toString();
        eventSource = new EventSource(`${API_BASE_URL}/stream_response?${queryParams}`);
        
        // Send request to initiate streaming
        fetch(`${API_BASE_URL}/stream_response`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                session_id: sessionId
            })
        });
        
        // Handle incoming chunks
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'chunk') {
                // Add text to accumulator and update display
                accumulatedText += data.text;
                streamingContent.textContent = accumulatedText;
                
                // Auto-play audio if enabled
                if (data.audio_path) {
                    const autoPlayEnabled = localStorage.getItem('autoPlayEnabled') !== 'false';
                    if (autoPlayEnabled) {
                        playStreamingAudio(data.audio_path);
                    }
                    
                    // Add audio controls
                    addAudioControlToStreaming(data.audio_path, streamingAudioControls);
                }
                
                // Scroll to bottom as content grows
                messageContainer.scrollTop = messageContainer.scrollHeight;
            } else if (data.type === 'complete') {
                // Close the SSE connection
                eventSource.close();
                eventSource = null;
                
                // Update memory display
                loadMemory();
                
                // Re-enable send button
                sendButton.disabled = false;
            }
        };
        
        // Handle SSE errors
        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            eventSource.close();
            eventSource = null;
            
            // Show error message
            streamingContent.textContent = '对不起，处理请求时出现错误。请稍后再试。';
            
            // Re-enable send button
            sendButton.disabled = false;
        };
    } catch (error) {
        console.error('Error:', error);
        
        // Add error message
        addMessage({
            role: 'assistant',
            content: '对不起，处理请求时出现错误。请稍后再试。',
            timestamp: new Date().toISOString()
        });
        
        // Re-enable send button
        sendButton.disabled = false;
    }
}

// Send message with regular (non-streaming) response
async function sendRegularMessage(text) {
    const messageContainer = document.getElementById('messageContainer');
    const sendButton = document.getElementById('sendButton');
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="message-content loading">
            小智正在思考
            <div class="dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;
    messageContainer.appendChild(loadingDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
    
    try {
        // Send request to server
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Server error');
        }
        
        const result = await response.json();
        
        // Remove loading indicator
        messageContainer.removeChild(loadingDiv);
        
        // Add assistant message to UI
        addMessage({
            role: 'assistant',
            content: result.llm_response,
            audio: result.audio_path,
            timestamp: new Date().toISOString()
        });
        
        // Update memory display
        loadMemory();
        
    } catch (error) {
        console.error('Error:', error);
        
        // Remove loading indicator
        messageContainer.removeChild(loadingDiv);
        
        // Add error message
        addMessage({
            role: 'assistant',
            content: '对不起，处理请求时出现错误。请稍后再试。',
            timestamp: new Date().toISOString()
        });
    } finally {
        // Re-enable send button
        sendButton.disabled = false;
    }
}

// Session management functions
function startNewSession() {
    if (confirm('确定要开始新的对话吗？当前对话记录将保留在服务器上。')) {
        // Generate new session ID
        sessionId = generateSessionId();
        localStorage.setItem('sessionId', sessionId);
        
        // Clear message container
        const messageContainer = document.getElementById('messageContainer');
        messageContainer.innerHTML = '';
        
        // Reset memory display
        const factsContainer = document.getElementById('factsContainer');
        const preferencesContainer = document.getElementById('preferencesContainer');
        factsContainer.innerHTML = '<div class="fact-item">暂无记录的信息</div>';
        preferencesContainer.innerHTML = '<div class="preference-item">暂无记录的偏好</div>';
        
        // Add welcome message
        addMessage({
            role: 'assistant',
            content: '你好！我是小智，7岁。想聊什么呀？',
            audio: null,
            timestamp: new Date().toISOString()
        });
    }
}

async function resetMemory() {
    if (confirm('确定要重置当前对话的记忆吗？这将清空所有已学习的信息和偏好。')) {
        try {
            // Make API call to reset memory
            const response = await fetch(`${API_BASE_URL}/memory/${sessionId}/reset`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to reset memory');
            }
            
            // Update UI
            const factsContainer = document.getElementById('factsContainer');
            const preferencesContainer = document.getElementById('preferencesContainer');
            factsContainer.innerHTML = '<div class="fact-item">暂无记录的信息</div>';
            preferencesContainer.innerHTML = '<div class="preference-item">暂无记录的偏好</div>';
            
            // Add system message
            addMessage({
                role: 'assistant',
                content: '我的记忆已重置，但我还记得我们刚才的对话哦！',
                audio: null,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Error resetting memory:', error);
            alert('重置记忆失败，请稍后再试');
        }
    }
}