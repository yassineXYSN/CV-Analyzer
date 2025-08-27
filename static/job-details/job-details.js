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
        
        // Debug complet de la réponse API
        console.log("🔍 DEBUG API RESPONSE:")
        console.log("   - Result success:", result.success)
        console.log("   - Result job:", result.job)
        console.log("   - Result job.applications:", result.job.applications)
        console.log("   - Applications variable:", applications)
        console.log("   - Applications type:", typeof applications)
        console.log("   - Applications is array:", Array.isArray(applications))
        if (applications && applications.length > 0) {
          console.log("   - First application:", applications[0])
        }
        
        // Vérifier si les applications sont vides et pourquoi
        if (!applications || applications.length === 0) {
          console.warn("⚠️ Aucune candidature trouvée pour ce poste")
          console.warn("   - Vérifier si le poste a des candidatures en base")
          console.warn("   - Vérifier les permissions d'accès")
          console.warn("   - Vérifier la requête base de données")
          
          // Debug supplémentaire pour identifier le problème
          console.log("🔍 DEBUG APPLICATIONS VIDE:")
          console.log("   - Result.job existe?", !!result.job)
          console.log("   - Result.job.applications existe?", !!result.job.applications)
          console.log("   - Result.job.applications type:", typeof result.job.applications)
          console.log("   - Result.job.applications length:", result.job.applications?.length)
          console.log("   - Result.job.applications contenu:", result.job.applications)
          
          // FALLBACK: Essayer de récupérer les candidatures directement
          console.log("🔄 Tentative de récupération directe des candidatures...")
          try {
            const appsResponse = await fetch(`/api/applications?job_id=${jobId}`)
            const appsResult = await appsResponse.json()
            
            if (appsResult.success && appsResult.applications) {
              console.log("✅ Candidatures récupérées directement:", appsResult.applications.length)
              console.log("🔍 Structure des candidatures récupérées:", appsResult.applications[0])
              applications = appsResult.applications
            } else {
              console.warn("⚠️ Échec récupération directe des candidatures:", appsResult.message)
            }
          } catch (error) {
            console.error("❌ Erreur récupération directe des candidatures:", error)
          }
        }
        
        // Log final applications count
        console.log("📊 Applications finales après fallback:", applications.length)
        
        // Debug each application structure
        if (applications && applications.length > 0) {
          console.log("🔍 DEBUG STRUCTURE APPLICATIONS:")
          applications.forEach((app, index) => {
            console.log(`   Application ${index}:`, {
              id: app.id,
              name: app.name,
              candidate_name: app.candidate_name,
              title: app.title,
              candidate_title: app.candidate_title,
              email: app.email,
              candidate_email: app.candidate_email,
              status: app.status,
              application_date: app.application_date,
              hr_rating: app.hr_rating,
              is_recommended: app.is_recommended,
              recommendation_priority: app.recommendation_priority,
              recommended_by: app.recommended_by,
              compatibility_percentage: app.compatibility_percentage,
              matched_skills_count: app.matched_skills_count,
              missing_skills_count: app.missing_skills_count,
              total_job_skills: app.total_job_skills,
              raw: app
            })
          })
        }
        
        // Debug the job structure
        console.log("🔍 Structure complète du job:", currentJob)
        console.log("🔍 Skills du job:", currentJob.skills)
        console.log("🔍 Type de skills:", typeof currentJob.skills)
        if (currentJob.skills) {
          console.log("🔍 Skills est un array?", Array.isArray(currentJob.skills))
          console.log("🔍 Longueur skills:", currentJob.skills?.length)
        }
        
        // Debug complet de la structure des données
        console.log("🔍 DEBUG COMPLET - Structure des données reçues:")
        console.log("   - Job ID:", currentJob.id)
        console.log("   - Job Title:", currentJob.title)
        console.log("   - Job Skills:", currentJob.skills)
        console.log("   - Applications count:", applications.length)
        if (currentJob.skills && Array.isArray(currentJob.skills)) {
          console.log("   - Skills structure:")
          currentJob.skills.forEach((skill, index) => {
            console.log(`     Skill ${index}:`, {
              name: skill.name,
              level: skill.level,
              required: skill.required,
              skill_name: skill.skill_name,
              skill_level: skill.skill_level,
              is_required: skill.is_required,
              raw: skill
            })
          })
        }

        // NOUVEAU: Calculer la compatibilité pour chaque candidature
        if (applications && applications.length > 0) {
          console.log("🧮 Calcul de compatibilité pour", applications.length, "candidatures")
          await calculateCompatibilityForApplications()
        } else {
          console.log("⚠️ Aucune candidature à traiter pour la compatibilité")
        }

        hideLoading()
        
        try {
          displayJobInfo()
        } catch (error) {
          console.error("❌ Erreur lors de l'affichage des informations du job:", error)
          showError("Erreur lors de l'affichage des données")
        }
        
        // Safe rendering with error handling
        try {
          console.log("🎨 Rendu des candidatures avec", applications.length, "candidatures")
          renderApplicationsWithCompatibility()
        } catch (error) {
          console.error("❌ Erreur lors du rendu des candidatures:", error)
        }
        
        try {
          updateCompatibilityStats()
        } catch (error) {
          console.error("❌ Erreur lors de la mise à jour des stats:", error)
        }
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
      // Debug the application structure
      console.log(`🔍 Application ${i}:`, {
        id: app.id,
        name: app.name,
        candidate_name: app.candidate_name,
        status: app.status,
        raw: app
      })
      
      const candidateName = app.name || app.candidate_name || "Candidat inconnu"
      console.log(`📊 Calcul compatibilité pour ${candidateName}`)
      
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
    const avgElement = document.getElementById("averageCompatibility")
    if (avgElement) {
      avgElement.textContent = "--"
    }
    return
  }

  const totalCompatibility = applications.reduce((sum, app) => sum + (app.compatibility_percentage || 0), 0)
  const averageCompatibility = Math.round(totalCompatibility / applications.length)

  const avgElement = document.getElementById("averageCompatibility")
  if (avgElement) {
    avgElement.textContent = `${averageCompatibility}%`
    console.log(`📊 Compatibilité moyenne: ${averageCompatibility}%`)
  } else {
    console.warn("⚠️ Élément averageCompatibility non trouvé dans le DOM")
  }
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

  // Log the skills data structure to debug
  console.log("📦 Skills data structure:", currentJob.skills)
  
  // Debug each skill object individually
  if (currentJob.skills && Array.isArray(currentJob.skills)) {
    currentJob.skills.forEach((skill, index) => {
      console.log(`🔍 Skill ${index}:`, skill)
      console.log(`   - Type:`, typeof skill)
      console.log(`   - Keys:`, Object.keys(skill || {}))
      console.log(`   - name:`, skill?.name)
      console.log(`   - level:`, skill?.level)
      console.log(`   - required:`, skill?.required)
      console.log(`   - skill_name (legacy):`, skill?.skill_name)
      console.log(`   - skill_level (legacy):`, skill?.skill_level)
      console.log(`   - is_required (legacy):`, skill?.is_required)
    })
  }

  // Validate skills data structure
  if (!Array.isArray(currentJob.skills)) {
    console.warn("⚠️ Skills data is not an array:", typeof currentJob.skills)
    skillsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-exclamation-triangle"></i>
          <h4>Erreur de données</h4>
          <p>Format des compétences invalide. Veuillez contacter l'administrateur.</p>
        </div>
      `
    return
  }

  // Filter out invalid skill objects
  const validSkills = currentJob.skills.filter(skill => {
    if (!skill || typeof skill !== 'object') {
      console.warn("⚠️ Skill invalide ignoré:", skill)
      return false
    }
    return true
  })

  if (validSkills.length === 0) {
    skillsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-tools"></i>
          <h4>Aucune compétence valide</h4>
          <p>Aucune compétence valide trouvée dans les données.</p>
        </div>
      `
    return
  }

  console.log(`🔍 ${validSkills.length} compétences valides trouvées sur ${currentJob.skills.length} total`)

  skillsContainer.innerHTML = `
      <div class="skills-grid">
        ${validSkills
          .map(
            (skill) => {
              try {
                // Safe access to skill properties with fallbacks
                const skillName = skill.name || skill.skill_name || skill.skill || "Compétence non spécifiée"
                const skillLevel = skill.level || skill.skill_level || skill.experience || "N/A"
                const isRequired = skill.required !== undefined ? skill.required : skill.is_required !== undefined ? skill.is_required : true
                
                // Safely format skill level
                let formattedLevel = "N/A"
                if (skillLevel && typeof skillLevel === 'string' && skillLevel.length > 0) {
                  try {
                    formattedLevel = skillLevel.charAt(0).toUpperCase() + skillLevel.slice(1)
                  } catch (error) {
                    console.warn("⚠️ Erreur formatage niveau compétence:", error)
                    formattedLevel = skillLevel
                  }
                }

                return `
                  <div class="skill-item">
                    <div class="skill-name">${skillName}</div>
                    <div class="skill-level">${formattedLevel}</div>
                    ${
                      isRequired
                        ? `<span class="skill-required-badge">Requis</span>`
                        : `<span class="skill-optional-badge">Optionnel</span>`
                    }
                  </div>
                `
              } catch (error) {
                console.error("❌ Erreur rendu skill principal:", error, skill)
                return `
                  <div class="skill-item error">
                    <div class="skill-name">Erreur affichage</div>
                    <div class="skill-level">N/A</div>
                    <span class="skill-optional-badge">Erreur</span>
                  </div>
                `
              }
            }
          )
          .join("")}
      </div>
    `
  console.log(`✅ ${validSkills.length} compétences affichées`)
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
      <div style="margin-top: 1rem; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px; font-size: 0.9rem;">
        <strong>Debug Info:</strong><br>
        - Applications array length: ${applications.length}<br>
        - Filter applied: ${filter}<br>
        - Job ID: ${currentJob?.id || 'N/A'}<br>
        - Job Title: ${currentJob?.title || 'N/A'}
      </div>
    </div>
  `
    return
  }

  container.innerHTML = filteredApplications
    .map((app) => {
      // Handle different data structures from different API endpoints
      const candidateName = app.name || app.candidate_name || "Candidat inconnu"
      const candidateTitle = app.title || app.candidate_title || "Candidat"
      const candidateEmail = app.email || app.candidate_email || "Email non disponible"
      const applicationDate = app.application_date || app.application_date || new Date().toISOString()
      const hrRating = app.hr_rating || app.hr_rating || null
      const isRecommended = app.is_recommended || false
      const recommendationPriority = app.recommendation_priority || "normal"
      const recommendedBy = app.recommended_by || null
      const compatibilityPercentage = app.compatibility_percentage || 0
      
      console.log(`🔍 Rendu candidature ${candidateName} avec compatibilité ${compatibilityPercentage}%`)

      return `
      <div class="application-item-detailed ${isRecommended ? "has-recommendation" : ""}">
        <div class="candidate-info">
          <div class="candidate-avatar">${candidateName
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="candidate-details">
            <div class="candidate-name-section">
              <div class="candidate-name">
                ${candidateName}
                ${
                  isRecommended
                    ? `
                  <span class="recommendation-badge ${recommendationPriority}" 
                       title="Candidat recommandé par ${recommendedBy || "un chef de département"}">
                    <i class="fas fa-star"></i> 
                    ${
                      recommendationPriority === "urgent"
                        ? "URGENT"
                        : recommendationPriority === "high"
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
                    isRecommended && recommendationPriority !== "normal"
                      ? `<span class="priority-indicator ${recommendationPriority}">
                      ${recommendationPriority === "urgent" ? "" : ""}
                    </span>`
                      : ""
                  }
                </div>
              </div>
            </div>
            
            <div class="candidate-title">${candidateTitle}</div>
            <div class="candidate-meta">
              <span class="application-date">
                Candidature: ${new Date(applicationDate).toLocaleDateString("fr-FR")}
              </span>
              ${hrRating ? `<span class="hr-rating">Note HR: ${hrRating}/5 ⭐</span>` : ""}
              ${
                isRecommended && recommendedBy
                  ? `<span class="recommendation-info">
                      <i class="fas fa-user-tie"></i> Recommandé par ${recommendedBy}
                      ${app.recommendation_date ? ` le ${new Date(app.recommendation_date).toLocaleDateString("fr-FR")}` : ""}
                    </span>`
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
            <div class="compatibility-percentage ${getCompatibilityClass(compatibilityPercentage)}">
              ${compatibilityPercentage}%
              <i class="fas fa-${getCompatibilityIcon(compatibilityPercentage)}"></i>
            </div>
          </div>
          
          <div class="compatibility-progress">
            <div class="compatibility-progress-bar ${getCompatibilityClass(compatibilityPercentage)}" 
                 style="width: ${compatibilityPercentage}%"></div>
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
            <button class="btn-compatibility-details" onclick="viewCompatibilityDetails(${app.id}, ${app.compatibility_percentage || 0}, '${app.compatibility_source || 'calculated'}', '${app.compatibility_reason || ''}')">
              <i class="fas fa-search"></i> Détails compatibilité
              ${app.compatibility_source === 'ai' ? ' <i class="fas fa-robot" title="Analyse IA"></i>' : ''}
            </button>
          </div>
        </div>

        <div class="application-status-section">
          <div class="status-badge ${app.status}">
            ${getStatusText(app.status)}
            ${
              isRecommended && recommendationPriority !== "normal"
                ? `<span class="priority-indicator ${recommendationPriority}">
                ${recommendationPriority === "urgent" ? "🔥" : ""}
              </span>`
                : ""
            }
          </div>
          <div class="application-actions">
            ${renderCandidateActions(app)}
          </div>
        </div>
        
        ${
          isRecommended && app.recommendation_comment
            ? `
          <div class="recommendation-comment">
            <i class="fas fa-comment-alt"></i>
            <strong style="color:black">Commentaire de recommandation:</strong>
            <p>"${app.recommendation_comment}"</p>
            ${recommendedBy ? `<small>— ${recommendedBy}</small>` : ""}
          </div>
        `
            : ""
        }
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
async function viewCompatibilityDetails(applicationId, compatibilityPercentage, compatibilitySource, compatibilityReason) {
  console.log("🔍 Affichage détails compatibilité pour candidature:", applicationId)

  try {
    showLoading("Chargement des détails de compatibilité...")

    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()

    hideLoading()

    if (result.success) {
      showDarkCompatibilityModal(result, compatibilityPercentage, compatibilitySource, compatibilityReason)
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
function showDarkCompatibilityModal(compatibilityData, compatibilityPercentage, compatibilitySource, compatibilityReason) {
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
            <div class="score-circle ${getCompatibilityClass(compatibilityPercentage)}" style="
              width: 120px;
              height: 120px;
              border-radius: 50%;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              background: conic-gradient(
                ${
                  compatibilityPercentage >= 75
                    ? "#10b981"
                    : compatibilityPercentage >= 50
                      ? "#f59e0b"
                      : compatibilityPercentage >= 25
                        ? "#ef4444"
                        : "#6b7280"
                } 
                ${compatibilityPercentage * 3.6}deg,
                rgba(255, 255, 255, 0.1) 0deg
              );
              position: relative;
            ">
              <div style="
                position: absolute;
                inset: 8px;
                background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border-radius: 50%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: white;
              ">
                <div style="font-size: 1.5rem; font-weight: 700;">${compatibilityPercentage}%</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">Compatibilité</div>
              </div>
            </div>
          </div>
          
          <div class="compatibility-summary">
            <h4 style="margin: 0 0 1rem 0; color: #f8fafc; display: flex; align-items: center; gap: 0.75rem;">
              <i class="fas fa-chart-pie" style="color: #3b82f6;"></i>
              Résumé de Compatibilité
              ${compatibilitySource === 'ai' ? '<i class="fas fa-robot" style="color: #10b981; margin-left: 0.5rem;" title="Analyse IA"></i>' : ''}
            </h4>
            
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
        
        ${compatibilitySource === 'ai' && compatibilityReason ? `
        <!-- AI Analysis Section -->
        <div class="ai-analysis-section" style="
          margin-bottom: 2rem;
          padding: 2rem;
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 16px;
        ">
          <div class="ai-analysis-header" style="
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
          ">
            <i class="fas fa-robot" style="color: #10b981; font-size: 1.5rem;"></i>
            <h4 style="margin: 0; color: #f8fafc; font-size: 1.3rem;">
              Analyse IA de Compatibilité
            </h4>
            <span class="ai-badge" style="
              background: linear-gradient(135deg, #10b981, #059669);
              color: white;
              padding: 0.25rem 0.75rem;
              border-radius: 20px;
              font-size: 0.8rem;
              font-weight: 600;
            ">
              IA
            </span>
          </div>
          
          <div class="ai-analysis-content" style="
            background: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
          ">
            <p style="
              color: #f8fafc;
              line-height: 1.6;
              margin: 0;
              font-size: 1rem;
            ">
              ${compatibilityReason}
            </p>
          </div>
        </div>
        ` : `
        <!-- Skills Breakdown Section (for calculated compatibility) -->
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
                  (skill) => {
                    try {
                      return `
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
                    ">${skill.name || skill.skill_name || "Compétence non spécifiée"}</span>
                    <span class="skill-level ${skill.level || skill.skill_level || "intermediate"}" style="
                      color: #cbd5e1;
                      font-size: 0.9rem;
                      margin-right: 0.5rem;
                    ">${getLevelText(skill.level || skill.skill_level || "intermediate")}</span>
                    <span class="skill-required ${(skill.required !== undefined ? skill.required : skill.is_required) ? "required" : "optional"}" style="
                      color: ${(skill.required !== undefined ? skill.required : skill.is_required) ? "#f59e0b" : "#6b7280"};
                      font-size: 0.8rem;
                      font-weight: 500;
                    ">
                      ${(skill.required !== undefined ? skill.required : skill.is_required) ? "Requis" : "Optionnel"}
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
              `
                    } catch (error) {
                      console.error("❌ Erreur rendu skill correspondant:", error, skill)
                      return `
                <div class="skill-item error" style="
                  padding: 1rem;
                  margin: 0.5rem 0;
                  background: rgba(239, 68, 68, 0.1);
                  border: 1px solid rgba(239, 68, 68, 0.3);
                  border-radius: 12px;
                  color: #ef4444;
                ">
                  Erreur affichage compétence
                </div>
              `
                    }
                  }
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
                  (skill) => {
                    try {
                      return `
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
                    ">${skill.name || skill.skill_name || "Compétence non spécifiée"}</span>
                    <span class="skill-level ${skill.level || skill.skill_level || "intermediate"}" style="
                      color: #cbd5e1;
                      font-size: 0.9rem;
                      margin-right: 0.5rem;
                    ">${getLevelText(skill.level || skill.skill_level || "intermediate")}</span>
                    <span class="skill-required ${(skill.required !== undefined ? skill.required : skill.is_required) ? "required" : "optional"}" style="
                      color: ${(skill.required !== undefined ? skill.required : skill.is_required) ? "#f59e0b" : "#6b7280"};
                      font-size: 0.8rem;
                      font-weight: 500;
                    ">
                      ${(skill.required !== undefined ? skill.required : skill.is_required) ? "Requis" : "Optionnel"}
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
              `
                    } catch (error) {
                      console.error("❌ Erreur rendu skill manquant:", error, skill)
                      return `
                <div class="skill-item error" style="
                  padding: 1rem;
                  margin: 0.5rem 0;
                  background: rgba(239, 68, 68, 0.1);
                  border: 1px solid rgba(239, 68, 68, 0.3);
                  border-radius: 12px;
                  color: #ef4444;
                ">
                  Erreur affichage compétence
                </div>
              `
                    }
                  }
                )
                .join("")}
            </div>
          </div>
        </div>
        `}
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
  // Handle different data structures from different API endpoints
  const candidateName = app.name || app.candidate_name || "Candidat inconnu"
  const candidateId = app.candidate_id || app.candidate_profile_id || app.id
  
  console.log(`🎯 Rendu actions pour ${candidateName}:`, {
    userRole: currentUser?.role,
    currentUser: currentUser,
    appStatus: app.status,
    isRecommended: app.is_recommended,
  })

  if (currentUser && currentUser.role === "department_head") {
    // ... (le code existant pour les chefs de département)
  }

  // Pour les recruteurs
  if (currentUser && currentUser.role === "recruiter") {
    console.log(`🎯 Rendu actions recruteur pour ${candidateName}, status: ${app.status}`)
    
    if (app.status === "pending") {
      const actions = `
      <button class="btn-action review" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-eye"></i> Examiner
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || 'Département'}')">
        <i class="fas fa-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
      console.log(`🎯 Actions pending générées:`, actions)
      return actions
    } else if (app.status === "reviewed") {
      return `
      <button class="btn-action schedule" onclick="updateApplicationStatus(${app.id}, 'interview_scheduled')">
        <i class="fas fa-calendar"></i> Programmer entretien
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || 'Département'}')">
        <i class="fas fa-check-circle"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
    } else if (app.status === "interview_scheduled") {
      return `
      <button class="btn-action complete" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-check-double"></i> Entretien terminé
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || 'Département'}')">
        <i class="fas fa-user-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
    } else if (app.status === "accepted_pending_validation") {
      return `
      <span class="status-badge pending-validation">
        <i class="fas fa-clock"></i> En attente validation admin
      </span>
    `
    }
  }

  // Pour les administrateurs
  if (currentUser && currentUser.role === "super_admin") {
    if (app.status === "accepted_pending_validation") {
      return `
      <button class="btn-action validate" onclick="showAdminValidationModal(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-user-shield"></i> Valider
      </button>
      <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
    `
    } else if (app.status === "pending" || app.status === "reviewed" || app.status === "interview_scheduled") {
      return `
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || 'Département'}')">
        <i class="fas fa-check"></i> Accepter définitivement
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
      <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
    `
    }
  }

  // Pour tous les autres cas
  return `
  <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
    <i class="fas fa-info-circle"></i> Voir profil
  </button>
`
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
    accepted_pending_validation: "accepted_pending_validation"
  }
  return statusTexts[status] || status
}

// Fonction pour afficher la modal de validation admin
function showAdminValidationModal(applicationId, candidateName, jobTitle) {
  console.log(`👑 Affichage validation admin pour ${candidateName}`)

  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.opacity = "1"

  modal.innerHTML = `
  <div class="confirmation-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="confirmation-icon validate">
          <i class="fas fa-user-shield"></i>
        </div>
        <h3>Validation Administrateur</h3>
        <p>Valider définitivement <strong>${candidateName}</strong> pour le poste</p>
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
        <p><strong>En tant qu'administrateur, votre validation est définitive :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            <li><i class="fas fa-user-plus"></i> Création automatique de l'employé</li>
            <li><i class="fas fa-briefcase"></i> Attribution du poste</li>
            <li><i class="fas fa-check-circle"></i> Marquage du poste comme pourvu</li>
            <li><i class="fas fa-times-circle"></i> Rejet automatique des autres candidatures</li>
            <li><i class="fas fa-envelope"></i> Envoi des notifications au candidat</li>
          </ul>
        </div>
        <div class="warning-note">
          <i class="fas fa-exclamation-triangle"></i>
          <p>Cette action est irréversible. Le candidat sera intégré en tant qu'employé.</p>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm validate" onclick="confirmAdminValidation(${applicationId})">
          <i class="fas fa-user-shield"></i> Valider Définitivement
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

// Fonction pour confirmer la validation admin
async function confirmAdminValidation(applicationId) {
  console.log(`✅ Confirmation validation admin candidature ${applicationId}`)

  try {
    closeConfirmationModal()
    showLoading("Validation en cours...")

    const response = await fetch(`/api/accept-application/${applicationId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: "accepted" })
    })

    const result = await response.json()
    hideLoading()

    if (response.ok && result.success) {
      showNotification("Candidat validé et employé créé avec succès", "success")
      setTimeout(() => {
        loadJobData()
      }, 1000)
    } else {
      showNotification(result.message || "Erreur lors de la validation", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur validation admin:", error)
    showNotification("Erreur de connexion lors de la validation", "error")
  }
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

  const isAdmin = currentUser && currentUser.role === "super_admin";
  const modalTitle = isAdmin ? "Accepter définitivement" : "Accepter la candidature";
  const modalDescription = isAdmin 
    ? "En tant qu'administrateur, votre acceptation sera définitive et créera immédiatement l'employé."
    : "Votre acceptation devra être validée par un administrateur avant la création de l'employé.";

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
        <h3>${modalTitle}</h3>
        <p>${modalDescription}</p>
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
        <p><strong>Processus d'acceptation :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            ${isAdmin ? `
            <li><i class="fas fa-user-plus"></i> Création automatique de l'employé</li>
            <li><i class="fas fa-briefcase"></i> Attribution du poste</li>
            <li><i class="fas fa-check-circle"></i> Marquage du poste comme pourvu</li>
            <li><i class="fas fa-times-circle"></i> Rejet automatique des autres candidatures</li>
            ` : `
            <li><i class="fas fa-check-circle"></i> Candidature marquée comme acceptée</li>
            <li><i class="fas fa-user-shield"></i> Envoi pour validation administrateur</li>
            <li><i class="fas fa-clock"></i> En attente d'approbation finale</li>
            `}
          </ul>
        </div>
        <div class="info-note">
          <i class="fas fa-info-circle"></i>
          <p>${isAdmin 
            ? "Cette action est définitive. Le candidat sera intégré en tant qu'employé." 
            : "La candidature sera envoyée à l'administrateur pour validation finale avant création de l'employé."}</p>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm" onclick="confirmAcceptApplication(${applicationId})">
          <i class="fas fa-check"></i> ${isAdmin ? "Confirmer l'acceptation définitive" : "Confirmer l'acceptation"}
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
// Fonction pour confirmer l'acceptation
async function confirmAcceptApplication(applicationId) {
  try {
    closeConfirmationModal()
    showLoading("Traitement de l'acceptation...")

    // Déterminer le statut en fonction du rôle
    let targetStatus = "accepted";
    if (currentUser && currentUser.role === "recruiter") {
      targetStatus = "accepted_pending_validation";
    }

    const response = await fetch(`/api/accept-application/${applicationId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: targetStatus })
    })

    const result = await response.json()
    hideLoading()

    if (response.ok && result.success) {
      const message = targetStatus === "accepted_pending_validation" 
        ? "Candidature acceptée, en attente de validation admin" 
        : "Candidat accepté avec succès";
      
      showNotification(message, "success")
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

// NOUVELLE FONCTION: Créer des candidatures de démonstration
async function createDemoApplications() {
  try {
    console.log("🔧 Création de candidatures de démonstration...")
    
    const response = await fetch("/api/applications/create-demo", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const result = await response.json()
    
    if (result.success) {
      console.log("✅ Candidatures demo créées:", result.message)
      showNotification(result.message, "success")
      
      // Recharger les données du job pour afficher les nouvelles candidatures
      if (currentJob && currentJob.id) {
        console.log("🔄 Rechargement des données du job...")
        await loadJobFromAPI(currentJob.id)
      }
    } else {
      console.error("❌ Erreur création candidatures demo:", result.message)
      showError(result.message || "Erreur lors de la création des candidatures demo")
    }
  } catch (error) {
    console.error("❌ Erreur réseau création candidatures demo:", error)
    showError("Erreur de connexion lors de la création des candidatures demo")
  }
}

// NOUVELLE FONCTION: Vérifier manuellement les candidatures en base
async function debugApplications() {
  try {
    console.log("🔍 Vérification manuelle des candidatures en base...")
    
    if (!currentJob || !currentJob.id) {
      console.error("❌ Aucun job chargé pour la vérification")
      return
    }
    
    // Vérifier directement les candidatures pour ce job
    const response = await fetch(`/api/applications?job_id=${currentJob.id}`)
    const result = await response.json()
    
    console.log("🔍 DEBUG APPLICATIONS DIRECT:")
    console.log("   - Response status:", response.status)
    console.log("   - Response result:", result)
    
    if (result.success) {
      console.log("   - Applications trouvées:", result.applications?.length || 0)
      if (result.applications && result.applications.length > 0) {
        console.log("   - Première candidature:", result.applications[0])
      }
    } else {
      console.log("   - Erreur API:", result.message)
    }
    
  } catch (error) {
    console.error("❌ Erreur vérification candidatures:", error)
  }
}
