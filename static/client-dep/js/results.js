// Results page JavaScript

document.addEventListener("DOMContentLoaded", () => {
  initializeScoreAnimation()
  initializeDetailedAnalysis()
  initializeTabs()
  initializeActions()
})

function initializeScoreAnimation() {
  const scoreDisplay = document.getElementById("scoreDisplay")
  const scoreBar = document.getElementById("scoreBar")
  const scoreInterpretation = document.getElementById("scoreInterpretation")

  if (!scoreDisplay || !window.analysisData) return

  const score = window.analysisData.score

  // Animate score
  let currentScore = 0
  const scoreInterval = setInterval(() => {
    currentScore += 1
    scoreDisplay.textContent = currentScore + "%"

    if (currentScore >= score) {
      clearInterval(scoreInterval)
      scoreDisplay.textContent = score + "%"
    }
  }, 30)

  // Animate progress bar
  setTimeout(() => {
    scoreBar.style.width = score + "%"
  }, 500)

  // Set interpretation
  let interpretation = ""
  let color = ""

  if (score >= 80) {
    interpretation = "🎉 Excellent match! Votre profil correspond parfaitement au poste."
    color = "#00ff88"
  } else if (score >= 60) {
    interpretation = "👍 Bon match! Quelques améliorations pourraient optimiser votre profil."
    color = "#00d4ff"
  } else if (score >= 40) {
    interpretation = "⚠️ Match modéré. Des améliorations significatives sont recommandées."
    color = "#ffa502"
  } else {
    interpretation = "❌ Match faible. Votre profil nécessite des améliorations importantes."
    color = "#ff4757"
  }

  if (scoreInterpretation) {
    scoreInterpretation.innerHTML = interpretation
    scoreInterpretation.style.color = color
  }
}

function initializeDetailedAnalysis() {
  const detailedAnalysisSection = document.getElementById("detailedAnalysis")
  const toggleButton = document.querySelector('[onclick="toggleDetailedAnalysis()"]')

  if (!toggleButton) return

  window.toggleDetailedAnalysis = () => {
    if (detailedAnalysisSection.style.display === "none" || !detailedAnalysisSection.style.display) {
      // Show detailed analysis
      detailedAnalysisSection.style.display = "block"
      toggleButton.textContent = "📊 Masquer l'analyse détaillée"

      // Load detailed analysis data
      loadDetailedAnalysis()
    } else {
      // Hide detailed analysis
      detailedAnalysisSection.style.display = "none"
      toggleButton.textContent = "📊 Créer une analyse détaillée"
    }
  }
}

function loadDetailedAnalysis() {
  if (!window.analysisData || !window.analysisData.pdf_text) {
    console.error("No analysis data available")
    return
  }

  // Show loading state
  const tabContent = document.querySelector(".tab-content")
  if (tabContent) {
    tabContent.innerHTML =
      '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Génération de l\'analyse détaillée...</div>'
  }

  // Make API call to generate detailed analysis
  fetch("/create-detailed-analysis", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      pdf_text: window.analysisData.pdf_text,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        populateDetailedAnalysis(data)
      } else {
        console.error("Error generating detailed analysis:", data.error)
        showError("Erreur lors de la génération de l'analyse détaillée.")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showError("Erreur de connexion lors de la génération de l'analyse.")
    })
}

function populateDetailedAnalysis(data) {
  // Populate category scores
  const categoryScoresList = document.getElementById("categoryScoresList")
  if (categoryScoresList && data.categorie_scores) {
    categoryScoresList.innerHTML = Object.entries(data.categorie_scores)
      .map(
        ([category, score], index) => `
            <div class="score-item" style="animation-delay: ${index * 0.1}s">
                <div class="score-info">
                    <span class="category-name">${category}</span>
                    <span class="score-value">${score}%</span>
                </div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: ${score}%; background: ${getScoreColor(score)}; animation-delay: ${index * 0.1 + 0.5}s"></div>
                </div>
            </div>
        `,
      )
      .join("")
  }

  // Populate good points
  const goodPointsList = document.getElementById("goodPointsList")
  if (goodPointsList && data.good_points) {
    goodPointsList.innerHTML = data.good_points
      .map(
        (point, index) => `
            <div class="point-item good-point" style="animation-delay: ${index * 0.1}s">
                <div class="point-icon">✓</div>
                <div class="point-text">${point}</div>
            </div>
        `,
      )
      .join("")
  }

  // Populate weak points
  const weakPointsList = document.getElementById("weakPointsList")
  if (weakPointsList && data.weak_points) {
    weakPointsList.innerHTML = data.weak_points
      .map(
        (point, index) => `
            <div class="point-item weak-point" style="animation-delay: ${index * 0.1}s">
                <div class="point-icon">!</div>
                <div class="point-text">${point}</div>
            </div>
        `,
      )
      .join("")
  }

  // Populate improvements
  const improvementsList = document.getElementById("improvementsList")
  if (improvementsList && data.improvements) {
    improvementsList.innerHTML = data.improvements
      .map(
        (improvement, index) => `
            <div class="improvement-item" style="animation-delay: ${index * 0.1}s">
                <div class="improvement-icon">💡</div>
                <div class="improvement-text">${improvement}</div>
            </div>
        `,
      )
      .join("")
  }
}

function getScoreColor(score) {
  if (score >= 80) return "linear-gradient(135deg, #00ff88, #00d4ff)"
  if (score >= 60) return "linear-gradient(135deg, #00d4ff, #667eea)"
  if (score >= 40) return "linear-gradient(135deg, #ffa502, #ff6348)"
  return "linear-gradient(135deg, #ff4757, #ff3838)"
}

function initializeTabs() {
  const tabButtons = document.querySelectorAll(".tab-button")
  const tabPanes = document.querySelectorAll(".tab-pane")

  window.switchTab = (tabId) => {
    // Remove active class from all tabs and panes
    tabButtons.forEach((btn) => btn.classList.remove("active"))
    tabPanes.forEach((pane) => pane.classList.remove("active"))

    // Add active class to selected tab and pane
    const selectedButton = document.querySelector(`[data-tab="${tabId}"]`)
    const selectedPane = document.getElementById(`${tabId}-tab`)

    if (selectedButton) selectedButton.classList.add("active")
    if (selectedPane) selectedPane.classList.add("active")
  }
}

function initializeActions() {
  // Download CV function
  window.downloadCV = () => {
    // Simulate CV download
    const link = document.createElement("a")
    link.href = "#" // This would be the actual CV file URL
    link.download = "cv-analyzed.pdf"
    link.click()

    if (window.CVAnalyzer) {
      window.CVAnalyzer.showNotification("Téléchargement du CV en cours...", "info")
    }
  }

  // Download report function
  window.downloadReport = () => {
    // Simulate report download
    const link = document.createElement("a")
    link.href = "#" // This would be the actual report file URL
    link.download = "rapport-analyse-cv.pdf"
    link.click()

    if (window.CVAnalyzer) {
      window.CVAnalyzer.showNotification("Téléchargement du rapport en cours...", "info")
    }
  }
}

function showError(message) {
  const tabContent = document.querySelector(".tab-content")
  if (tabContent) {
    tabContent.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ff4757;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>${message}</p>
                <button onclick="loadDetailedAnalysis()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--accent-gradient); color: #000; border: none; border-radius: 8px; cursor: pointer;">
                    Réessayer
                </button>
            </div>
        `
  }
}
