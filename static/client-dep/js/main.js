document.addEventListener('DOMContentLoaded', async () => {
      try {
          const response = await fetch('/static/client-dep/components/header.html');
          const headerHTML = await response.text();
          document.getElementById('header-component').innerHTML = headerHTML;
      } catch (error) {
          console.error('Failed to load header component:', error);
      }
  });

document.addEventListener("DOMContentLoaded", () => {
  // Initialize animations
  initializeAnimations()

  // Initialize stats counter
  initializeStatsCounter()

  // Initialize smooth scrolling
  initializeSmoothScrolling()

  // Initialize navbar scroll effect
  initializeNavbarScroll()
})

function initializeAnimations() {
  // Animate elements on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1"
        entry.target.style.transform = "translateY(0)"
      }
    })
  }, observerOptions)

  // Observe elements that should animate
  const animateElements = document.querySelectorAll(".feature-card, .step-item, .stat-item")
  animateElements.forEach((el) => {
    el.style.opacity = "0"
    el.style.transform = "translateY(30px)"
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease"
    observer.observe(el)
  })
}

function initializeStatsCounter() {
  const stats = document.querySelectorAll(".stat-number[data-count]")

  const countUp = (element, target) => {
    let current = 0
    const increment = target / 100
    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        current = target
        clearInterval(timer)
      }

      // Format number with commas
      const formatted = Math.floor(current).toLocaleString()
      element.textContent = formatted + (element.textContent.includes("%") ? "%" : "")
    }, 20)
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const target = Number.parseInt(entry.target.dataset.count)
        countUp(entry.target, target)
        observer.unobserve(entry.target)
      }
    })
  })

  stats.forEach((stat) => observer.observe(stat))
}

function initializeSmoothScrolling() {
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })
}

function initializeNavbarScroll() {
  const navbar = document.querySelector(".navbar")
  if (!navbar) {
    // Header may not be injected yet; skip safely
    return
  }
  let lastScrollY = window.scrollY

  window.addEventListener("scroll", () => {
    const currentScrollY = window.scrollY

    if (currentScrollY > 100) {
      navbar.style.background = "rgba(10, 10, 10, 0.95)"
      navbar.style.backdropFilter = "blur(20px)"
    } else {
      navbar.style.background = "rgba(10, 10, 10, 0.9)"
      navbar.style.backdropFilter = "blur(20px)"
    }

    lastScrollY = currentScrollY
  })
}

// Utility functions
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.innerHTML = `
        <i class="fas fa-${type === "success" ? "check-circle" : type === "error" ? "exclamation-triangle" : "info-circle"}"></i>
        <span>${message}</span>
    `

  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => notification.classList.add("show"), 100)

  // Hide notification after 5 seconds
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => notification.remove(), 300)
  }, 5000)
}

// Export functions for use in other scripts
window.CVAnalyzer = {
  showNotification,
}
