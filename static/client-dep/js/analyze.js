// Analyze page JavaScript

document.addEventListener("DOMContentLoaded", () => {
  initializeFileUpload()
  initializeProfileModal()
  initializeFormSubmission()
})

let selectedProfiles = []

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
  const profileCards = document.querySelectorAll(".profile-card")
  const customProfileInput = document.getElementById("customProfileInput")
  const addCustomBtn = document.getElementById("addCustomBtn")
  const profileSearch = document.getElementById("profileSearch")

  // Open modal
  profileSelectorBtn.addEventListener("click", () => {
    profileModal.classList.add("show")
    document.body.style.overflow = "hidden"
  })

  // Close modal
  function closeModal() {
    profileModal.classList.remove("show")
    document.body.style.overflow = ""
  }

  closeModalBtn.addEventListener("click", closeModal)
  cancelModalBtn.addEventListener("click", closeModal)

  profileModal.addEventListener("click", (e) => {
    if (e.target === profileModal) {
      closeModal()
    }
  })

  // Profile card selection
  profileCards.forEach((card) => {
    card.addEventListener("click", () => {
      const profileName = card.querySelector(".profile-name").textContent
      const profileId = card.dataset.profile

      if (card.classList.contains("selected")) {
        // Deselect
        card.classList.remove("selected")
        selectedProfiles = selectedProfiles.filter((p) => p.id !== profileId)
      } else {
        // Select
        card.classList.add("selected")
        selectedProfiles.push({
          id: profileId,
          name: profileName,
        })
      }

      updateSelectedProfiles()
    })
  })

  // Add custom profile
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
    }
  })

  // Search functionality
  profileSearch.addEventListener("input", (e) => {
    const searchTerm = e.target.value.toLowerCase()
    profileCards.forEach((card) => {
      const profileName = card.querySelector(".profile-name").textContent.toLowerCase()
      const profileDesc = card.querySelector(".profile-description").textContent.toLowerCase()

      if (profileName.includes(searchTerm) || profileDesc.includes(searchTerm)) {
        card.style.display = "block"
      } else {
        card.style.display = "none"
      }
    })
  })

  // Confirm selection
  confirmModalBtn.addEventListener("click", () => {
    if (selectedProfiles.length === 0) {
      alert("Veuillez sélectionner au moins un profil.")
      return
    }

    updateProfileSelector()
    closeModal()
  })

  function updateSelectedProfiles() {
    const selectedContainer = document.getElementById("selectedProfiles")
    const selectedCount = document.getElementById("selectedCount")

    selectedCount.textContent = selectedProfiles.length

    if (selectedProfiles.length === 0) {
      selectedContainer.innerHTML = '<div class="no-selection">Aucun profil sélectionné</div>'
    } else {
      selectedContainer.innerHTML = selectedProfiles
        .map(
          (profile) => `
                <div class="selected-tag">
                    ${profile.name}
                    <button class="remove-tag" onclick="removeProfile('${profile.id}')">×</button>
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
      selectorSubtitle.textContent = "Cliquez pour choisir un ou plusieurs profils"
    } else if (selectedProfiles.length === 1) {
      selectorSubtitle.textContent = `1 profil sélectionné: ${selectedProfiles[0].name}`
    } else {
      selectorSubtitle.textContent = `${selectedProfiles.length} profils sélectionnés`
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
  }

  // Make fillCustomExample global
  window.fillCustomExample = (example) => {
    customProfileInput.value = example
    customProfileInput.focus()
  }
}

function initializeFormSubmission() {
  const uploadForm = document.getElementById("uploadForm")
  const submitBtn = document.getElementById("submitBtn")
  const submitText = document.getElementById("submitText")
  const progressContainer = document.getElementById("progressContainer")
  const progressBar = document.getElementById("progressBar")
  const progressText = document.getElementById("progressText")

  uploadForm.addEventListener("submit", (e) => {
    // Validate form
    const fileInput = document.getElementById("filetoscan")
    const selectedProfilesInput = document.getElementById("selectedProfilesInput")

    if (!fileInput.files.length) {
      e.preventDefault()
      alert("Veuillez sélectionner un fichier CV.")
      return
    }

    if (!selectedProfilesInput.value) {
      e.preventDefault()
      alert("Veuillez sélectionner au moins un profil.")
      return
    }

    // Show loading state
    submitBtn.classList.add("loading")
    submitText.style.display = "none"
    progressContainer.style.display = "block"

    // Simulate progress
    const progress = 0
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
  })
}
