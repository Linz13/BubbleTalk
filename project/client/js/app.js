// Global variables
const API_BASE_URL = 'http://127.0.0.1:5001';
const API_WHISPER_URL = 'http://127.0.0.1:5000';
let sessionId = localStorage.getItem('sessionId') || generateSessionId();
let audioCache = {};
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];
let currentAudioPlayer = null;
let eventSource = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Save session ID
    localStorage.setItem('sessionId', sessionId);
    
    // Initialize UI components
    initializeChat();
    initializeVoiceSelector();
    initializeRecording();
    
    // Load memory and history
    loadMemory();
    loadHistory();
    
    // Add welcome message
    addMessage({
        role: 'assistant',
        content: '你好！我是小智，7岁。想聊什么呀？',
        audio: null,
        timestamp: new Date().toISOString()
    });
});

// Utility Functions
function generateSessionId() {
    return new Date().toISOString().replace(/[-:.TZ]/g, '');
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Initialize chat interface
function initializeChat() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const newSessionButton = document.getElementById('newSessionButton');
    const resetMemoryButton = document.getElementById('resetMemoryButton');
    
    // Event listeners
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        
        // Resize textarea based on content
        setTimeout(() => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
        }, 0);
    });
    
    sendButton.addEventListener('click', sendMessage);
    newSessionButton.addEventListener('click', startNewSession);
    resetMemoryButton.addEventListener('click', resetMemory);
}

// Initialize voice selector
function initializeVoiceSelector() {
    const voiceSelector = document.getElementById('voiceSelector');
    const autoPlayToggle = document.getElementById('autoPlayToggle');
    
    voiceSelector.addEventListener('change', () => {
        setVoicePreference(voiceSelector.value);
    });
    
    autoPlayToggle.addEventListener('change', () => {
        localStorage.setItem('autoPlayEnabled', autoPlayToggle.checked);
    });
    
    // Load saved preference
    const autoPlayEnabled = localStorage.getItem('autoPlayEnabled');
    if (autoPlayEnabled !== null) {
        autoPlayToggle.checked = autoPlayEnabled === 'true';
    }
}