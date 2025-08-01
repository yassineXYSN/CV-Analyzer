// Initialize results
function initializeResults() {
  const scoreValue = Number.parseFloat("{{ score }}".replace(",", "."))
  const bar = document.getElementById("scoreBar")
  const scoreDisplay = document.getElementById("scoreDisplay")
  const interpretation = document.getElementById("scoreInterpretation")

  // Animate score bar
  setTimeout(() => {
    bar.style.width = scoreValue + "%"
  }, 500)

  // Set color and interpretation based on score
  let color, message
  if (scoreValue < 50) {
    color = "var(--danger-gradient)"
    message = "⚠️ Score faible - Optimisation nécessaire"
  } else if (scoreValue < 75) {
    color = "var(--warning-gradient)"
    message = "📈 Score correct - Améliorations possibles"
  } else {
    color = "var(--accent-gradient)"
    message = "🎉 Excellent score - Profil très adapté !"
  }

  bar.style.background = color
  interpretation.innerHTML = message
  interpretation.style.color = scoreValue < 50 ? "#ff4757" : scoreValue < 75 ? "#ffa502" : "#00ff88"

  // Animate score number
  let currentScore = 0
  const increment = scoreValue / 50
  const timer = setInterval(() => {
    currentScore += increment
    if (currentScore >= scoreValue) {
      currentScore = scoreValue
      clearInterval(timer)
    }
    scoreDisplay.textContent = Math.round(currentScore) + "%"
  }, 40)
}

// Switch between tabs
function switchTab(tabName) {
  // Remove active class from all tabs and panes
  document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"))
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"))

  // Add active class to selected tab and pane
  document.querySelector(`[data-tab="${tabName}"]`).classList.add("active")
  document.getElementById(`${tabName}-tab`).classList.add("active")
}

// Toggle detailed analysis
async function toggleDetailedAnalysis() {
  const detailedSection = document.getElementById("detailedAnalysis")
  const button = document.getElementById("createDetailedAnalysisButton") // Get button by its ID

  // If the button is already hidden, do nothing (safety check)
  if (button.style.display === "none") {
    return
  }

  // Show loading state
  button.innerHTML = "⏳ Création d'une analyse détaillée en cours..."
  button.disabled = true
  button.style.opacity = "0.6"
  button.style.cursor = "not-allowed"

  try {
    // Fetch detailed analysis
    const response = await fetch("/create-detailed-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: "{{ filename }}", // This will still be a Jinja variable from the HTML context
        summary: `{{ summary }}`, // This will still be a Jinja variable from the HTML context
        pdf_text: window.analysisData.pdf_text, // Use data passed to window.analysisData
        score: window.analysisData.score, // Use data passed to window.analysisData
      }),
    })

    if (!response.ok) {
      throw new Error("Erreur réseau: " + response.status)
    }

    const data = await response.json()
    console.log("Received data:", data) // Debug log

    if (!data.success) {
      throw new Error(data.error || "Erreur inconnue")
    }

    // Populate detailed analysis
    populateDetailedAnalysis(data)

    // Show the section
    detailedSection.style.display = "block"

    // Hide the button permanently after successful generation
    button.style.display = "none"

    // Smooth scroll to detailed section with offset for navbar
    setTimeout(() => {
      const navbarHeight = document.querySelector(".navbar").offsetHeight
      const elementPosition = detailedSection.offsetTop - navbarHeight - 20

      window.scrollTo({
        top: elementPosition,
        behavior: "smooth",
      })
    }, 300)
  } catch (error) {
    console.error("Erreur:", error)
    alert("Erreur lors de la création de l'analyse détaillée: " + error.message)
    // Reset button state if there was an error, so user can try again
    button.innerHTML = "📊 Créer une analyse détaillée"
    button.disabled = false
    button.style.opacity = "1"
    button.style.cursor = "pointer"
  }
}

// Populate detailed analysis content
function populateDetailedAnalysis(data) {
  console.log("Populating detailed analysis with data:", data)

  // Populate category scores
  const categoryScoresList = document.getElementById("categoryScoresList")
  categoryScoresList.innerHTML = ""

  if (data.categorie_scores) {
    Object.entries(data.categorie_scores).forEach(([category, score], index) => {
      const scoreItem = document.createElement("div")
      scoreItem.className = "score-item"
      scoreItem.style.animationDelay = `${index * 0.1}s`

      scoreItem.innerHTML = `
                        <div class="score-info">
                            <span class="category-name">${category}</span>
                            <span class="score-value">${score}%</span>
                        </div>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: 0%; background: ${getScoreColor(score)}; transition: width 1.5s ease;"></div>
                        </div>
                    `

      categoryScoresList.appendChild(scoreItem)

      // Animate the score bar
      setTimeout(
        () => {
          const bar = scoreItem.querySelector(".score-bar")
          bar.style.width = score + "%"
        },
        200 + index * 100,
      )
    })
  }

  // Populate good points
  const goodPointsList = document.getElementById("goodPointsList")
  goodPointsList.innerHTML = ""

  if (data.good_points && Array.isArray(data.good_points)) {
    console.log("Good points:", data.good_points)
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
  weakPointsList.innerHTML = ""

  if (data.weak_points && Array.isArray(data.weak_points)) {
    console.log("Weak points:", data.weak_points)
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
    console.log("No weak points data found:", data.weak_points)
    // Add a fallback message
    const noDataItem = document.createElement("div")
    noDataItem.className = "point-item weak-point"
    noDataItem.innerHTML = `
                    <div class="point-icon">ℹ</div>
                    <div class="point-text">Aucun point faible majeur identifié dans cette analyse.</div>
                `
    weakPointsList.appendChild(noDataItem)
  }

  // Populate improvements
  const improvementsList = document.getElementById("improvementsList")
  improvementsList.innerHTML = ""

  if (data.improvements && Array.isArray(data.improvements)) {
    console.log("Improvements:", data.improvements)
    data.improvements.forEach((improvement, index) => {
      const improvementItem = document.createElement("div")
      improvementItem.className = "improvement-item"
      improvementItem.style.animationDelay = `${index * 0.1}s`
      improvementItem.innerHTML = `
                        <div class="improvement-icon">💡</div>
                        <div class="improvement-text">${improvement}</div>
                    `
      improvementsList.appendChild(improvementItem)
    })
  }
}

// Get color based on score
function getScoreColor(score) {
  if (score >= 80) return "var(--accent-gradient)"
  if (score >= 60) return "var(--warning-gradient)"
  return "var(--danger-gradient)"
}

// Create account function
function createAccount() {
  const formData = {
    fullName: document.getElementById("fullName").value,
    email: document.getElementById("email").value,
    phone: document.getElementById("phone").value,
    currentPosition: document.getElementById("currentPosition").value,
    experience: document.getElementById("experience").value,
    skills: document.getElementById("skills").value,
    cvAnalysis: {
      score: "{{ score }}",
      summary: "{{ summary }}",
      filename: "{{ filename }}",
    },
  }

  // Validate required fields
  if (!formData.fullName || !formData.email) {
    alert("⚠️ Veuillez remplir au moins votre nom et email.")
    return
  }

  // Simulate account creation
  const button = event.target
  button.innerHTML = '<span class="loading-spinner"></span> Création en cours...'
  button.disabled = true

  setTimeout(() => {
    alert("🎉 Profil créé avec succès ! Vous recevrez un email de confirmation.")
    button.innerHTML = "✅ Profil créé !"
    button.style.background = "var(--accent-gradient)"

    // Show success message
    const successMsg = document.createElement("div")
    successMsg.style.cssText = `
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid rgba(0, 255, 136, 0.3);
                    border-radius: 12px;
                    padding: 1rem;
                    margin-top: 1rem;
                    text-align: center;
                    color: #00ff88;
                `
    successMsg.innerHTML =
      "🎉 Votre profil professionnel a été créé ! Vous pouvez maintenant suivre vos analyses et candidatures."
    button.parentNode.appendChild(successMsg)
  }, 2000)
}

// Download CV function
function downloadCV() {
  alert("Fonctionnalité de téléchargement CV en cours de développement !")
}

// Download report function
function downloadReport() {
  alert("Fonctionnalité de téléchargement PDF en cours de développement !")
}

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
  initializeResults()
})

// Navbar scroll effect
window.addEventListener("scroll", () => {
  const navbar = document.querySelector(".navbar")
  if (window.scrollY > 100) {
    navbar.style.background = "rgba(10, 10, 10, 0.95)"
  } else {
    navbar.style.background = "rgba(10, 10, 10, 0.9)"
  }
})
