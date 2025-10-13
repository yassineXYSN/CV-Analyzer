// Conversation Analysis JavaScript

class ConversationAnalysis {
    constructor() {
        this.data = null;
        this.currentSegmentIndex = 0;
        this.isPlaying = false;
        this.timelineInterval = null;
        this.isDetailedView = false;
        this.filteredSegments = [];
        
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.renderSummaryCards();
            this.renderCharts();
            this.renderSegments();
            this.setupFilters();
            this.hideLoadingState();
        } catch (error) {
            this.showErrorState(error.message);
        }
    }

    async loadData() {
        try {
            const response = await fetch('/api/conversation-analysis-data');
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.message || 'Failed to load data');
            }
            
            this.data = result.data;
            this.filteredSegments = this.data.conversation_segments;
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Timeline controls
        document.getElementById('play-timeline').addEventListener('click', () => this.playTimeline());
        document.getElementById('pause-timeline').addEventListener('click', () => this.pauseTimeline());
        document.getElementById('reset-timeline').addEventListener('click', () => this.resetTimeline());
        
        // View toggle
        document.getElementById('toggle-view').addEventListener('click', () => this.toggleView());
        
        // Filters
        document.getElementById('speaker-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('emotion-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-text').addEventListener('input', () => this.applyFilters());
        
        // Retry button
        document.getElementById('retry-btn').addEventListener('click', () => this.init());
    }

    renderSummaryCards() {
        const summary = this.data.summary;
        
        document.getElementById('total-segments').textContent = summary.total_segments;
        document.getElementById('total-duration').textContent = this.formatDuration(summary.total_duration);
        document.getElementById('speakers-count').textContent = summary.speakers.length;
        document.getElementById('emotions-count').textContent = summary.emotions_detected.length;
    }

    renderCharts() {
        this.renderEmotionChart();
        this.renderSpeakerChart();
    }

    renderEmotionChart() {
        const emotionData = this.calculateEmotionDistribution();
        const ctx = document.getElementById('emotion-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: emotionData.labels,
                datasets: [{
                    data: emotionData.values,
                    backgroundColor: [
                        '#ff6b6b', // angry
                        '#4ecdc4', // happy
                        '#45b7d1', // neutral
                        '#f9ca24', // disgust
                        '#6c5ce7', // sad
                        '#a29bfe', // fear
                        '#fd79a8', // surprise
                        '#ddd'     // unknown
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    renderSpeakerChart() {
        const speakerData = this.calculateSpeakerTime();
        const ctx = document.getElementById('speaker-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: speakerData.labels,
                datasets: [{
                    label: 'Speaking Time (seconds)',
                    data: speakerData.values,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 's';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    calculateEmotionDistribution() {
        const emotions = {};
        
        this.data.conversation_segments.forEach(segment => {
            const emotion = segment.dominant_emotion || 'unknown';
            emotions[emotion] = (emotions[emotion] || 0) + 1;
        });
        
        return {
            labels: Object.keys(emotions),
            values: Object.values(emotions)
        };
    }

    calculateSpeakerTime() {
        const speakers = {};
        
        this.data.conversation_segments.forEach(segment => {
            const speaker = segment.speaker || 'Unknown';
            const duration = (segment.end || 0) - (segment.start || 0);
            speakers[speaker] = (speakers[speaker] || 0) + duration;
        });
        
        return {
            labels: Object.keys(speakers),
            values: Object.values(speakers)
        };
    }

    renderSegments() {
        const segmentsList = document.getElementById('segments-list');
        segmentsList.innerHTML = '';
        
        this.filteredSegments.forEach((segment, index) => {
            const segmentElement = this.createSegmentElement(segment, index);
            segmentsList.appendChild(segmentElement);
        });
    }

    createSegmentElement(segment, index) {
        const div = document.createElement('div');
        div.className = 'segment-item';
        div.dataset.index = index;
        div.dataset.start = segment.start;
        div.dataset.end = segment.end;
        
        const emotion = segment.dominant_emotion || 'unknown';
        const confidence = segment.emotion_confidence || 0;
        
        div.innerHTML = `
            <div class="segment-header">
                <span class="segment-speaker">${segment.speaker || 'Unknown'}</span>
                <span class="segment-time">${this.formatTime(segment.start)} - ${this.formatTime(segment.end)}</span>
            </div>
            <div class="segment-emotion emotion-${emotion}">${emotion}</div>
            <p class="segment-text">${segment.text || 'No text available'}</p>
            ${this.isDetailedView ? this.createDetailedMeta(segment) : ''}
            ${confidence > 0 ? `<div class="segment-confidence">Confidence: ${confidence.toFixed(1)}%</div>` : ''}
        `;
        
        div.addEventListener('click', () => this.seekToSegment(index));
        
        return div;
    }

    createDetailedMeta(segment) {
        return `
            <div class="segment-meta">
                <div class="meta-item">
                    <span class="meta-label">Language</span>
                    <span class="meta-value">${segment.detected_language || 'Unknown'}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Duration</span>
                    <span class="meta-value">${this.formatDuration((segment.end || 0) - (segment.start || 0))}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Type</span>
                    <span class="meta-value">${segment.type || 'speech'}</span>
                </div>
                ${segment.emotion_frame ? `
                <div class="meta-item">
                    <span class="meta-label">Frame</span>
                    <span class="meta-value">${segment.emotion_frame}</span>
                </div>
                ` : ''}
            </div>
        `;
    }

    setupFilters() {
        const speakerFilter = document.getElementById('speaker-filter');
        const emotionFilter = document.getElementById('emotion-filter');
        
        // Populate speaker filter
        const speakers = [...new Set(this.data.conversation_segments.map(s => s.speaker).filter(Boolean))];
        speakers.forEach(speaker => {
            const option = document.createElement('option');
            option.value = speaker;
            option.textContent = speaker;
            speakerFilter.appendChild(option);
        });
        
        // Populate emotion filter
        const emotions = [...new Set(this.data.conversation_segments.map(s => s.dominant_emotion).filter(e => e && e !== 'unknown'))];
        emotions.forEach(emotion => {
            const option = document.createElement('option');
            option.value = emotion;
            option.textContent = emotion;
            emotionFilter.appendChild(option);
        });
    }

    applyFilters() {
        const speakerFilter = document.getElementById('speaker-filter').value;
        const emotionFilter = document.getElementById('emotion-filter').value;
        const searchText = document.getElementById('search-text').value.toLowerCase();
        
        this.filteredSegments = this.data.conversation_segments.filter(segment => {
            const matchesSpeaker = !speakerFilter || segment.speaker === speakerFilter;
            const matchesEmotion = !emotionFilter || segment.dominant_emotion === emotionFilter;
            const matchesSearch = !searchText || (segment.text && segment.text.toLowerCase().includes(searchText));
            
            return matchesSpeaker && matchesEmotion && matchesSearch;
        });
        
        this.renderSegments();
    }

    toggleView() {
        this.isDetailedView = !this.isDetailedView;
        const button = document.getElementById('toggle-view');
        button.textContent = this.isDetailedView ? 'Switch to Compact View' : 'Switch to Detailed View';
        
        this.renderSegments();
    }

    playTimeline() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        document.body.classList.add('timeline-playing');
        
        const totalDuration = this.data.summary.total_duration;
        const segmentDuration = totalDuration / this.filteredSegments.length;
        
        this.timelineInterval = setInterval(() => {
            this.currentSegmentIndex++;
            
            if (this.currentSegmentIndex >= this.filteredSegments.length) {
                this.pauseTimeline();
                return;
            }
            
            this.updateTimelineProgress();
            this.highlightCurrentSegment();
        }, segmentDuration * 1000);
    }

    pauseTimeline() {
        this.isPlaying = false;
        document.body.classList.remove('timeline-playing');
        
        if (this.timelineInterval) {
            clearInterval(this.timelineInterval);
            this.timelineInterval = null;
        }
    }

    resetTimeline() {
        this.pauseTimeline();
        this.currentSegmentIndex = 0;
        this.updateTimelineProgress();
        this.highlightCurrentSegment();
    }

    updateTimelineProgress() {
        const progress = (this.currentSegmentIndex / this.filteredSegments.length) * 100;
        document.getElementById('timeline-track').style.width = `${progress}%`;
        document.getElementById('timeline-progress').style.left = `${progress}%`;
    }

    highlightCurrentSegment() {
        // Remove active class from all segments
        document.querySelectorAll('.segment-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current segment
        const currentSegment = document.querySelector(`[data-index="${this.currentSegmentIndex}"]`);
        if (currentSegment) {
            currentSegment.classList.add('active');
            currentSegment.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    seekToSegment(index) {
        this.currentSegmentIndex = index;
        this.updateTimelineProgress();
        this.highlightCurrentSegment();
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    formatDuration(seconds) {
        if (seconds < 60) {
            return `${Math.round(seconds)}s`;
        } else {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.round(seconds % 60);
            return `${minutes}m ${remainingSeconds}s`;
        }
    }

    hideLoadingState() {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('analysis-content').style.display = 'block';
    }

    showErrorState(message) {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('error-state').style.display = 'block';
        document.getElementById('error-message').textContent = message;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConversationAnalysis();
});
