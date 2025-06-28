// Variables globales
let departments = []
let jobs = []
let employees = []
let activityLog = []
let applications = [] // Nouvelle variable pour les candidatures

// Nouvelles variables
let expandedDept = null
const activeTab = {}
let filteredDepartments = []

// Vérifier si la configuration est terminée
document.addEventListener("DOMContentLoaded", () => {
  const setupCompleted = localStorage.getItem("setupCompleted")
  if (!setupCompleted) {
    window.location.href = "/company-setup"
    return
  }

  console.log("DOM loaded, initializing...")
  updateStats()
  updateDepartmentSelects()
  updateEmployeeSelects()
  renderDepartments()
  renderActivity()
  addSampleApplications()
  renderApplications()

  // Vérifier que les boutons existent
  const quickActionBtn = document.querySelector('.quick-action-card[onclick*="openDepartmentModal"]')
  const addBtn = document.querySelector('.add-btn[onclick*="openDepartmentModal"]')

  console.log("Quick action button found:", !!quickActionBtn)
  console.log("Add button found:", !!addBtn)

  // Charger les données du profil d'entreprise
  loadCompanyProfile()
})

// Charger le profil d'entreprise
function loadCompanyProfile() {
  const companyProfile = localStorage.getItem("companyProfile")
  if (companyProfile) {
    const profile = JSON.parse(companyProfile)
    // Mettre à jour l'interface avec les données de l'entreprise
    const logoSection = document.querySelector(".logo span")
    if (logoSection) {
      logoSection.textContent = `${profile.companyName} - Tableau de Bord RH`
    }
  }
}

// Fonctions de gestion des départements
function openDepartmentModal() {
  console.log("Opening department modal...")
  const modal = document.getElementById("departmentModal")
  if (modal) {
    modal.classList.add("show")
    document.body.style.overflow = "hidden"
    console.log("Modal opened successfully")
  } else {
    console.error("Modal element not found!")
  }
}

function closeDepartmentModal() {
  console.log("Closing department modal...")
  const modal = document.getElementById("departmentModal")
  if (modal) {
    modal.classList.remove("show")
    document.body.style.overflow = "auto"
    document.getElementById("departmentForm").reset()
    console.log("Modal closed successfully")
  }
}

function createDepartment() {
  const name = document.getElementById("departmentName").value.trim()
  const description = document.getElementById("departmentDescription").value.trim()
  const manager = document.getElementById("departmentManager").value.trim()
  const color = document.getElementById("departmentColor").value

  if (!name) {
    showNotification("Le nom du département est requis", "error")
    return
  }

  const department = {
    id: Date.now(),
    name: name,
    description: description,
    manager: manager,
    color: color,
    jobs: [],
    employees: [],
    createdAt: new Date(),
  }

  departments.push(department)

  // Ajouter à l'activité
  addActivity(`Nouveau département "${name}" créé`, "department")

  updateStats()
  updateDepartmentSelects()
  renderDepartments()
  closeDepartmentModal()
  showNotification(`Département "${name}" créé avec succès !`, "success")
}

function deleteDepartment(id) {
  if (confirm("Êtes-vous sûr de vouloir supprimer ce département ?")) {
    const dept = departments.find((d) => d.id === id)
    departments = departments.filter((d) => d.id !== id)

    // Supprimer les jobs associés
    jobs = jobs.filter((j) => j.departmentId !== id)

    // Mettre à jour les employés
    employees = employees.filter((e) => e.departmentId !== id)

    addActivity(`Département "${dept.name}" supprimé`, "delete")

    updateStats()
    updateDepartmentSelects()
    updateEmployeeSelects()
    renderDepartments()
    showNotification(`Département "${dept.name}" supprimé`, "warning")
  }
}

// Fonctions de gestion des jobs
function openJobModal() {
  if (departments.length === 0) {
    showNotification("Veuillez d'abord créer un département", "warning")
    return
  }
  document.getElementById("jobModal").classList.add("show")
  document.body.style.overflow = "hidden"
}

function closeJobModal() {
  document.getElementById("jobModal").classList.remove("show")
  document.body.style.overflow = "auto"
  document.getElementById("jobForm").reset()
}

function createJob() {
  const title = document.getElementById("jobTitle").value.trim()
  const departmentId = Number.parseInt(document.getElementById("jobDepartment").value)
  const type = document.getElementById("jobType").value
  const salary = document.getElementById("jobSalary").value.trim()
  const description = document.getElementById("jobDescription").value.trim()
  const employeeId = document.getElementById("jobEmployee").value
  const priority = document.getElementById("jobPriority").value
  const deadline = document.getElementById("jobDeadline").value

  if (!title || !departmentId || !type || !description) {
    showNotification("Veuillez remplir tous les champs requis", "error")
    return
  }

  const job = {
    id: Date.now(),
    title: title,
    departmentId: departmentId,
    type: type,
    salary: salary,
    description: description,
    employeeId: employeeId || null,
    priority: priority,
    deadline: deadline,
    createdAt: new Date(),
  }

  jobs.push(job)

  const department = departments.find((d) => d.id === departmentId)
  if (department) {
    department.jobs.push(job.id)
  }

  addActivity(`Nouveau poste "${title}" créé dans ${department.name}`, "job")

  updateStats()
  renderDepartments()
  closeJobModal()
  showNotification(`Poste "${title}" créé avec succès !`, "success")
}

function deleteJob(id) {
  if (confirm("Êtes-vous sûr de vouloir supprimer ce poste ?")) {
    const job = jobs.find((j) => j.id === id)
    const department = departments.find((d) => d.id === job.departmentId)

    jobs = jobs.filter((j) => j.id !== id)

    // Retirer du département
    if (department) {
      department.jobs = department.jobs.filter((jId) => jId !== id)
    }

    addActivity(`Poste "${job.title}" supprimé`, "delete")

    updateStats()
    renderDepartments()
    showNotification(`Poste "${job.title}" supprimé`, "warning")
  }
}

function assignEmployee(jobId, employeeId) {
  const job = jobs.find((j) => j.id === jobId)
  const employee = employees.find((e) => e.id === Number.parseInt(employeeId))

  if (job && employee) {
    job.employeeId = Number.parseInt(employeeId)
    addActivity(`${employee.firstName} ${employee.lastName} assigné(e) au poste "${job.title}"`, "assign")
    renderDepartments()
    showNotification(`${employee.firstName} ${employee.lastName} assigné(e) au poste "${job.title}"`, "success")
  }
}

function unassignEmployee(jobId) {
  const job = jobs.find((j) => j.id === jobId)
  if (job) {
    const employee = employees.find((e) => e.id === job.employeeId)
    job.employeeId = null
    if (employee) {
      addActivity(`${employee.firstName} ${employee.lastName} retiré(e) du poste "${job.title}"`, "unassign")
      showNotification(`${employee.firstName} ${employee.lastName} retiré(e) du poste`, "info")
    }
    renderDepartments()
  }
}

// Fonctions de gestion des employés
function openEmployeeModal() {
  if (departments.length === 0) {
    showNotification("Veuillez d'abord créer un département", "warning")
    return
  }
  document.getElementById("employeeModal").classList.add("show")
  document.body.style.overflow = "hidden"
}

function closeEmployeeModal() {
  document.getElementById("employeeModal").classList.remove("show")
  document.body.style.overflow = "auto"
  document.getElementById("employeeForm").reset()
}

function createEmployee() {
  const firstName = document.getElementById("employeeFirstName").value.trim()
  const lastName = document.getElementById("employeeLastName").value.trim()
  const email = document.getElementById("employeeEmail").value.trim()
  const departmentId = Number.parseInt(document.getElementById("employeeDepartment").value)
  const position = document.getElementById("employeePosition").value.trim()

  if (!firstName || !lastName || !email || !departmentId || !position) {
    showNotification("Veuillez remplir tous les champs", "error")
    return
  }

  const employee = {
    id: Date.now(),
    firstName: firstName,
    lastName: lastName,
    email: email,
    departmentId: departmentId,
    position: position,
    createdAt: new Date(),
  }

  employees.push(employee)

  // Ajouter l'employé au département
  const department = departments.find((d) => d.id === departmentId)
  if (department) {
    department.employees.push(employee.id)
  }

  addActivity(`Nouvel employé ${firstName} ${lastName} ajouté`, "employee")

  updateStats()
  updateEmployeeSelects()
  renderDepartments()
  closeEmployeeModal()
  showNotification(`Employé ${firstName} ${lastName} ajouté avec succès !`, "success")
}

// Fonctions d'ajout rapide depuis les départements
function quickAddEmployee(deptId) {
  setEmployeeDepartment(deptId)
  openEmployeeModal()
}

function quickAddJob(deptId) {
  setJobDepartment(deptId)
  openJobModal()
}

// Fonction pour ouvrir le profil d'entreprise
function openCompanyProfile() {
  window.open("/company-profile", "_blank")
}

// Fonctions de gestion des candidatures
function addSampleApplications() {
  // Ajouter quelques candidatures d'exemple
  const sampleApplications = [
    {
      id: 1,
      applicantName: "Marie Dubois",
      applicantEmail: "marie.dubois@email.com",
      jobId: null,
      jobTitle: "Développeur Frontend",
      department: "IT",
      status: "pending",
      appliedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      cv: "marie_dubois_cv.pdf",
    },
    {
      id: 2,
      applicantName: "Pierre Martin",
      applicantEmail: "pierre.martin@email.com",
      jobId: null,
      jobTitle: "Chef de Projet",
      department: "Management",
      status: "pending",
      appliedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      cv: "pierre_martin_cv.pdf",
    },
  ]

  applications.push(...sampleApplications)
  updateStats()
}

function acceptApplication(applicationId) {
  const application = applications.find((app) => app.id === applicationId)
  if (application) {
    application.status = "accepted"
    addActivity(`Candidature de ${application.applicantName} acceptée`, "accept")
    updateStats()
    renderApplications()
    showNotification(`Candidature de ${application.applicantName} acceptée`, "success")
  }
}

function rejectApplication(applicationId) {
  const application = applications.find((app) => app.id === applicationId)
  if (application) {
    application.status = "rejected"
    addActivity(`Candidature de ${application.applicantName} rejetée`, "reject")
    updateStats()
    renderApplications()
    showNotification(`Candidature de ${application.applicantName} rejetée`, "warning")
  }
}

function viewApplicationCV(applicationId) {
  const application = applications.find((app) => app.id === applicationId)
  if (application) {
    showNotification(`Ouverture du CV de ${application.applicantName}`, "info")
    // Ici vous pourriez ouvrir un modal avec le CV ou télécharger le fichier
  }
}

function filterApplications(status) {
  renderApplications(status)
}

function clearApplications() {
  if (confirm("Effacer toutes les candidatures ?")) {
    applications = []
    updateStats()
    renderApplications()
    showNotification("Toutes les candidatures ont été effacées", "info")
  }
}

function renderApplications(filter = "all") {
  const container = document.getElementById("applicationsContainer")

  let filteredApps = applications
  if (filter !== "all") {
    filteredApps = applications.filter((app) => app.status === filter)
  }

  if (filteredApps.length === 0) {
    container.innerHTML = `
      <div class="empty-applications">
        <i class="fas fa-file-alt"></i>
        <p>Aucune candidature ${filter === "all" ? "" : filter === "pending" ? "en attente" : "examinée"}</p>
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
          <div class="applicant-avatar">${app.applicantName
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="applicant-details">
            <h4>${app.applicantName}</h4>
            <p>${app.applicantEmail}</p>
          </div>
        </div>
        <div class="application-status ${app.status}">
          ${app.status === "pending" ? "En attente" : app.status === "accepted" ? "Acceptée" : "Rejetée"}
        </div>
      </div>
      
      <div class="application-job">
        <div class="job-info">
          <div class="job-title">${app.jobTitle}</div>
          <div class="job-department">${app.department}</div>
        </div>
        <div class="application-date">
          Candidature envoyée le ${app.appliedAt.toLocaleDateString("fr-FR")}
        </div>
      </div>
      
      <div class="application-actions">
        <button class="app-btn view" onclick="viewApplicationCV(${app.id})">
          <i class="fas fa-file-pdf"></i> Voir CV
        </button>
        ${
          app.status === "pending"
            ? `
          <button class="app-btn accept" onclick="acceptApplication(${app.id})">
            <i class="fas fa-check"></i> Accepter
          </button>
          <button class="app-btn reject" onclick="rejectApplication(${app.id})">
            <i class="fas fa-times"></i> Rejeter
          </button>
        `
            : ""
        }
      </div>
    </div>
  `,
    )
    .join("")
}

// Système de notifications moderne
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
    success: "rgba(39, 174, 96, 0.9)",
    error: "rgba(231, 76, 60, 0.9)",
    warning: "rgba(243, 156, 18, 0.9)",
    info: "rgba(52, 152, 219, 0.9)",
  }

  notification.innerHTML = `
    <i class="fas ${icons[type]}"></i>
    <span>${message}</span>
    <button class="notification-close" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `

  // Styles pour la notification
  notification.style.cssText = `
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: ${colors[type]};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    z-index: 10000;
    backdrop-filter: blur(10px);
    animation: slideInRight 0.3s ease;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    min-width: 300px;
    max-width: 400px;
  `

  document.body.appendChild(notification)

  // Supprimer la notification après 4 secondes
  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 4000)
}

// Ajouter les animations CSS pour les notifications
const notificationStyle = document.createElement("style")
notificationStyle.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
  
  .notification-close {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    transition: all 0.3s ease;
    margin-left: auto;
  }
  
  .notification-close:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`
document.head.appendChild(notificationStyle)

// Reste des fonctions existantes...
function filterDepartments() {
  const searchTerm = document.getElementById("searchInput").value.toLowerCase()
  filteredDepartments = departments.filter(
    (dept) =>
      dept.name.toLowerCase().includes(searchTerm) ||
      dept.description.toLowerCase().includes(searchTerm) ||
      (dept.manager && dept.manager.toLowerCase().includes(searchTerm)),
  )
  renderDepartments()
}

function toggleDepartment(deptId) {
  expandedDept = expandedDept === deptId ? null : deptId
  if (!activeTab[deptId]) {
    activeTab[deptId] = "workers"
  }
  renderDepartments()
}

function switchTab(deptId, tab) {
  activeTab[deptId] = tab
  renderDepartments()
}

function exportData() {
  const data = {
    departments: departments,
    jobs: jobs,
    employees: employees,
    applications: applications,
    exportDate: new Date().toISOString(),
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `hr-data-${new Date().toISOString().split("T")[0]}.json`
  a.click()
  URL.revokeObjectURL(url)

  addActivity("Données exportées", "export")
  showNotification("Données exportées avec succès !", "success")
}

function generateReport() {
  const report = {
    totalDepartments: departments.length,
    totalJobs: jobs.length,
    totalEmployees: employees.length,
    urgentJobs: jobs.filter((j) => j.priority === "urgent").length,
    pendingApplications: applications.filter((app) => app.status === "pending").length,
    departmentBreakdown: departments.map((dept) => ({
      name: dept.name,
      employees: employees.filter((e) => e.departmentId === dept.id).length,
      jobs: jobs.filter((j) => j.departmentId === dept.id).length,
    })),
  }

  console.log("Rapport RH:", report)
  showNotification("Rapport généré ! Consultez la console pour les détails.", "success")
  addActivity("Rapport RH généré", "report")
}

function clearActivity() {
  if (confirm("Effacer tout l'historique d'activité ?")) {
    activityLog = []
    renderActivity()
    showNotification("Historique d'activité effacé", "info")
  }
}

function updateStats() {
  document.getElementById("totalDepartments").textContent = departments.length
  document.getElementById("totalJobs").textContent = jobs.length
  document.getElementById("totalEmployees").textContent = employees.length
  document.getElementById("urgentJobs").textContent = jobs.filter((j) => j.priority === "urgent").length
  document.getElementById("totalApplications").textContent = applications.filter(
    (app) => app.status === "pending",
  ).length
}

function updateDepartmentSelects() {
  const selects = ["jobDepartment", "employeeDepartment"]

  selects.forEach((selectId) => {
    const select = document.getElementById(selectId)
    // Garder la première option
    const firstOption = select.querySelector('option[value=""]')
    select.innerHTML = ""
    if (firstOption) {
      select.appendChild(firstOption)
    }

    departments.forEach((dept) => {
      const option = document.createElement("option")
      option.value = dept.id
      option.textContent = dept.name
      select.appendChild(option)
    })
  })
}

function updateEmployeeSelects() {
  const selects = document.querySelectorAll(".employee-select")

  selects.forEach((select) => {
    const currentValue = select.value
    const firstOption = select.querySelector('option[value=""]')
    select.innerHTML = ""
    if (firstOption) {
      select.appendChild(firstOption.cloneNode(true))
    }

    employees.forEach((emp) => {
      const option = document.createElement("option")
      option.value = emp.id
      option.textContent = `${emp.firstName} ${emp.lastName}`
      select.appendChild(option)
    })

    select.value = currentValue
  })
}

function renderDepartments() {
  const container = document.getElementById("departmentsList")
  const depsToShow =
    filteredDepartments.length > 0 || document.getElementById("searchInput").value ? filteredDepartments : departments

  if (depsToShow.length === 0) {
    container.innerHTML = `
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

  container.innerHTML = depsToShow
    .map((dept) => {
      const deptJobs = jobs.filter((j) => j.departmentId === dept.id)
      const deptEmployees = employees.filter((e) => e.departmentId === dept.id)
      const isExpanded = expandedDept === dept.id

      return `
      <div class="department-dropdown ${isExpanded ? "expanded" : ""}">
        <div class="department-header" onclick="toggleDepartment(${dept.id})">
          <div class="department-info">
            <div class="dept-color" style="background-color: ${dept.color}"></div>
            <div class="dept-details">
              <h4>${dept.name}</h4>
              <div class="dept-stats">${deptEmployees.length} employés • ${deptJobs.length} postes</div>
            </div>
          </div>
          <div class="department-actions">
            <button class="dept-action-btn delete" onclick="event.stopPropagation(); deleteDepartment(${dept.id})" title="Supprimer">
              <i class="fas fa-trash"></i>
            </button>
            <div class="dropdown-arrow">
              <i class="fas fa-chevron-down"></i>
            </div>
          </div>
        </div>

        <div class="department-content ${isExpanded ? "expanded" : ""}">
          <div class="department-tabs">
            <button class="tab-btn ${activeTab[dept.id] === "workers" ? "active" : ""}" 
                    onclick="switchTab(${dept.id}, 'workers')">
              <i class="fas fa-users"></i> Employés (${deptEmployees.length})
            </button>
            <button class="tab-btn ${activeTab[dept.id] === "jobs" ? "active" : ""}" 
                    onclick="switchTab(${dept.id}, 'jobs')">
              <i class="fas fa-briefcase"></i> Postes (${deptJobs.length})
            </button>
          </div>

          <div class="tab-content">
            ${activeTab[dept.id] === "workers" ? renderWorkersTab(dept, deptEmployees) : renderJobsTab(dept, deptJobs)}
          </div>
        </div>
        <div class="dept-quick-actions">
          <button class="quick-add-btn" onclick="quickAddEmployee(${dept.id})">
            <i class="fas fa-user-plus"></i> Ajouter Employé
          </button>
          <button class="quick-add-btn" onclick="quickAddJob(${dept.id})">
            <i class="fas fa-briefcase"></i> Ajouter Poste
          </button>
        </div>
      </div>
    `
    })
    .join("")

  updateEmployeeSelects()
}

function renderWorkersTab(dept, deptEmployees) {
  if (deptEmployees.length === 0) {
    return `
      <div class="empty-tab">
        <p>Aucun employé dans ce département</p>
        <button onclick="setEmployeeDepartment(${dept.id}); openEmployeeModal()">
          <i class="fas fa-user-plus"></i> Ajouter
        </button>
      </div>
    `
  }

  return `
    <div class="workers-list">
      ${deptEmployees
        .map(
          (employee) => `
        <div class="worker-item">
          <div class="worker-avatar">${employee.firstName[0]}${employee.lastName[0]}</div>
          <div class="worker-info">
            <div class="worker-name">${employee.firstName} ${employee.lastName}</div>
            <div class="worker-role">${employee.position}</div>
          </div>
          <div class="worker-status"></div>
          <div class="worker-actions">
            <button class="worker-btn" onclick="deleteEmployee(${employee.id}, ${dept.id})" title="Supprimer">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      `,
        )
        .join("")}
    </div>
  `
}

function renderJobsTab(dept, deptJobs) {
  if (deptJobs.length === 0) {
    return `
      <div class="empty-tab">
        <p>Aucun poste dans ce département</p>
        <button onclick="setJobDepartment(${dept.id}); openJobModal()">
          <i class="fas fa-briefcase"></i> Créer
        </button>
      </div>
    `
  }

  return `
    <div class="jobs-list">
      ${deptJobs
        .map((job) => {
          const assignedEmployee = job.employeeId ? employees.find((e) => e.id === job.employeeId) : null
          const deptEmployees = employees.filter((e) => e.departmentId === dept.id)

          return `
          <div class="job-item">
            <div class="job-header">
              <div class="job-title">${job.title}</div>
              <div class="job-priority ${job.priority}">${job.priority}</div>
            </div>
            <div class="job-details">
              <span>${job.type.toUpperCase()}</span>
              ${job.salary ? `<span>${job.salary}€</span>` : ""}
            </div>
            <div class="job-assignment ${assignedEmployee ? "assigned" : ""}">
              ${
                assignedEmployee
                  ? `<i class="fas fa-user"></i> ${assignedEmployee.firstName} ${assignedEmployee.lastName}`
                  : '<i class="fas fa-user-slash"></i> Non assigné'
              }
            </div>
            <div class="job-actions">
              <select class="assign-select" onchange="assignEmployee(${job.id}, this.value)">
                <option value="">Assigner à...</option>
                ${deptEmployees
                  .map(
                    (emp) =>
                      `<option value="${emp.id}" ${job.employeeId === emp.id ? "selected" : ""}>
                    ${emp.firstName} ${emp.lastName}
                  </option>`,
                  )
                  .join("")}
              </select>
              ${
                assignedEmployee
                  ? `<button class="job-btn" onclick="unassignEmployee(${job.id})">
                  <i class="fas fa-user-minus"></i> Retirer
                </button>`
                  : ""
              }
              <button class="job-btn" onclick="deleteJob(${job.id})" title="Supprimer">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        `
        })
        .join("")}
    </div>
  `
}

function setEmployeeDepartment(deptId) {
  document.getElementById("employeeDepartment").value = deptId
}

function setJobDepartment(deptId) {
  document.getElementById("jobDepartment").value = deptId
}

function addActivity(message, type) {
  const activity = {
    id: Date.now(),
    message: message,
    type: type,
    timestamp: new Date(),
  }

  activityLog.unshift(activity)

  // Garder seulement les 10 dernières activités
  if (activityLog.length > 10) {
    activityLog = activityLog.slice(0, 10)
  }

  renderActivity()
}

function renderActivity() {
  const container = document.getElementById("activityTimeline")

  if (activityLog.length === 0) {
    container.innerHTML = `
      <div class="empty-activity">
        <i class="fas fa-info-circle"></i>
        <p>Aucune activité récente</p>
      </div>
    `
    return
  }

  container.innerHTML = activityLog
    .map((activity) => {
      const timeAgo = getTimeAgo(activity.timestamp)
      const initials = getInitials(activity.message)

      return `
      <div class="activity-item ${activity.type}">
        <div class="activity-avatar">${initials}</div>
        <div class="activity-info">
          <p>${activity.message}</p>
          <span>${timeAgo}</span>
        </div>
      </div>
    `
    })
    .join("")
}

function getInitials(message) {
  const words = message.split(" ")
  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

function getTimeAgo(date) {
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return "À l'instant"
  if (minutes < 60) return `Il y a ${minutes} min`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Il y a ${hours}h`

  const days = Math.floor(hours / 24)
  return `Il y a ${days}j`
}

function logout() {
  if (confirm("Êtes-vous sûr de vouloir vous déconnecter ?")) {
    localStorage.removeItem("setupCompleted")
    localStorage.removeItem("companyProfile")
    window.location.href = "/hr-login"
  }
}

// Fermer les modals en cliquant à l'extérieur
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("show")
    document.body.style.overflow = "auto"
  }
})

// Fermer les modals avec Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const openModal = document.querySelector(".modal-overlay.show")
    if (openModal) {
      openModal.classList.remove("show")
      document.body.style.overflow = "auto"
    }
  }
})

// Mettre à jour la prévisualisation de couleur
document.getElementById("departmentColor").addEventListener("input", (e) => {
  const preview = document.querySelector(".color-preview")
  if (preview) {
    preview.style.backgroundColor = e.target.value
  }
})

// Raccourcis clavier pour améliorer l'UX
document.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + N pour nouveau département
  if ((e.ctrlKey || e.metaKey) && e.key === "n") {
    e.preventDefault()
    openDepartmentModal()
  }

  // Ctrl/Cmd + J pour nouveau job
  if ((e.ctrlKey || e.metaKey) && e.key === "j") {
    e.preventDefault()
    openJobModal()
  }

  // Ctrl/Cmd + E pour nouvel employé
  if ((e.ctrlKey || e.metaKey) && e.key === "e") {
    e.preventDefault()
    openEmployeeModal()
  }

  // Ctrl/Cmd + P pour profil d'entreprise
  if ((e.ctrlKey || e.metaKey) && e.key === "p") {
    e.preventDefault()
    openCompanyProfile()
  }
})
