// Authentication JavaScript

document.addEventListener("DOMContentLoaded", () => {
  initializePasswordToggle()
  initializePasswordStrength()
  initializeFormValidation()
  initializeSocialLogin()
})

function initializePasswordToggle() {
  const passwordToggles = document.querySelectorAll(".password-toggle")

  passwordToggles.forEach((toggle) => {
    toggle.addEventListener("click", function () {
      const input = this.parentElement.querySelector("input")
      const icon = this.querySelector("i")

      if (input.type === "password") {
        input.type = "text"
        icon.classList.remove("fa-eye")
        icon.classList.add("fa-eye-slash")
      } else {
        input.type = "password"
        icon.classList.remove("fa-eye-slash")
        icon.classList.add("fa-eye")
      }
    })
  })
}

function initializePasswordStrength() {
  const passwordInput = document.getElementById("password")
  const strengthFill = document.getElementById("strengthFill")
  const strengthText = document.getElementById("strengthText")

  if (!passwordInput || !strengthFill || !strengthText) return

  passwordInput.addEventListener("input", function () {
    const password = this.value
    const strength = calculatePasswordStrength(password)

    // Update strength bar
    strengthFill.style.width = strength.percentage + "%"
    strengthFill.style.background = strength.color

    // Update strength text
    strengthText.textContent = strength.text
    strengthText.style.color = strength.color
  })
}

function calculatePasswordStrength(password) {
  let score = 0
  const feedback = []

  if (password.length >= 8) score += 25
  else feedback.push("8+ caractères")

  if (/[a-z]/.test(password)) score += 25
  else feedback.push("minuscules")

  if (/[A-Z]/.test(password)) score += 25
  else feedback.push("majuscules")

  if (/[0-9]/.test(password)) score += 25
  else feedback.push("chiffres")

  if (/[^A-Za-z0-9]/.test(password)) score += 10
  else feedback.push("caractères spéciaux")

  const strength = {
    percentage: Math.min(score, 100),
    color: "#ff4757",
    text: "Très faible",
  }

  if (score >= 90) {
    strength.color = "#00ff88"
    strength.text = "Très fort"
  } else if (score >= 70) {
    strength.color = "#00d4ff"
    strength.text = "Fort"
  } else if (score >= 50) {
    strength.color = "#ffa502"
    strength.text = "Moyen"
  } else if (score >= 25) {
    strength.color = "#ff6348"
    strength.text = "Faible"
  }

  if (feedback.length > 0 && password.length > 0) {
    strength.text += ` (manque: ${feedback.join(", ")})`
  }

  return strength
}

function initializeFormValidation() {
  const loginForm = document.getElementById("loginForm")
  const signupForm = document.getElementById("signupForm")

  if (loginForm) {
    loginForm.addEventListener("submit", handleLoginSubmit)
  }

  if (signupForm) {
    signupForm.addEventListener("submit", handleSignupSubmit)

    // Password confirmation validation
    const password = document.getElementById("password")
    const confirmPassword = document.getElementById("confirmPassword")

    if (password && confirmPassword) {
      confirmPassword.addEventListener("input", function () {
        if (this.value !== password.value) {
          this.setCustomValidity("Les mots de passe ne correspondent pas")
        } else {
          this.setCustomValidity("")
        }
      })
    }
  }
}

function handleLoginSubmit(e) {
  e.preventDefault()

  const submitBtn = document.getElementById("submitBtn")
  const btnContent = document.getElementById("btnContent")
  const loadingSpinner = document.getElementById("loadingSpinner")
  const errorMessage = document.getElementById("errorMessage")
  const successMessage = document.getElementById("successMessage")

  // Show loading state
  submitBtn.classList.add("loading")
  btnContent.style.display = "none"
  loadingSpinner.style.display = "flex"

  // Hide previous messages
  errorMessage.style.display = "none"
  successMessage.style.display = "none"

  // Get form data
  const formData = new FormData(e.target)
  const loginData = {
    email: formData.get("email"),
    password: formData.get("password"),
    remember: formData.get("remember") === "on",
  }

  // Simulate login API call
  setTimeout(() => {
    // Demo credentials check
    if (loginData.email === "client@cvanalyzer.com" && loginData.password === "client123") {
      // Success
      successMessage.style.display = "flex"

      setTimeout(() => {
        window.location.href = "/"
      }, 1500)
    } else {
      // Error
      errorMessage.style.display = "flex"

      // Reset button
      submitBtn.classList.remove("loading")
      btnContent.style.display = "flex"
      loadingSpinner.style.display = "none"
    }
  }, 2000)
}

function handleSignupSubmit(e) {
  e.preventDefault()

  const submitBtn = document.getElementById("submitBtn")
  const btnContent = document.getElementById("btnContent")
  const loadingSpinner = document.getElementById("loadingSpinner")
  const errorMessage = document.getElementById("errorMessage")
  const successMessage = document.getElementById("successMessage")
  const acceptTerms = document.getElementById("acceptTerms")

  // Check terms acceptance
  if (!acceptTerms.checked) {
    errorMessage.querySelector("#errorText").textContent = "Vous devez accepter les conditions d'utilisation."
    errorMessage.style.display = "flex"
    return
  }

  // Show loading state
  submitBtn.classList.add("loading")
  btnContent.style.display = "none"
  loadingSpinner.style.display = "flex"

  // Hide previous messages
  errorMessage.style.display = "none"
  successMessage.style.display = "none"

  // Get form data
  const formData = new FormData(e.target)
  const signupData = {
    firstName: formData.get("firstName"),
    lastName: formData.get("lastName"),
    email: formData.get("email"),
    password: formData.get("password"),
    newsletter: formData.get("newsletter") === "on",
  }

  // Simulate signup API call
  setTimeout(() => {
    // Simulate success (in real app, handle actual API response)
    successMessage.style.display = "flex"

    // Reset form
    e.target.reset()

    // Reset button
    setTimeout(() => {
      submitBtn.classList.remove("loading")
      btnContent.style.display = "flex"
      loadingSpinner.style.display = "none"
    }, 2000)
  }, 2000)
}

function initializeSocialLogin() {
  const socialButtons = document.querySelectorAll(".social-btn")

  socialButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const provider = this.classList.contains("google-btn")
        ? "Google"
        : this.classList.contains("microsoft-btn")
          ? "Microsoft"
          : "LinkedIn"

      // Simulate social login
      this.style.opacity = "0.6"
      this.style.pointerEvents = "none"

      setTimeout(() => {
        alert(`Connexion avec ${provider} simulée. Cette fonctionnalité sera disponible prochainement.`)

        this.style.opacity = "1"
        this.style.pointerEvents = "auto"
      }, 1000)
    })
  })
}
