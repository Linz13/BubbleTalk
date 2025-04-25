// Memory management functions
async function loadMemory() {
    const factsContainer = document.getElementById('factsContainer');
    const preferencesContainer = document.getElementById('preferencesContainer');
    
    try {
        const response = await fetch(`${API_BASE_URL}/memory/${sessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load memory');
        }
        
        const memory = await response.json();
        updateMemoryDisplay(memory);
        
    } catch (error) {
        console.error('Error loading memory:', error);
        factsContainer.innerHTML = '<div class="fact-item">加载失败</div>';
        preferencesContainer.innerHTML = '<div class="preference-item">加载失败</div>';
    }
}

async function loadHistory() {
    const messageContainer = document.getElementById('messageContainer');
    
    try {
        const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load history');
        }
        
        const history = await response.json();
        
        // Clear message container except for welcome message
        const welcomeMessage = messageContainer.firstChild;
        messageContainer.innerHTML = '';
        if (welcomeMessage) {
            messageContainer.appendChild(welcomeMessage);
        }
        
        // Add history messages
        history.forEach(turn => {
            if (turn.user) {
                addMessage({
                    role: 'user',
                    content: turn.user,
                    timestamp: turn.timestamp ? new Date(turn.timestamp * 1000).toISOString() : new Date().toISOString()
                });
            }
            
            if (turn.assistant) {
                addMessage({
                    role: 'assistant',
                    content: turn.assistant,
                    audio: null, // We don't have audio path for history
                    timestamp: turn.timestamp ? new Date(turn.timestamp * 1000).toISOString() : new Date().toISOString()
                });
            }
        });
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function setVoicePreference(voiceType) {
    try {
        const response = await fetch(`${API_BASE_URL}/set_voice`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voice: voiceType,
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to set voice preference');
        }
        
        console.log(`Voice preference set to: ${voiceType}`);
    } catch (error) {
        console.error('Error setting voice preference:', error);
    }
}

function updateMemoryDisplay(memory) {
    const factsContainer = document.getElementById('factsContainer');
    const preferencesContainer = document.getElementById('preferencesContainer');
    
    // Update facts
    factsContainer.innerHTML = '';
    if (memory.facts && memory.facts.length > 0) {
        memory.facts.forEach(fact => {
            const factDiv = document.createElement('div');
            factDiv.className = 'fact-item';
            factDiv.textContent = fact;
            factsContainer.appendChild(factDiv);
        });
    } else {
        factsContainer.innerHTML = '<div class="fact-item">暂无记录的信息</div>';
    }
    
    // Update preferences
    preferencesContainer.innerHTML = '';
    if (memory.preferences && Object.keys(memory.preferences).length > 0) {
        for (const [key, value] of Object.entries(memory.preferences)) {
            const prefDiv = document.createElement('div');
            prefDiv.className = 'preference-item';
            prefDiv.textContent = `${key}: ${value}`;
            preferencesContainer.appendChild(prefDiv);
        }
    } else {
        preferencesContainer.innerHTML = '<div class="preference-item">暂无记录的偏好</div>';
    }
    
    // Update voice selector if preference exists
    const voiceSelector = document.getElementById('voiceSelector');
    if (memory.voice_preference && voiceSelector) {
        voiceSelector.value = memory.voice_preference;
    }
}