// Variables globales
let currentJob = null
let applications = []
let allCandidates = []
let currentUser = null

// Charger les données du job au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Page job-details chargée avec compatibilité")
  loadCurrentUser()
  loadJobData()
  loadAllCandidates()
})

// Charger l'utilisateur actuel
async function loadCurrentUser() {
  try {
    console.log("👤 Chargement utilisateur actuel")
    const response = await fetch("/api/current-user")
    const result = await response.json()

    if (result.success) {
      currentUser = result.user
      console.log("✅ Utilisateur chargé:", currentUser)
    } else {
      console.error("❌ Erreur chargement utilisateur:", result.message)
      if (result.message === "Utilisateur non connecté") {
        window.location.href = "/hr-login"
      }
    }
  } catch (error) {
    console.error("❌ Erreur réseau chargement utilisateur:", error)
  }
}

// Charger tous les candidats disponibles
async function loadAllCandidates() {
  try {
    console.log("👥 Chargement de tous les candidats")
    allCandidates = [
      {
        id: 1,
        name: "Marie Dubois",
        title: "Développeuse Full-Stack",
        email: "marie.dubois@email.com",
        skills: ["React", "Node.js", "Python"],
        experience: "3 ans",
      },
      {
        id: 2,
        name: "Pierre Martin",
        title: "Designer UX/UI",
        email: "pierre.martin@email.com",
        skills: ["Figma", "Adobe XD", "Sketch"],
        experience: "5 ans",
      },
      {
        id: 3,
        name: "Sophie Laurent",
        title: "Data Scientist",
        email: "sophie.laurent@email.com",
        skills: ["Python", "R", "Machine Learning"],
        experience: "4 ans",
      },
    ]
    console.log(`✅ ${allCandidates.length} candidats chargés`)
  } catch (error) {
    console.error("❌ Erreur chargement candidats:", error)
  }
}

// Charger les données du job depuis localStorage ou URL
function loadJobData() {
  console.log("📊 Début chargement des données")
  const urlParams = new URLSearchParams(window.location.search)
  const jobId = urlParams.get("id")
  console.log("🔍 Job ID depuis URL:", jobId)

  if (jobId) {
    console.log("🌐 Chargement depuis API")
    loadJobFromAPI(jobId)
  } else {
    console.log("💾 Tentative chargement depuis localStorage")
    const jobData = localStorage.getItem("selectedJob")
    if (jobData) {
      try {
        currentJob = JSON.parse(jobData)
        console.log("✅ Données chargées depuis localStorage:", currentJob)
        displayJobInfo()
        renderApplicationsWithCompatibility()
      } catch (error) {
        console.error("❌ Erreur parsing localStorage:", error)
        showError("Erreur lors du chargement des données du poste")
      }
    } else {
      console.log("❌ Aucune donnée trouvée")
      showError("Aucun poste sélectionné. Veuillez retourner au dashboard et sélectionner un poste.")
    }
  }
}

// FONCTION AMÉLIORÉE: Charger le job depuis l'API avec calcul de compatibilité
async function loadJobFromAPI(jobId) {
  try {
    console.log(`🔄 Chargement job ID: ${jobId}`)
    showLoading("Chargement des détails du poste...")

    const response = await fetch(`/api/job/${jobId}`)
    console.log("📡 Réponse API:", response.status)

    if (response.ok) {
      const result = await response.json()
      console.log("📦 Données reçues:", result)

      if (result.success) {
        currentJob = result.job
        applications = result.job.applications || []

        console.log("✅ Job chargé:", currentJob.title)
        console.log("👥 Candidatures:", applications.length)

        // NOUVEAU: Calculer la compatibilité pour chaque candidature
        await calculateCompatibilityForApplications()

        hideLoading()
        displayJobInfo()
        renderApplicationsWithCompatibility()
        updateCompatibilityStats()
      } else {
        console.error("❌ Erreur API:", result.message)
        showError(result.message || "Erreur lors du chargement du poste")
      }
    } else {
      console.error("❌ Erreur HTTP:", response.status)
      showError("Erreur de connexion au serveur")
    }
  } catch (error) {
    console.error("❌ Erreur critique:", error)
    showError("Erreur lors du chargement des données")
  }
}

// NOUVELLE FONCTION: Calculer la compatibilité pour toutes les candidatures
async function calculateCompatibilityForApplications() {
  console.log("🧮 Calcul de compatibilité pour toutes les candidatures")

  for (let i = 0; i < applications.length; i++) {
    const app = applications[i]
    try {
      console.log(`📊 Calcul compatibilité pour ${app.name}`)
      const response = await fetch(`/api/application/${app.id}/compatibility`)
      const result = await response.json()

      if (result.success) {
        applications[i].compatibility_percentage = result.compatibility_percentage || 0
        applications[i].matched_skills_count = result.matched_count || 0
        applications[i].missing_skills_count = result.missing_count || 0
        applications[i].total_job_skills = result.total_job_skills || 0
        applications[i].matched_skills = result.matched_skills || []
        applications[i].missing_skills = result.missing_skills || []

        console.log(`✅ Compatibilité calculée pour ${app.name}: ${applications[i].compatibility_percentage}%`)
      } else {
        console.warn(`⚠️ Erreur calcul compatibilité pour ${app.name}:`, result.message)
        applications[i].compatibility_percentage = 0
        applications[i].matched_skills_count = 0
        applications[i].missing_skills_count = 0
        applications[i].total_job_skills = 0
      }
    } catch (error) {
      console.error(`❌ Erreur réseau compatibilité pour ${app.name}:`, error)
      applications[i].compatibility_percentage = 0
      applications[i].matched_skills_count = 0
      applications[i].missing_skills_count = 0
      applications[i].total_job_skills = 0
    }
  }

  console.log("✅ Calcul de compatibilité terminé pour toutes les candidatures")
}

// NOUVELLE FONCTION: Mettre à jour les statistiques de compatibilité
function updateCompatibilityStats() {
  if (applications.length === 0) {
    document.getElementById("averageCompatibility").textContent = "--"
    return
  }

  const totalCompatibility = applications.reduce((sum, app) => sum + (app.compatibility_percentage || 0), 0)
  const averageCompatibility = Math.round(totalCompatibility / applications.length)

  const avgElement = document.getElementById("averageCompatibility")
  if (avgElement) {
    avgElement.textContent = `${averageCompatibility}%`
  }

  console.log(`📊 Compatibilité moyenne: ${averageCompatibility}%`)
}

// Afficher les informations du job
function displayJobInfo() {
  if (!currentJob) {
    console.error("❌ Aucun job à afficher")
    return
  }

  console.log("🎨 Affichage des informations du job")

  try {
    const titleElement = document.getElementById("jobTitle")
    if (titleElement) {
      titleElement.textContent = currentJob.title || "Titre non disponible"
    }

    const departmentElement = document.getElementById("jobDepartment")
    if (departmentElement) {
      departmentElement.textContent = currentJob.department_name || "Département non spécifié"
    }

    const descriptionElement = document.getElementById("jobDescription")
    if (descriptionElement) {
      descriptionElement.textContent = currentJob.description || "Description non disponible"
    }

    const responsibilitiesElement = document.getElementById("jobResponsibilities")
    if (responsibilitiesElement) {
      responsibilitiesElement.textContent = currentJob.responsibilities || "Aucune responsabilité spécifiée"
    }

    const typeElement = document.getElementById("jobType")
    if (typeElement) {
      typeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    }

    const priorityElement = document.getElementById("jobPriority")
    if (priorityElement) {
      priorityElement.textContent = (currentJob.priority || "").toUpperCase()
    }

    const deadlineElement = document.getElementById("jobDeadline")
    if (deadlineElement) {
      deadlineElement.textContent = currentJob.deadline
        ? new Date(currentJob.deadline).toLocaleDateString("fr-FR")
        : "Non définie"
    }

    const statusElement = document.getElementById("jobStatus")
    if (statusElement) {
      statusElement.textContent = (currentJob.status || "").toUpperCase()
      statusElement.className = `status-badge ${currentJob.status || "draft"}`
    }

    const salaryElement = document.getElementById("jobSalary")
    if (salaryElement) {
      let salaryText = "Non spécifié"
      if (currentJob.salary_min && currentJob.salary_max) {
        salaryText = `€ ${currentJob.salary_min} - ${currentJob.salary_max}`
      } else if (currentJob.salary_min) {
        salaryText = `€ ${currentJob.salary_min}+`
      }
      salaryElement.textContent = salaryText
    }

    const contractTypeElement = document.getElementById("contractType")
    if (contractTypeElement) {
      contractTypeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    }

    const jobCreatedElement = document.getElementById("jobCreated")
    if (jobCreatedElement) {
      jobCreatedElement.textContent = new Date(currentJob.created_at).toLocaleDateString("fr-FR")
    }

    const assignedEmployeeElement = document.getElementById("assignedEmployee")
    if (assignedEmployeeElement) {
      assignedEmployeeElement.textContent = currentJob.assigned_employee_name || "Non assigné"
    }

    const applicationsElement = document.getElementById("jobApplications")
    if (applicationsElement) {
      applicationsElement.textContent = currentJob.applications_count || 0
    }

    const daysRemainingElement = document.getElementById("daysRemaining")
    if (daysRemainingElement) {
      if (currentJob.days_remaining !== null && currentJob.days_remaining !== undefined) {
        daysRemainingElement.textContent = currentJob.days_remaining
      } else {
        daysRemainingElement.textContent = "--"
      }
    }

    console.log("📦 Skills data received:", currentJob.skills)
    renderJobSkills()

    console.log("✅ Informations affichées avec succès")
  } catch (error) {
    console.error("❌ Erreur lors de l'affichage:", error)
    showError("Erreur lors de l'affichage des données")
  }
}

// Fonction pour afficher les compétences requises
function renderJobSkills() {
  console.log("🛠️ Affichage des compétences requises")
  const skillsContainer = document.getElementById("jobSkillsContainer")
  if (!skillsContainer) {
    console.error("❌ Container jobSkillsContainer non trouvé")
    return
  }

  if (!currentJob.skills || currentJob.skills.length === 0) {
    skillsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-tools"></i>
          <h4>Aucune compétence spécifiée</h4>
          <p>Ce poste ne liste pas de compétences spécifiques pour le moment.</p>
        </div>
      `
    return
  }

  skillsContainer.innerHTML = `
      <div class="skills-grid">
        ${currentJob.skills
          .map(
            (skill) => `
          <div class="skill-item">
            <div class="skill-name">${skill.skill_name}</div>
            <div class="skill-level">${skill.skill_level.charAt(0).toUpperCase() + skill.skill_level.slice(1)}</div>
            ${
              skill.is_required
                ? `<span class="skill-required-badge">Requis</span>`
                : `<span class="skill-optional-badge">Optionnel</span>`
            }
          </div>
        `,
          )
          .join("")}
      </div>
    `
  console.log(`✅ ${currentJob.skills.length} compétences affichées`)
}

// FONCTION AMÉLIORÉE: Rendre les candidatures avec compatibilité
function renderApplicationsWithCompatibility(filter = "all") {
  console.log(`👥 Rendu des candidatures avec compatibilité (filtre: ${filter})`)

  const container = document.getElementById("applicationsList")
  if (!container) {
    console.error("❌ Container applicationsList non trouvé")
    return
  }

  let filteredApplications = applications
  if (filter !== "all") {
    filteredApplications = applications.filter((app) => app.status === filter)
  }

  console.log(`📊 ${filteredApplications.length} candidatures à afficher`)

  if (filteredApplications.length === 0) {
    container.innerHTML = `
    <div class="empty-state">
      <i class="fas fa-inbox"></i>
      <h4>Aucune candidature ${filter === "all" ? "" : filter}</h4>
      <p>Les candidatures apparaîtront ici une fois soumises.</p>
    </div>
  `
    return
  }

  container.innerHTML = filteredApplications
    .map((app) => {
      console.log(`🔍 Rendu candidature ${app.name} avec compatibilité ${app.compatibility_percentage}%`)

      return `
      <div class="application-item-detailed ${app.is_recommended ? "has-recommendation" : ""}">
        <div class="candidate-info">
          <div class="candidate-avatar">${app.name
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="candidate-details">
            <div class="candidate-name-section">
              <div class="candidate-name">
                ${app.name}
                ${
                  app.is_recommended
                    ? `
                  <span class="recommendation-badge ${app.recommendation_priority || "normal"}" 
                         title="Candidat recommandé par ${app.recommended_by || "un chef de département"}">
                    <i class="fas fa-star"></i> 
                    ${
                      app.recommendation_priority === "urgent"
                        ? "URGENT"
                        : app.recommendation_priority === "high"
                          ? "PRIORITÉ HAUTE"
                          : "RECOMMANDÉ"
                    }
                  </span>
                `
                    : ""
                }
              </div>
              
              <div class="application-status-section">
                <div class="status-badge ${app.status}">
                  ${getStatusText(app.status)}
                  ${
                    app.is_recommended && app.recommendation_priority !== "normal"
                      ? `<span class="priority-indicator ${app.recommendation_priority}">
                      ${app.recommendation_priority === "urgent" ? "" : ""}
                    </span>`
                      : ""
                  }
                </div>
              </div>
            </div>
            
            <div class="candidate-title">${app.title || "Candidat"}</div>
            <div class="candidate-meta">
              <span class="application-date">
                Candidature: ${new Date(app.application_date).toLocaleDateString("fr-FR")}
              </span>
              ${app.hr_rating ? `<span class="hr-rating">Note HR: ${app.hr_rating}/5 ⭐</span>` : ""}
              ${
                app.is_recommended && app.recommended_by
                  ? `
                <span class="recommendation-info">
                  <i class="fas fa-user-tie"></i> Recommandé par ${app.recommended_by}
                  ${app.recommendation_date ? ` le ${new Date(app.recommendation_date).toLocaleDateString("fr-FR")}` : ""}
                </span>
              `
                  : ""
              }
            </div>
          </div>
        </div>

        <!-- NOUVELLE SECTION: Compatibilité des compétences -->
        <div class="application-compatibility-section">
          <div class="compatibility-header">
            <div class="compatibility-title">
              <i class="fas fa-chart-pie"></i>
              Compatibilité des compétences
            </div>
            <div class="compatibility-percentage ${getCompatibilityClass(app.compatibility_percentage || 0)}">
              ${app.compatibility_percentage || 0}%
              <i class="fas fa-${getCompatibilityIcon(app.compatibility_percentage || 0)}"></i>
            </div>
          </div>
          
          <div class="compatibility-progress">
            <div class="compatibility-progress-bar ${getCompatibilityClass(app.compatibility_percentage || 0)}" 
                 style="width: ${app.compatibility_percentage || 0}%"></div>
          </div>
          
          <div class="compatibility-details">
            <span class="skill-stat matched">
              <i class="fas fa-check-circle"></i>
              ${app.matched_skills_count || 0} compétences correspondantes
            </span>
            <span class="skill-stat missing">
              <i class="fas fa-times-circle"></i>
              ${(app.total_job_skills || 0) - (app.matched_skills_count || 0)} manquantes
            </span>
            <span>Total: ${app.total_job_skills || 0} compétences</span>
          </div>
          
          <div class="compatibility-actions">
            <button class="btn-compatibility-details" onclick="viewCompatibilityDetails(${app.id})">
              <i class="fas fa-search"></i> Détails compatibilité
            </button>
          </div>
        </div>

        
        ${
          app.is_recommended && app.recommendation_comment
            ? `
          <div class="recommendation-comment">
            <i class="fas fa-comment-alt"></i>
            <strong style="color:black">Commentaire de recommandation:</strong>
            <p>"${app.recommendation_comment}"</p>
            ${app.recommended_by ? `<small>— ${app.recommended_by}</small>` : ""}
          </div>
        `
            : ""
        }
        <div class="application-actions">
            ${renderCandidateActions(app)}
          </div>
      </div>
      
    `
    })
    .join("")
}

// NOUVELLES FONCTIONS: Helpers pour la compatibilité
function getCompatibilityClass(percentage) {
  if (percentage >= 75) return "high"
  if (percentage >= 50) return "medium"
  if (percentage >= 25) return "low"
  return "very-low"
}

function getCompatibilityIcon(percentage) {
  if (percentage >= 75) return "star"
  if (percentage >= 50) return "star-half-alt"
  if (percentage >= 25) return "exclamation-triangle"
  return "times-circle"
}

// NOUVELLE FONCTION: Filtrer par compatibilité
function filterApplicationsByCompatibility(minCompatibility) {
  console.log("🔍 Filtrage par compatibilité:", minCompatibility)

  if (minCompatibility === "all") {
    renderApplicationsWithCompatibility()
    return
  }

  const threshold = Number.parseInt(minCompatibility)
  const filteredApps = applications.filter((app) => (app.compatibility_percentage || 0) >= threshold)

  const container = document.getElementById("applicationsList")
  if (!container) return

  if (filteredApps.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-chart-pie"></i>
        <h4>Aucune candidature avec ${threshold}%+ de compatibilité</h4>
        <p>Aucune candidature ne correspond au niveau de compatibilité sélectionné.</p>
      </div>
    `
    return
  }

  // Utiliser la même logique de rendu mais avec les candidatures filtrées
  const originalApplications = applications
  applications = filteredApps
  renderApplicationsWithCompatibility()
  applications = originalApplications
}

// NOUVELLE FONCTION: Voir les détails de compatibilité avec thème sombre
async function viewCompatibilityDetails(applicationId) {
  console.log("🔍 Affichage détails compatibilité pour candidature:", applicationId)

  try {
    showLoading("Chargement des détails de compatibilité...")

    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()

    hideLoading()

    if (result.success) {
      showDarkCompatibilityModal(result)
    } else {
      showNotification("Erreur lors du chargement des détails de compatibilité", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur chargement détails compatibilité:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// NOUVELLE FONCTION: Afficher la modal de détails de compatibilité avec thème sombre
function showDarkCompatibilityModal(compatibilityData) {
  console.log("🔍 Affichage modal compatibilité sombre:", compatibilityData)

  const modal = document.createElement("div")
  modal.className = "modal-overlay compatibility-modal-overlay"
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 25000;
    padding: 2rem;
  `

  modal.innerHTML = `
    <div class="modal-content" style="
      max-width: 900px;
      width: 95%;
      max-height: 90vh;
      overflow-y: auto;
      background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
      border-radius: 20px;
      border: 2px solid rgba(59, 130, 246, 0.4);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    ">
      <div class="modal-header" style="
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px 20px 0 0;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
      ">
        <h3 style="margin: 0; display: flex; align-items: center; gap: 1rem; font-size: 1.5rem;">
          <i class="fas fa-chart-pie" style="color: #3b82f6;"></i> 
          Analyse Détaillée de Compatibilité
        </h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()" style="
          position: absolute;
          top: 2rem;
          right: 2rem;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 1.2rem;
        ">&times;</button>
      </div>
      
      <div class="modal-body" style="padding: 2rem; background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);">
        <div class="compatibility-overview" style="
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 2rem;
          align-items: center;
          margin-bottom: 2rem;
          padding: 2rem;
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 16px;
        ">
          <div class="compatibility-score">
            <div class="score-circle ${getCompatibilityClass(compatibilityData.compatibility_percentage)}" style="
              width: 120px;
              height: 120px;
              border-radius: 50%;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              background: conic-gradient(
                ${
                  compatibilityData.compatibility_percentage >= 75
                    ? "#10b981"
                    : compatibilityData.compatibility_percentage >= 50
                      ? "#f59e0b"
                      : compatibilityData.compatibility_percentage >= 25
                        ? "#ef4444"
                        : "#6b7280"
                } 
                ${compatibilityData.compatibility_percentage * 3.6}deg,
                rgba(255, 255, 255, 0.1) 0deg
              );
              position: relative;
            ">
              <div style="
                position: absolute;
                inset: 8px;
                background: linear-gradient(145deg, #0f172a, #1e293b);
                border-radius: 50%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
              ">
                <span class="score-number" style="
                  font-size: 2rem;
                  font-weight: bold;
                  color: white;
                ">${compatibilityData.compatibility_percentage}%</span>
                <span class="score-label" style="
                  font-size: 0.8rem;
                  color: #cbd5e1;
                  text-transform: uppercase;
                  letter-spacing: 1px;
                ">Compatibilité</span>
              </div>
            </div>
          </div>
          
          <div class="compatibility-summary">
            <div class="summary-stat" style="
              display: flex;
              align-items: center;
              gap: 1rem;
              margin: 1rem 0;
              padding: 1rem;
              background: rgba(16, 185, 129, 0.1);
              border: 1px solid rgba(16, 185, 129, 0.3);
              border-radius: 12px;
            ">
              <i class="fas fa-check-circle" style="color: #10b981; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">
                ${compatibilityData.matched_count} compétences correspondantes
              </span>
            </div>
            <div class="summary-stat" style="
              display: flex;
              align-items: center;
              gap: 1rem;
              margin: 1rem 0;
              padding: 1rem;
              background: rgba(239, 68, 68, 0.1);
              border: 1px solid rgba(239, 68, 68, 0.3);
              border-radius: 12px;
            ">
              <i class="fas fa-times-circle" style="color: #ef4444; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">
                ${compatibilityData.missing_count} compétences manquantes
              </span>
            </div>
            <div class="summary-stat" style="
              display: flex;
              align-items: center;
              gap: 1rem;
              margin: 1rem 0;
              padding: 1rem;
              background: rgba(107, 114, 128, 0.1);
              border: 1px solid rgba(107, 114, 128, 0.3);
              border-radius: 12px;
            ">
              <i class="fas fa-list" style="color: #6b7280; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">
                ${compatibilityData.total_job_skills} compétences requises au total
              </span>
            </div>
          </div>
        </div>
        
        <div class="skills-breakdown" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
          <div class="skills-section">
            <div class="skills-breakdown-header" style="
              margin-bottom: 1.5rem;
              padding: 1rem;
              background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
              border: 1px solid rgba(16, 185, 129, 0.3);
              border-radius: 12px;
            ">
              <h4 class="skills-breakdown-title" style="
                margin: 0;
                color: #f8fafc;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 1.2rem;
              ">
                <i class="fas fa-check-circle" style="color: #10b981;"></i>
                Compétences Correspondantes (${compatibilityData.matched_count})
              </h4>
            </div>
            <div class="skills-list">
              ${compatibilityData.matched_skills
                .map(
                  (skill) => `
                <div class="skill-item matched" style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  padding: 1rem;
                  margin: 0.5rem 0;
                  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
                  border: 1px solid rgba(16, 185, 129, 0.3);
                  border-radius: 12px;
                ">
                  <div class="skill-info">
                    <span class="skill-name" style="
                      color: #f8fafc;
                      font-weight: 600;
                      display: block;
                      margin-bottom: 0.25rem;
                    ">${skill.skill_name}</span>
                    <span class="skill-level ${skill.skill_level}" style="
                      color: #cbd5e1;
                      font-size: 0.9rem;
                      margin-right: 0.5rem;
                    ">${getLevelText(skill.skill_level)}</span>
                    <span class="skill-required ${skill.is_required ? "required" : "optional"}" style="
                      color: ${skill.is_required ? "#f59e0b" : "#6b7280"};
                      font-size: 0.8rem;
                      font-weight: 500;
                    ">
                      ${skill.is_required ? "Requis" : "Optionnel"}
                    </span>
                  </div>
                  <div class="skill-status matched" style="
                    color: #10b981;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                  ">
                    <i class="fas fa-check"></i>
                    Possédée
                  </div>
                </div>
              `,
                )
                .join("")}
            </div>
          </div>
          
          <div class="skills-section">
            <div class="skills-breakdown-header" style="
              margin-bottom: 1.5rem;
              padding: 1rem;
              background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
              border: 1px solid rgba(239, 68, 68, 0.3);
              border-radius: 12px;
            ">
              <h4 class="skills-breakdown-title" style="
                margin: 0;
                color: #f8fafc;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 1.2rem;
              ">
                <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                Compétences Manquantes (${compatibilityData.missing_count})
              </h4>
            </div>
            <div class="skills-list">
              ${compatibilityData.missing_skills
                .map(
                  (skill) => `
                <div class="skill-item missing" style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  padding: 1rem;
                  margin: 0.5rem 0;
                  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
                  border: 1px solid rgba(239, 68, 68, 0.3);
                  border-radius: 12px;
                ">
                  <div class="skill-info">
                    <span class="skill-name" style="
                      color: #f8fafc;
                      font-weight: 600;
                      display: block;
                      margin-bottom: 0.25rem;
                    ">${skill.skill_name}</span>
                    <span class="skill-level ${skill.skill_level}" style="
                      color: #cbd5e1;
                      font-size: 0.9rem;
                      margin-right: 0.5rem;
                    ">${getLevelText(skill.skill_level)}</span>
                    <span class="skill-required ${skill.is_required ? "required" : "optional"}" style="
                      color: ${skill.is_required ? "#f59e0b" : "#6b7280"};
                      font-size: 0.8rem;
                      font-weight: 500;
                    ">
                      ${skill.is_required ? "Requis" : "Optionnel"}
                    </span>
                  </div>
                  <div class="skill-status missing" style="
                    color: #ef4444;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                  ">
                    <i class="fas fa-times"></i>
                    Manquante
                  </div>
                </div>
              `,
                )
                .join("")}
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer" style="
        padding: 1.5rem 2rem;
        border-top: 1px solid rgba(59, 130, 246, 0.2);
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 0 0 20px 20px;
        display: flex;
        justify-content: flex-end;
      ">
        <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()" style="
          padding: 0.875rem 1.75rem;
          border: none;
          border-radius: 12px;
          font-weight: 600;
          cursor: pointer;
          background: linear-gradient(135deg, #64748b, #475569);
          color: white;
          border: 1px solid rgba(100, 116, 139, 0.3);
        ">
          Fermer
        </button>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Close modal when clicking outside
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.remove()
    }
  })
}

// Helper function pour les niveaux de compétences
function getLevelText(level) {
  const levelTexts = {
    beginner: "Débutant",
    intermediate: "Intermédiaire",
    advanced: "Avancé",
    expert: "Expert",
  }
  return levelTexts[level] || level
}

// FONCTION CORRIGÉE: Rendre les actions pour chaque candidat selon le rôle
function renderCandidateActions(app) {
  console.log(`🎯 Rendu actions pour ${app.name}:`, {
    userRole: currentUser?.role,
    appStatus: app.status,
    isRecommended: app.is_recommended,
  })

  if (currentUser && currentUser.role === "department_head") {
    console.log("🏢 Mode chef de département")

    if ((app.status === "pending" || app.status === "reviewed") && !app.is_recommended) {
      const safeCandidateName = app.name.replace(/'/g, "\\'").replace(/"/g, '\\"')
      const safeJobTitle = currentJob.title.replace(/'/g, "\\'").replace(/"/g, '\\"')

      console.log("✅ Affichage bouton recommander")
      return `
      <button class="btn-action recommend" onclick="showRecommendConfirmation(${app.id}, '${safeCandidateName}', '${safeJobTitle}')">
        <i class="fas fa-thumbs-up"></i> Recommander
      </button>
      <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
    `
    } else if (app.is_recommended) {
      console.log("✅ Affichage statut recommandé")
      return `
      <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
    `
    } else {
      console.log("ℹ️ Candidature non éligible pour recommandation")
      return `
      <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
      <small style="color: #6b7280; font-style: italic;">
        ${
          app.status === "accepted"
            ? "Candidature déjà acceptée"
            : app.status === "rejected"
              ? "Candidature rejetée"
              : "Statut: " + getStatusText(app.status)
        }
      </small>
    `
    }
  }

  // Pour les autres rôles (recruteur, super_admin) : boutons complets
  if (app.status === "pending") {
    return `
    <button class="btn-action review" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
      <i class="fas fa-eye"></i> Examiner
    </button>
    <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
      <i class="fas fa-check"></i> Accepter
    </button>
    <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
      <i class="fas fa-times"></i> Rejeter
    </button>
  `
  } else if (app.status === "reviewed") {
    return `
    <button class="btn-action schedule" onclick="updateApplicationStatus(${app.id}, 'interview_scheduled')">
      <i class="fas fa-calendar"></i> Programmer entretien
    </button>
    <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
      <i class="fas fa-check-circle"></i> Accepter
    </button>
    <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
      <i class="fas fa-times"></i> Rejeter
    </button>
  `
  } else if (app.status === "interview_scheduled") {
    return `
    <button class="btn-action complete" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
      <i class="fas fa-check-double"></i> Entretien terminé
    </button>
    <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
      <i class="fas fa-user-check"></i> Accepter
    </button>
    <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
      <i class="fas fa-times"></i> Rejeter
    </button>
  `
  } else {
    return `
    <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
      <i class="fas fa-info-circle"></i> Voir profil
    </button>
  `
  }
}

// Fonction pour retourner au dashboard
function goBackToDashboard() {
  console.log("🔙 Retour au dashboard")
  window.location.href = "/dashboard"
}

// Obtenir le texte du statut
function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    interview_scheduled: "Entretien programmé",
    interview_completed: "Entretien terminé",
    accepted: "Acceptée",
    rejected: "Rejetée",
    withdrawn: "Retirée",
    recommended: "Recommandée",
  }
  return statusTexts[status] || status
}

// FONCTION CORRIGÉE: Afficher la modal de confirmation de recommandation
function showRecommendConfirmation(applicationId, candidateName, jobTitle) {
  console.log(`👍 Affichage confirmation recommandation pour ${candidateName} (ID: ${applicationId})`)

  if (!currentUser || currentUser.role !== "department_head") {
    showNotification("Seuls les chefs de département peuvent recommander des candidatures", "warning")
    return
  }

  const safeCandidateName = candidateName.replace(/'/g, "\\'").replace(/"/g, '\\"')
  const safeJobTitle = jobTitle.replace(/'/g, "\\'").replace(/"/g, '\\"')

  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.opacity = "1"

  modal.innerHTML = `
  <div class="confirmation-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="confirmation-icon recommend">
          <i class="fas fa-thumbs-up"></i>
        </div>
        <h3>Recommander cette candidature</h3>
        <p>Recommander <strong>${candidateName}</strong> pour le poste</p>
      </div>
      
      <div class="candidate-modal-info">
        <div class="candidate-modal-avatar">${candidateName
          .split(" ")
          .map((n) => n[0])
          .join("")}</div>
        <div class="candidate-modal-details">
          <h4>${candidateName}</h4>
          <p>Poste: ${jobTitle}</p>
        </div>
      </div>
      
      <div class="modal-body">
        <p><strong>En tant que chef de département, vous pouvez recommander cette candidature :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            <li><i class="fas fa-star"></i> Marquer la candidature comme recommandée</li>
            <li><i class="fas fa-bell"></i> Notifier les recruteurs et super admins</li>
            <li><i class="fas fa-comment"></i> Ajouter vos commentaires de recommandation</li>
            <li><i class="fas fa-priority-high"></i> Donner une priorité élevée à cette candidature</li>
          </ul>
        </div>
        
        <div class="recommendation-form">
          <label for="recommendationComment">Commentaire de recommandation :</label>
          <textarea id="recommendationComment" placeholder="Expliquez pourquoi vous recommandez ce candidat..." rows="3" required></textarea>
          
          <label for="recommendationPriority">Niveau de recommandation :</label>
          <select id="recommendationPriority">
            <option value="normal">Recommandation normale</option>
            <option value="high">Recommandation forte</option>
            <option value="urgent">Recommandation urgente</option>
          </select>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm recommend" onclick="confirmRecommendApplication(${applicationId})">
          <i class="fas fa-thumbs-up"></i> Confirmer la recommandation
        </button>
        <button class="btn-cancel" onclick="closeConfirmationModal()">
          <i class="fas fa-times"></i> Annuler
        </button>
      </div>
    </div>
  </div>
`

  document.body.appendChild(modal)

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  document.addEventListener("keydown", handleEscapeKey)
}

// FONCTION CORRIGÉE: Confirmer la recommandation avec meilleur feedback
async function confirmRecommendApplication(applicationId) {
  console.log(`👍 Confirmation recommandation candidature ${applicationId}`)

  try {
    const commentElement = document.getElementById("recommendationComment")
    const priorityElement = document.getElementById("recommendationPriority")

    if (!commentElement || !priorityElement) {
      showNotification("Erreur: éléments du formulaire non trouvés", "error")
      return
    }

    const comment = commentElement.value.trim()
    const priority = priorityElement.value

    if (!comment) {
      showNotification("Le commentaire de recommandation est obligatoire", "warning")
      commentElement.focus()
      return
    }

    if (comment.length < 10) {
      showNotification("Le commentaire doit contenir au moins 10 caractères", "warning")
      commentElement.focus()
      return
    }

    closeConfirmationModal()
    showLoading("Traitement de votre recommandation...")

    const response = await fetch(`/api/applications/${applicationId}/recommend`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        comment: comment,
        priority: priority,
      }),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("👍 Candidature recommandée avec succès")
      showNotification(`✅ ${result.message || "Candidature recommandée avec succès"}`, "success")

      setTimeout(async () => {
        console.log("🔄 Rechargement des données après recommandation...")
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)

      setTimeout(() => {
        showNotification("🎯 Les recruteurs et super admins ont été notifiés de votre recommandation", "info")
      }, 2000)
    } else {
      console.error("❌ Erreur recommandation candidature:", result.message)
      showNotification(`❌ ${result.message}`, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur réseau recommandation candidature:", error)
    showNotification("❌ Erreur de connexion lors de la recommandation", "error")
  }
}

// Fonction pour afficher la modal de confirmation d'acceptation
function showAcceptConfirmation(applicationId, candidateName, jobTitle, departmentName) {
  console.log(`🎉 Affichage confirmation acceptation pour ${candidateName}`)

  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.opacity = "1"

  modal.innerHTML = `
  <div class="confirmation-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="confirmation-icon accept">
          <i class="fas fa-user-check"></i>
        </div>
        <h3>Confirmer l'acceptation</h3>
        <p>Accepter la candidature de <strong>${candidateName}</strong></p>
      </div>
      
      <div class="candidate-modal-info">
        <div class="candidate-modal-avatar">${candidateName
          .split(" ")
          .map((n) => n[0])
          .join("")}</div>
        <div class="candidate-modal-details">
          <h4>${candidateName}</h4>
          <p>Poste: ${jobTitle} - ${departmentName}</p>
        </div>
      </div>
      
      <div class="modal-body">
        <p><strong>Actions automatiques qui seront effectuées :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            <li><i class="fas fa-user-plus"></i> Création automatique de l'employé dans le système</li>
            <li><i class="fas fa-briefcase"></i> Attribution du poste "${jobTitle}" à l'employé</li>
            <li><i class="fas fa-building"></i> Assignation au département "${departmentName}"</li>
            <li><i class="fas fa-check-circle"></i> Marquage du poste comme pourvu</li>
            <li><i class="fas fa-times-circle"></i> Rejet automatique des autres candidatures</li>
            <li><i class="fas fa-calendar-check"></i> Date d'embauche fixée à aujourd'hui</li>
          </ul>
        </div>
        <div class="warning-note">
          <i class="fas fa-exclamation-triangle"></i>
          <p>Cette action est irréversible et modifiera définitivement le statut du poste.</p>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm" onclick="confirmAcceptApplication(${applicationId})">
          <i class="fas fa-check"></i> Confirmer l'acceptation
        </button>
        <button class="btn-cancel" onclick="closeConfirmationModal()">
          <i class="fas fa-times"></i> Annuler
        </button>
      </div>
    </div>
  </div>
`

  document.body.appendChild(modal)

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  document.addEventListener("keydown", handleEscapeKey)
}

// Fonction pour afficher la modal de confirmation de rejet
function showRejectConfirmation(applicationId, candidateName, jobTitle) {
  console.log(`❌ Affichage confirmation rejet pour ${candidateName}`)

  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.opacity = "1"

  modal.innerHTML = `
  <div class="confirmation-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="confirmation-icon reject">
          <i class="fas fa-user-times"></i>
        </div>
        <h3>Confirmer le rejet</h3>
        <p>Rejeter la candidature de <strong>${candidateName}</strong></p>
      </div>
      
      <div class="candidate-modal-info">
        <div class="candidate-modal-avatar">${candidateName
          .split(" ")
          .map((n) => n[0])
          .join("")}</div>
        <div class="candidate-modal-details">
          <h4>${candidateName}</h4>
          <p>Poste: ${jobTitle}</p>
        </div>
      </div>
      
      <div class="modal-body">
        <p><strong>Conséquences du rejet :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            <li><i class="fas fa-times-circle"></i> La candidature sera marquée comme rejetée</li>
            <li><i class="fas fa-envelope"></i> Le candidat sera notifié automatiquement</li>
            <li><i class="fas fa-archive"></i> Le dossier sera archivé dans l'historique</li>
            <li><i class="fas fa-ban"></i> Le candidat ne pourra plus postuler pour ce poste</li>
          </ul>
        </div>
        <div class="warning-note">
          <i class="fas fa-exclamation-triangle"></i>
          <p>Cette action est définitive. Le candidat sera informé du rejet de sa candidature.</p>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm reject" onclick="confirmRejectApplication(${applicationId})">
          <i class="fas fa-times"></i> Confirmer le rejet
        </button>
        <button class="btn-cancel" onclick="closeConfirmationModal()">
          <i class="fas fa-arrow-left"></i> Annuler
        </button>
      </div>
    </div>
  </div>
`

  document.body.appendChild(modal)

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  document.addEventListener("keydown", handleEscapeKey)
}

// Fonction pour gérer la touche Escape
function handleEscapeKey(e) {
  if (e.key === "Escape") {
    closeConfirmationModal()
  }
}

// Fonction pour fermer la modal de confirmation avec animation
function closeConfirmationModal() {
  const modal = document.querySelector(".modal-overlay")
  if (modal) {
    modal.classList.add("closing")
    const confirmationModal = modal.querySelector(".confirmation-modal")
    if (confirmationModal) {
      confirmationModal.classList.add("closing")
    }

    setTimeout(() => {
      modal.remove()
      document.removeEventListener("keydown", handleEscapeKey)
    }, 300)
  }
}

// Fonction pour confirmer l'acceptation
async function confirmAcceptApplication(applicationId) {
  try {
    closeConfirmationModal()
    showLoading("Traitement de l'acceptation...")

    const response = await fetch(`/api/accept-application/${applicationId}`, {
      method: "POST",
    })

    const result = await response.json()
    hideLoading()

    if (response.ok && result.success) {
      showNotification(result.message || "Candidat accepté avec succès", "success")
      setTimeout(() => {
        loadJobData()
      }, 1000)
    } else {
      console.warn("Erreur renvoyée:", result)
      showNotification(result.message || "Erreur lors de l'acceptation", "error")
    }
  } catch (error) {
    console.error("❌ Erreur réseau ou système:", error)
    hideLoading()
    showNotification("Erreur inattendue lors de la communication avec le serveur", "error")
  }
}

// Fonction pour confirmer le rejet
async function confirmRejectApplication(applicationId) {
  console.log(`❌ Confirmation rejet candidature ${applicationId}`)

  try {
    closeConfirmationModal()
    showLoading("Traitement du rejet...")

    const response = await fetch(`/api/applications/${applicationId}/update-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: "rejected",
        hr_notes: "Candidature rejetée via la page détails du poste",
      }),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("❌ Candidature rejetée avec succès")
      showNotification(result.message || "Candidature rejetée", "success")

      setTimeout(async () => {
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)
    } else {
      console.error("❌ Erreur rejet candidature:", result.message)
      showNotification(result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur réseau rejet candidature:", error)
    showNotification("Erreur de connexion lors du rejet", "error")
  }
}

// Fonction pour mettre à jour le statut d'une candidature
async function updateApplicationStatus(applicationId, newStatus) {
  console.log(`📝 Mise à jour statut candidature ${applicationId} vers ${newStatus}`)

  try {
    const response = await fetch(`/api/applications/${applicationId}/update-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: newStatus,
      }),
    })

    const result = await response.json()

    if (result.success) {
      console.log(`✅ Statut mis à jour vers ${newStatus}`)
      showNotification(result.message, "success")

      setTimeout(async () => {
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)
    } else {
      console.error("❌ Erreur mise à jour statut:", result.message)
      showNotification(result.message, "error")
    }
  } catch (error) {
    console.error("❌ Erreur réseau mise à jour statut:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Filtrer les candidatures
function filterApplications(filter) {
  console.log(`🔍 Filtrage: ${filter}`)

  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.remove("active")
  })

  const clickedBtn = Array.from(document.querySelectorAll(".filter-btn")).find((btn) =>
    btn.textContent.toLowerCase().includes(filter === "all" ? "toutes" : filter),
  )
  if (clickedBtn) {
    clickedBtn.classList.add("active")
  }

  renderApplicationsWithCompatibility(filter)
}

// Fonctions pour les actions
function editJob() {
  showNotification("Fonction de modification en cours de développement", "info")
}

function shareJob() {
  if (!currentJob) {
    showNotification("Aucun poste à partager", "error")
    return
  }

  if (navigator.share) {
    navigator
      .share({
        title: currentJob.title,
        text: `Découvrez cette offre d'emploi: ${currentJob.title}`,
        url: window.location.href,
      })
      .then(() => {
        showNotification("Poste partagé avec succès !", "success")
      })
      .catch(() => {
        fallbackShare()
      })
  } else {
    fallbackShare()
  }
}

function fallbackShare() {
  const url = window.location.href
  navigator.clipboard
    .writeText(url)
    .then(() => {
      showNotification("Lien copié dans le presse-papiers !", "success")
    })
    .catch(() => {
      showNotification("Impossible de copier le lien", "error")
    })
}

function closeJob() {
  if (confirm("Êtes-vous sûr de vouloir fermer ce poste ?")) {
    showNotification("Poste fermé avec succès", "success")
    setTimeout(() => {
      goBackToDashboard()
    }, 2000)
  }
}

function viewCandidateProfile(candidateId) {
  console.log(`👤 Voir profil candidat ${candidateId}`)
  window.open(`/employee-profile?candidate_id=${candidateId}`, "_blank")
}

// Fonctions utilitaires
function showLoading(message) {
  console.log("⏳ Affichage loading:", message)

  hideLoading()

  const loadingHTML = `
  <div class="loading-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; z-index: 25000;">
    <div class="loading-content" style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9)); backdrop-filter: blur(20px); padding: 2rem; border-radius: 16px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);">
      <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem; color: #3498db;"></i>
      <p style="margin: 0; font-weight: 500; color: #374151;">${message}</p>
    </div>
  </div>
`
  document.body.insertAdjacentHTML("beforeend", loadingHTML)
}

function hideLoading() {
  const loadingOverlay = document.querySelector(".loading-overlay")
  if (loadingOverlay) {
    loadingOverlay.remove()
  }
}

function showError(message) {
  console.log("❌ Affichage erreur:", message)

  const errorHTML = `
  <div class="error-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 25000;">
    <div class="error-content" style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9)); backdrop-filter: blur(20px); padding: 2rem; border-radius: 16px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25); max-width: 400px;">
      <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
      <h2 style="color: #374151; margin-bottom: 1rem;">Erreur</h2>
      <p style="color: #6b7280; margin-bottom: 2rem;">${message}</p>
      <button onclick="goBackToDashboard()" class="btn-primary" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 500; cursor: pointer;">
        <i class="fas fa-arrow-left"></i> Retour au Dashboard
      </button>
    </div>
  </div>
`
  document.body.innerHTML = errorHTML
}

// Système de notifications
function showNotification(message, type = "info") {
  console.log(`📢 Notification ${type}:`, message)

  const notification = document.createElement("div")
  notification.className = `notification ${type}`

  const icons = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
  }

  const colors = {
    success: "linear-gradient(135deg, #10b981, #059669)",
    error: "linear-gradient(135deg, #ef4444, #dc2626)",
    warning: "linear-gradient(135deg, #f59e0b, #d97706)",
    info: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
  }

  notification.innerHTML = `
  <i class="fas ${icons[type]}"></i>
  <span>${message}</span>
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
  padding: 1rem 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  z-index: 20000;
  backdrop-filter: blur(10px);
  animation: slideInRight 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  min-width: 300px;
  max-width: 400px;
  border: 1px solid rgba(255, 255, 255, 0.2);
`

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 4000)
}

// Gestion des événements globaux
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("filter-btn")) {
    const filterText = e.target.textContent.toLowerCase()
    let filter = "all"

    if (filterText.includes("attente")) filter = "pending"
    else if (filterText.includes("examinées")) filter = "reviewed"
    else if (filterText.includes("acceptées")) filter = "accepted"

    filterApplications(filter)
  }
})

// Ajouter les animations CSS
const style = document.createElement("style")
style.textContent = `
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOutRight {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100px);
  }
}
`
document.head.appendChild(style)

console.log("✅ Script job-details-enhanced.js chargé complètement avec compatibilité et modal sombre")
