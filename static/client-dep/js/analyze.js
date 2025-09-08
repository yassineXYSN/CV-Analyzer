// Analyze page JavaScript

document.addEventListener("DOMContentLoaded", () => {
  initializeFileUpload()
  initializeProfileModal()
  initializeFormSubmission()
  loadHeaderComponent()
  loadJobProfiles()
})

let selectedProfiles = []
let availableJobProfiles = []

function initializeFileUpload() {
  const fileUploadArea = document.getElementById("fileUploadArea")
  const fileInput = document.getElementById("filetoscan")
  const uploadText = document.getElementById("uploadText")

  // Drag and drop functionality
  fileUploadArea.addEventListener("dragover", (e) => {
    e.preventDefault()
    fileUploadArea.classList.add("dragover")
  })

  fileUploadArea.addEventListener("dragleave", (e) => {
    e.preventDefault()
    fileUploadArea.classList.remove("dragover")
  })

  fileUploadArea.addEventListener("drop", (e) => {
    e.preventDefault()
    fileUploadArea.classList.remove("dragover")

    const files = e.dataTransfer.files
    if (files.length > 0) {
      fileInput.files = files
      updateFileDisplay(files[0])
    }
  })

  // File input change
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      updateFileDisplay(e.target.files[0])
    }
  })

  function updateFileDisplay(file) {
    const fileName = file.name
    const fileSize = (file.size / 1024 / 1024).toFixed(2)

    uploadText.innerHTML = `
            <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">
                📄 ${fileName}
            </div>
            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                Taille: ${fileSize} MB
            </div>
        `

    fileUploadArea.style.borderColor = "rgba(0, 212, 255, 0.5)"
    fileUploadArea.style.background = "rgba(0, 212, 255, 0.05)"
  }
}

function initializeProfileModal() {
  const profileSelectorBtn = document.getElementById("profileSelectorBtn")
  const profileModal = document.getElementById("profileSelectionModal")
  const closeModalBtn = document.getElementById("closeProfileModal")
  const cancelModalBtn = document.getElementById("cancelProfileModal")
  const confirmModalBtn = document.getElementById("confirmProfileModal")
  const customProfileInput = document.getElementById("customProfileInput")
  const addCustomBtn = document.getElementById("addCustomBtn")
  const profileSearch = document.getElementById("profileSearch")

  // Open modal
  profileSelectorBtn.addEventListener("click", () => {
    console.log("[v0] Profile selector button clicked")
    console.log("[v0] Modal element:", profileModal)

    if (profileModal) {
      profileModal.classList.add("active")
      document.body.style.overflow = "hidden"
      console.log("[v0] Modal should now be visible")
    } else {
      console.error("[v0] Modal element not found!")
    }
  })

  // Close modal
  function closeModal() {
    console.log("[v0] Closing modal")
    if (profileModal) {
      profileModal.classList.remove("active")
      document.body.style.overflow = ""
    }
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", closeModal)
  }

  if (cancelModalBtn) {
    cancelModalBtn.addEventListener("click", closeModal)
  }

  if (profileModal) {
    profileModal.addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-overlay")) {
        closeModal()
      }
    })
  }

  // Add custom profile
  if (addCustomBtn && customProfileInput) {
    addCustomBtn.addEventListener("click", () => {
      const customName = customProfileInput.value.trim()
      if (customName) {
        const customId = "custom_" + Date.now()
        selectedProfiles.push({
          id: customId,
          name: customName,
          custom: true,
        })

        customProfileInput.value = ""
        updateSelectedProfiles()
        updateProfileSelector()
      }
    })

    // Custom profile input enter key
    customProfileInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        addCustomBtn.click()
      }
    })
  }

  // Search functionality
  if (profileSearch) {
    profileSearch.addEventListener("input", (e) => {
      const searchTerm = e.target.value.toLowerCase()
      filterProfiles(searchTerm)
    })
  }

  // Confirm selection
  if (confirmModalBtn) {
    confirmModalBtn.addEventListener("click", () => {
      console.log("[v0] Confirm button clicked, selected profiles:", selectedProfiles)
      if (selectedProfiles.length === 0) {
        // Show error message if no profiles selected
        const errorDiv = document.createElement("div")
        errorDiv.className = "error-message"
        errorDiv.style.cssText =
          "color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 0.75rem; border-radius: 8px; margin-top: 1rem; text-align: center;"
        errorDiv.textContent = "⚠️ Veuillez sélectionner au moins une offre d'emploi"

        // Remove existing error message if any
        const existingError = document.querySelector(".error-message")
        if (existingError) {
          existingError.remove()
        }

        // Add error message to modal footer
        const modalFooter = document.querySelector(".modal-footer")
        if (modalFooter) {
          modalFooter.insertBefore(errorDiv, modalFooter.firstChild)
        }

        // Remove error message after 3 seconds
        setTimeout(() => {
          if (errorDiv.parentNode) {
            errorDiv.remove()
          }
        }, 3000)

        return // Don't close modal
      }

      updateProfileSelector()
      closeModal()
    })
  }

  function updateSelectedProfiles() {
    const selectedContainer = document.getElementById("selectedProfiles")
    const selectedCount = document.getElementById("selectedCount")

    selectedCount.textContent = selectedProfiles.length

    if (selectedProfiles.length === 0) {
      selectedContainer.innerHTML = '<div class="no-selection">Aucune offre sélectionnée</div>'
    } else {
      selectedContainer.innerHTML = selectedProfiles
        .map(
          (profile) => `
                <div class="selected-profile-item">
                    <div class="selected-profile-info">
                        <div class="profile-icon">💼</div>
                        <div>
                            <div class="profile-name">${profile.name}</div>
                            ${profile.company ? `<div class="profile-company">${profile.company} - ${profile.department || ""}</div>` : ""}
                        </div>
                    </div>
                    <button class="remove-profile-btn" onclick="removeProfile('${profile.id}')">✕</button>
                </div>
            `,
        )
        .join("")
    }
  }

  function updateProfileSelector() {
    const selectorSubtitle = document.getElementById("profileSelectorSubtitle")
    const selectedProfilesInput = document.getElementById("selectedProfilesInput")

    if (selectedProfiles.length === 0) {
      selectorSubtitle.textContent = "Cliquez pour choisir une ou plusieurs offres d'emploi"
    } else if (selectedProfiles.length === 1) {
      selectorSubtitle.textContent = `1 offre sélectionnée: ${selectedProfiles[0].name}`
    } else {
      selectorSubtitle.textContent = `${selectedProfiles.length} offres sélectionnées`
    }

    selectedProfilesInput.value = JSON.stringify(selectedProfiles)
  }

  // Make removeProfile global
  window.removeProfile = (profileId) => {
    selectedProfiles = selectedProfiles.filter((p) => p.id !== profileId)

    // Update UI
    const profileCard = document.querySelector(`[data-profile="${profileId}"]`)
    if (profileCard) {
      profileCard.classList.remove("selected")
    }

    updateSelectedProfiles()
    updateProfileSelector()
  }

  // Make fillCustomExample global
  window.fillCustomExample = (example) => {
    customProfileInput.value = example
    customProfileInput.focus()
  }
}

async function loadJobProfiles() {
  try {
    const response = await fetch("/api/job-profiles")
    const data = await response.json()

    if (data.success) {
      availableJobProfiles = data.profiles
      renderJobProfiles(availableJobProfiles)
    } else {
      console.error("Failed to load job profiles:", data.error)
      showFallbackProfiles()
    }
  } catch (error) {
    console.error("Error loading job profiles:", error)
    showFallbackProfiles()
  }
}

function renderJobProfiles(profiles) {
  const profilesGrid = document.getElementById("profilesGrid")
  const loadingMessage = document.getElementById("loadingProfiles")

  loadingMessage.style.display = "none"
  profilesGrid.style.display = "grid"

  profilesGrid.innerHTML = profiles
    .map(
      (profile) => `
        <div class="profile-card ${selectedProfiles.some((p) => p.id === profile.id.toString()) ? "selected" : ""}" 
             data-profile="${profile.id}" 
             data-job-title="${profile.title}"
             data-job-company="${profile.company}"
             data-job-department="${profile.department}">
            <div class="profile-icon">💼</div>
            <div class="profile-name">${profile.title}</div>
            <div class="profile-company">${profile.company} - ${profile.department}</div>
            <div class="profile-description">${profile.description}</div>
            <div class="profile-skills">
                ${profile.skills
                  .slice(0, 3)
                  .map((skill) => `<span class="skill-tag">${skill}</span>`)
                  .join("")}
                ${profile.skills.length > 3 ? `<span class="skill-more">+${profile.skills.length - 3}</span>` : ""}
            </div>
        </div>
    `,
    )
    .join("")

  profilesGrid.querySelectorAll(".profile-card").forEach((card) => {
    card.addEventListener("click", function () {
      const profileId = this.dataset.profile
      const jobData = profiles.find((p) => p.id.toString() === profileId)
      console.log("[v0] Profile card clicked:", profileId, jobData)

      if (this.classList.contains("selected")) {
        // Deselect
        this.classList.remove("selected")
        selectedProfiles = selectedProfiles.filter((p) => p.id !== profileId)
      } else {
        // Select
        this.classList.add("selected")
        selectedProfiles.push({
          id: profileId,
          name: jobData.title,
          company: jobData.company,
          department: jobData.department,
          skills: jobData.skills,
          requirements: jobData.requirements,
        })
      }

      window.updateSelectedProfiles() // Ensure the function is called globally
    })
  })
}

function filterProfiles(searchTerm) {
  const filteredProfiles = availableJobProfiles.filter(
    (profile) =>
      profile.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      profile.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      profile.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
      profile.skills.some((skill) => skill.toLowerCase().includes(searchTerm.toLowerCase())),
  )
  renderJobProfiles(filteredProfiles)
}

function showFallbackProfiles() {
  const profilesGrid = document.getElementById("profilesGrid")
  const loadingMessage = document.getElementById("loadingProfiles")

  loadingMessage.textContent = "⚠️ Utilisation des profils par défaut"

  const fallbackProfiles = [
    {
      id: "cybersecurity",
      title: "Expert en Cybersécurité",
      description: "Sécurité informatique, audit, protection des données",
      company: "Entreprise",
      department: "IT",
      skills: ["Cybersécurité", "Audit", "Protection données"],
    },
    {
      id: "webdev",
      title: "Développeur Full-Stack",
      description: "Développement web, frontend, backend",
      company: "Entreprise",
      department: "IT",
      skills: ["JavaScript", "React", "Node.js"],
    },
    {
      id: "datascientist",
      title: "Data Scientist",
      description: "Analyse de données, machine learning, IA",
      company: "Entreprise",
      department: "Data",
      skills: ["Python", "Machine Learning", "IA"],
    },
  ]

  availableJobProfiles = fallbackProfiles
  renderJobProfiles(fallbackProfiles)
  profilesGrid.style.display = "grid"
}

async function loadHeaderComponent() {
  try {
    const response = await fetch("/static/client-dep/components/header.html")
    if (response.ok) {
      const headerHTML = await response.text()
      const container = document.getElementById("header-component")
      container.innerHTML = headerHTML

      // Execute scripts from the loaded HTML
      const scripts = container.querySelectorAll("script")
      scripts.forEach((oldScript) => {
        const newScript = document.createElement("script")
        newScript.textContent = oldScript.textContent
        oldScript.parentNode.removeChild(oldScript)
        document.body.appendChild(newScript)
      })
    }
  } catch (error) {
    console.error("Failed to load header component:", error)
  }
}

function initializeFormSubmission() {
  const uploadForm = document.getElementById("uploadForm")
  const submitBtn = document.getElementById("submitBtn")
  const submitText = document.getElementById("submitText")
  const progressContainer = document.getElementById("progressContainer")
  const progressBar = document.getElementById("progressBar")
  const progressText = document.getElementById("progressText")

  // Track if form is being submitted to prevent double-clicks
  let isSubmitting = false

  uploadForm.addEventListener("submit", (e) => {
    // Prevent double submission
    if (isSubmitting) {
      e.preventDefault()
      console.log("[v0] Form submission already in progress, ignoring duplicate click")
      return
    }
    console.log("[v0] Form submit, selected profiles:", selectedProfiles)

    // Validate form
    const fileInput = document.getElementById("filetoscan")
    const selectedProfilesInput = document.getElementById("selectedProfilesInput")

    if (!fileInput.files.length) {
      e.preventDefault()
      alert("Veuillez sélectionner un fichier CV.")
      return
    }

    if (selectedProfiles.length === 0) {
      e.preventDefault()
      alert("Veuillez sélectionner au moins un profil d'emploi avant de continuer.")
      return
    }

    // Set submitting flag to prevent double-clicks
    isSubmitting = true

    const selectedJobsData = selectedProfiles.map((profile) => ({
      id: profile.id,
      title: profile.name,
      requirements: profile.requirements || "",
      skills: profile.skills || [],
      company: profile.company || "",
      department: profile.department || "",
    }))

    console.log("[v0] Submitting with job data:", selectedJobsData)
    document.getElementById("selectedJobsData").value = JSON.stringify(selectedJobsData)

    // Show loading state and disable button
    submitBtn.classList.add("loading")
    submitBtn.disabled = true
    submitText.style.display = "none"
    progressContainer.style.display = "block"

    // Simulate progress
    const progressSteps = [
      { progress: 20, text: "Téléchargement du fichier..." },
      { progress: 40, text: "Extraction du texte..." },
      { progress: 60, text: "Analyse par IA..." },
      { progress: 80, text: "Calcul du score..." },
      { progress: 95, text: "Génération du rapport..." },
    ]

    let stepIndex = 0
    const progressInterval = setInterval(() => {
      if (stepIndex < progressSteps.length) {
        const step = progressSteps[stepIndex]
        progressBar.style.width = step.progress + "%"
        progressText.textContent = step.text
        stepIndex++
      } else {
        clearInterval(progressInterval)
        progressBar.style.width = "100%"
        progressText.textContent = "Redirection vers les résultats..."
      }
    }, 800)

    // Reset submitting flag after a timeout (in case of errors)
    setTimeout(() => {
      isSubmitting = false
      submitBtn.disabled = false
      submitBtn.classList.remove("loading")
      submitText.style.display = "block"
      progressContainer.style.display = "none"
    }, 30000) // 30 seconds timeout
  })

  // Add error handling for form submission
  uploadForm.addEventListener("error", () => {
    isSubmitting = false
    submitBtn.disabled = false
    submitBtn.classList.remove("loading")
    submitText.style.display = "block"
    progressContainer.style.display = "none"
  })
}

// Declare the function globally
window.updateSelectedProfiles = function updateSelectedProfiles() {
  const selectedContainer = document.getElementById("selectedProfiles")
  const selectedCount = document.getElementById("selectedCount")

  selectedCount.textContent = selectedProfiles.length

  if (selectedProfiles.length === 0) {
    selectedContainer.innerHTML = '<div class="no-selection">Aucune offre sélectionnée</div>'
  } else {
    selectedContainer.innerHTML = selectedProfiles
      .map(
        (profile) => `
                <div class="selected-profile-item">
                    <div class="selected-profile-info">
                        <div class="profile-icon">💼</div>
                        <div>
                            <div class="profile-name">${profile.name}</div>
                            ${profile.company ? `<div class="profile-company">${profile.company} - ${profile.department || ""}</div>` : ""}
                        </div>
                    </div>
                    <button class="remove-profile-btn" onclick="removeProfile('${profile.id}')">✕</button>
                </div>
            `,
      )
      .join("")
  }
}
