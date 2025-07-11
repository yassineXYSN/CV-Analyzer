// Variables globales
let isEditMode = false
let originalData = {}

// Initialisation
document.addEventListener("DOMContentLoaded", () => {
  saveOriginalData()
})

// Sauvegarder les données originales
function saveOriginalData() {
  const fields = document.querySelectorAll("[data-field]")
  originalData = {}

  fields.forEach((field) => {
    const fieldName = field.getAttribute("data-field")
    if (field.classList.contains("detail-value")) {
      originalData[fieldName] = field.textContent.trim()
    }
  })
}

// Basculer le mode édition
function toggleEditMode() {
  isEditMode = !isEditMode
  const editBtn = document.getElementById("editBtnText")
  const editActions = document.getElementById("editActions")
  const uploadBtn = document.querySelector(".upload-logo-btn")

  if (isEditMode) {
    enterEditMode()
    editBtn.textContent = "Annuler"
    editActions.style.display = "flex"
    uploadBtn.style.display = "flex"
  } else {
    exitEditMode()
    editBtn.textContent = "Modifier"
    editActions.style.display = "none"
    uploadBtn.style.display = "none"
    restoreOriginalData()
  }
}

// Entrer en mode édition
function enterEditMode() {
  const detailValues = document.querySelectorAll(".detail-value")
  const detailInputs = document.querySelectorAll(".detail-input")

  detailValues.forEach((value) => {
    value.style.display = "none"
  })

  detailInputs.forEach((input) => {
    input.style.display = "block"
    const fieldName = input.getAttribute("data-field")
    if (originalData[fieldName]) {
      if (input.tagName === "TEXTAREA") {
        input.value = originalData[fieldName]
      } else if (input.tagName === "SELECT") {
        input.value = originalData[fieldName]
      } else {
        input.value = originalData[fieldName]
      }
    }
  })
}

// Sortir du mode édition
function exitEditMode() {
  const detailValues = document.querySelectorAll(".detail-value")
  const detailInputs = document.querySelectorAll(".detail-input")

  detailValues.forEach((value) => {
    value.style.display = "block"
  })

  detailInputs.forEach((input) => {
    input.style.display = "none"
  })
}

// Restaurer les données originales
function restoreOriginalData() {
  const fields = document.querySelectorAll("[data-field]")

  fields.forEach((field) => {
    const fieldName = field.getAttribute("data-field")
    if (field.classList.contains("detail-value") && originalData[fieldName]) {
      field.textContent = originalData[fieldName]
    }
  })
}

// Annuler les modifications
function cancelEdit() {
  toggleEditMode()
}

// Sauvegarder les modifications
function saveChanges() {
  const detailInputs = document.querySelectorAll(".detail-input")
  const detailValues = document.querySelectorAll(".detail-value")

  // Mettre à jour les valeurs affichées avec les nouvelles données
  detailInputs.forEach((input) => {
    const fieldName = input.getAttribute("data-field")
    const correspondingValue = document.querySelector(`.detail-value[data-field="${fieldName}"]`)

    if (correspondingValue) {
      correspondingValue.textContent = input.value
    }
  })

  // Sauvegarder les nouvelles données comme données originales
  saveOriginalData()

  // Sortir du mode édition
  isEditMode = false
  const editBtn = document.getElementById("editBtnText")
  const editActions = document.getElementById("editActions")
  const uploadBtn = document.querySelector(".upload-logo-btn")

  exitEditMode()
  editBtn.textContent = "Modifier"
  editActions.style.display = "none"
  uploadBtn.style.display = "none"

  // Afficher un message de confirmation
  showNotification("Profil mis à jour avec succès !", "success")
}

// Télécharger un logo
function uploadLogo() {
  const input = document.createElement("input")
  input.type = "file"
  input.accept = "image/*"

  input.onchange = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const logoPlaceholder = document.getElementById("companyLogo")
        logoPlaceholder.innerHTML = `<img src="${e.target.result}" alt="Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;">`
        showNotification("Logo mis à jour !", "success")
      }
      reader.readAsDataURL(file)
    }
  }

  input.click()
}

// Retourner au dashboard
function goBack() {
  if (isEditMode) {
    if (confirm("Vous avez des modifications non sauvegardées. Voulez-vous vraiment quitter ?")) {
      window.close()
    }
  } else {
    window.close()
  }
}

// Afficher une notification
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.innerHTML = `
    <i class="fas ${type === "success" ? "fa-check-circle" : "fa-info-circle"}"></i>
    <span>${message}</span>
  `

  // Styles pour la notification
  notification.style.cssText = `
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: ${type === "success" ? "rgba(39, 174, 96, 0.9)" : "rgba(52, 152, 219, 0.9)"};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    z-index: 10000;
    backdrop-filter: blur(10px);
    animation: slideIn 0.3s ease;
  `

  document.body.appendChild(notification)

  // Supprimer la notification après 3 secondes
  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease"
    setTimeout(() => {
      document.body.removeChild(notification)
    }, 300)
  }, 3000)
}

// Ajouter les animations CSS
const style = document.createElement("style")
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`
document.head.appendChild(style)

// Gestion des raccourcis clavier
document.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + S pour sauvegarder
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault()
    if (isEditMode) {
      saveChanges()
    }
  }

  // Escape pour annuler
  if (e.key === "Escape" && isEditMode) {
    cancelEdit()
  }
})

// Prévenir la perte de données
window.addEventListener("beforeunload", (e) => {
  if (isEditMode) {
    e.preventDefault()
    e.returnValue = "Vous avez des modifications non sauvegardées. Voulez-vous vraiment quitter ?"
  }
})
