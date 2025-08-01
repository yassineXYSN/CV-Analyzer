// Jobs page functionality
document.addEventListener("DOMContentLoaded", () => {
  console.log("Jobs page loading...")
  initializeJobsPage()
})

function initializeJobsPage() {
  console.log("Initializing jobs page...")

  // Initialize search functionality
  initializeSearch()

  // Initialize job interactions
  initializeJobInteractions()

  // Initialize filters
  initializeFilters()

  // Initialize pagination
  initializePagination()

  // Initialize toast notifications
  initializeToast()

  // Add keyboard shortcuts
  addKeyboardShortcuts()

  console.log("Jobs page initialized successfully")
}

function initializeSearch() {
  const searchForm = document.querySelector(".search-form")
  const searchInput = document.querySelector('input[name="search"]')
  const locationInput = document.querySelector('input[name="location"]')

  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      console.log("Search form submitted")
      showLoadingSpinner()
      // Let the form submit naturally to the backend
    })
  }

  // Auto-submit form on filter changes
  const filterSelects = document.querySelectorAll(".filter-select")
  const salaryInputs = document.querySelectorAll(".salary-input")

  filterSelects.forEach((select) => {
    select.addEventListener("change", () => {
      console.log("Filter changed:", select.name, select.value)
      showLoadingSpinner()
      if (searchForm) {
        searchForm.submit()
      }
    })
  })

  salaryInputs.forEach((input) => {
    input.addEventListener("blur", () => {
      console.log("Salary input changed:", input.name, input.value)
      if (input.value) {
        showLoadingSpinner()
        if (searchForm) {
          searchForm.submit()
        }
      }
    })
  })

  // Search suggestions (optional enhancement)
  if (searchInput) {
    let searchTimeout
    searchInput.addEventListener("input", () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        console.log("Search input:", searchInput.value)
      }, 300)
    })
  }
}

function initializeJobInteractions() {
  console.log("Initializing job interactions...")

  // Save/unsave job functionality
  window.toggleSaveJob = (jobId, button) => {
    console.log("Toggle save job:", jobId)

    const icon = button.querySelector("i")
    const isSaved = button.classList.contains("saved")

    // Optimistic UI update
    if (isSaved) {
      button.classList.remove("saved")
      if (icon) {
        icon.className = "far fa-heart"
      }
    } else {
      button.classList.add("saved")
      if (icon) {
        icon.className = "fas fa-heart"
      }
    }

    // Make API call
    const method = isSaved ? "DELETE" : "POST"
    fetch(`/api/jobs/${jobId}/save`, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Save job response:", data)
        if (data.success) {
          showToast(data.message || (isSaved ? "Offre retirée des favoris" : "Offre ajoutée aux favoris"), "success")
        } else {
          // Revert UI change on error
          if (isSaved) {
            button.classList.add("saved")
            if (icon) icon.className = "fas fa-heart"
          } else {
            button.classList.remove("saved")
            if (icon) icon.className = "far fa-heart"
          }
          showToast(data.message || "Erreur lors de la sauvegarde", "error")
        }
      })
      .catch((error) => {
        console.error("Error saving job:", error)
        // Revert UI change on error
        if (isSaved) {
          button.classList.add("saved")
          if (icon) icon.className = "fas fa-heart"
        } else {
          button.classList.remove("saved")
          if (icon) icon.className = "far fa-heart"
        }
        showToast("Erreur de connexion", "error")
      })
  }

  // Quick apply functionality
  window.quickApply = (jobId) => {
    console.log("Quick apply to job:", jobId)

    // Show confirmation dialog
    if (confirm("Voulez-vous postuler à cette offre ?")) {
      showLoadingSpinner()

      fetch(`/api/jobs/${jobId}/apply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: "Application submitted via job portal",
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Apply job response:", data)
          hideLoadingSpinner()

          if (data.success) {
            showToast(data.message || "Candidature envoyée avec succès!", "success")

            // Update button state
            const applyButtons = document.querySelectorAll(`[onclick="quickApply(${jobId})"]`)
            applyButtons.forEach((btn) => {
              btn.innerHTML = '<i class="fas fa-check"></i> Candidature envoyée'
              btn.disabled = true
              btn.style.background = "#10b981"
              btn.style.cursor = "not-allowed"
            })
          } else {
            showToast(data.message || "Erreur lors de la candidature", "error")
          }
        })
        .catch((error) => {
          console.error("Error applying to job:", error)
          hideLoadingSpinner()
          showToast("Erreur de connexion", "error")
        })
    }
  }

  // Job card click handlers
  const jobCards = document.querySelectorAll(".job-card")
  jobCards.forEach((card) => {
    card.addEventListener("click", function (e) {
      // Don't trigger if clicking on buttons or links
      if (e.target.closest("button") || e.target.closest("a")) {
        return
      }

      const jobId = this.dataset.jobId
      if (jobId) {
        window.location.href = `/jobs/${jobId}`
      }
    })
  })
}

function initializeFilters() {
  console.log("Initializing filters...")

  // Clear filters functionality
  window.clearFilters = () => {
    console.log("Clearing filters...")

    const form = document.querySelector(".search-form")
    if (form) {
      const inputs = form.querySelectorAll("input, select")

      inputs.forEach((input) => {
        if (input.type === "text" || input.type === "number") {
          input.value = ""
        } else if (input.tagName === "SELECT") {
          input.selectedIndex = 0
        }
      })

      showLoadingSpinner()
      form.submit()
    }
  }

  // Sort functionality
  window.sortJobs = (sortBy) => {
    console.log("Sorting jobs by:", sortBy)

    const url = new URL(window.location)
    url.searchParams.set("sort", sortBy)
    url.searchParams.set("page", "1") // Reset to first page

    showLoadingSpinner()
    window.location.href = url.toString()
  }
}

function initializePagination() {
  console.log("Initializing pagination...")

  // Add smooth scrolling to top when pagination is clicked
  const paginationLinks = document.querySelectorAll(".pagination a")

  paginationLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      console.log("Pagination link clicked:", link.href)
      showLoadingSpinner()

      // Scroll to top of main content
      setTimeout(() => {
        const mainContent = document.querySelector(".main-content")
        if (mainContent) {
          mainContent.scrollIntoView({
            behavior: "smooth",
            block: "start",
          })
        }
      }, 100)
    })
  })
}

function initializeToast() {
  // Create toast container if it doesn't exist
  if (!document.getElementById("toast")) {
    const toast = document.createElement("div")
    toast.id = "toast"
    toast.className = "toast"
    toast.innerHTML = `
            <div class="toast-content">
                <i class="toast-icon"></i>
                <span class="toast-message"></span>
            </div>
            <button class="toast-close" onclick="hideToast()">&times;</button>
        `
    document.body.appendChild(toast)
  }
}

function addKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault()
      const searchInput = document.querySelector('input[name="search"]')
      if (searchInput) {
        searchInput.focus()
        searchInput.select()
      }
    }

    // Escape to clear search focus
    if (e.key === "Escape") {
      const searchInput = document.querySelector('input[name="search"]')
      if (searchInput && document.activeElement === searchInput) {
        searchInput.blur()
      }

      // Also hide toast if visible
      hideToast()
    }

    // Ctrl/Cmd + Enter to submit search
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const searchForm = document.querySelector(".search-form")
      if (searchForm) {
        searchForm.submit()
      }
    }
  })
}

// Utility functions
function showLoadingSpinner() {
  console.log("Showing loading spinner...")

  const existingSpinner = document.getElementById("loadingSpinner")
  if (existingSpinner) {
    existingSpinner.style.display = "flex"
  }

  // Also dim the jobs grid
  const jobsGrid = document.querySelector(".jobs-grid")
  if (jobsGrid) {
    jobsGrid.style.opacity = "0.6"
    jobsGrid.style.pointerEvents = "none"
  }
}

function hideLoadingSpinner() {
  console.log("Hiding loading spinner...")

  const existingSpinner = document.getElementById("loadingSpinner")
  if (existingSpinner) {
    existingSpinner.style.display = "none"
  }

  // Restore jobs grid
  const jobsGrid = document.querySelector(".jobs-grid")
  if (jobsGrid) {
    jobsGrid.style.opacity = "1"
    jobsGrid.style.pointerEvents = "auto"
  }
}

function showToast(message, type = "info") {
  console.log("Showing toast:", message, type)

  const toast = document.getElementById("toast")
  if (!toast) {
    console.error("Toast element not found")
    return
  }

  const toastMessage = toast.querySelector(".toast-message")
  const toastIcon = toast.querySelector(".toast-icon")

  if (toastMessage) {
    toastMessage.textContent = message
  }

  // Set type and icon
  toast.className = `toast ${type}`

  if (toastIcon) {
    switch (type) {
      case "success":
        toastIcon.className = "fas fa-check-circle toast-icon"
        break
      case "error":
        toastIcon.className = "fas fa-exclamation-circle toast-icon"
        break
      case "warning":
        toastIcon.className = "fas fa-exclamation-triangle toast-icon"
        break
      default:
        toastIcon.className = "fas fa-info-circle toast-icon"
    }
  }

  // Show toast
  toast.classList.add("show")

  // Auto hide after 5 seconds
  setTimeout(() => {
    hideToast()
  }, 5000)
}

function hideToast() {
  const toast = document.getElementById("toast")
  if (toast) {
    toast.classList.remove("show")
  }
}

// Global function for hiding toast
window.hideToast = hideToast

// Job card hover effects
document.addEventListener("DOMContentLoaded", () => {
  const jobCards = document.querySelectorAll(".job-card")

  jobCards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-4px)"
    })

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)"
    })
  })
})

// Page performance monitoring
window.addEventListener("load", () => {
  console.log("Jobs page loaded successfully")

  // Hide any loading states that might still be showing
  hideLoadingSpinner()

  // Track page load time
  const loadTime = performance.now()
  console.log(`Page load time: ${loadTime.toFixed(2)}ms`)
})

// Handle page visibility changes
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    console.log("Jobs page hidden")
  } else {
    console.log("Jobs page visible")
  }
})

console.log("Jobs page JavaScript loaded successfully")
