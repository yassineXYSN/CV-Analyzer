console.log("🎯 FRONTEND: Dashboard chargé avec succès")

// Variables globales
let departments = []
let employees = []
let jobs = []
let applications = [] // Variable pour les candidatures
let currentUser = null
const expandedDepartments = new Set()
let filteredDepartments = []
let isSearchActive = false

// Initialisation du dashboard
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 FRONTEND: Initialisation du dashboard")
  initializeDashboard()
})

// Fonction d'initialisation
async function initializeDashboard() {
  try {
    console.log("🔄 FRONTEND: Début initialisation")

    // Charger l'utilisateur actuel
    await loadCurrentUser()

    // Charger les données de base
    await Promise.all([
      loadDepartments(),
      loadEmployees(),
      loadJobs(),
      loadApplications(), // NOUVEAU: Charger les candidatures
      loadDashboardStats(),
    ])

    console.log("✅ FRONTEND: Initialisation terminée")
  } catch (error) {
    console.error("❌ FRONTEND: Erreur lors de l'initialisation:", error)
  }
}

// NOUVELLE FONCTION: Charger les candidatures depuis l'API
async function loadApplications() {
  console.log("📋 FRONTEND: Chargement des candidatures")

  try {
    const response = await fetch("/api/applications")
    const result = await response.json()

    if (result.success) {
      applications = result.applications || []
      console.log(`✅ FRONTEND: ${applications.length} candidatures chargées`)
      renderApplications()
    } else {
      console.error("❌ FRONTEND: Erreur chargement candidatures:", result.message)
      // En cas d'erreur, afficher un état vide
      applications = []
      renderApplications()
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement candidatures:", error)
    // En cas d'erreur réseau, afficher un état vide
    applications = []
    renderApplications()
  }
}

// FONCTION MISE À JOUR: Rendu des candidatures
function renderApplications(filter = "all") {
  console.log("📋 FRONTEND: Rendu des candidatures, filtre:", filter)

  const container = document.getElementById("applicationsContainer")
  if (!container) {
    console.error("❌ FRONTEND: Container candidatures non trouvé")
    return
  }

  let filteredApps = applications
  if (filter !== "all") {
    filteredApps = applications.filter((app) => app.status === filter)
  }

  if (filteredApps.length === 0) {
    container.innerHTML = `
            <div class="empty-applications">
                <i class="fas fa-file-alt"></i>
                <h4>Aucune candidature</h4>
                <p>Aucune candidature ${getFilterText(filter)}</p>
            </div>
        `
    return
  }

  container.innerHTML = filteredApps
    .map(
      (app) => `
            <div class="application-card ${app.status}">
                <div class="application-header">
                    <div class="applicant-info">
                        <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
                        <div class="applicant-details">
                            <h4>${app.candidate_name}</h4>
                            <p>${app.candidate_email}</p>
                            <small><i class="fas fa-briefcase"></i> ${app.job_title}</small>
                        </div>
                    </div>
                    <div class="application-status ${app.status}">
                        ${getStatusText(app.status)}
                    </div>
                </div>
                
                <div class="application-job">
                    <div class="job-info">
                        <div class="job-title">${app.job_title}</div>
                        <div class="job-department">${app.department_name}</div>
                        <div class="job-priority priority-${app.priority || "normal"}">${(app.priority || "normal").toUpperCase()}</div>
                    </div>
                    <div class="application-date">
                        Candidature envoyée le ${formatDate(app.application_date)}
                        <br><small>Il y a ${app.days_since_application} jour(s)</small>
                    </div>
                </div>
                
                <div class="application-actions">
                    <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
                        <i class="fas fa-user"></i> Voir Profil
                    </button>
                    <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
                        <i class="fas fa-info-circle"></i> Détails sur le job
                    </button>
                </div>
            </div>
        `,
    )
    .join("")
}

// Fonctions utilitaires pour les candidatures
function getInitials(name) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
}

function getFilterText(filter) {
  const filterTexts = {
    all: "",
    pending: "en attente",
    reviewed: "examinées",
    interview_scheduled: "avec entretien programmé",
    accepted: "acceptées",
    rejected: "rejetées",
  }
  return filterTexts[filter] || ""
}

function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    interview_scheduled: "Entretien programmé",
    accepted: "Acceptée",
    rejected: "Rejetée",
  }
  return statusTexts[status] || status
}

function formatDate(dateString) {
  if (!dateString) return "Date inconnue"
  const date = new Date(dateString)
  return date.toLocaleDateString("fr-FR")
}

// Fonctions d'interaction avec les candidatures
function viewCandidateProfile(candidateId) {
  console.log("👤 FRONTEND: Ouverture profil candidat:", candidateId)
  window.open(`/employee-profile?candidate_id=${candidateId}`, "_blank")
}

function viewJobDetails(jobId) {
  console.log("💼 FRONTEND: Détails du poste:", jobId)
  window.location.href = `/job-details?id=${jobId}`
}

function filterApplications(status) {
  console.log("🔍 FRONTEND: Filtrage candidatures:", status)
  renderApplications(status)
}

// Fonction pour charger l'utilisateur actuel
// Fonction pour charger l'utilisateur actuel
async function loadCurrentUser() {
  console.log("👤 FRONTEND: Chargement utilisateur actuel")

  try {
    const response = await fetch("/api/current-user")
    const result = await response.json()
    console.log("API Response:", result)  // Debugging log

    if (result.success) {
      currentUser = result.user
      console.log("✅ FRONTEND: Utilisateur chargé:", currentUser)
      updateUserDisplay()
    } else {
      console.error("❌ FRONTEND: Erreur chargement utilisateur:", result.message)
      if (result.message === "Utilisateur non connecté") {
        window.location.href = "/hr-login"
      }
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement utilisateur:", error)
  }
}

// Fonction pour mettre à jour l'affichage utilisateur
// Fonction pour mettre à jour l'affichage utilisateur
function updateUserDisplay() {
    if (currentUser) {
        const userName = `${currentUser.first_name} ${currentUser.last_name}`;
        const userInitials = `${currentUser.first_name.charAt(0)}${currentUser.last_name.charAt(0)}`;
        
        const roleTranslations = {
            'super_admin': 'Super Admin',
            'recruiter': 'Recruteur',
            'department_head': 'Chef de Département'
        };
        
        const translatedRole = roleTranslations[currentUser.role] || currentUser.role;
        
        // Mettre à jour le rôle au-dessus du titre
        const roleElement = document.getElementById("userRoleDisplay");
        if (roleElement) {
            roleElement.textContent = translatedRole;
        }
        
        // Mettre à jour le message de bienvenue
        const welcomeElement = document.getElementById("welcomeMessage");
        if (welcomeElement) {
            welcomeElement.textContent = `Bienvenue, ${userName}`;
        }
        
        // Mettre à jour l'avatar
        const avatar = document.getElementById("userAvatar");
        if (avatar) {
            avatar.textContent = userInitials;
        }
    }
}

// Fonction pour charger les statistiques du dashboard
async function loadDashboardStats() {
  console.log("📊 FRONTEND: Chargement statistiques dashboard")

  try {
    const response = await fetch("/api/dashboard-stats")
    const result = await response.json()

    if (result.success) {
      const stats = result.stats
      console.log("✅ FRONTEND: Statistiques chargées:", stats)
      updateStatsDisplay(stats)
    } else {
      console.error("❌ FRONTEND: Erreur chargement statistiques:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement statistiques:", error)
  }
}

// Fonction pour mettre à jour l'affichage des statistiques
function updateStatsDisplay(stats) {
  document.getElementById("totalDepartments").textContent = stats.total_departments || 0
  document.getElementById("totalEmployees").textContent = stats.total_employees || 0
  document.getElementById("totalJobs").textContent = stats.total_jobs || 0
  document.getElementById("urgentJobs").textContent = stats.urgent_jobs || 0
  document.getElementById("totalApplications").textContent = stats.total_applications || 0

  // Mettre à jour les pourcentages de changement
  const deptChange = document.querySelector("#totalDepartments").parentElement.querySelector(".stat-change")
  const jobChange = document.querySelector("#totalJobs").parentElement.querySelector(".stat-change")
  const empChange = document.querySelector("#totalEmployees").parentElement.querySelector(".stat-change")

  if (deptChange) deptChange.textContent = stats.dept_change || "+0%"
  if (jobChange) jobChange.textContent = stats.job_change || "+0%"
  if (empChange) empChange.textContent = stats.emp_change || "+0%"

  // Mettre à jour les classes de couleur
  updateStatChangeClass(deptChange, stats.dept_change || "+0%")
  updateStatChangeClass(jobChange, stats.job_change || "+0%")
  updateStatChangeClass(empChange, stats.emp_change || "+0%")

  console.log("✅ FRONTEND: Statistiques affichées")
}

// Fonction pour mettre à jour les classes de couleur des changements
function updateStatChangeClass(element, change) {
  if (!element) return

  element.classList.remove("positive", "negative", "warning")

  if (change.startsWith("+")) {
    element.classList.add("positive")
  } else if (change.startsWith("-")) {
    element.classList.add("negative")
  } else {
    element.classList.add("warning")
  }
}

// Fonctions de navigation
function openCompanyProfile() {
  console.log("🏢 FRONTEND: Ouverture profil entreprise")
  window.location.href = "/company-profile"
}

function logout() {
  console.log("🚪 FRONTEND: Déconnexion")
  window.location.href = "/hr-login"
}

// Gestion des modals
function closeAllModals() {
  document.getElementById("departmentModal").style.display = "none"
  document.getElementById("jobModal").style.display = "none"
  document.getElementById("employeeModal").style.display = "none"
}

// Fonctions modales
function openDepartmentModal() {
  console.log("🏢 FRONTEND: Ouverture modal département")
  closeAllModals()
  document.getElementById("departmentModal").style.display = "flex"
}

function closeDepartmentModal() {
  console.log("🏢 FRONTEND: Fermeture modal département")
  document.getElementById("departmentModal").style.display = "none"
  document.getElementById("departmentForm").reset()
}

function openJobModal(preselectedDeptId = null) {
  console.log("💼 FRONTEND: Ouverture modal poste")
  closeAllModals()
  loadDepartmentsInSelect("jobDepartment")
  loadEmployeesInSelect("jobEmployee")
  document.getElementById("jobModal").style.display = "flex"

  if (preselectedDeptId) {
    setTimeout(() => {
      document.getElementById("jobDepartment").value = preselectedDeptId
    }, 100)
  }
}

function closeJobModal() {
  console.log("💼 FRONTEND: Fermeture modal poste")
  document.getElementById("jobModal").style.display = "none"
  document.getElementById("jobForm").reset()
}

function closeEmployeeModal() {
  console.log("👤 FRONTEND: Fermeture modal employé")
  document.getElementById("employeeModal").style.display = "none"
  document.getElementById("employeeForm").reset()
}

// Fonction pour basculer l'expansion d'un département
function toggleDepartmentExpansion(departmentId) {
  if (expandedDepartments.has(departmentId)) {
    expandedDepartments.delete(departmentId)
  } else {
    expandedDepartments.add(departmentId)
  }

  // Réafficher les départements (filtrés ou non)
  if (isSearchActive) {
    displayFilteredDepartments(filteredDepartments)
  } else {
    displayDepartments()
  }
}

// Fonction pour créer un département
async function createDepartment() {
  console.log("🏢 FRONTEND: Début création département")

  const name = document.getElementById("departmentName").value.trim()
  const description = document.getElementById("departmentDescription").value.trim()
  const manager = document.getElementById("departmentManager").value.trim()
  const color = document.getElementById("departmentColor").value

  if (!name) {
    showNotification("Le nom du département est requis", "warning")
    return
  }

  const departmentData = {
    name: name,
    description: description || "",
    manager_name: manager || "",
    color: color,
    budget: 0.0,
  }

  console.log("📤 FRONTEND: Envoi données département:", departmentData)

  try {
    const response = await fetch("/api/create-department", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(departmentData),
    })

    const result = await response.json()
    console.log("📥 FRONTEND: Réponse reçue:", result)

    if (result.success) {
      console.log("✅ FRONTEND: Département créé avec succès")
      showNotification(`Département "${name}" créé avec succès !`, "success")
      closeDepartmentModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création département:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour créer un employé
async function createEmployee() {
  console.log("👤 FRONTEND: Début création employé")

  const firstName = document.getElementById("employeeFirstName").value.trim()
  const lastName = document.getElementById("employeeLastName").value.trim()
  const email = document.getElementById("employeeEmail").value.trim()
  const departmentId = document.getElementById("employeeDepartment").value
  const position = document.getElementById("employeePosition").value.trim()
  const phone = document.getElementById("employeePhone").value.trim()
  const hireDate = document.getElementById("employeeHireDate").value
  const salary = document.getElementById("employeeSalary").value
  const employmentType = document.getElementById("employeeType").value

  if (!firstName || !lastName || !email || !departmentId || !position) {
    showNotification("Veuillez remplir tous les champs obligatoires", "warning")
    return
  }

  const employeeData = {
    first_name: firstName,
    last_name: lastName,
    email: email,
    department_id: Number.parseInt(departmentId),
    position: position,
    phone: phone || "",
    hire_date: hireDate || null,
    salary: salary ? Number.parseFloat(salary) : null,
    employment_type: employmentType,
    employee_id: "",
  }

  console.log("📤 FRONTEND: Envoi données employé:", employeeData)

  try {
    const response = await fetch("/api/create-employee", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(employeeData),
    })

    const result = await response.json()
    console.log("📥 FRONTEND: Réponse reçue:", result)

    if (result.success) {
      console.log("✅ FRONTEND: Employé créé avec succès")
      showNotification(`Employé "${firstName} ${lastName}" créé avec succès !`, "success")
      closeEmployeeModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création employé:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour créer un poste
async function createJob() {
  console.log("💼 FRONTEND: Début création poste")

  const title = document.getElementById("jobTitle").value.trim()
  const departmentId = document.getElementById("jobDepartment").value
  const priority = document.getElementById("jobPriority").value
  const deadline = document.getElementById("jobDeadline").value
  const employmentType = document.getElementById("jobType").value
  const salaryMin = document.getElementById("jobSalaryMin").value
  const salaryMax = document.getElementById("jobSalaryMax").value
  const description = document.getElementById("jobDescription").value.trim()
  const requirements = document.getElementById("jobRequirements").value.trim()
  const responsibilities = document.getElementById("jobResponsibilities").value.trim()
  const assignedEmployeeId = document.getElementById("jobEmployee").value

  if (!title || !departmentId || !employmentType || !description) {
    showNotification("Veuillez remplir tous les champs obligatoires", "warning")
    return
  }

  const jobData = {
    title: title,
    department_id: Number.parseInt(departmentId),
    description: description,
    employment_type: employmentType,
    priority: priority,
    deadline: deadline || null,
    salary_min: salaryMin ? Number.parseFloat(salaryMin) : null,
    salary_max: salaryMax ? Number.parseFloat(salaryMax) : null,
    requirements: requirements || "",
    responsibilities: responsibilities || "",
    assigned_employee_id: assignedEmployeeId ? Number.parseInt(assignedEmployeeId) : null,
  }

  console.log("📤 FRONTEND: Envoi données poste:", jobData)

  try {
    const response = await fetch("/api/create-job", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(jobData),
    })

    const result = await response.json()
    console.log("📥 FRONTEND: Réponse reçue:", result)

    if (result.success) {
      console.log("✅ FRONTEND: Poste créé avec succès")
      showNotification(`Poste "${title}" créé avec succès !`, "success")
      closeJobModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création poste:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour rafraîchir tout le dashboard
async function refreshDashboard() {
  console.log("🔄 FRONTEND: Rafraîchissement complet du dashboard")
  await loadDepartments()
  await loadEmployees()
  await loadJobs()
  await loadApplications() // NOUVEAU: Recharger les candidatures
  await loadDashboardStats()
}

// Fonction pour charger les départements
async function loadDepartments() {
  console.log("🔄 FRONTEND: Chargement des départements")

  try {
    const response = await fetch("/api/departments")
    const result = await response.json()

    if (result.success) {
      departments = result.departments || []
      console.log(`✅ FRONTEND: ${departments.length} départements chargés`)

      // Si une recherche est active, refiltrer les résultats
      if (isSearchActive) {
        const searchTerm = document.getElementById("searchInput").value.toLowerCase().trim()
        if (searchTerm) {
          filterDepartments()
        } else {
          displayDepartments()
        }
      } else {
        displayDepartments()
      }
    } else {
      console.error("❌ FRONTEND: Erreur chargement départements:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement départements:", error)
  }
}

// Fonction pour charger les postes
async function loadJobs() {
  console.log("🔄 FRONTEND: Chargement des postes")

  try {
    const response = await fetch("/api/jobs")
    const result = await response.json()

    if (result.success) {
      jobs = result.jobs || []
      console.log(`✅ FRONTEND: ${jobs.length} postes chargés`)
    } else {
      console.error("❌ FRONTEND: Erreur chargement postes:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement postes:", error)
  }
}

// Fonction pour afficher les départements
function displayDepartments() {
  const departmentsList = document.getElementById("departmentsList")

  if (!departmentsList) {
    console.error("❌ FRONTEND: Element departmentsList non trouvé")
    return
  }

  if (departments.length === 0) {
    departmentsList.innerHTML = `
            <div class="empty-departments">
                <div class="empty-icon"><i class="fas fa-building"></i></div>
                <h4>Aucun département</h4>
                <p>Commencez par créer votre premier département</p>
                <button class="empty-btn" onclick="openDepartmentModal()">
                    <i class="fas fa-plus"></i> Créer Département
                </button>
            </div>
        `
    return
  }

  renderDepartmentsList(departments)
}

// Fonction pour afficher les départements filtrés
function displayFilteredDepartments(filteredDepts) {
  const departmentsList = document.getElementById("departmentsList")

  if (!departmentsList) {
    console.error("❌ FRONTEND: Element departmentsList non trouvé")
    return
  }

  if (filteredDepts.length === 0) {
    departmentsList.innerHTML = `
            <div class="empty-departments">
                <div class="empty-icon"><i class="fas fa-search"></i></div>
                <h4>Aucun résultat trouvé</h4>
                <p>Aucun département ne correspond à votre recherche</p>
                <button class="empty-btn" onclick="clearSearch()">
                    <i class="fas fa-times"></i> Effacer la recherche
                </button>
            </div>
        `
    return
  }

  renderDepartmentsList(filteredDepts)
}

// Fonction pour générer le HTML des départements
function renderDepartmentsList(deptList) {
  const departmentsList = document.getElementById("departmentsList")
  let html = ""

  deptList.forEach((dept) => {
    const isExpanded = expandedDepartments.has(dept.id)
    const departmentEmployees = employees.filter((emp) => emp.department_id === dept.id)
    const departmentJobs = jobs.filter((job) => job.department_id === dept.id)

    html += `
            <div class="department-card-enhanced" style="border-left: 4px solid ${dept.color || "#e74c3c"}">
                <div class="department-header">
                    <div class="department-info">
                        <h4>${dept.name || "Département sans nom"}</h4>
                        <p>${dept.description || "Aucune description"}</p>
                        ${dept.manager_name ? `<span class="manager">👤 ${dept.manager_name}</span>` : ""}
                    </div>
                    <div class="department-stats">
                        <span class="stat-badge employees">
                            <i class="fas fa-users"></i> ${dept.employee_count || 0}
                        </span>
                        <span class="stat-badge jobs">
                            <i class="fas fa-briefcase"></i> ${dept.job_count || 0}
                        </span>
                    </div>
                </div>
                
                <div class="department-actions">
                    <button class="btn-expand ${isExpanded ? "expanded" : ""}" 
                            onclick="toggleDepartmentExpansion(${dept.id})" 
                            title="${isExpanded ? "Réduire" : "Voir les détails"}">
                        <i class="fas fa-chevron-${isExpanded ? "up" : "down"}"></i>
                        ${isExpanded ? "Réduire" : "Voir Détails"}
                    </button>

                    <button class="btn-add-job" onclick="openJobModal(${dept.id})" title="Ajouter un poste">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                
                ${
                  isExpanded
                    ? `
                    <div class="department-details">
                        <div class="details-tabs">
                            <div class="tab-section">
                                <h5><i class="fas fa-users"></i> Employés (${departmentEmployees.length})</h5>
                                <div class="items-list">
                                    ${
                                      departmentEmployees.length === 0
                                        ? '<p class="empty-message">Aucun employé dans ce département</p>'
                                        : departmentEmployees
                                            .map(
                                              (emp) => `
                                            <div class="item-card employee-card">
                                                <div class="item-avatar">
                                                    ${emp.first_name.charAt(0)}${emp.last_name.charAt(0)}
                                                </div>
                                                <div class="item-info">
                                                    <strong>${emp.first_name} ${emp.last_name}</strong>
                                                    <span>${emp.position}</span>
                                                    <small>${emp.email}</small>
                                                </div>
                                                <div class="item-actions">
                                                    <button class="btn-icon-small" onclick="viewEmployeeProfile(${emp.id})" title="Voir le profil">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        `,
                                            )
                                            .join("")
                                    }
                                </div>
                            </div>
                            
                            <div class="tab-section">
                                <h5><i class="fas fa-briefcase"></i> Postes (${departmentJobs.length})</h5>
                                <div class="items-list">
                                    ${
                                      departmentJobs.length === 0
                                        ? '<p class="empty-message">Aucun poste dans ce département</p>'
                                        : departmentJobs
                                            .map(
                                              (job) => `
                                            <div class="item-card job-card">
                                                <div class="item-info">
                                                    <strong>${job.title}</strong>
                                                    <span>${job.employment_type}</span>
                                                    <small class="priority-${job.priority}">${job.priority.toUpperCase()}</small>
                                                    ${job.status === "filled" ? '<small class="status-filled">✅ POURVU</small>' : ""}
                                                </div>
                                                <div class="item-actions">
                                                    <button class="btn-icon-small" onclick="viewJobDetails(${job.id})" title="Voir les détails">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        `,
                                            )
                                            .join("")
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `
                    : ""
                }
            </div>
        `
  })

  departmentsList.innerHTML = html
}

// Fonction pour charger les départements dans un select
function loadDepartmentsInSelect(selectId) {
  const select = document.getElementById(selectId)
  if (!select) return

  select.innerHTML = '<option value="">Sélectionner un département</option>'

  departments.forEach((dept) => {
    const option = document.createElement("option")
    option.value = dept.id
    option.textContent = dept.name
    select.appendChild(option)
  })
}

// Fonction pour charger les employés dans un select
function loadEmployeesInSelect(selectId) {
  const select = document.getElementById(selectId)
  if (!select) return

  select.innerHTML = '<option value="">Aucun employé assigné</option>'

  employees.forEach((emp) => {
    const option = document.createElement("option")
    option.value = emp.id
    option.textContent = `${emp.first_name} ${emp.last_name} (${emp.position})`
    select.appendChild(option)
  })
}

function viewEmployeeProfile(employeeId) {
  const employee = employees.find(e => e.id === employeeId)

  if (!employee) {
    showNotification("Employé introuvable", "error")
    return
  }

  // S'il a une propriété candidate_id, alors il vient d'un candidat
  if (employee.candidate_id) {
    console.log("➡️ Ouvrir comme candidat")
    window.open(`/employee-profile?candidate_id=${employee.candidate_id}`, "_blank")
  } else {
    console.log("➡️ Ouvrir comme employé normal")
    window.open(`/employee-profile?id=${employeeId}`, "_blank")
  }
}

// Fonction pour voir les détails d'un poste
function viewJobDetails(jobId) {
  console.log("💼 FRONTEND: Navigation vers job-details pour le poste:", jobId)
  window.location.href = `/job-details?id=${jobId}`
}

// Fonctions placeholder
function exportData() {
  console.log("📊 FRONTEND: Export données")
  showNotification("Fonctionnalité en cours de développement", "info")
}

function generateReport() {
  console.log("📈 FRONTEND: Génération rapport")
  window.location.href = "/hr-reports"
}

// ==================== FONCTION DE RECHERCHE CORRIGÉE ====================
function filterDepartments() {
  console.log("🔍 FRONTEND: Filtrage départements")

  const searchInput = document.getElementById("searchInput")
  if (!searchInput) {
    console.error("❌ FRONTEND: Input de recherche non trouvé")
    return
  }

  const searchTerm = searchInput.value.toLowerCase().trim()
  console.log(`🔍 FRONTEND: Terme de recherche: "${searchTerm}"`)

  // Si le terme de recherche est vide, afficher tous les départements
  if (!searchTerm) {
    console.log("🔍 FRONTEND: Recherche vide, affichage de tous les départements")
    isSearchActive = false
    filteredDepartments = []
    displayDepartments()
    return
  }

  // Marquer qu'une recherche est active
  isSearchActive = true

  // Filtrer les départements selon le terme de recherche
  filteredDepartments = departments.filter((dept) => {
    const name = (dept.name || "").toLowerCase()
    const description = (dept.description || "").toLowerCase()
    const manager = (dept.manager_name || "").toLowerCase()

    const matches = name.includes(searchTerm) || description.includes(searchTerm) || manager.includes(searchTerm)

    if (matches) {
      console.log(`✅ FRONTEND: Département "${dept.name}" correspond à la recherche`)
    }

    return matches
  })

  console.log(`🔍 FRONTEND: ${filteredDepartments.length} départements trouvés pour "${searchTerm}"`)

  // Afficher les départements filtrés
  displayFilteredDepartments(filteredDepartments)
}

// Fonction pour effacer la recherche
function clearSearch() {
  console.log("🔍 FRONTEND: Effacement de la recherche")

  const searchInput = document.getElementById("searchInput")
  if (searchInput) {
    searchInput.value = ""
  }

  isSearchActive = false
  filteredDepartments = []
  displayDepartments()
}

// Fermer les modales en cliquant à l'extérieur
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.style.display = "none"
  }
})

// Mise à jour de la couleur preview
document.addEventListener("DOMContentLoaded", () => {
  const colorInput = document.getElementById("departmentColor")
  const colorPreview = document.querySelector(".color-preview")

  if (colorInput && colorPreview) {
    colorInput.addEventListener("change", function () {
      colorPreview.style.backgroundColor = this.value
    })

    // Initialiser la couleur preview
    colorPreview.style.backgroundColor = colorInput.value
  }
})

// Fonction de notification améliorée
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`

  const icons = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
  }

  const colors = {
    success: "linear-gradient(135deg, #27ae60, #2ecc71)",
    error: "linear-gradient(135deg, #e74c3c, #c0392b)",
    warning: "linear-gradient(135deg, #f39c12, #e67e22)",
    info: "linear-gradient(135deg, #3498db, #2980b9)",
  }

  notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="notification-content">
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `

  notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: ${colors[type]};
        color: white;
        padding: 1rem;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 20000;
        backdrop-filter: blur(10px);
        animation: slideInRight 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        min-width: 320px;
        max-width: 450px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    `

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease-in"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 5000)
}

function filterApplicationByName() {
  const input = document.getElementById("applicationSearchInput")
  const searchTerm = input.value.toLowerCase().trim()

  const filtered = applications.filter((app) => {
    return (
      app.candidate_name.toLowerCase().includes(searchTerm) ||
      app.candidate_email.toLowerCase().includes(searchTerm)
    )
  })

  renderApplicationsList(filtered)
}

function renderApplicationsList(list) {
  const container = document.getElementById("applicationsContainer")

  if (!container) return

  if (list.length === 0) {
    container.innerHTML = `
      <div class="empty-applications">
        <i class="fas fa-search"></i>
        <h4>Aucun résultat</h4>
        <p>Aucune candidature ne correspond à votre recherche</p>
      </div>
    `
    return
  }

  container.innerHTML = list
    .map((app) => `
      <div class="application-card ${app.status}">
        <div class="application-header">
          <div class="applicant-info">
            <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
            <div class="applicant-details">
              <h4>${app.candidate_name}</h4>
              <p>${app.candidate_email}</p>
              <small><i class="fas fa-briefcase"></i> ${app.job_title}</small>
            </div>
          </div>
          <div class="application-status ${app.status}">
            ${getStatusText(app.status)}
          </div>
        </div>
        
        <div class="application-job">
          <div class="job-info">
            <div class="job-title">${app.job_title}</div>
            <div class="job-department">${app.department_name}</div>
            <div class="job-priority priority-${app.priority || "normal"}">${(app.priority || "normal").toUpperCase()}</div>
          </div>
          <div class="application-date">
            Candidature envoyée le ${formatDate(app.application_date)}
            <br><small>Il y a ${app.days_since_application} jour(s)</small>
          </div>
        </div>
        
        <div class="application-actions">
          <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
            <i class="fas fa-user"></i> Voir Profil
          </button>
          <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
            <i class="fas fa-info-circle"></i> Détails
          </button>
        </div>
      </div>
    `)
    .join("")
}

// Charger les employés depuis l’API
async function loadEmployees() {
  console.log("👥 FRONTEND: Chargement des employés")

  try {
    const response = await fetch("/api/employees")
    const result = await response.json()

    if (result.success) {
      employees = result.employees
      console.log(`✅ FRONTEND: ${employees.length} employés chargés`)
      renderEmployees()
    } else {
      console.error("❌ FRONTEND: Erreur chargement employés:", result.message)
      employees = []
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement employés:", error)
    employees = []
  }
}

// Affichage simple des employés
function renderEmployees() {
  const container = document.getElementById("employeesContainer")
  if (!container) {
    console.warn("📦 FRONTEND: Container employés introuvable")
    return
  }

  if (employees.length === 0) {
    container.innerHTML = "<p>Aucun employé trouvé.</p>"
    return
  }

  container.innerHTML = employees.map(emp => `
    <div class="employee-card">
      <h4>${emp.first_name} ${emp.last_name}</h4>
      <p><strong>Poste:</strong> ${emp.position}</p>
      <p><strong>Email:</strong> ${emp.email}</p>
      <p><strong>Département:</strong> ${emp.department_name}</p>
      <p><strong>Compétences:</strong> ${(emp.skills || []).map(s => s.name).join(", ") || "Non spécifiées"}</p>
    </div>
  `).join("")
}