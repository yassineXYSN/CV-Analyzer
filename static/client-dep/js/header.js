class HeaderComponent {
  constructor() {
    this.currentUser = null
    this.notificationCount = 0
    this.notificationWs = null
    this.reconnectInterval = null // Added for managing reconnects
    this.init()
  }

  init() {
    this.setActivePage()
    this.setupEventListeners()
    this.checkAuthStatus()
  }

  setupEventListeners() {
    // Hamburger menu
    const hamburger = document.getElementById("hamburger")
    const navMenu = document.getElementById("navMenu")

    if (hamburger && navMenu) {
      hamburger.addEventListener("click", () => {
        hamburger.classList.toggle("active")
        navMenu.classList.toggle("active")

        // Prevent body scroll when menu is open
        if (navMenu.classList.contains("active")) {
          document.body.style.overflow = "hidden"
        } else {
          document.body.style.overflow = "auto"
        }
      })
    }

    // User menu dropdown
    const userMenuTrigger = document.getElementById("userMenuTrigger")
    const userDropdown = document.getElementById("userDropdown")

    if (userMenuTrigger && userDropdown) {
      const closeDropdown = () => {
        userMenuTrigger.classList.remove("active")
        userDropdown.classList.remove("show")
      }

      userMenuTrigger.addEventListener("click", (e) => {
        e.stopPropagation()
        const isOpen = userDropdown.classList.contains("show")

        // Close others if needed
        document.querySelectorAll(".user-dropdown.show").forEach((d) => d.classList.remove("show"))
        document.querySelectorAll(".user-menu-trigger.active").forEach((t) => t.classList.remove("active"))
        // Close notification dropdown if open
        const notificationDropdown = document.getElementById("notificationDropdown")
        const notificationBellTrigger = document.getElementById("notificationBellTrigger")
        if (notificationDropdown && notificationBellTrigger && notificationDropdown.classList.contains("show")) {
          notificationDropdown.classList.remove("show")
          notificationBellTrigger.classList.remove("active")
        }

        if (!isOpen) {
          userMenuTrigger.classList.add("active")
          userDropdown.classList.add("show")
        }
      })

      // Close on outside click
      document.addEventListener("click", (e) => {
        if (!userMenuTrigger.contains(e.target) && !userDropdown.contains(e.target)) {
          closeDropdown()
        }
      })

      // Close on Esc
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeDropdown()
      })
    }
  }

  async checkAuthStatus() {
    try {
      // First try to check via API
      const response = await fetch("/api/auth/status", {
        credentials: "include",
      })

      if (response.ok) {
        const userData = await response.json()
        if (userData.authenticated && userData.user) {
          this.setUser(userData.user)
          if (userData.user.profile === null) {
            const step2Item = document.getElementById("setupstep2")
            if (step2Item) {
              step2Item.style.display = "block"
            }
          }
          return
        }
      }

      // Fallback: check if we have user data passed from the server
      if (window.currentUser) {
        this.setUser(window.currentUser)
        return
      }

      // If no user data found, set as guest
      this.setGuest()
    } catch (error) {
      console.error("Auth check error:", error)
      // Fallback: check if we have user data from server
      if (window.currentUser) {
        this.setUser(window.currentUser)
      } else {
        this.setGuest()
      }
    }
  }

  setUser(user) {
    this.currentUser = user

    const userMenuContainer = document.getElementById("userMenuContainer")
    const notificationBellContainer = document.getElementById("notificationBellContainer")
    const guestMenuContainers = document.querySelectorAll(".guest-menu-container")

    if (userMenuContainer) {
      userMenuContainer.style.display = "block"
    }

    if (notificationBellContainer) {
      notificationBellContainer.style.display = "block"
    }

    guestMenuContainers.forEach((container) => {
      container.style.display = "none"
    })

    this.updateUserInfo(user)
    this.setupEventListeners()
    this.setupNotificationDropdown()

    // Set profile link dynamically
    const profileLink = document.getElementById("profileLink")
    if (profileLink && user.id) {
      profileLink.href = `/profile/by_user/${user.id}`
    }

    // Fetch notification count and setup WebSocket
    this.fetchNotificationCount()
    this.setupNotificationWebSocket()
  }

  setGuest() {
    this.currentUser = null

    // Hide user menu and notification bell, show guest menu
    const userMenuContainer = document.getElementById("userMenuContainer")
    const notificationBellContainer = document.getElementById("notificationBellContainer")
    const guestMenuContainers = document.querySelectorAll(".guest-menu-container")

    if (userMenuContainer) {
      userMenuContainer.style.display = "none"
    }

    if (notificationBellContainer) {
      notificationBellContainer.style.display = "none"
    }

    guestMenuContainers.forEach((container) => {
      container.style.display = "block"
    })

    // Close notification WebSocket if exists
    if (this.notificationWs) {
      this.notificationWs.close()
      this.notificationWs = null
    }
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval)
      this.reconnectInterval = null
    }
    this.dispatchWebSocketStatus(false) // Dispatch status change
  }

  updateUserInfo(user) {
    const userName = document.getElementById("userName")
    const userFullName = document.getElementById("userFullName")
    const userEmail = document.getElementById("userEmail")
    const userAvatar = document.getElementById("userAvatar")
    const userAvatarLarge = document.getElementById("userAvatarLarge")

    if (userName) {
      userName.textContent = user.first_name || user.name || "Utilisateur"
    }

    if (userFullName) {
      userFullName.textContent = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.name || "Utilisateur"
    }

    if (userEmail) {
      userEmail.textContent = user.email || ""
    }

    // Set avatar
    const profilePic = user.profile_picture || "/static/client-dep/images/placeholder.svg"
    if (userAvatar) {
      userAvatar.innerHTML = `
        <img src="${profilePic}" alt="Photo de profil" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
      `
    }
    if (userAvatarLarge) {
      userAvatarLarge.innerHTML = `
        <img src="${profilePic}" alt="Photo de profil" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
      `
    }
  }

  async fetchNotificationCount() {
    if (!this.currentUser) return

    try {
      const response = await fetch("/api/notifications/count", {
        credentials: "include",
      })

      if (response.ok) {
        const data = await response.json()
        this.updateNotificationCount(data.unread_count || 0)
      }
    } catch (error) {
      console.error("Error fetching notification count:", error)
    }
  }

  updateNotificationCount(count) {
    this.notificationCount = count
    const countElement = document.getElementById("notificationCount")

    if (countElement) {
      if (count > 0) {
        countElement.textContent = count > 99 ? "99+" : count.toString()
        countElement.style.display = "flex"
      } else {
        countElement.style.display = "none"
      }
    }
  }

  setupNotificationWebSocket() {
    if (!this.currentUser || !this.currentUser.id) {
      console.log("No current user ID available, skipping WebSocket connection setup.")
      this.dispatchWebSocketStatus(false)
      return
    }

    // Close existing connection if any
    if (this.notificationWs) {
      this.notificationWs.close()
      this.notificationWs = null
    }
    // Clear any existing reconnect interval
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval)
      this.reconnectInterval = null
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${this.currentUser.id}`
    console.log(`Attempting to connect WebSocket to: ${wsUrl}`)

    try {
      this.notificationWs = new WebSocket(wsUrl)

      this.notificationWs.onopen = () => {
        console.log("Notification WebSocket connected (header)")
        this.dispatchWebSocketStatus(true)
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval)
          this.reconnectInterval = null
        }
        // Start client heartbeat to keep connection alive
        if (this._heartbeatTimer) {
          clearInterval(this._heartbeatTimer)
        }
        this._heartbeatTimer = setInterval(() => {
          try {
            if (this.notificationWs && this.notificationWs.readyState === WebSocket.OPEN) {
              this.notificationWs.send(JSON.stringify({ type: "heartbeat", at: new Date().toISOString() }))
            }
          } catch (e) {
            // no-op
          }
        }, 25000)
      }

      this.notificationWs.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log("Received notification via WebSocket (header):", data)
        // Ignore pure heartbeat echoes
        if (data && data.type === "heartbeat") return

        // Increment notification count for any incoming notification payload
        this.updateNotificationCount(this.notificationCount + 1)
        this.showNotificationIndicator()

        // Dispatch custom event for other parts of the app (e.g., notifications page)
        document.dispatchEvent(new CustomEvent("newNotificationReceived", { detail: data }))

        // Update dropdown in real-time if it's open
        const dropdown = document.getElementById("notificationDropdown")
        if (dropdown && dropdown.classList.contains("show")) {
          this.addNotificationToDropdown(data)
        }
      }

      this.notificationWs.onerror = (error) => {
        console.error("Notification WebSocket error (header):", error)
        this.dispatchWebSocketStatus(false)
      }

      this.notificationWs.onclose = (event) => {
        console.log("Notification WebSocket disconnected (header):", event.code, event.reason)
        this.dispatchWebSocketStatus(false)
        if (this._heartbeatTimer) {
          clearInterval(this._heartbeatTimer)
          this._heartbeatTimer = null
        }
        // Attempt to reconnect after 5 seconds if user is still logged in
        if (this.currentUser && !this.reconnectInterval) {
          console.log("Attempting to reconnect WebSocket in 5 seconds...")
          this.reconnectInterval = setInterval(() => {
            this.setupNotificationWebSocket()
          }, 5000)
        }
      }
    } catch (error) {
      console.error("Failed to create WebSocket connection (header):", error)
      this.dispatchWebSocketStatus(false)
    }
  }

  dispatchWebSocketStatus(connected) {
    document.dispatchEvent(new CustomEvent("websocketStatusChange", { detail: { connected: connected } }))
    const statusElement = document.getElementById("connection-status")
    if (statusElement) {
      if (connected) {
        statusElement.textContent = "🟢 Connecté"
        statusElement.className = "connection-status connected"
      } else {
        statusElement.textContent = "🔴 Déconnecté"
        statusElement.className = "connection-status disconnected"
      }
    }
  }

  showNotificationIndicator() {
    const bellElement = document.querySelector(".notification-bell")
    if (bellElement) {
      // Add a brief animation to indicate new notification
      bellElement.style.animation = "none"
      bellElement.offsetHeight // Trigger reflow
      bellElement.style.animation = "bell-shake 0.5s ease-in-out"

      // Remove animation after it completes
      setTimeout(() => {
        bellElement.style.animation = ""
      }, 500)
    }
  }

  setActivePage() {
    const currentPath = window.location.pathname
    const navLinks = document.querySelectorAll(".nav-link[data-page]")

    navLinks.forEach((link) => {
      link.classList.remove("active")
      const page = link.getAttribute("data-page")

      if (
        (page === "home" && currentPath === "/") ||
        (page === "analyze" && currentPath.includes("/analyze")) ||
        (page === "jobs" && currentPath.includes("/jobs")) ||
        (page === "step2" && currentPath.includes("/signup/step2"))
      ) {
        link.classList.add("active")
      }
    })
  }

  async logout() {
    try {
      const response = await fetch("/logout", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        // Clear any client-side user data
        window.currentUser = null
        this.setGuest()

        // Show success message
        if (window.showToast) {
          window.showToast("Déconnexion réussie", "success")
        }

        // Redirect to home page after a short delay
        setTimeout(() => {
          window.location.href = "/"
        }, 1000)
      } else {
        console.error("Logout failed")
        if (window.showToast) {
          window.showToast("Erreur lors de la déconnexion", "error")
        }
      }
    } catch (error) {
      console.error("Logout error:", error)
      if (window.showToast) {
        window.showToast("Erreur lors de la déconnexion", "error")
      }
    }
  }

  setupNotificationDropdown() {
    const bellTrigger = document.getElementById("notificationBellTrigger")
    const dropdown = document.getElementById("notificationDropdown")

    if (bellTrigger && dropdown) {
      const closeDropdown = () => {
        bellTrigger.classList.remove("active")
        dropdown.classList.remove("show")
      }

      bellTrigger.addEventListener("click", async (e) => {
        e.stopPropagation()
        const isOpen = dropdown.classList.contains("show")

        // Close other dropdowns
        document.querySelectorAll(".user-dropdown.show").forEach((d) => d.classList.remove("show"))
        document.querySelectorAll(".user-menu-trigger.active").forEach((t) => t.classList.remove("active"))

        if (!isOpen) {
          bellTrigger.classList.add("active")
          dropdown.classList.add("show")
          await this.loadRecentNotifications()
        } else {
          closeDropdown()
        }
      })

      // Close on outside click
      document.addEventListener("click", (e) => {
        if (!bellTrigger.contains(e.target) && !dropdown.contains(e.target)) {
          closeDropdown()
        }
      })

      // Close on Esc
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeDropdown()
      })
    }
  }

  async loadRecentNotifications() {
    const contentElement = document.getElementById("notificationDropdownContent")
    const loadingElement = document.getElementById("notificationLoading")

    if (!contentElement || !this.currentUser) return

    // Show loading
    if (loadingElement) {
      loadingElement.style.display = "flex"
    }
    contentElement.innerHTML = "" // Clear previous content

    try {
      const response = await fetch("/api/notifications/recent?limit=3", {
        credentials: "include",
      })

      if (response.ok) {
        const data = await response.json()
        this.renderRecentNotifications(data.notifications || [])
      } else {
        this.renderNotificationError()
      }
    } catch (error) {
      console.error("Error loading recent notifications:", error)
      this.renderNotificationError()
    } finally {
      // Hide loading
      if (loadingElement) {
        loadingElement.style.display = "none"
      }
    }
  }

  renderRecentNotifications(notifications) {
    const contentElement = document.getElementById("notificationDropdownContent")
    if (!contentElement) return

    if (notifications.length === 0) {
      contentElement.innerHTML = `
      <div class="notification-empty">
        <i class="fas fa-bell-slash"></i>
        <div>Aucune notification récente</div>
      </div>
    `
      return
    }

    const notificationsHTML = notifications
      .map((notification) => this.createNotificationMiniHtml(notification))
      .join("")

    contentElement.innerHTML = notificationsHTML
  }

  addNotificationToDropdown(notification) {
    const contentElement = document.getElementById("notificationDropdownContent")
    if (!contentElement) return

    // Remove empty state if present
    const emptyState = contentElement.querySelector(".notification-empty")
    if (emptyState) {
      emptyState.remove()
    }

    const newNotificationHtml = this.createNotificationMiniHtml(notification)
    contentElement.insertAdjacentHTML("afterbegin", newNotificationHtml)

    // Keep only the latest 3 notifications in the dropdown
    const notificationItems = contentElement.querySelectorAll(".notification-item-mini")
    if (notificationItems.length > 3) {
      for (let i = 3; i < notificationItems.length; i++) {
        notificationItems[i].remove()
      }
    }
  }

  createNotificationMiniHtml(notification) {
    const createdAtStr = notification.created_at || notification.timestamp
    const timeAgo = this.getTimeAgo(new Date(createdAtStr))
    const statusClass = `status-${notification.status}`
    const unreadClass = notification.is_read ? "" : "unread"

    return `
      <div class="notification-item-mini ${unreadClass}" onclick="window.location.href='/notifications'">
        <div class="notification-mini-header">
          <div class="notification-mini-title">${notification.title}</div>
          <div class="notification-mini-time">${timeAgo}</div>
        </div>
        <div class="notification-mini-message">${notification.message}</div>
        <span class="notification-mini-status ${statusClass}">
          ${notification.status.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
        </span>
      </div>
    `
  }

  renderNotificationError() {
    const contentElement = document.getElementById("notificationDropdownContent")
    if (!contentElement) return

    contentElement.innerHTML = `
    <div class="notification-empty">
      <i class="fas fa-exclamation-triangle"></i>
      <div>Erreur lors du chargement</div>
    </div>
  `
  }

  getTimeAgo(date) {
    const now = new Date()
    const diffInSeconds = Math.floor((now - date) / 1000)

    if (diffInSeconds < 60) {
      return "À l'instant"
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return `Il y a ${minutes} min`
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600)
      return `Il y a ${hours}h`
    } else {
      const days = Math.floor(diffInSeconds / 86400)
      return `Il y a ${days}j`
    }
  }

  // Static methods for global access
  static setCurrentUser(user) {
    if (window.headerComponent) {
      window.headerComponent.setUser(user)
    }
  }

  static setGuest() {
    if (window.headerComponent) {
      window.headerComponent.setGuest()
    }
  }

  static logout() {
    if (window.headerComponent) {
      window.headerComponent.logout()
    }
  }
}

// Add CSS for bell shake animation
const style = document.createElement("style")
style.textContent = `
  @keyframes bell-shake {
    0%, 100% { transform: rotate(0deg); }
    10%, 30%, 50%, 70%, 90% { transform: rotate(-10deg); }
    20%, 40%, 60%, 80% { transform: rotate(10deg); }
  }
`
document.head.appendChild(style)

// Initialize header component when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.headerComponent = new HeaderComponent()
})
