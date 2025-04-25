// Voice Activity Detection
class VoiceActivityDetection {
    constructor(options = {}) {
        this.options = {
            threshold: options.threshold || 30,
            speakingThreshold: options.speakingThreshold || 30,
            silenceThreshold: options.silenceThreshold || 20,
            speakingTime: options.speakingTime || 300,
            silenceTime: options.silenceTime || 1500,
            onSpeechStart: options.onSpeechStart || (() => {}),
            onSpeechEnd: options.onSpeechEnd || (() => {}),
            enabled: options.enabled !== undefined ? options.enabled : true
        };
        
        this.audioContext = null;
        this.analyzer = null;
        this.microphone = null;
        this.stream = null;
        this.speaking = false;
        this.speakingTimer = null;
        this.silenceTimer = null;
        this.initialized = false;
        this.monitoring = false;
    }
    
    async initialize() {
        if (this.initialized) return;
        
        try {
            // Get microphone stream
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Create audio context and analyzer
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.microphone = this.audioContext.createMediaStreamSource(this.stream);
            this.analyzer = this.audioContext.createAnalyser();
            
            // Configure analyzer
            this.analyzer.fftSize = 512;
            this.analyzer.smoothingTimeConstant = 0.8;
            this.microphone.connect(this.analyzer);
            
            this.initialized = true;
            console.log('VAD initialized successfully');
            
            // Start monitoring if enabled
            if (this.options.enabled) {
                this.startMonitoring();
            }
        } catch (error) {
            console.error('Error initializing VAD:', error);
            throw error;
        }
    }
    
    startMonitoring() {
        if (!this.initialized) {
            console.error('VAD not initialized');
            return;
        }
        
        if (this.monitoring) return;
        
        this.monitoring = true;
        this.monitorAudioLevel();
        console.log('VAD monitoring started');
    }
    
    stopMonitoring() {
        this.monitoring = false;
        
        // Clear any pending timers
        clearTimeout(this.speakingTimer);
        clearTimeout(this.silenceTimer);
        
        console.log('VAD monitoring stopped');
    }
    
    monitorAudioLevel() {
        if (!this.monitoring || !this.analyzer) return;
        
        const bufferLength = this.analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Get current audio data
        this.analyzer.getByteFrequencyData(dataArray);
        
        // Calculate average volume
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
        }
        const average = sum / bufferLength;
        
        // Check against thresholds
        if (average > this.options.speakingThreshold) {
            // Speaking detected
            if (!this.speaking) {
                clearTimeout(this.speakingTimer);
                this.speakingTimer = setTimeout(() => {
                    this.speaking = true;
                    this.options.onSpeechStart();
                }, this.options.speakingTime);
            }
            
            // Reset silence timer
            clearTimeout(this.silenceTimer);
        } else if (average < this.options.silenceThreshold) {
            // Silence detected
            if (this.speaking) {
                clearTimeout(this.silenceTimer);
                this.silenceTimer = setTimeout(() => {
                    this.speaking = false;
                    this.options.onSpeechEnd();
                }, this.options.silenceTime);
            }
            
            // Reset speaking timer
            clearTimeout(this.speakingTimer);
        }
        
        // Continue monitoring
        if (this.monitoring) {
            requestAnimationFrame(() => this.monitorAudioLevel());
        }
    }
    
    setEnabled(enabled) {
        this.options.enabled = enabled;
        
        if (enabled && this.initialized && !this.monitoring) {
            this.startMonitoring();
        } else if (!enabled && this.monitoring) {
            this.stopMonitoring();
        }
    }
    
    cleanup() {
        this.stopMonitoring();
        
        // Stop microphone
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        // Close audio context
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        this.initialized = false;
        console.log('VAD cleaned up');
    }
}

// Initialize VAD with auto-recording
document.addEventListener('DOMContentLoaded', async () => {
    const vad = new VoiceActivityDetection({
        threshold: 25,
        speakingThreshold: 30,
        silenceThreshold: 20,
        speakingTime: 300,
        silenceTime: 1500,
        onSpeechStart: () => {
            console.log('Speech detected');
            // Auto-start recording
            if (!isRecording) {
                startRecording();
            }
        },
        onSpeechEnd: () => {
            console.log('Speech ended');
            // Auto-stop recording
            if (isRecording) {
                stopRecording();
            }
        },
        enabled: true // Start disabled and let user enable
    });
    
    try {
        await vad.initialize();
        
        // Add VAD toggle button
        const vadToggle = document.getElementById('vadToggle');
        if (vadToggle) {
            vadToggle.addEventListener('change', () => {
                vad.setEnabled(vadToggle.checked);
                localStorage.setItem('vadEnabled', vadToggle.checked);
            });
            
            // Load saved preference
            const vadEnabled = localStorage.getItem('vadEnabled');
            if (vadEnabled !== null) {
                const enabled = vadEnabled === 'true';
                vadToggle.checked = enabled;
                vad.setEnabled(enabled);
            }
        }
    } catch (error) {
        console.error('Failed to initialize VAD:', error);
    }
});