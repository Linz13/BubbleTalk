// Audio playback functions
async function playAudio(audioPath, statusElement) {
    if (!audioPath) return;
    
    try {
        statusElement.textContent = '加载中...';
        
        // Create audio element
        let audio;
        
        // Check if audio is already cached
        if (audioCache[audioPath]) {
            audio = audioCache[audioPath];
        } else {
            // Construct audio URL
            const audioUrl = `${API_BASE_URL}/audio/${audioPath.split('/').pop()}`;
            
            audio = new Audio(audioUrl);
            audioCache[audioPath] = audio;
            
            // Wait for audio to load
            await new Promise((resolve, reject) => {
                audio.addEventListener('canplaythrough', resolve);
                audio.addEventListener('error', reject);
                audio.load();
            });
        }
        
        statusElement.textContent = '播放中...';
        
        // Stop any currently playing audio
        if (currentAudioPlayer) {
            currentAudioPlayer.pause();
        }
        
        // Set as current player and play
        currentAudioPlayer = audio;
        await audio.play();
        
        // Update status when finished
        audio.addEventListener('ended', () => {
            statusElement.textContent = '点击播放语音';
            currentAudioPlayer = null;
        });
        
    } catch (error) {
        console.error('Error playing audio:', error);
        statusElement.textContent = '播放失败';
    }
}

// Play streaming audio chunks
async function playStreamingAudio(audioPath) {
    if (!audioPath) return;
    
    try {
        // Construct audio URL
        const audioUrl = `${API_BASE_URL}/audio/${audioPath.split('/').pop()}`;
        
        // Create audio element
        const audio = new Audio(audioUrl);
        
        // Stop any currently playing audio
        if (currentAudioPlayer) {
            currentAudioPlayer.pause();
        }
        
        // Set as current player and play
        currentAudioPlayer = audio;
        await audio.play();
        
        // Handle playback end
        audio.addEventListener('ended', () => {
            currentAudioPlayer = null;
        });
        
    } catch (error) {
        console.error('Error playing streaming audio:', error);
    }
}

// Add audio control to streaming message
function addAudioControlToStreaming(audioPath, controlsContainer) {
    // Create unique ID for this audio chunk
    const audioId = `audio_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    
    // Create audio control element
    const audioControl = document.createElement('div');
    audioControl.className = 'audio-control';
    audioControl.innerHTML = `
        <button class="play-button" data-audio="${audioPath}" id="${audioId}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 5v14l11-7z" fill="white"/>
            </svg>
        </button>
        <span class="play-status" id="${audioId}_status">点击播放语音</span>
    `;
    
    // Add to container
    controlsContainer.appendChild(audioControl);
    
    // Add event listener
    const playButton = document.getElementById(audioId);
    const playStatus = document.getElementById(`${audioId}_status`);
    
    if (playButton && playStatus) {
        playButton.addEventListener('click', () => {
            playAudio(audioPath, playStatus);
        });
    }
}

// Recording functions
async function initializeRecording() {
    try {
        // Check if browser supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('getUserMedia not supported in this browser');
            alert('您的浏览器不支持录音功能');
            return;
        }
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Initialize MediaRecorder
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            // Create blob from recorded chunks
            const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
            recordedChunks = [];
            
            // Create file from blob
            const fileName = `recording_${Date.now()}.wav`;
            const file = new File([audioBlob], fileName);
            
            // Send for transcription
            await transcribeAndSend(file);
        };
        
        // Initialize record button
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.addEventListener('click', toggleRecording);
        }
        
        console.log('Recording initialized successfully');
    } catch (error) {
        console.error('Error initializing recording:', error);
        alert('无法访问麦克风，语音输入功能不可用');
    }
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    if (!mediaRecorder || isRecording) return;
    
    // Stop any playing audio
    if (currentAudioPlayer) {
        currentAudioPlayer.pause();
        currentAudioPlayer = null;
    }
    
    // Start recording
    recordedChunks = [];
    mediaRecorder.start();
    isRecording = true;
    
    // Update UI
    const recordButton = document.getElementById('recordButton');
    recordButton.classList.add('recording');
    recordButton.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="6" y="6" width="12" height="12" fill="white"/>
        </svg>
    `;
    
    console.log('Recording started');
}

function stopRecording() {
    if (!mediaRecorder || !isRecording) return;
    
    mediaRecorder.stop();
    isRecording = false;
    
    // Update UI
    const recordButton = document.getElementById('recordButton');
    recordButton.classList.remove('recording');
    recordButton.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" fill="white"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" fill="white"/>
        </svg>
    `;
    
    console.log('Recording stopped');
}

async function transcribeAndSend(audioFile) {
    const messageContainer = document.getElementById('messageContainer');
    const userInput = document.getElementById('userInput');
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="message-content loading">
            正在识别语音
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
        // Create FormData
        const formData = new FormData();
        formData.append('audio', audioFile);
        
        // Send to Whisper server
        const response = await fetch(`${API_WHISPER_URL}/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('语音识别服务错误');
        }
        
        const result = await response.json();
        
        // Remove loading indicator
        messageContainer.removeChild(loadingDiv);
        
        if (result.transcription) {
            // Add transcribed text to input
            userInput.value = result.transcription;
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
            
            // Auto-send after transcription
            sendMessage();
        } else {
            throw new Error('未能识别语音');
        }
    } catch (error) {
        console.error('Error transcribing audio:', error);
        
        // Remove loading indicator
        messageContainer.removeChild(loadingDiv);
        
        // Show error message
        addMessage({
            role: 'assistant',
            content: `语音识别失败：${error.message}`,
            audio: null,
            timestamp: new Date().toISOString()
        });
    }
}