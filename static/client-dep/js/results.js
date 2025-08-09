// Global variables
const analysisData = {
  score: 85,
  pdf_text: "Sample CV text content...",
  detailed_analysis: {
    success: true,
    categorie_scores: {
      "Expérience technique": 90,
      "Compétences managériales": 75,
      Formation: 85,
      Langues: 70,
      Projets: 88,
    },
    good_points: [
      "Excellente maîtrise des technologies JavaScript modernes",
      "Expérience solide en développement full-stack",
      "Bonne connaissance des méthodologies agiles",
      "Projets variés démontrant une polyvalence technique",
      "Formation continue et certifications récentes",
    ],
    weak_points: [
      "Manque d'expérience en leadership d'équipe",
      "Peu de projets en architecture cloud native",
      "Absence de certifications en sécurité informatique",
    ],
    improvements: [
      { category: "Leadership", action: "Développer des compétences en management d'équipe" },
      { category: "Cloud", action: "Obtenir des certifications AWS ou Azure" },
      { category: "Sécurité", action: "Suivre une formation en cybersécurité" },
      { category: "Communication", action: "Améliorer les compétences de présentation" },
    ],
  },
}

// Initialize results when page loads
function initializeResults() {
  // Use data from window.analysisData if available, otherwise use default
  const scoreValue = window.analysisData ? window.analysisData.score : analysisData.score
  const bar = document.getElementById("scoreBar")
  const scoreDisplay = document.getElementById("scoreDisplay")
  const interpretation = document.getElementById("scoreInterpretation")

  // Animate score bar
  setTimeout(() => {
    if (bar) {
      bar.style.width = scoreValue + "%"
    }
  }, 500)

  // Set color and interpretation based on score
  let color, message
  if (scoreValue < 50) {
    color = "linear-gradient(135deg, #ff6b6b, #ee5a52)"
    message = "⚠️ Score faible - Optimisation nécessaire"
  } else if (scoreValue < 75) {
    color = "linear-gradient(135deg, #feca57, #ff9ff3)"
    message = "📈 Score correct - Améliorations possibles"
  } else {
    color = "linear-gradient(135deg, #48dbfb, #0abde3)"
    message = "🎉 Excellent score - Profil très adapté !"
  }

  if (bar) {
    bar.style.background = color
  }

  if (interpretation) {
    interpretation.innerHTML = message
    interpretation.style.color = scoreValue < 50 ? "#ef4444" : scoreValue < 75 ? "#f59e0b" : "#10b981"
  }

  // Animate score number
  let currentScore = 0
  const increment = scoreValue / 50
  const timer = setInterval(() => {
    currentScore += increment
    if (currentScore >= scoreValue) {
      currentScore = scoreValue
      clearInterval(timer)
    }
    if (scoreDisplay) {
      scoreDisplay.textContent = Math.round(currentScore) + "%"
    }
  }, 40)

  // Initialize score circles
  initializeScoreCircles()
}

// Initialize score circles
function initializeScoreCircles() {
  const circles = document.querySelectorAll(".score-circle, .score-circle-large")
  circles.forEach((circle) => {
    const score =
      circle.getAttribute("data-score") || (window.analysisData ? window.analysisData.score : analysisData.score)
    circle.style.setProperty("--score", score)
  })
}

// Switch between tabs
function switchTab(tabName) {
  // Remove active class from all tabs and panes
  document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"))
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"))

  // Add active class to selected tab and pane
  const tabButton = document.querySelector(`[data-tab="${tabName}"]`)
  const tabPane = document.getElementById(`${tabName}-tab`)

  if (tabButton) tabButton.classList.add("active")
  if (tabPane) tabPane.classList.add("active")
}

// Populate detailed analysis content
function populateDetailedAnalysis(data) {
  if (!data || !data.success) return

  // Populate category scores
  const categoryScoresList = document.getElementById("categoryScoresList")
  if (categoryScoresList && data.categorie_scores) {
    categoryScoresList.innerHTML = ""
    Object.entries(data.categorie_scores).forEach(([category, score], index) => {
      // Ensure score is a number
      const numericScore = Number.parseInt(score) || 0

      const scoreItem = document.createElement("div")
      scoreItem.className = "score-item"
      scoreItem.style.animationDelay = `${index * 0.1}s`

      scoreItem.innerHTML = `
      <div class="score-info">
        <span class="category-name">${category}</span>
        <span class="score-value">${numericScore}%</span>
      </div>
      <div class="score-bar-container">
        <div class="score-bar" style="width: 0%; background: ${getScoreColorGradient(numericScore)}; transition: width 1.5s ease-out; height: 10px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>
      </div>
    `

      categoryScoresList.appendChild(scoreItem)

      // Force a reflow to ensure the bar starts at 0%
      const bar = scoreItem.querySelector(".score-bar")
      if (bar) {
        // Force reflow
        bar.offsetHeight

        // Animate the score bar with a slight delay
        setTimeout(
          () => {
            bar.style.width = numericScore + "%"
          },
          300 + index * 150,
        )
      }
    })
  }

  // Populate good points
  const goodPointsList = document.getElementById("goodPointsList")
  if (goodPointsList && Array.isArray(data.good_points)) {
    goodPointsList.innerHTML = ""
    data.good_points.forEach((point, index) => {
      const pointItem = document.createElement("div")
      pointItem.className = "point-item good-point"
      pointItem.style.animationDelay = `${index * 0.1}s`
      pointItem.innerHTML = `
                <div class="point-icon">✓</div>
                <div class="point-text">${point}</div>
            `
      goodPointsList.appendChild(pointItem)
    })
  }

  // Populate weak points
  const weakPointsList = document.getElementById("weakPointsList")
  if (weakPointsList) {
    weakPointsList.innerHTML = ""
    if (Array.isArray(data.weak_points) && data.weak_points.length) {
      data.weak_points.forEach((point, index) => {
        const pointItem = document.createElement("div")
        pointItem.className = "point-item weak-point"
        pointItem.style.animationDelay = `${index * 0.1}s`
        pointItem.innerHTML = `
                    <div class="point-icon">⚠</div>
                    <div class="point-text">${point}</div>
                `
        weakPointsList.appendChild(pointItem)
      })
    } else {
      const noDataItem = document.createElement("div")
      noDataItem.className = "point-item weak-point"
      noDataItem.innerHTML = `
                <div class="point-icon">ℹ</div>
                <div class="point-text">Aucun point faible majeur identifié dans cette analyse.</div>
            `
      weakPointsList.appendChild(noDataItem)
    }
  }

  // Populate improvements
  const improvementsList = document.getElementById("improvementsList")
  if (improvementsList && Array.isArray(data.improvements)) {
    improvementsList.innerHTML = ""
    data.improvements.forEach((improvement, index) => {
      const improvementItem = document.createElement("div")
      improvementItem.className = "improvement-item"
      improvementItem.style.animationDelay = `${index * 0.1}s`

      const isObject = typeof improvement === "object" && improvement !== null
      const category = isObject ? improvement.category || "Général" : "Général"
      const action = isObject ? improvement.action || improvement.improvement || "" : String(improvement)

      improvementItem.innerHTML = `
                <span class="improvement-category">${category}</span>
                <div class="improvement-text">${action}</div>
            `
      improvementsList.appendChild(improvementItem)
    })
  }
}

// Get color based on score - Enhanced with beautiful gradients
function getScoreColor(score) {
  if (score >= 90) return "#00ff88" // Excellent - Bright Green
  if (score >= 80) return "#48dbfb" // Very Good - Cyan
  if (score >= 70) return "#feca57" // Good - Yellow
  if (score >= 60) return "#ff9ff3" // Average - Pink
  if (score >= 50) return "#ff6b6b" // Below Average - Light Red
  return "#ee5a52" // Poor - Red
}

// Get gradient color based on score - New function for beautiful gradients
function getScoreColorGradient(score) {
  if (score >= 90) return "linear-gradient(135deg, #00ff88, #00d4ff)" // Excellent - Green to Cyan
  if (score >= 80) return "linear-gradient(135deg, #48dbfb, #0abde3)" // Very Good - Light to Dark Cyan
  if (score >= 70) return "linear-gradient(135deg, #feca57, #ff9ff3)" // Good - Yellow to Pink
  if (score >= 60) return "linear-gradient(135deg, #ff9ff3, #feca57)" // Average - Pink to Yellow
  if (score >= 50) return "linear-gradient(135deg, #ff6b6b, #ee5a52)" // Below Average - Light to Dark Red
  return "linear-gradient(135deg, #ee5a52, #c44569)" // Poor - Red to Dark Red
}

// Download functions
function downloadCV() {
  showNotification("Fonctionnalité de téléchargement CV en cours de développement !", "info")
}

function downloadReport() {
  showNotification("Fonctionnalité de téléchargement PDF en cours de développement !", "info")
}

// Modal functions
function openModal() {
  const modal = document.getElementById("modalOverlay")
  if (modal) {
    modal.classList.add("show")
    document.body.style.overflow = "hidden"
  }
}

function closeModal() {
  const modal = document.getElementById("modalOverlay")
  if (modal) {
    modal.classList.remove("show")
    document.body.style.overflow = ""
  }
}

// Notification system
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
        </div>
    `

  // Add styles
  notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 2rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        color: var(--text-primary);
        z-index: 10001;
        transform: translateX(400px);
        transition: transform var(--transition-normal);
        box-shadow: var(--shadow-lg);
        max-width: 300px;
    `

  if (type === "success") {
    notification.style.borderLeftColor = "var(--accent-green)"
    notification.style.borderLeftWidth = "4px"
  } else if (type === "error") {
    notification.style.borderLeftColor = "var(--accent-red)"
    notification.style.borderLeftWidth = "4px"
  } else if (type === "warning") {
    notification.style.borderLeftColor = "var(--accent-orange)"
    notification.style.borderLeftWidth = "4px"
  }

  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)

  // Hide notification after 3 seconds
  setTimeout(() => {
    notification.style.transform = "translateX(400px)"
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }, 3000)
}

function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "✅"
    case "error":
      return "❌"
    case "warning":
      return "⚠️"
    default:
      return "ℹ️"
  }
}

// Navbar scroll effect
function handleNavbarScroll() {
  const navbar = document.querySelector(".navbar")
  if (navbar) {
    if (window.scrollY > 100) {
      navbar.style.background = "rgba(255, 255, 255, 0.98)"
      navbar.style.boxShadow = "var(--shadow-md)"
    } else {
      navbar.style.background = "rgba(255, 255, 255, 0.95)"
      navbar.style.boxShadow = "none"
    }
  }
}

// Add CSS styles for score bars with beautiful colors
const addScoreBarStyles = () => {
  const existingStyle = document.getElementById("score-bar-styles")
  if (!existingStyle) {
    const style = document.createElement("style")
    style.id = "score-bar-styles"
    style.textContent = `
      .score-item {
        margin-bottom: 1.5rem;
        padding: 1.25rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: fadeInUp 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(20px);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
      }
      
      .score-item:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
      }
      
      .score-item.animate {
        opacity: 1;
        transform: translateY(0);
      }
      
      .score-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
      }
      
      .category-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 1.1rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
      }
      
      .score-value {
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.2rem;
        text-shadow: none;
      }
      
      .score-bar-container {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 6px;
        height: 10px;
        overflow: hidden;
        position: relative;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      
      .score-bar {
        height: 100%;
        border-radius: 6px;
        transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      }
      
      .score-bar::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, 
          rgba(255,255,255,0) 0%, 
          rgba(255,255,255,0.3) 50%, 
          rgba(255,255,255,0) 100%);
        animation: shimmer 2s infinite;
      }
      
      .score-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 50%;
        background: linear-gradient(180deg, 
          rgba(255,255,255,0.4) 0%, 
          rgba(255,255,255,0) 100%);
        border-radius: 6px 6px 0 0;
      }
      
      /* Color-specific glow effects */
      .score-bar[style*="00ff88"] {
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
      }
      
      .score-bar[style*="48dbfb"] {
        box-shadow: 0 0 20px rgba(72, 219, 251, 0.4);
      }
      
      .score-bar[style*="feca57"] {
        box-shadow: 0 0 20px rgba(254, 202, 87, 0.4);
      }
      
      .score-bar[style*="ff9ff3"] {
        box-shadow: 0 0 20px rgba(255, 159, 243, 0.4);
      }
      
      .score-bar[style*="ff6b6b"] {
        box-shadow: 0 0 20px rgba(255, 107, 107, 0.4);
      }
      
      @keyframes fadeInUp {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      
      @keyframes shimmer {
        0% { 
          transform: translateX(-100%); 
        }
        100% { 
          transform: translateX(100%); 
        }
      }
      
      /* Pulse animation for high scores */
      .score-bar[style*="00ff88"]::before {
        animation: shimmer 2s infinite, pulse-green 3s infinite;
      }
      
      @keyframes pulse-green {
        0%, 100% { 
          box-shadow: 0 0 20px rgba(0, 255, 136, 0.4); 
        }
        50% { 
          box-shadow: 0 0 30px rgba(0, 255, 136, 0.6); 
        }
      }
    `
    document.head.appendChild(style)
  }
}

// Initialize everything when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Add score bar styles
  addScoreBarStyles()

  initializeResults()

  // Populate detailed analysis immediately since it's always visible
  // Check if detailed analysis data is available from server
  if (window.detailedAnalysisData && window.detailedAnalysisData.success) {
    populateDetailedAnalysis(window.detailedAnalysisData)
  } else if (analysisData.detailed_analysis && analysisData.detailed_analysis.success !== false) {
    populateDetailedAnalysis(analysisData.detailed_analysis)
  }

  // Add scroll listener for navbar
  window.addEventListener("scroll", handleNavbarScroll)

  // Close modal when clicking outside
  const modalOverlay = document.getElementById("modalOverlay")
  if (modalOverlay) {
    modalOverlay.addEventListener("click", (e) => {
      if (e.target === modalOverlay) {
        closeModal()
      }
    })
  }

  // Handle escape key for modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal()
    }
  })
})

// Handle window resize
window.addEventListener("resize", () => {
  // Reinitialize score circles on resize
  initializeScoreCircles()
})

// Export functions for global access
window.switchTab = switchTab
window.downloadCV = downloadCV
window.downloadReport = downloadReport
window.openModal = openModal
window.closeModal = closeModal
