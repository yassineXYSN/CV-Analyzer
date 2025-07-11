// Profile detail page JavaScript

document.addEventListener("DOMContentLoaded", () => {
  initializeSkillBars()
  initializeActions()
})

function initializeSkillBars() {
  const skillBars = document.querySelectorAll(".skill-progress")

  // Animate skill bars on page load
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const width = entry.target.dataset.width || 0
        setTimeout(() => {
          entry.target.style.width = width + "%"
        }, 200)
        observer.unobserve(entry.target)
      }
    })
  })

  skillBars.forEach((bar) => {
    observer.observe(bar)
  })
}

function initializeActions() {
  // Download profile function
  window.downloadProfile = () => {
    // Simulate profile download
    const link = document.createElement("a")
    link.href = "#" // This would be the actual profile PDF URL
    link.download = "profil-candidat.pdf"
    link.click()

    if (window.CVAnalyzer) {
      window.CVAnalyzer.showNotification("Téléchargement du profil en cours...", "info")
    }
  }

  // Share profile function
  window.shareProfile = () => {
    if (navigator.share) {
      navigator
        .share({
          title: "Profil Candidat - CV Analyzer Pro",
          text: "Découvrez ce profil de candidat analysé par CV Analyzer Pro",
          url: window.location.href,
        })
        .then(() => {
          if (window.CVAnalyzer) {
            window.CVAnalyzer.showNotification("Profil partagé avec succès!", "success")
          }
        })
        .catch((err) => {
          console.log("Error sharing:", err)
          fallbackShare()
        })
    } else {
      fallbackShare()
    }
  }

  function fallbackShare() {
    // Fallback: copy URL to clipboard
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        if (window.CVAnalyzer) {
          window.CVAnalyzer.showNotification("Lien copié dans le presse-papiers!", "success")
        }
      })
      .catch((err) => {
        console.log("Error copying to clipboard:", err)
        if (window.CVAnalyzer) {
          window.CVAnalyzer.showNotification("Impossible de copier le lien", "error")
        }
      })
  }
}
