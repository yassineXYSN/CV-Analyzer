// Créer l'enregistreur audio
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Initialiser l'enregistrement
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('timeslot_id', timeslotId);
            formData.append('user_id', userId);
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.success) {
                    displayTranscript(data.transcript);
                } else {
                    console.error('Erreur lors de la transcription:', data.error);
                }
            } catch (error) {
                console.error('Erreur:', error);
            }
            
            audioChunks = [];
        };
        
        mediaRecorder.start();
        isRecording = true;
        updateRecordingUI();
    } catch (error) {
        console.error('Erreur lors de l\'initialisation de l\'enregistrement:', error);
    }
}

// Arrêter l'enregistrement
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        updateRecordingUI();
    }
}

// Mettre à jour l'interface utilisateur
function updateRecordingUI() {
    const recordButton = document.getElementById('recordButton');
    const stopButton = document.getElementById('stopButton');
    
    if (isRecording) {
        recordButton.disabled = true;
        stopButton.disabled = false;
    } else {
        recordButton.disabled = false;
        stopButton.disabled = true;
    }
}

// Afficher la transcription
function displayTranscript(text) {
    const transcriptContainer = document.getElementById('transcript');
    const newTranscript = document.createElement('div');
    newTranscript.className = 'transcript-item';
    newTranscript.textContent = text;
    transcriptContainer.appendChild(newTranscript);
}
