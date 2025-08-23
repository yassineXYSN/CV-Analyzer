// Global variables for real data
let companies = []
let users = []
const companyAdmins = {} // Store admins by company ID

// Variables for users table functionality
let usersTableData = []
let sortColumn = "name"
let sortDirection = "asc"

// Initialize the interface
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[v0] Admin interface loading...")
  await loadCompaniesFromAPI()
  await loadUsersFromAPI()
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
      console.log("Users loaded:", users) // Check what data you're receiving
      loadUsers()
      loadUsersTable() // Load users table when users are loaded
    } else {
      showNotification("Erreur lors du chargement des utilisateurs", "error")
    }
  } catch (error) {
    console.error("Error loading users:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Add this function near the top with other helper functions
function formatLastActivity(dateString) {
  if (!dateString || dateString === "-") return "-"
  
  try {
    // If it's already a formatted string like "Today", "Yesterday", etc.
    if (typeof dateString === 'string' && !dateString.includes('-') && !dateString.includes('T')) {
      return dateString;
    }
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return "-"
    
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffTime / (1000 * 60))
    
    if (diffDays > 30) {
      return date.toLocaleDateString('fr-FR')
    } else if (diffDays > 0) {
      return `Il y a ${diffDays} jour${diffDays > 1 ? 's' : ''}`
    } else if (diffHours > 0) {
      return `Il y a ${diffHours} heure${diffHours > 1 ? 's' : ''}`
    } else if (diffMinutes > 0) {
      return `Il y a ${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`
    } else {
      return "À l'instant"
    }
  } catch (e) {
    console.error("Error formatting date:", e, dateString)
    return "-"
  }
}

// Also add this function to handle the last login date
function getLastLoginDisplay(lastLogin) {
  if (!lastLogin) return "-"
  
  try {
    // If it's already a formatted string
    if (typeof lastLogin === 'string' && !lastLogin.includes('T') && !lastLogin.includes('-')) {
      return lastLogin;
    }
    
    const loginDate = new Date(lastLogin);
    if (isNaN(loginDate.getTime())) return "-"
    
    return formatLastActivity(lastLogin);
  } catch (e) {
    console.error("Error processing last login:", e, lastLogin)
    return "-"
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
  console.log("[v0] Switching to tab:", tabName)

  // Remove active class from all tabs and content
  document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"))
  document.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"))

  // Add active class to current tab
  event.target.classList.add("active")

  // Show corresponding content
  const tabContent = document.getElementById(`${tabName}-tab`)
  if (tabContent) {
    tabContent.classList.add("active")
  }

  // Load data based on tab
  switch (tabName) {
    case "companies":
      loadCompanies()
      break
    case "users":
      loadUsers()
      break
    case "users-table":
      loadUsersTable()
      break
  }
}

// Load Companies
function loadCompanies() {
  console.log("[v0] Rendering companies:", companies.length)
  const grid = document.getElementById("companies-grid")
  const searchTerm = document.getElementById("company-search").value.toLowerCase()
  const industryFilter = document.getElementById("company-filter").value

  const filteredCompanies = companies.filter((company) => {
    const matchesSearch =
  ((company.name || company.company_name) &&
   (company.name || company.company_name).toLowerCase().includes(searchTerm)) ||
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
    .map((company) => {
      console.log(
        "[v0] Company:",
        company.name,
        "founded_year:",
        company.founded_year,
        "type:",
        typeof company.founded_year,
      )

      return `
        <div class="company-card" onclick="showCompanyDetails(${company.id})">
          <div class="company-header">
            <div class="company-logo">
              ${
                company.logo_url
                  ? `<img src="${company.logo_url}" alt="${company.name || "Company"}">`
                  : (company.name || "N/A").charAt(0)
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

              <button class="btn-icon danger" onclick="deleteCompany(${company.id})" title="Supprimer">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
          <p class="company-description">
            ${company.description || "Aucune description"}
          </p>
          <div class="company-details">
            <div class="detail-item">
              <i class="fas fa-users"></i>
              <span>Taille: ${company.company_size || "Non spécifiée"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-calendar"></i>
              <span>Fondée: ${formatFoundedYear(company.founded_year)}</span>
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
      `
    })
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

  const cleanDescription = (desc) => {
    if (!desc || typeof desc !== "string") return null
    // Remove technical code patterns and return clean description
    if (desc.includes("try:") || desc.includes("return") || desc.includes('"""') || desc.length < 10) {
      return null
    }
    return desc.trim()
  }

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
                : (company.name || "N/A").charAt(0)
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
          <div class="company-details">
            <div class="detail-item">
              <i class="fas fa-calendar"></i>
              <span>Fondée en ${formatFoundedYear(company.founded_year)}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-envelope"></i>
              <span>${company.email || "Email non spécifié"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-phone"></i>
              <span>${company.phone || "Téléphone non spécifié"}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-globe"></i>
              <span>${company.website ? `Site web non spécifié` : "Site web non spécifié"}</span>
            </div>
          </div>
          ${
            cleanDescription(company.description)
              ? `
            <div class="company-description">
              <strong>Description:</strong><br>
              ${cleanDescription(company.description)}
            </div>
          `
              : ""
          }
        </div>

        <div class="admins-section">
          <div class="admins-header">
            <h3><i class="fas fa-users-cog"></i> Administrateurs (${admins.length})</h3>
            <button class="add-admin-btn" onclick="showAddAdminModal(${companyId})">
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
                  ${(admin.name || admin.first_name || "UN").charAt(0).toUpperCase()}${((admin.name || admin.last_name || "N").charAt(1) || "").toUpperCase()}
                </div>
                <div class="admin-info">
                  <h4>${admin.name || `${admin.first_name || ""} ${admin.last_name || ""}`.trim() || "Nom non spécifié"}</h4>
                  <p class="admin-email">${admin.email}</p>
                  <span class="admin-role role-${(admin.position || admin.access_level || "employee").toLowerCase().replace("_", "-")}">
                    ${formatRoleDisplay(admin.position || admin.access_level || "employee")}
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
  console.log("[v0] Loading users grid...")
  const usersGrid = document.getElementById("users-grid")

  if (users.length === 0) {
    usersGrid.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-users"></i>
        <h3>Aucun utilisateur trouvé</h3>
        <p>Aucun utilisateur n'a été créé pour le moment.</p>
        <button class="btn-add" onclick="showAddUserModal()">
          <i class="fas fa-user-plus"></i>
          Ajouter un utilisateur
        </button>
      </div>
    `
    return
  }

  usersGrid.innerHTML = users
    .map((user) => {
      const initials = user.name
        .split(" ")
        .map((n) => n.charAt(0))
        .join("")
        .substring(0, 2)
        .toUpperCase()
      const userType = user.user_type === "admin" ? "Admin" : "Employé"
      const roleDisplay = formatRoleDisplay(user.position)

      return `
      <div class="user-card" onclick="showUserDetails(${user.id})">
        <div class="user-header">
          <div class="user-avatar">
            ${initials}
          </div>
          <div class="user-info">
            <h3>${user.name}</h3>
            <p class="user-email">${user.email}</p>
            <span class="user-type ${user.user_type}">${userType}</span>
          </div>
          <div class="user-actions">
            <button class="btn-icon" onclick="event.stopPropagation(); editUser('${user.id}')" title="Modifier">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn-icon btn-danger" onclick="event.stopPropagation(); deleteUser('${user.id}')" title="Supprimer">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
        <div class="user-details">
          <div class="user-detail">
            <i class="fas fa-briefcase"></i>
            <span>${roleDisplay}</span>
          </div>
          ${
            user.company_name
              ? `
            <div class="user-detail">
              <i class="fas fa-building"></i>
              <span>${user.company_name}</span>
            </div>
          `
              : ""
          }

        </div>
      </div>
    `
    })
    .join("")
}

function showUserDetails(userId) {
  const user = users.find((u) => u.id == userId)
  if (!user) return

  // Afficher les détails de l'utilisateur (à implémenter selon vos besoins)
  showNotification(`Détails de ${user.name}`, "info")
}

function loadUsersTable() {
  console.log("[v0] Loading users table...")
  
  // Map the users data correctly
  usersTableData = users.map((user) => {
    // Handle different user types and ID formats
    const userId = typeof user.id === 'string' && user.id.startsWith('emp_') 
      ? user.id.replace('emp_', '') 
      : user.id;
    
    return {
      id: userId,
      name: user.name || `${user.first_name || ""} ${user.last_name || ""}`.trim() || "Nom non spécifié",
      email: user.email || "Email non spécifié",
      type: getUserTypeForTable(user.position || user.role),
      lastActivity: user.last_login || user.lastActivity || "-",
      position: user.position || user.role,
      isActive: user.is_active !== false,
      isVerified: user.is_verified || user.isVerified || false
    }
  })

  renderUsersTable()
}

function getUserTypeForTable(position) {
  const typeMap = {
    super_admin: "Admin",
    hr_manager: "Admin",
    hr_admin: "Admin",
    department_head: "Member",
    recruiter: "Member",
  }
  return typeMap[position] || "Member"
}

function getRandomLastActivity() {
  const activities = ["Today", "Yesterday", "2 days ago", "1 week ago", "2 weeks ago", "1 month ago", "-"]
  return activities[Math.floor(Math.random() * activities.length)]
}

function getAvatarColor(name) {
  const colors = ["blue", "green", "purple", "pink", "orange", "red", "indigo", "teal"]
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}

function renderUsersTable() {
  const tbody = document.getElementById("users-table-body")

  if (usersTableData.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="table-empty-state">
          <i class="fas fa-users"></i>
          <h3>Aucun utilisateur trouvé</h3>
          <p>Aucun utilisateur ne correspond à vos critères de recherche.</p>
        </td>
      </tr>
    `
    return
  }

  tbody.innerHTML = usersTableData
    .map((user) => {
      const initials = user.name
        .split(" ")
        .map((n) => n.charAt(0))
        .join("")
        .substring(0, 2)
        .toUpperCase()
      const avatarColor = getAvatarColor(user.name)

return `
  <tr>
    <td>
      <div class="table-user-info">
        <div class="table-user-avatar avatar-${avatarColor}">
          ${initials}
        </div>
        <div class="table-user-details">
          <h4>${user.name}</h4>
          <p class="table-user-email">${user.email}</p>
        </div>
      </div>
    </td>
    <td>
      <span class="table-user-type ${user.type.toLowerCase().replace(" ", "-")}">
        ${user.type}
      </span>
    </td>

    <td>
      <span class="table-user-verified ${user.isVerified ? 'verified' : 'not-verified'}">
        <i class="fas ${user.isVerified ? 'fa-check-circle' : 'fa-times-circle'}"></i>
        ${user.isVerified ? 'Oui' : 'Non'}
      </span>
    </td>
    <td class="table-last-activity">
      ${getLastLoginDisplay(user.lastActivity)}
    </td>
    <td>
      <div class="table-actions">
        ${!user.isVerified ? `
        <button class="table-actions-btn warning" onclick="resendVerification('${user.id}')" title="Renvoyer la vérification">
          <i class="fas fa-envelope"></i>
        </button>
        ` : ''}
        <button class="table-actions-btn danger" onclick="deleteUser('${user.id}')" title="Supprimer">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </td>
  </tr>
`

    })
    .join("")
}

// Add this function to safely parse dates
function safeParseDate(dateString) {
  if (!dateString) return null;
  
  try {
    // Handle ISO string
    if (typeof dateString === 'string' && dateString.includes('T')) {
      return new Date(dateString);
    }
    
    // Handle timestamp
    if (typeof dateString === 'number' || !isNaN(dateString)) {
      return new Date(parseInt(dateString));
    }
    
    // Handle other string formats
    return new Date(dateString);
  } catch (e) {
    console.error("Error parsing date:", e, dateString);
    return null;
  }
}

function filterUsersTable() {
  const searchTerm = document.getElementById("users-table-search").value.toLowerCase()
  const typeFilter = document.getElementById("users-table-filter").value

  // Use the actual users data from the API
  let filteredData = users.map((user) => {
    const userId = typeof user.id === 'string' && user.id.startsWith('emp_') 
      ? user.id.replace('emp_', '') 
      : user.id;
    
    return {
      id: userId,
      name: user.name || `${user.first_name || ""} ${user.last_name || ""}`.trim() || "Nom non spécifié",
      email: user.email || "Email non spécifié",
      type: getUserTypeForTable(user.position || user.role),
      lastActivity: user.last_login || "-",
      position: user.position || user.role,
      isActive: user.is_active !== false,
      isVerified: user.is_verified || false
    }
  })

  if (searchTerm) {
    filteredData = filteredData.filter(
      (user) => user.name.toLowerCase().includes(searchTerm) || user.email.toLowerCase().includes(searchTerm),
    )
  }

  if (typeFilter) {
    filteredData = filteredData.filter((user) => user.type === typeFilter)
  }

  usersTableData = filteredData
  renderUsersTable()
}

function sortUsersTable(column) {
  if (sortColumn === column) {
    sortDirection = sortDirection === "asc" ? "desc" : "asc"
  } else {
    sortColumn = column
    sortDirection = "asc"
  }

  usersTableData.sort((a, b) => {
    let aVal = a[column]
    let bVal = b[column]

    if (column === "activity") {
      // Custom sorting for last activity
      const activityOrder = {
        Today: 0,
        Yesterday: 1,
        "2 days ago": 2,
        "1 week ago": 3,
        "2 weeks ago": 4,
        "1 month ago": 5,
        "-": 6,
      }
      aVal = activityOrder[a.lastActivity] || 999
      bVal = activityOrder[b.lastActivity] || 999
    }

    if (typeof aVal === "string") {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    }

    if (sortDirection === "asc") {
      return aVal < bVal ? -1 : aVal > bVal ? 1 : 0
    } else {
      return aVal > bVal ? -1 : aVal < bVal ? 1 : 0
    }
  })

  renderUsersTable()

  // Update sort indicators
  document.querySelectorAll(".users-table th i").forEach((icon) => {
    icon.className = "fas fa-sort"
  })

  const currentHeader = document.querySelector(`[onclick="sortUsersTable('${column}')"] i`)
  if (currentHeader) {
    currentHeader.className = `fas fa-sort-${sortDirection === "asc" ? "up" : "down"}`
  }
}

function showUserTableActions(userId) {
  // Simple implementation - could be expanded with a dropdown menu
  const actions = [
    { label: "Modifier", action: () => editUser(userId) },
    { label: "Désactiver", action: () => toggleUserStatus(userId) },
    { label: "Supprimer", action: () => deleteUser(userId) },
  ]

  // For now, just show the first action (edit)
  editUser(userId)
}

// Update Statistics
function updateStatistics() {
  // Vérifier si les éléments existent avant de les mettre à jour
  const totalCompaniesEl = document.getElementById("total-companies")
  const totalUsersEl = document.getElementById("total-users")
  const activeUsersEl = document.getElementById("active-users")
  const completedCompaniesEl = document.getElementById("completed-companies")

  if (totalCompaniesEl) totalCompaniesEl.textContent = companies.length
  if (totalUsersEl) totalUsersEl.textContent = users.length

  // Calculer les statistiques supplémentaires
  const activeUsers = users.filter((u) => u.is_active).length
  const completedCompanies = companies.filter((c) => c.setup_completed).length

  // Mettre à jour seulement si les éléments existent
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
    hr_admin: "HR Admin",
  }
  return labels[role] || role
}

function formatRoleDisplay(role) {
  if (!role) return "EMPLOYEE"

  const roleMap = {
    SUPER_ADMIN: "Admin",
    DEPARTMENT_HEAD: "Chef de département",
    RECRUITER: "Recruteur",
    HR_ADMIN: "Admin RH",
    HR_MANAGER: "Manager RH",
  }

  return roleMap[role.toUpperCase()] || role.replace("_", " ").toUpperCase()
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
    company_name: formData.get("company_name"), // Changed from name to company_name
    industry: formData.get("industry") || "", // Added industry field
    company_size: formData.get("company_size") || "", // Added company_size field
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    website: formData.get("website") || "", // Added website field
    description: formData.get("description") || "", // Added description field
    founded_year: formData.get("founded_year") ? Number.parseInt(formData.get("founded_year")) : null, // Added founded_year
    setup_completed: false, // Default value
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
      console.error("API Error:", error) // Added error logging for debugging
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
    company_name: formData.get("company_name"), // Changed from name to company_name
    industry: formData.get("industry") || "",
    company_size: formData.get("company_size") || "",
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    website: formData.get("website") || "",
    description: formData.get("description") || "",
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
      console.error("API Error:", error) // Added error logging for debugging
      showNotification(error.detail || "Erreur lors de la modification", "error")
    }
  } catch (error) {
    console.error("Error updating company:", error)
    showNotification("Erreur de connexion", "error")
  }
}

async function deleteCompany(companyId) {
  showConfirmationModal({
    title: "Supprimer l'entreprise",
    message:
      "Êtes-vous sûr de vouloir supprimer cette entreprise ? Cette action est irréversible et supprimera également tous les administrateurs associés.",
    confirmText: "Supprimer",
    cancelText: "Annuler",
    type: "danger",
    onConfirm: async () => {
      try {
        showNotification("Suppression en cours...", "info")

        const response = await fetch(`/admin/api/companies/${companyId}`, {
          method: "DELETE",
        })

        if (response.ok) {
          showNotification("Entreprise supprimée avec succès", "success")
          loadCompanies()
        } else {
          const error = await response.text()
          showNotification(`Erreur: ${error}`, "error")
        }
      } catch (error) {
        console.error("Error deleting company:", error)
        showNotification("Erreur lors de la suppression", "error")
      }
    },
  })
}

async function createUser(event) {
  event.preventDefault()
  const formData = new FormData(event.target)

  const userData = {
    first_name: formData.get("first_name"),
    last_name: formData.get("last_name"),
    email: formData.get("email"),
    password: formData.get("password"),
    role: formData.get("role"),
    company_id: formData.get("company_id") ? Number.parseInt(formData.get("company_id")) : null,
  }

  try {
    console.log("[v0] Creating user with data:", userData)
    const response = await fetch("/admin/api/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    })

    if (response.ok) {
      showNotification("Utilisateur créé avec succès! Un email de vérification a été envoyé.", "success")
      closeModal("add-user-modal")
      event.target.reset()

      try {
        const result = await response.json()
        console.log("[v0] User creation result:", result)

        // Recharger les données
        await loadUsersFromAPI()
        updateStatistics()
      } catch (updateError) {
        console.warn("[v0] Error updating UI after user creation:", updateError)
        showNotification("Utilisateur créé avec succès", "success")
      }
    } else {
      const errorText = await response.text()
      console.log("[v0] Error response:", errorText)

      let errorMessage = "Erreur lors de la création"
      try {
        const error = JSON.parse(errorText)
        errorMessage = error.detail || error.message || errorMessage
      } catch (e) {
        errorMessage = errorText || errorMessage
      }

      showNotification(errorMessage, "error")
    }
  } catch (error) {
    console.error("[v0] Error creating user:", error)
    showNotification("Erreur de connexion au serveur", "error")
  }
}

async function resendVerification(userId) {
  try {
    const response = await fetch(`/admin/api/users/${userId}/resend-verification`, {
      method: "POST",
    })

    if (response.ok) {
      showNotification("Email de vérification renvoyé avec succès", "success")
    } else {
      const error = await response.json()
      showNotification(error.detail || "Erreur lors de l'envoi de l'email", "error")
    }
  } catch (error) {
    console.error("Error resending verification:", error)
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
  console.log("Tentative de suppression de l'utilisateur avec ID:", userId)

  showConfirmationModal({
    title: "Supprimer l'utilisateur",
    message:
      "Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action est irréversible et retirera tous ses accès administrateur.",
    confirmText: "Supprimer",
    cancelText: "Annuler",
    type: "danger",
    onConfirm: async () => {
      try {
        showNotification("Suppression en cours...", "info")

        const response = await fetch(`/admin/api/users/${userId}`, {
          method: "DELETE",
        })

        if (response.ok) {
          showNotification("Utilisateur supprimé avec succès!", "success")
          loadUsers()
        } else {
          const error = await response.text()
          showNotification(`Erreur: ${error}`, "error")
        }
      } catch (error) {
        console.error("Error deleting user:", error)
        showNotification("Erreur lors de la suppression", "error")
      }
    },
  })
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

function formatFoundedYear(foundedYear) {
  console.log("[v0] formatFoundedYear input:", foundedYear, "type:", typeof foundedYear)

  if (!foundedYear || foundedYear === null || foundedYear === undefined) {
    console.log("[v0] Founded year is null/undefined")
    return "Non spécifiée"
  }

  // Handle different formats: could be a year number, date string, or null
  if (typeof foundedYear === "number") {
    console.log("[v0] Founded year is number:", foundedYear)
    return foundedYear.toString()
  }

  if (typeof foundedYear === "string") {
    console.log("[v0] Founded year is string:", foundedYear)
    // If it's a date string, extract the year
    const year = new Date(foundedYear).getFullYear()
    if (!isNaN(year) && year > 1800 && year <= new Date().getFullYear()) {
      console.log("[v0] Extracted year from date:", year)
      return year.toString()
    }
    // If it's already just a year string
    const yearNum = Number.parseInt(foundedYear)
    if (!isNaN(yearNum) && yearNum > 1800 && yearNum <= new Date().getFullYear()) {
      console.log("[v0] Parsed year from string:", yearNum)
      return yearNum.toString()
    }
  }

  console.log("[v0] Could not format founded year, returning default")
  return "Non spécifiée"
}

// Custom Confirmation Modal System
function showConfirmationModal(options) {
  const {
    title = "Confirmation",
    message = "Êtes-vous sûr de vouloir continuer ?",
    confirmText = "Confirmer",
    cancelText = "Annuler",
    type = "warning", // warning, danger, info
    onConfirm = () => {},
    onCancel = () => {},
  } = options

  // Remove any existing confirmation modal
  const existingModal = document.querySelector(".confirmation-modal-overlay")
  if (existingModal) {
    existingModal.remove()
  }

  const modal = document.createElement("div")
  modal.className = "confirmation-modal-overlay"

  const typeIcons = {
    warning: "fas fa-exclamation-triangle",
    danger: "fas fa-exclamation-circle",
    info: "fas fa-info-circle",
  }

  modal.innerHTML = `
    <div class="confirmation-modal">
      <div class="confirmation-header">
        <div class="confirmation-icon ${type}">
          <i class="${typeIcons[type]}"></i>
        </div>
        <h3>${title}</h3>
      </div>
      
      <div class="confirmation-content">
        <p>${message}</p>
      </div>
      
      <div class="confirmation-actions">
        <button class="btn-cancel" id="confirmCancel">${cancelText}</button>
        <button class="btn-confirm ${type}" id="confirmAction">${confirmText}</button>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Add show class after a brief delay for animation
  setTimeout(() => modal.classList.add("show"), 10)

  // Event listeners
  const confirmBtn = modal.querySelector("#confirmAction")
  const cancelBtn = modal.querySelector("#confirmCancel")

  const closeModal = () => {
    modal.classList.remove("show")
    setTimeout(() => modal.remove(), 300)
  }

  confirmBtn.addEventListener("click", () => {
    onConfirm()
    closeModal()
  })

  cancelBtn.addEventListener("click", () => {
    onCancel()
    closeModal()
  })

  // Close on outside click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      onCancel()
      closeModal()
    }
  })

  // Close on Escape key
  const escapeHandler = (e) => {
    if (e.key === "Escape") {
      onCancel()
      closeModal()
      document.removeEventListener("keydown", escapeHandler)
    }
  }
  document.addEventListener("keydown", escapeHandler)
}

// Function to remove admin access with confirmation
async function removeAdminAccess(adminId, companyId) {
  showConfirmationModal({
    title: "Retirer l'accès administrateur",
    message: "Êtes-vous sûr de vouloir retirer l'accès administrateur à cet utilisateur pour cette entreprise ?",
    confirmText: "Retirer l'accès",
    cancelText: "Annuler",
    type: "warning",
    onConfirm: async () => {
      try {
        showNotification("Suppression de l'accès en cours...", "info")

        const response = await fetch(`/admin/api/companies/${companyId}/admins/${adminId}`, {
          method: "DELETE",
        })

        if (response.ok) {
          showNotification("Accès administrateur retiré avec succès", "success")
          // Refresh the company details
          showCompanyDetails(companyId)
        } else {
          const error = await response.text()
          showNotification(`Erreur: ${error}`, "error")
        }
      } catch (error) {
        console.error("Error removing admin access:", error)
        showNotification("Erreur lors de la suppression de l'accès", "error")
      }
    },
  })
}
