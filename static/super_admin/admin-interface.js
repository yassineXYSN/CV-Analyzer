// Global variables for real data
let companies = []
let users = []
const companyAdmins = {} // Store admins by company ID

// Initialize the interface
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[v0] Admin interface loading...")
  await loadCompaniesFromAPI()
  await loadUsersFromAPI()
  updateStatistics()
  loadCompanyOptions()
  console.log("[v0] Admin interface loaded successfully")
})

// API Functions
async function loadCompaniesFromAPI() {
  try {
    console.log("[v0] Loading companies from API...")
    const response = await fetch("/admin/api/companies")
    if (response.ok) {
      companies = await response.json()
      console.log("[v0] Companies loaded:", companies)
      loadCompanies()
    } else {
      showNotification("Erreur lors du chargement des entreprises", "error")
    }
  } catch (error) {
    console.error("Error loading companies:", error)
    showNotification("Erreur de connexion", "error")
  }
}

async function loadUsersFromAPI() {
  try {
    const response = await fetch("/admin/api/users")
    if (response.ok) {
      users = await response.json()
      loadUsers()
    } else {
      showNotification("Erreur lors du chargement des utilisateurs", "error")
    }
  } catch (error) {
    console.error("Error loading users:", error)
    showNotification("Erreur de connexion", "error")
  }
}

async function loadCompanyAdmins(companyId) {
  try {
    console.log("[v0] Loading admins for company ID:", companyId)

    // First try to get admins via dedicated API endpoint
    try {
      const response = await fetch(`/admin/api/companies/${companyId}/admins`)
      console.log("[v0] API response status:", response.status)

      if (response.ok) {
        const admins = await response.json()
        console.log("[v0] Admins loaded from API:", admins)
        companyAdmins[companyId] = admins
        return admins
      } else {
        console.log("[v0] API endpoint returned error:", response.status, await response.text())
      }
    } catch (apiError) {
      console.log("[v0] API endpoint error:", apiError.message)
    }

    // Fallback: filter users by company_id or company relationship
    console.log("[v0] Using fallback logic - All users:", users.length)
    console.log("[v0] Looking for company ID:", companyId)

    const companyUsers = users.filter((user) => {
      console.log("[v0] Checking user:", user.name, "company_id:", user.company_id, "company_name:", user.company_name)

      // Check direct company_id match (convert both to numbers for comparison)
      if (user.company_id && Number.parseInt(user.company_id) === Number.parseInt(companyId)) {
        console.log("[v0] Found user by company_id:", user.name)
        return true
      }

      // Check if user has company_name that matches our company
      const company = companies.find((c) => c.id === Number.parseInt(companyId))
      if (company && user.company_name && user.company_name === company.name) {
        console.log("[v0] Found user by company_name:", user.name)
        return true
      }

      return false
    })

    console.log("[v0] Filtered company users:", companyUsers.length, "users found")
    companyAdmins[companyId] = companyUsers
    return companyUsers
  } catch (error) {
    console.error("[v0] Error loading company admins:", error)
    showNotification("Erreur lors du chargement des administrateurs", "error")
  }
  return []
}

// Tab Management
function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.classList.remove("active")
  })

  // Remove active class from all buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active")
  })

  // Show selected tab
  document.getElementById(tabName + "-tab").classList.add("active")

  // Add active class to clicked button
  event.target.classList.add("active")
}

// Load Companies
function loadCompanies() {
  console.log("[v0] Rendering companies:", companies.length)
  const grid = document.getElementById("companies-grid")
  const searchTerm = document.getElementById("company-search").value.toLowerCase()
  const industryFilter = document.getElementById("company-filter").value

  const filteredCompanies = companies.filter((company) => {
    const matchesSearch =
      (company.name && company.name.toLowerCase().includes(searchTerm)) ||
      (company.description && company.description.toLowerCase().includes(searchTerm))
    const matchesIndustry = !industryFilter || company.industry === industryFilter
    return matchesSearch && matchesIndustry
  })

  if (filteredCompanies.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="fas fa-building"></i>
        <h3>Aucune entreprise trouvée</h3>
        <p>Aucune entreprise ne correspond à vos critères de recherche.</p>
      </div>
    `
    return
  }

  grid.innerHTML = filteredCompanies
    .map(
      (company) => `
        <div class="company-card" onclick="showCompanyDetails(${company.id})">
          <div class="company-header">
            <div class="company-logo">
              ${
                company.logo_url
                  ? `<img src="${company.logo_url}" alt="${company.name || "Company"}">`
                  : // Using 'name' instead of 'company_name'
                    (company.name || "N/A").charAt(0)
              }
            </div>
            <div class="company-info">
              <h3>${company.name || "Nom non spécifié"}</h3>
              <div class="industry">
                <i class="fas fa-industry"></i>
                ${getIndustryLabel(company.industry)}
              </div>
            </div>
            <div class="company-actions" onclick="event.stopPropagation()">
              <button class="btn-icon" onclick="editCompany(${company.id})" title="Modifier">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn-icon danger" onclick="deleteCompany(${company.id})" title="Supprimer">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>

          <div class="company-details">
            <div class="detail-item">
              <i class="fas fa-users"></i>
              <span>Taille: ${company.company_size || "Non spécifiée"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-calendar"></i>
              <span>Fondée: ${company.founded_year || "Non spécifiée"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-envelope"></i>
              <span>${company.email || "Non spécifié"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-${company.setup_completed ? "check-circle" : "clock"}"></i>
              <span style="color: ${company.setup_completed ? "var(--success-color)" : "var(--warning-color)"}">
                ${company.setup_completed ? "Configurée" : "En cours"}
              </span>
            </div>
          </div>
          <div class="company-footer">
            <small>Cliquez pour voir les administrateurs</small>
          </div>
        </div>
      `,
    )
    .join("")
}

// Show Company Details with Admins
async function showCompanyDetails(companyId) {
  console.log("[v0] Opening company details for ID:", companyId)
  const company = companies.find((c) => c.id === companyId)
  if (!company) {
    console.error("[v0] Company not found:", companyId)
    return
  }

  console.log("[v0] Company found:", company)
  // Load admins for this company
  const admins = await loadCompanyAdmins(companyId)
  console.log("[v0] Admins loaded:", admins)

  // Create and show modal
  const modal = document.createElement("div")
  modal.className = "company-details-overlay"
  modal.innerHTML = `
    <div class="company-details-panel">
      <div class="details-header">
        <div class="company-title">
          <div class="company-logo-large">
            ${
              company.logo_url
                ? `<img src="${company.logo_url}" alt="${company.name || "Company"}">`
                : // Using 'name' instead of 'company_name'
                  (company.name || "N/A").charAt(0)
            }
          </div>
          <div>
            <h2>${company.name || "Nom non spécifié"}</h2>
            <p>${getIndustryLabel(company.industry)} • ${company.company_size || "Taille non spécifiée"}</p>
          </div>
        </div>
        <button class="close-details" onclick="closeCompanyDetails()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="details-content">
        <div class="company-overview">
          <h3><i class="fas fa-info-circle"></i> Informations générales</h3>
          <div class="overview-grid">
            <div class="overview-item">
              <i class="fas fa-calendar"></i>
              <span>Fondée en ${company.founded_year || "Non spécifiée"}</span>
            </div>
            <div class="overview-item">
              <i class="fas fa-envelope"></i>
              <span>${company.email || "Email non spécifié"}</span>
            </div>
            <div class="overview-item">
              <i class="fas fa-phone"></i>
              <span>${company.phone || "Téléphone non spécifié"}</span>
            </div>
            <div class="overview-item">
              <i class="fas fa-globe"></i>
              <span>${company.website ? `<a href="${company.website}" target="_blank">Site web</a>` : "Site web non spécifié"}</span>
            </div>
          </div>
          ${
            company.description
              ? `
            <div class="company-description">
              <strong>Description:</strong><br>
              ${company.description}
            </div>
          `
              : ""
          }
        </div>

        <div class="admins-section">
          <div class="section-header">
            <h3><i class="fas fa-users-cog"></i> Administrateurs (${admins.length})</h3>
            <button class="btn btn-primary" onclick="showAddAdminModal(${companyId})">
              <i class="fas fa-plus"></i> Ajouter Admin
            </button>
          </div>
          
          <div class="admins-grid">
            ${
              admins.length > 0
                ? admins
                    .map(
                      (admin) => `
              <div class="admin-card">
                <div class="admin-avatar">
                  ${(admin.name || "UN").charAt(0)}${(admin.name || "UN").charAt(1) || ""}
                </div>
                <div class="admin-info">
                  <h4>${admin.name || "Nom non spécifié"}</h4>
                  <p class="admin-email">${admin.email}</p>
                <span class="admin-role role-${admin.position || "employee"}">
                  ${{
                    super_admin: "ADMIN",
                    recruiter: "RECRUTEUR",
                    department_head: "CHEF DE DÉPARTEMENT"
                  }[admin.position] || (admin.position || "employee").toUpperCase()}
                </span>

                </div>
                <div class="admin-actions">
                  <button class="btn-icon" onclick="editAdminAccess(${admin.id}, ${companyId})" title="Modifier accès">
                    <i class="fas fa-key"></i>
                  </button>
                  <button class="btn-icon danger" onclick="removeAdminAccess(${admin.id}, ${companyId})" title="Retirer accès">
                    <i class="fas fa-user-minus"></i>
                  </button>
                </div>
              </div>
            `,
                    )
                    .join("")
                : `
              <div class="empty-admins">
                <i class="fas fa-users-slash"></i>
                <h4>Aucun administrateur</h4>
                <p>Cette entreprise n'a pas encore d'administrateurs assignés.</p>
              </div>
            `
            }
          </div>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Close on outside click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeCompanyDetails()
    }
  })
}

function closeCompanyDetails() {
  const modal = document.querySelector(".company-details-overlay")
  if (modal) {
    modal.remove()
  }
}

// Load Users
function loadUsers() {
  console.log("[v0] Rendering users:", users.length)
  const grid = document.getElementById("users-grid")
  const searchTerm = document.getElementById("user-search").value.toLowerCase()
  const roleFilter = document.getElementById("user-role-filter").value

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      (user.name && user.name.toLowerCase().includes(searchTerm)) ||
      (user.email && user.email.toLowerCase().includes(searchTerm))
    const matchesRole = !roleFilter || user.position === roleFilter
    return matchesSearch && matchesRole
  })

  if (filteredUsers.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="fas fa-users"></i>
        <h3>Aucun utilisateur trouvé</h3>
        <p>Aucun utilisateur ne correspond à vos critères de recherche.</p>
      </div>
    `
    return
  }

  grid.innerHTML = filteredUsers
    .map(
      (user) => `
        <div class="admin-card-full">
          <div class="user-header">
            <div class="user-avatar">
              ${(user.name || "UN").charAt(0)}${(user.name || "UN").charAt(1) || ""}
            </div>
            <div class="user-info">
              <h3>${user.name || "Nom non spécifié"}</h3>
              <div class="email">${user.email || "Email non spécifié"}</div>
              <span class="user-role ${user.position || "employee"}">${getRoleLabel(user.position)}</span>
              <div class="user-status ${user.is_active !== false ? "active" : "inactive"}">
                <i class="fas fa-circle"></i>
                ${user.is_active !== false ? "Actif" : "Inactif"}
              </div>
            </div>
            <div class="user-actions">
              <button class="btn-icon" onclick="editUser(${user.id})" title="Modifier">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn-icon ${user.is_active !== false ? "danger" : ""}" 
                      onclick="toggleUserStatus(${user.id})" 
                      title="${user.is_active !== false ? "Désactiver" : "Activer"}">
                <i class="fas fa-${user.is_active !== false ? "user-slash" : "user-check"}"></i>
              </button>
              <button class="btn-icon danger" onclick="deleteUser(${user.id})" title="Supprimer">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
          
          <div class="admin-companies">
            <h4><i class="fas fa-building"></i> Entreprises assignées</h4>
            <div class="company-tags" id="user-companies-${user.id}">
              <span class="loading">Chargement...</span>
            </div>
          </div>
        </div>
      `,
    )
    .join("")

  // Load companies for each user
  filteredUsers.forEach((user) => {
    loadUserCompanies(user.id)
  })
}

async function loadUserCompanies(userId) {
  try {
    const user = users.find((u) => u.id === userId)
    const container = document.getElementById(`user-companies-${userId}`)

    if (user && user.company_id && user.company_name) {
      container.innerHTML = `
        <span class="company-tag" onclick="showCompanyDetails(${user.company_id})">
          ${user.company_name}
          <small>(employee)</small>
        </span>
      `
    } else {
      container.innerHTML = '<span class="no-companies">Aucune entreprise assignée</span>'
    }
  } catch (error) {
    console.error("Error loading user companies:", error)
    const container = document.getElementById(`user-companies-${userId}`)
    if (container) {
      container.innerHTML = '<span class="error">Erreur de chargement</span>'
    }
  }
}

// Update Statistics
function updateStatistics() {
  document.getElementById("total-companies").textContent = companies.length
  document.getElementById("total-users").textContent = users.length

  // Calculate additional stats
  const activeUsers = users.filter((u) => u.is_active).length
  const completedCompanies = companies.filter((c) => c.setup_completed).length

  // Update additional stats if elements exist
  const activeUsersEl = document.getElementById("active-users")
  const completedCompaniesEl = document.getElementById("completed-companies")

  if (activeUsersEl) activeUsersEl.textContent = activeUsers
  if (completedCompaniesEl) completedCompaniesEl.textContent = completedCompanies
}

// Load Company Options for User Form
function loadCompanyOptions() {
  const select = document.getElementById("user-company-select")
  if (select) {
    select.innerHTML =
      '<option value="">Aucune entreprise</option>' +
      companies
        .map((company) => `<option value="${company.id}">${company.name || "Entreprise sans nom"}</option>`)
        .join("")
  }
}

// Helper Functions
function getIndustryLabel(industry) {
  const labels = {
    tech: "Technologie",
    finance: "Finance",
    healthcare: "Santé",
    education: "Éducation",
    retail: "Commerce",
    manufacturing: "Industrie",
  }
  return labels[industry] || industry || "Non spécifiée"
}

function getRoleLabel(role) {
  const labels = {
    super_admin: "Super Admin",
    hr_manager: "HR Manager",
    hr_admin: "HR Admin",
  }
  return labels[role] || role
}

// Modal Management
function showAddCompanyModal() {
  document.getElementById("add-company-modal").classList.add("show")
}

function showAddUserModal() {
  document.getElementById("add-user-modal").classList.add("show")
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("show")
}

// Company Management
async function createCompany(event) {
  event.preventDefault()
  const formData = new FormData(event.target)

  const companyData = {
    name: formData.get("company_name"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
  }

  try {
    const response = await fetch("/admin/api/companies", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(companyData),
    })

    if (response.ok) {
      await loadCompaniesFromAPI()
      loadCompanyOptions()
      updateStatistics()
      closeModal("add-company-modal")
      showNotification("Entreprise créée avec succès!", "success")
      event.target.reset()
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de la création", "error")
    }
  } catch (error) {
    console.error("Error creating company:", error)
    showNotification("Erreur de connexion", "error")
  }
}

function editCompany(companyId) {
  const company = companies.find((c) => c.id === companyId)
  if (!company) return

  // Fill the edit form
  document.getElementById("edit-company-id").value = company.id
  document.getElementById("edit-company-name").value = company.name
  document.getElementById("edit-company-industry").value = company.industry || ""

  // Show modal
  document.getElementById("edit-company-modal").classList.add("show")
}

async function updateCompany(event) {
  event.preventDefault()
  const formData = new FormData(event.target)
  const companyId = Number.parseInt(formData.get("company_id"))

  const companyData = {
    name: formData.get("company_name"),
    industry: formData.get("industry"),
  }

  try {
    const response = await fetch(`/admin/api/companies/${companyId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(companyData),
    })

    if (response.ok) {
      await loadCompaniesFromAPI()
      loadCompanyOptions()
      closeModal("edit-company-modal")
      showNotification("Entreprise modifiée avec succès!", "success")
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de la modification", "error")
    }
  } catch (error) {
    console.error("Error updating company:", error)
    showNotification("Erreur de connexion", "error")
  }
}

async function deleteCompany(companyId) {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cette entreprise ?")) return

  try {
    const response = await fetch(`/admin/api/companies/${companyId}`, {
      method: "DELETE",
    })

    if (response.ok) {
      await loadCompaniesFromAPI()
      loadCompanyOptions()
      updateStatistics()
      showNotification("Entreprise supprimée avec succès!", "success")
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de la suppression", "error")
    }
  } catch (error) {
    console.error("Error deleting company:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// User Management
async function createUser(event) {
  event.preventDefault()
  const formData = new FormData(event.target)

  const userData = {
    name: formData.get("first_name") + " " + formData.get("last_name"),
    email: formData.get("email"),
    phone: formData.get("phone") || "",
    position: formData.get("role"),
    company_id: formData.get("company_id") ? Number.parseInt(formData.get("company_id")) : null,
  }

  try {
    const response = await fetch("/admin/api/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    })

    if (response.ok) {
      await loadUsersFromAPI()
      updateStatistics()
      closeModal("add-user-modal")
      showNotification("Utilisateur créé avec succès!", "success")
      event.target.reset()
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de la création", "error")
    }
  } catch (error) {
    console.error("Error creating user:", error)
    showNotification("Erreur de connexion", "error")
  }
}

function editUser(userId) {
  showNotification("Fonctionnalité de modification en cours de développement", "info")
}

async function toggleUserStatus(userId) {
  showNotification("Fonctionnalité de changement de statut en cours de développement", "info")
}

async function deleteUser(userId) {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) return

  try {
    const response = await fetch(`/admin/api/users/${userId}`, {
      method: "DELETE",
    })

    if (response.ok) {
      await loadUsersFromAPI()
      updateStatistics()
      showNotification("Utilisateur supprimé avec succès!", "success")
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de la suppression", "error")
    }
  } catch (error) {
    console.error("Error deleting user:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Notification System
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type} show`

  const icons = {
    success: "fas fa-check-circle",
    error: "fas fa-exclamation-circle",
    warning: "fas fa-exclamation-triangle",
    info: "fas fa-info-circle",
  }

  notification.innerHTML = `
        <div class="notification-content">
            <i class="${icons[type]}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `

  document.body.appendChild(notification)

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.classList.remove("show")
      setTimeout(() => notification.remove(), 300)
    }
  }, 5000)
}

// Close modals when clicking outside
document.querySelectorAll(".modal-overlay").forEach((overlay) => {
  overlay.addEventListener("click", function (e) {
    if (e.target === this) {
      this.classList.remove("show")
    }
  })
})

// Close company details with Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.show").forEach((modal) => {
      modal.classList.remove("show")
    })
    closeCompanyDetails()
  }
})
