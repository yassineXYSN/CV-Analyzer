// Variables globales
let currentStep = 1
const totalSteps = 4
let formData = {}

// Initialisation
document.addEventListener("DOMContentLoaded", () => {
  updateProgress()
  setupFormValidation()
  setupCharacterCounter()
})

// Navigation entre les étapes
function nextStep() {
  if (validateCurrentStep()) {
    if (currentStep < totalSteps) {
      currentStep++
      updateStepDisplay()
      updateProgress()

      if (currentStep === totalSteps) {
        generateSummary()
      }
    }
  }
}

function previousStep() {
  if (currentStep > 1) {
    currentStep--
    updateStepDisplay()
    updateProgress()
  }
}

// Mise à jour de l'affichage des étapes
function updateStepDisplay() {
  // Masquer toutes les étapes
  document.querySelectorAll(".step-content").forEach((step) => {
    step.classList.remove("active")
  })

  // Afficher l'étape actuelle
  document.querySelector(`.step-content[data-step="${currentStep}"]`).classList.add("active")

  // Mettre à jour les indicateurs d'étapes
  document.querySelectorAll(".step").forEach((step, index) => {
    const stepNumber = index + 1
    step.classList.remove("active", "completed")

    if (stepNumber < currentStep) {
      step.classList.add("completed")
    } else if (stepNumber === currentStep) {
      step.classList.add("active")
    }
  })

  // Mettre à jour les boutons de navigation
  const prevBtn = document.getElementById("prevBtn")
  const nextBtn = document.getElementById("nextBtn")
  const finishBtn = document.getElementById("finishBtn")

  prevBtn.style.display = currentStep > 1 ? "flex" : "none"
  nextBtn.style.display = currentStep < totalSteps ? "flex" : "none"
  finishBtn.style.display = currentStep === totalSteps ? "flex" : "none"
}

// Mise à jour de la barre de progression
function updateProgress() {
  const progressFill = document.getElementById("progressFill")
  const percentage = (currentStep / totalSteps) * 100
  progressFill.style.width = `${percentage}%`
}

// Validation de l'étape actuelle
function validateCurrentStep() {
  const currentStepElement = document.querySelector(`.step-content[data-step="${currentStep}"]`)
  const requiredFields = currentStepElement.querySelectorAll("[required]")
  let isValid = true

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      showFieldError(field, "Ce champ est requis")
      isValid = false
    } else {
      showFieldSuccess(field)
    }
  })

  // Validation spécifique par étape
  if (currentStep === 1) {
    isValid = validateStep1() && isValid
  } else if (currentStep === 2) {
    isValid = validateStep2() && isValid
  } else if (currentStep === 3) {
    isValid = validateStep3() && isValid
  }

  return isValid
}

// Validation étape 1
function validateStep1() {
  const companyName = document.getElementById("companyName")
  const industry = document.getElementById("industry")
  const companySize = document.getElementById("companySize")

  let isValid = true

  if (companyName.value.length < 2) {
    showFieldError(companyName, "Le nom doit contenir au moins 2 caractères")
    isValid = false
  }

  return isValid
}

// Validation étape 2
function validateStep2() {
  const email = document.getElementById("email")
  const phone = document.getElementById("phone")

  let isValid = true

  // Validation email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    showFieldError(email, "Veuillez entrer un email valide")
    isValid = false
  }

  // Validation téléphone
  const phoneRegex = /^[+]?216[0-9\s\-]{8,}$/
  if (!phoneRegex.test(phone.value)) {
    showFieldError(phone, "Veuillez entrer un numéro de téléphone valide")
    isValid = false
  }

  return isValid
}

// Validation étape 3
function validateStep3() {
  const description = document.getElementById("description")
  const adminName = document.getElementById("adminName")

  let isValid = true

  if (description.value.length < 50) {
    showFieldError(description, "La description doit contenir au moins 50 caractères")
    isValid = false
  }

  if (adminName.value.split(" ").length < 2) {
    showFieldError(adminName, "Veuillez entrer votre prénom et nom")
    isValid = false
  }

  return isValid
}

// Affichage des erreurs de champ
function showFieldError(field, message) {
  field.style.borderColor = "#e74c3c"
  const feedback = field.parentElement.querySelector(".input-feedback")
  if (feedback) {
    feedback.textContent = message
    feedback.className = "input-feedback error"
  }

  // Animation de secousse
  field.style.animation = "shake 0.5s ease-in-out"
  setTimeout(() => {
    field.style.animation = ""
  }, 500)
}

// Affichage du succès de champ
function showFieldSuccess(field) {
  field.style.borderColor = "#27ae60"
  const feedback = field.parentElement.querySelector(".input-feedback")
  if (feedback) {
    feedback.textContent = "✓ Valide"
    feedback.className = "input-feedback success"
  }
}

// Configuration de la validation en temps réel
function setupFormValidation() {
  const inputs = document.querySelectorAll(".form-input, .form-select, .form-textarea")

  inputs.forEach((input) => {
    input.addEventListener("blur", () => {
      if (input.hasAttribute("required") && input.value.trim()) {
        showFieldSuccess(input)
      }
    })

    input.addEventListener("input", () => {
      if (input.style.borderColor === "rgb(231, 76, 60)") {
        input.style.borderColor = ""
        const feedback = input.parentElement.querySelector(".input-feedback")
        if (feedback) {
          feedback.textContent = ""
          feedback.className = "input-feedback"
        }
      }
    })
  })
}

// Configuration du compteur de caractères
function setupCharacterCounter() {
  const description = document.getElementById("description")
  const charCount = document.getElementById("charCount")

  description.addEventListener("input", () => {
    const count = description.value.length
    charCount.textContent = count

    if (count > 500) {
      charCount.style.color = "#e74c3c"
      description.value = description.value.substring(0, 500)
      charCount.textContent = "500"
    } else if (count > 450) {
      charCount.style.color = "#f39c12"
    } else {
      charCount.style.color = "#7f8c8d"
    }
  })
}

// Génération du récapitulatif
function generateSummary() {
  const summaryContent = document.getElementById("summaryContent")

  const data = {
    Entreprise: document.getElementById("companyName").value,
    Secteur: document.getElementById("industry").options[document.getElementById("industry").selectedIndex].text,
    Taille: document.getElementById("companySize").value,
    Email: document.getElementById("email").value,
    Téléphone: document.getElementById("phone").value,
    Administrateur: document.getElementById("adminName").value,
    Fonction: document.getElementById("adminRole").value,
  }

  summaryContent.innerHTML = Object.entries(data)
    .filter(([key, value]) => value)
    .map(
      ([key, value]) => `
      <div class="summary-item">
        <span class="summary-label">${key}</span>
        <span class="summary-value">${value}</span>
      </div>
    `,
    )
    .join("")
}

// Finalisation de la configuration
function finishSetup() {
  // Collecter toutes les données
  formData = {
    companyName: document.getElementById("companyName").value,
    industry: document.getElementById("industry").value,
    companySize: document.getElementById("companySize").value,
    foundedYear: document.getElementById("foundedYear").value,
    address: document.getElementById("address").value,
    phone: document.getElementById("phone").value,
    email: document.getElementById("email").value,
    website: document.getElementById("website").value,
    description: document.getElementById("description").value,
    adminName: document.getElementById("adminName").value,
    adminRole: document.getElementById("adminRole").value,
    setupDate: new Date().toISOString(),
  }

  // Afficher le loading
  document.getElementById("loadingOverlay").style.display = "flex"

  // Simuler la sauvegarde
  setTimeout(() => {
    // Sauvegarder dans le localStorage
    localStorage.setItem("companyProfile", JSON.stringify(formData))
    localStorage.setItem("setupCompleted", "true")

    // Rediriger vers le dashboard
    window.location.href = "/dashboard"
  }, 3000)
}

// Animation de secousse pour les erreurs
const shakeKeyframes = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
  }
`

// Ajouter les keyframes au document
const style = document.createElement("style")
style.textContent = shakeKeyframes
document.head.appendChild(style)

// Gestion des raccourcis clavier
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault()
    if (currentStep < totalSteps) {
      nextStep()
    } else {
      finishSetup()
    }
  }

  if (e.key === "ArrowLeft" && e.ctrlKey) {
    e.preventDefault()
    previousStep()
  }

  if (e.key === "ArrowRight" && e.ctrlKey) {
    e.preventDefault()
    nextStep()
  }
})
