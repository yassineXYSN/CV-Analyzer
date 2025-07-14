// Gestionnaire de la transcription en temps réel avec détection d'émotions
let transcriptionContainer = document.getElementById('transcription-container');
let currentSlotId = null;

const socket = io();

function getEmotionIcon(emotion) {
    const icons = {
        'joy': '😊',
        'sadness': '😢',
        'anger': '😠',
        'fear': '😨',
        'surprise': '😲',
        'neutral': '😐'
    };
    return icons[emotion] || '😐';
}

function getEmotionColor(emotion) {
    const colors = {
        'joy': '#4CAF50',
        'sadness': '#2196F3',
        'anger': '#F44336',
        'fear': '#FF9800',
        'surprise': '#9C27B0',
        'neutral': '#757575'
    };
    return colors[emotion] || '#757575';
}

socket.on('transcription_update', function(data) {
    if (data.slot_id === currentSlotId) {
        const lineContainer = document.createElement('div');
        lineContainer.className = 'transcription-line-container';
        const textLine = document.createElement('div');
        textLine.className = 'transcription-line';
        textLine.textContent = data.text;
        lineContainer.appendChild(textLine);
        if (data.emotions && data.emotions.length > 0) {
            const emotionsDiv = document.createElement('div');
            emotionsDiv.className = 'emotions-display';
            data.emotions.forEach(emotion => {
                const emotionSpan = document.createElement('span');
                emotionSpan.className = 'emotion-tag';
                emotionSpan.style.backgroundColor = getEmotionColor(emotion);
                emotionSpan.innerHTML = `${getEmotionIcon(emotion)} ${emotion}`;
                emotionsDiv.appendChild(emotionSpan);
            });
            lineContainer.appendChild(emotionsDiv);
        }
        transcriptionContainer.appendChild(lineContainer);
        transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
        updateEmotionsStats();
    }
});

socket.on('transcription_error', function(data) {
    if (data.slot_id === currentSlotId) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'transcription-error';
        errorDiv.textContent = `Erreur de transcription: ${data.error}`;
        transcriptionContainer.appendChild(errorDiv);
        transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
    }
});

socket.on('realtime_transcription', function(data) {
    if (data.slot_id === currentSlotId) {
        const lineContainer = document.createElement('div');
        lineContainer.className = 'transcription-line-container realtime';
        const textLine = document.createElement('div');
        textLine.className = 'transcription-line';
        textLine.textContent = data.text;
        lineContainer.appendChild(textLine);
        if (data.emotions && data.emotions.length > 0) {
            const emotionsDiv = document.createElement('div');
            emotionsDiv.className = 'emotions-display';
            data.emotions.forEach(emotion => {
                const emotionSpan = document.createElement('span');
                emotionSpan.className = 'emotion-tag';
                emotionSpan.style.backgroundColor = getEmotionColor(emotion);
                emotionSpan.innerHTML = `${getEmotionIcon(emotion)} ${emotion}`;
                emotionsDiv.appendChild(emotionSpan);
                showLiveEmotion(emotion);
            });
            lineContainer.appendChild(emotionsDiv);
        }
        transcriptionContainer.appendChild(lineContainer);
        transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
        updateEmotionsStats();
    }
});

function startTranscription() {
    const slotId = document.getElementById('slot-id').value;
    if (!slotId) {
        alert('ID de créneau non trouvé');
        return;
    }
    currentSlotId = parseInt(slotId);
    transcriptionContainer.innerHTML = '';
    document.getElementById('start-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = '';
    document.getElementById('download-btn').style.display = 'none';
    fetch(`/start_transcription/${slotId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Erreur lors du démarrage de la transcription: ' + data.message);
            document.getElementById('start-btn').style.display = '';
            document.getElementById('stop-btn').style.display = 'none';
        }
    })
    .catch(error => {
        alert('Erreur lors du démarrage de la transcription');
        document.getElementById('start-btn').style.display = '';
        document.getElementById('stop-btn').style.display = 'none';
    });
}

function stopTranscription() {
    document.getElementById('start-btn').style.display = '';
    document.getElementById('stop-btn').style.display = 'none';
    document.getElementById('download-btn').style.display = '';
    const stopMessage = document.createElement('div');
    stopMessage.className = 'transcription-stop';
    stopMessage.textContent = '🛑 Transcription arrêtée';
    transcriptionContainer.appendChild(stopMessage);
}

function sendTextForEmotionAnalysis(text) {
    const slotId = document.getElementById('slot-id').value;
    if (!slotId || !text.trim()) return;
    fetch('/realtime-transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, slot_id: parseInt(slotId) })
    });
}

function updateEmotionsStats() {
    const slotId = document.getElementById('slot-id').value;
    if (!slotId) return;
    fetch(`/emotions-stats/${slotId}`)
        .then(response => response.json())
        .then(data => {
            if (data.emotions) {
                displayEmotionsStats(data.emotions);
            }
        });
}

function displayEmotionsStats(emotions) {
    const statsContainer = document.getElementById('emotions-chart');
    if (!statsContainer) return;
    const emotionIcons = {
        'joy': '😊',
        'sadness': '😢',
        'anger': '😠',
        'fear': '😨',
        'surprise': '😲',
        'neutral': '😐'
    };
    const emotionLabels = {
        'joy': 'Joie',
        'sadness': 'Tristesse',
        'anger': 'Colère',
        'fear': 'Peur',
        'surprise': 'Surprise',
        'neutral': 'Neutre'
    };
    let statsHTML = '<div class="emotion-stats-container">';
    for (const [emotion, count] of Object.entries(emotions)) {
        const icon = emotionIcons[emotion] || '😐';
        const label = emotionLabels[emotion] || emotion;
        statsHTML += `
            <div class="emotion-stat">
                <div class="emotion-stat-icon">${icon}</div>
                <div class="emotion-stat-count">${count}</div>
                <div class="emotion-stat-label">${label}</div>
            </div>
        `;
    }
    statsHTML += '</div>';
    statsContainer.innerHTML = statsHTML;
}

function showLiveEmotion(emotion) {
    const existingIndicator = document.querySelector('.live-emotion-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    const indicator = document.createElement('div');
    indicator.className = `live-emotion-indicator emotion-${emotion}`;
    indicator.textContent = `Émotion détectée: ${emotion}`;
    document.body.appendChild(indicator);
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.remove();
        }
    }, 3000);
}

function downloadTranscriptionAndStats() {
    const transcription = document.getElementById('transcription-container').innerText;
    const stats = document.getElementById('emotions-chart').innerText;
    const content = "Transcription :\n\n" + transcription + "\n\nStatistiques des émotions :\n" + stats;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transcription_et_emotions.txt";
    a.click();
    URL.revokeObjectURL(url);
}

// Affichage de l'émotion audio globale
function showAudioEmotion(emotion) {
    let emotionDisplay = document.getElementById('audio-emotion-display');
    if (!emotionDisplay) {
        emotionDisplay = document.createElement('div');
        emotionDisplay.id = 'audio-emotion-display';
        emotionDisplay.style.fontSize = '1.2em';
        emotionDisplay.style.fontWeight = 'bold';
        emotionDisplay.style.marginBottom = '12px';
        emotionDisplay.style.textAlign = 'center';
        emotionDisplay.style.padding = '8px 0';
        emotionDisplay.style.background = '#f3f6fd';
        emotionDisplay.style.borderRadius = '8px';
        emotionDisplay.style.color = '#6366f1';
        const box = document.getElementById('transcription-box');
        box.insertBefore(emotionDisplay, box.children[1]);
    }
    if (emotion) {
        emotionDisplay.innerHTML = `Votre voix semble : <span style="text-transform:capitalize">${emotion}</span>`;
    } else {
        emotionDisplay.innerHTML = '';
    }
}

// Ajout d'une fonction pour afficher une ligne de transcription avec émotion audio
function addTranscriptionLineWithEmotion(text, emotion) {
    const lineContainer = document.createElement('div');
    lineContainer.className = 'transcription-line-container';
    const textLine = document.createElement('div');
    textLine.className = 'transcription-line';
    textLine.textContent = text;
    lineContainer.appendChild(textLine);
    if (emotion) {
        const emotionSpan = document.createElement('span');
        emotionSpan.className = 'emotion-tag emotion-' + emotion.toLowerCase();
        emotionSpan.style.marginLeft = '10px';
        emotionSpan.innerHTML = `${getEmotionIcon(emotion)} ${emotion}`;
        textLine.appendChild(emotionSpan);
    }
    transcriptionContainer.appendChild(lineContainer);
    transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
}

// Zone pour la transcription complète
let fullTranscription = '';
let fullTranscriptionDiv = null;

function updateFullTranscription(newText) {
    if (!fullTranscriptionDiv) {
        fullTranscriptionDiv = document.createElement('div');
        fullTranscriptionDiv.id = 'full-transcription';
        fullTranscriptionDiv.style.marginTop = '24px';
        fullTranscriptionDiv.style.padding = '12px';
        fullTranscriptionDiv.style.background = '#f8f9fa';
        fullTranscriptionDiv.style.borderRadius = '8px';
        fullTranscriptionDiv.style.fontSize = '1.1em';
        fullTranscriptionDiv.style.color = '#222';
        fullTranscriptionDiv.innerHTML = '<b>Transcription complète :</b><br><span id="full-transcription-text"></span>';
        // Ajoute la zone à la fin du container principal
        transcriptionContainer.parentNode.appendChild(fullTranscriptionDiv);
    }
    if (newText && newText.trim()) {
        fullTranscription += (fullTranscription ? ' ' : '') + newText.trim();
        document.getElementById('full-transcription-text').textContent = fullTranscription;
    }
}

// === AUTOMATISATION : Démarrage auto de l'enregistrement ===
let mediaRecorder;
let audioChunks = [];
let recordingInterval = null;
let lastEmotion = null;

function getEmotionSentence(emotion) {
    const sentences = {
        'joy': "Vous semblez joyeux(se)",
        'sadness': "Vous semblez triste",
        'anger': "Vous semblez en colère",
        'fear': "Vous semblez stressé(e)",
        'surprise': "Vous semblez surpris(e)",
        'neutral': "Votre voix semble neutre"
    };
    return sentences[emotion] || "Votre voix semble neutre";
}

function startRecordingAuto() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.start();

    mediaRecorder.ondataavailable = event => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
        sendAudioChunkToBackend(event.data);
      }
    };

    // On force un chunk toutes les 2 secondes
    recordingInterval = setInterval(() => {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.requestData();
      }
    }, 2000);
  });
}

function stopRecordingAuto() {
  if (mediaRecorder) {
    mediaRecorder.stop();
    mediaRecorder = null;
  }
  if (recordingInterval) {
    clearInterval(recordingInterval);
    recordingInterval = null;
  }
}

async function sendAudioChunkToBackend(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "chunk.webm");
  const response = await fetch("/upload-audio", {
    method: "POST",
    body: formData
  });
  const data = await response.json();
  showAudioEmotionPro(data.audio_emotion); // Affichage pro
  addPersonalizedSpeechAndEmotionLine(data.text, data.audio_emotion); // Affiche phrase personnalisée
  updateFullTranscription(data.text); // Ajoute à la transcription complète
}

// === Affichage pro de l'émotion dominante ===
function showAudioEmotionPro(emotion) {
    let emotionDisplay = document.getElementById('audio-emotion-display');
    if (!emotionDisplay) {
        emotionDisplay = document.createElement('div');
        emotionDisplay.id = 'audio-emotion-display';
        emotionDisplay.style.fontSize = '1.4em';
        emotionDisplay.style.fontWeight = 'bold';
        emotionDisplay.style.marginBottom = '16px';
        emotionDisplay.style.textAlign = 'center';
        emotionDisplay.style.padding = '12px 0';
        emotionDisplay.style.background = '#f3f6fd';
        emotionDisplay.style.borderRadius = '12px';
        emotionDisplay.style.transition = 'background 0.5s, color 0.5s';
        emotionDisplay.style.color = '#6366f1';
        const box = document.getElementById('transcription-box') || document.body;
        box.insertBefore(emotionDisplay, box.firstChild);
    }
    // Couleur selon émotion
    const colorMap = {
        'joy': '#4CAF50',
        'sadness': '#2196F3',
        'anger': '#F44336',
        'fear': '#FF9800',
        'surprise': '#9C27B0',
        'neutral': '#757575'
    };
    const iconMap = {
        'joy': '😊',
        'sadness': '😢',
        'anger': '😠',
        'fear': '😨',
        'surprise': '😲',
        'neutral': '😐'
    };
    emotionDisplay.style.background = colorMap[emotion] || '#f3f6fd';
    emotionDisplay.style.color = '#fff';
    emotionDisplay.innerHTML = `<span style="font-size:1.5em;">${iconMap[emotion] || '😐'}</span> <span style="margin-left:10px;">${getEmotionSentence(emotion)}</span>`;
    // Animation douce si changement d'émotion
    if (lastEmotion !== emotion) {
        emotionDisplay.animate([
            { opacity: 0.5 },
            { opacity: 1 }
        ], { duration: 400 });
        lastEmotion = emotion;
    }
}

// === Lancement auto à l'ouverture de la page ===
document.addEventListener('DOMContentLoaded', function() {
    const slotIdElement = document.getElementById('slot-id');
    if (slotIdElement) {
        currentSlotId = parseInt(slotIdElement.value);
    }
    // Démarrage automatique
    startRecordingAuto();
});

// Nouvelle fonction : phrase personnalisée texte + émotion
let lastDisplayedTexts = [];
function addPersonalizedSpeechAndEmotionLine(text, emotion) {
    if (!text || !text.trim()) return; // N'affiche rien si texte vide
    const trimmed = text.trim();
    // Anti-duplication sur les 3 derniers segments
    if (lastDisplayedTexts.includes(trimmed)) return;
    lastDisplayedTexts.push(trimmed);
    if (lastDisplayedTexts.length > 3) lastDisplayedTexts.shift();
    const lineContainer = document.createElement('div');
    lineContainer.className = 'transcription-line-container';
    lineContainer.style.marginBottom = '10px';
    // Ligne texte
    const speechDiv = document.createElement('div');
    speechDiv.className = 'speech-text';
    speechDiv.style.fontStyle = 'italic';
    speechDiv.style.color = '#333';
    speechDiv.textContent = `Vous avez dit : "${trimmed}"`;
    lineContainer.appendChild(speechDiv);
    // Ligne émotion (sauf si neutral ou vide)
    if (emotion && emotion.toLowerCase() !== 'neutral') {
        const emotionDiv = document.createElement('div');
        emotionDiv.className = 'emotion-line';
        emotionDiv.style.marginTop = '2px';
        emotionDiv.style.display = 'flex';
        emotionDiv.style.alignItems = 'center';
        const icon = getEmotionIcon(emotion);
        const color = getEmotionColor(emotion);
        const spanIcon = document.createElement('span');
        spanIcon.style.fontSize = '1.3em';
        spanIcon.style.marginRight = '8px';
        spanIcon.textContent = icon;
        const spanText = document.createElement('span');
        spanText.textContent = emotion;
        spanText.style.color = color;
        spanText.style.fontWeight = 'bold';
        emotionDiv.appendChild(spanIcon);
        emotionDiv.appendChild(spanText);
        lineContainer.appendChild(emotionDiv);
    }
    transcriptionContainer.appendChild(lineContainer);
    transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
}
