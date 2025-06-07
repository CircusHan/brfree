let timer = setTimeout(() => {
  window.location.href = '/home';
}, 120000);

document.addEventListener('click', () => {
  clearTimeout(timer);
  timer = setTimeout(() => { window.location.href = '/home'; }, 120000);
});

function playTTS(text) {
  fetch(`/tts?text=${encodeURIComponent(text)}`)
    .then((res) => res.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();
    });
}

function openMap() {
  window.open('/static/images/map/clinic_map.png', '_blank');
}

// --------------------------------------------------------
// AI Chatbot --- BEGIN
// --------------------------------------------------------
const aiChatbotInvokeButton = document.getElementById('aiChatbotInvokeButton');
const aiChatbotModal = document.getElementById('aiChatbotModal');
const aiChatbotCloseButton = document.getElementById('aiChatbotCloseButton');
const aiChatbotVideo = document.getElementById('aiChatbotVideo'); // Placeholder for video/avatar
const aiChatbotChatbox = document.getElementById('aiChatbotChatbox');
const aiChatbotInput = document.getElementById('aiChatbotInput');
const aiChatbotSendButton = document.getElementById('aiChatbotSendButton');

let chatbotStream; // For webcam/mic stream
let speechRecognition;
let isChatbotOpen = false;
const backendApiUrl = '/api/chatbot'; // ADAPTED

const synth = window.speechSynthesis;
let chatbotVoice = null;

function loadChatbotVoices() {
    const voices = synth.getVoices();
    // Prefer Korean voice if available
    chatbotVoice = voices.find(voice => voice.lang.startsWith('ko')) || voices.find(voice => voice.default) || voices[0];
}

if (synth.onvoiceschanged !== undefined) {
    synth.onvoiceschanged = loadChatbotVoices;
}
loadChatbotVoices(); // Initial attempt

function chatbotSpeak(text, instant = false) {
    if (!text || !synth) return;

    // If speaking and instant is false, might consider queuing or skipping.
    // For now, new speech will interrupt previous if it hasn't finished.
    if (synth.speaking && !instant) {
         // console.log("Chatbot is already speaking. New message queued or ignored.");
         // return; // Or implement a queue if needed
    }
    if (synth.speaking && instant) {
        synth.cancel(); // Stop current speech if new one needs to start immediately
    }

    // A small delay can sometimes help ensure cancel takes effect or voices are loaded.
    setTimeout(() => {
        const utterance = new SpeechSynthesisUtterance(text);
        if (chatbotVoice) {
            utterance.voice = chatbotVoice;
        }
        // Fallback language if voice not specifically set or found
        utterance.lang = chatbotVoice ? chatbotVoice.lang : 'ko-KR';
        utterance.pitch = 1;
        utterance.rate = 1; // Adjust rate as needed
        synth.speak(utterance);
    }, 50);
}

function initializeChatbotSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        speechRecognition = new webkitSpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;
        speechRecognition.lang = 'ko-KR';

        speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if(aiChatbotInput) aiChatbotInput.value = transcript;
            askAiChatbot(transcript);
        };

        speechRecognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let errorMessage = `음성 인식 오류: ${event.error}`;
            if (event.error === 'no-speech') {
                errorMessage = '마이크 입력이 없습니다. 다시 시도해주세요.';
            } else if (event.error === 'audio-capture') {
                errorMessage = '마이크 접근에 실패했습니다. 권한을 확인해주세요.';
            } else if (event.error === 'not-allowed') {
                errorMessage = '마이크 사용 권한이 차단되었습니다.';
            }
            // Optionally display this message in the chatbox
            // addMessageToChatbot(errorMessage, 'bot');
        };

        speechRecognition.onstart = () => {
            // console.log('Speech recognition started.');
        };

        speechRecognition.onend = () => {
            // console.log('Speech recognition ended.');
        };

    } else {
        console.warn('Speech recognition not supported in this browser.');
        // Optionally disable mic features if not supported
    }
}

function startChatbotWebcam() {
    if(aiChatbotVideo) aiChatbotVideo.textContent = "AI 아바타 영상 (준비중)";
}

function stopChatbotWebcam() {
    if(aiChatbotVideo) aiChatbotVideo.textContent = "AI 아바타 영상 (종료됨)";
}

function addMessageToChatbot(text, sender) {
    if (!aiChatbotChatbox) return;
    const messageElement = document.createElement('div');
    messageElement.classList.add('ai-chatbot-message');
    messageElement.classList.add(sender === 'user' ? 'ai-user-message' : 'ai-bot-message');
    messageElement.textContent = text;
    aiChatbotChatbox.appendChild(messageElement);
    aiChatbotChatbox.scrollTop = aiChatbotChatbox.scrollHeight;

    if (sender === 'bot') {
        chatbotSpeak(text, true); // Use true for instant speech from bot
    }
}

async function askAiChatbot(query) {
    if (!query || !query.trim()) return;

    addMessageToChatbot(query, 'user');
    if(aiChatbotInput) aiChatbotInput.value = '';

    try {
        const response = await fetch(backendApiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: query })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const errorMessage = errorData?.error || `서버 응답 오류: ${response.status}`;
            addMessageToChatbot(errorMessage, 'bot');
            return;
        }

        const data = await response.json();
        addMessageToChatbot(data.reply, 'bot');

    } catch (error) {
        console.error('Error calling chatbot API:', error);
        addMessageToChatbot('챗봇 API 호출 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.', 'bot');
    }
}

function openAiChatbot() {
    if (aiChatbotModal) aiChatbotModal.style.display = 'flex';
    isChatbotOpen = true;
    startChatbotWebcam();
    // Initialize speech recognition when chatbot opens, if not already.
    if (!speechRecognition) {
        initializeChatbotSpeechRecognition();
    }
    if (aiChatbotInput) aiChatbotInput.focus();
    // Only add welcome message if chatbox is empty, to avoid duplication on reopen
    if (aiChatbotChatbox && aiChatbotChatbox.children.length === 0) {
        addMessageToChatbot("안녕하세요! AI 상담원입니다. 무엇을 도와드릴까요?", "bot");
    }
}

function closeAiChatbot() {
    if (aiChatbotModal) aiChatbotModal.style.display = 'none';
    isChatbotOpen = false;
    stopChatbotWebcam();
    if (speechRecognition) {
        speechRecognition.stop();
    }
    if (synth && synth.speaking) {
        synth.cancel();
    }
}

// Event Listeners should be attached once DOM is ready.
// Assuming this script is loaded at the end of the body, direct attachment is fine.
// If it were in <head>, a DOMContentLoaded wrapper would be essential.

if (aiChatbotInvokeButton) {
    aiChatbotInvokeButton.addEventListener('click', openAiChatbot);
} else {
    console.error("aiChatbotInvokeButton not found");
}

if (aiChatbotCloseButton) {
    aiChatbotCloseButton.addEventListener('click', closeAiChatbot);
} else {
    console.error("aiChatbotCloseButton not found");
}

if (aiChatbotSendButton) {
    aiChatbotSendButton.addEventListener('click', () => {
        if(aiChatbotInput) askAiChatbot(aiChatbotInput.value);
    });
} else {
    console.error("aiChatbotSendButton not found");
}

if (aiChatbotInput) {
    aiChatbotInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            askAiChatbot(aiChatbotInput.value);
            event.preventDefault(); // Prevent form submission if it's part of a form
        }
    });
} else {
    console.error("aiChatbotInput not found");
}

// Call initialize for speech recognition once at the start if you want it ready.
// However, initializing it only when the chatbot opens might be better for permissions.
// initializeChatbotSpeechRecognition();

// --------------------------------------------------------
// AI Chatbot --- END
// --------------------------------------------------------
