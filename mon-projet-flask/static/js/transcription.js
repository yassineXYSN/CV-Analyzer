// Gestionnaire de la transcription en temps réel
let transcriptionContainer = document.getElementById('transcription-container');

// Connexion à SocketIO
const socket = io();

// Lorsqu'une mise à jour de transcription arrive
socket.on('transcription_update', function(data) {
    if (data.slot_id === currentSlotId) {
        // Ajouter le nouveau texte à la transcription
        const newLine = document.createElement('div');
        newLine.className = 'transcription-line';
        newLine.textContent = data.text;
        transcriptionContainer.appendChild(newLine);
        
        // Scroller automatiquement vers le bas
        transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
        
        // Mettre à jour le texte complet
        document.getElementById('full-transcription').textContent = data.full_transcription;
    }
});

// Lorsqu'une erreur de transcription arrive
socket.on('transcription_error', function(data) {
    if (data.slot_id === currentSlotId) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'transcription-error';
        errorDiv.textContent = `Erreur de transcription: ${data.error}`;
        transcriptionContainer.appendChild(errorDiv);
        
        // Scroller automatiquement vers le bas
        transcriptionContainer.scrollTop = transcriptionContainer.scrollHeight;
    }
});

// Fonction pour démarrer la transcription
function startTranscription() {
    const slotId = document.getElementById('slot-id').value;
    if (!slotId) {
        alert('ID de créneau non trouvé');
        return;
    }
    
    // Démarrer la transcription côté serveur
    fetch(`/start_transcription/${slotId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Vider la transcription existante
                transcriptionContainer.innerHTML = '';
                
                // Afficher le message de démarrage
                const startMessage = document.createElement('div');
                startMessage.className = 'transcription-start';
                startMessage.textContent = 'Transcription démarrée...';
                transcriptionContainer.appendChild(startMessage);
            } else {
                alert('Erreur lors du démarrage de la transcription: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors du démarrage de la transcription');
        });
}
