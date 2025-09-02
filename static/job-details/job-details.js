// Variables globales
let currentJob = null
let applications = []
let allCandidates = []
let currentUser = null

// Focused date debugging and safe formatting helpers
const DATE_DEBUG = true
const dateLog = (...args) => {
  if (DATE_DEBUG) console.log(...args)
}
function formatDateSafe(input, locale = "fr-FR") {
  try {
    if (!input) return "--"
    let value = input
    if (typeof value === "string" && value.indexOf(" ") > -1 && value.indexOf("T") === -1) {
      value = value.replace(" ", "T")
    }
    const d = new Date(value)
    if (isNaN(d.getTime())) return "--"
    return d.toLocaleDateString(locale)
  } catch (_e) {
    return "--"
  }
}

// Fonction pour formater la durée du quiz
function formatDuration(seconds) {
  if (!seconds || seconds === 0) return "N/A"
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  if (minutes === 0) {
    return `${remainingSeconds}s`
  } else if (remainingSeconds === 0) {
    return `${minutes}min`
  } else {
    return `${minutes}min ${remainingSeconds}s`
  }
}

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
        // Initialiser l'état de validation des compétences après le rendu
        setTimeout(() => {
          initializeSkillsValidationState()
        }, 100)
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

    const response = await fetch(`/api/job-basic/${jobId}`)
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
              raw: app,
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
            const skill_level = skill.skill_level
            const is_required = skill.is_required
            const skill_name = skill.skill_name
            console.log(`     Skill ${index}:`, {
              name: skill.name,
              level: skill.level,
              required: skill.required,
              skill_name: skill_name,
              skill_level: skill_level,
              is_required: is_required,
              raw: skill,
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
          console.log("🔍 DEBUG - Applications avant rendu:", applications)
          renderApplicationsWithCompatibility()
          // Initialiser l'état de validation des compétences après le rendu
          setTimeout(() => {
            initializeSkillsValidationState()
          }, 100)
        } catch (error) {
          console.error("❌ Erreur lors du rendu des candidatures:", error)
          console.error("❌ Stack trace:", error.stack)
        }

        try {
          updateCompatibilityStats()
        } catch (error) {
          console.error("❌ Erreur lors de la mise à jour des stats:", error)
        }

        try {
          updateFilterCounts()
        } catch (error) {
          console.error("❌ Erreur lors de la mise à jour des compteurs de filtres:", error)
        }

        // Refresh validation button states after applications are loaded
        setTimeout(() => {
          // Validation button states removed
        }, 200)
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
  setTimeout(() => {
    initializeSkillsValidationState()
    initializeQuizValidationState() // Ajoutez cette ligne
  }, 100)
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
        raw: app,
      })

      const candidateName = app.name || app.candidate_name || "Candidat inconnu"
      console.log(`📊 Calcul compatibilité pour ${candidateName}`)

      const response = await fetch(`/api/application/${app.id}/compatibility`)
      const result = await response.json()

      if (result.success) {
        // Mettre à jour les données de compatibilité
        applications[i].compatibility_percentage = result.compatibility_percentage || result.score || 0

        // Extraire les compteurs de compétences avec fallback
        applications[i].matched_skills_count =
          result.matched_count ||
          result.matched_skills_count ||
          (result.matched_skills ? result.matched_skills.length : 0)

        applications[i].missing_skills_count =
          result.missing_count ||
          result.missing_skills_count ||
          (result.missing_skills ? result.missing_skills.length : 0)

        applications[i].total_job_skills =
          result.total_job_skills ||
          result.total_skills ||
          applications[i].matched_skills_count + applications[i].missing_skills_count

        applications[i].matched_skills = result.matched_skills || []
        applications[i].missing_skills = result.missing_skills || []

        // Si les compteurs sont toujours 0, utiliser le fallback
        if (applications[i].matched_skills_count === 0 && applications[i].missing_skills_count === 0) {
          const fallback = calculateCompatibilityFallback(
            applications[i].compatibility_percentage,
            applications[i].total_job_skills || currentJob.skills?.length || 0,
          )
          applications[i].matched_skills_count = fallback.matched
          applications[i].missing_skills_count = fallback.missing
          applications[i].total_job_skills = applications[i].total_job_skills || currentJob.skills?.length || 0
        }

        console.log(
          `✅ ${candidateName}: ${applications[i].compatibility_percentage}% - ${applications[i].matched_skills_count} matchés, ${applications[i].missing_skills_count} manquants`,
        )
      } else {
        console.warn(`⚠️ Erreur calcul compatibilité pour ${app.name}:`, result.message)
        // Fallback si l'API échoue
        const fallback = calculateCompatibilityFallback(
          app.compatibility_percentage || 0,
          currentJob.skills?.length || 0,
        )
        applications[i].compatibility_percentage = app.compatibility_percentage || 0
        applications[i].matched_skills_count = fallback.matched
        applications[i].missing_skills_count = fallback.missing
        applications[i].total_job_skills = currentJob.skills?.length || 0
      }
    } catch (error) {
      console.error(`❌ Erreur réseau compatibilité pour ${app.name}:`, error)
      // Fallback en cas d'erreur réseau
      const fallback = calculateCompatibilityFallback(app.compatibility_percentage || 0, currentJob.skills?.length || 0)
      applications[i].compatibility_percentage = app.compatibility_percentage || 0
      applications[i].matched_skills_count = fallback.matched
      applications[i].missing_skills_count = fallback.missing
      applications[i].total_job_skills = currentJob.skills?.length || 0
    }

    // Debug final pour chaque application
    console.log(`Application ${i} finale:`, {
      compatibility: applications[i].compatibility_percentage,
      matched: applications[i].matched_skills_count,
      missing: applications[i].missing_skills_count,
      total: applications[i].total_job_skills,
    })
  }

  console.log("✅ Calcul de compatibilité terminé pour toutes les candidatures")
}

// Ajouter cette fonction utilitaire
function calculateCompatibilityFallback(compatibilityPercentage, totalSkills) {
  if (!totalSkills || totalSkills === 0) return { matched: 0, missing: 0 }

  const matched = Math.round((compatibilityPercentage / 100) * totalSkills)
  const missing = totalSkills - matched

  return { matched, missing }
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
      const formattedDeadline = currentJob.deadline ? formatDateSafe(currentJob.deadline) : "Non définie"
      deadlineElement.textContent = formattedDeadline
      dateLog("[DATE] deadline:", currentJob.deadline, "->", formattedDeadline)
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
      const formattedCreated = formatDateSafe(currentJob.created_at)
      jobCreatedElement.textContent = formattedCreated
      dateLog("[DATE] created_at:", currentJob.created_at, "->", formattedCreated)
    }

    const assignedEmployeeElement = document.getElementById("assignedEmployee")
    if (assignedEmployeeElement) {
      assignedEmployeeElement.textContent = currentJob.assigned_employee_name || "Non assigné"
    }

    const applicationsElement = document.getElementById("jobApplications")
    if (applicationsElement) {
      const count =
        typeof currentJob.applications_count === "number" && !isNaN(currentJob.applications_count)
          ? currentJob.applications_count
          : Array.isArray(applications)
            ? applications.length
            : 0
      applicationsElement.textContent = count
      if (typeof currentJob.applications_count === "undefined") {
        console.warn("⚠️ applications_count missing, using applications.length:", count)
      }
    }

    const daysRemainingElement = document.getElementById("daysRemaining")
    if (daysRemainingElement) {
      try {
        let days = currentJob.days_remaining
        if (days === null || days === undefined) {
          // Fallback: compute from deadline
          if (currentJob.deadline) {
            let deadlineStr = currentJob.deadline
            if (typeof deadlineStr === "string" && deadlineStr.indexOf(" ") > -1 && deadlineStr.indexOf("T") === -1) {
              deadlineStr = deadlineStr.replace(" ", "T")
            }
            const deadlineDate = new Date(deadlineStr)
            if (!isNaN(deadlineDate.getTime())) {
              const today = new Date()
              const diffMs = deadlineDate.setHours(0, 0, 0, 0) - today.setHours(0, 0, 0, 0)
              days = Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)))
              console.warn("ℹ️ days_remaining missing, computed from deadline:", days)
            }
          }
        }
        daysRemainingElement.textContent = days !== null && days !== undefined ? days : "--"
      } catch (e) {
        console.error("❌ Error computing days_remaining:", e)
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
  const validSkills = currentJob.skills.filter((skill) => {
    if (!skill || typeof skill !== "object") {
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
          .map((skill) => {
            try {
              // Safe access to skill properties with fallbacks
              const skillName = skill.name || skill.skill_name || skill.skill || "Compétence non spécifiée"
              const skillLevel = skill.level || skill.skill_level || skill.experience || "N/A"
              const isRequired =
                skill.required !== undefined
                  ? skill.required
                  : skill.is_required !== undefined
                    ? skill.is_required
                    : true

              // Safely format skill level
              let formattedLevel = "N/A"
              if (skillLevel && typeof skillLevel === "string" && skillLevel.length > 0) {
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
          })
          .join("")}
      </div>
    `
  console.log(`✅ ${validSkills.length} compétences affichées`)
}

// Fonction pour initialiser l'état de validation des compétences
function initializeSkillsValidationState() {
  console.log("🔧 Initialisation de l'état de validation des compétences")
  
  applications.forEach(app => {
    const quizSection = document.getElementById(`quiz-section-${app.id}`)
    const validateBtn = document.getElementById(`validate-btn-${app.id}`)
    const validationStatus = document.getElementById(`validation-status-${app.id}`)
    
    if (app.skills_validated) {
      // Si les compétences sont déjà validées, retirer l'overlay et mettre à jour le bouton
      if (quizSection) {
        quizSection.classList.remove("locked")
        const overlay = quizSection.querySelector(".quiz-validation-overlay")
        if (overlay) {
          overlay.remove()
        }
      }
      
      if (validateBtn) {
        validateBtn.classList.add("validated")
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Validé'
        validateBtn.disabled = true
      }
      
      if (validationStatus) {
        validationStatus.classList.add("success")
      }
    }
  })
}

function renderApplicationsWithCompatibility(filter = "all") {
  console.log(`👥 Rendu des candidatures avec compatibilité (filtre: ${filter})`)
  console.log(`🔍 DEBUG - Fonction appelée avec filter: ${filter}`)
  console.log(`🔍 DEBUG - Applications disponibles:`, applications)

  const container = document.getElementById("applicationsList")
  if (!container) {
    console.error("❌ Container applicationsList non trouvé")
    console.error("❌ Container applicationsList non trouvé - DOM non prêt?")
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
      // Handle different data structures from different API endpoints
      const candidateName = app.name || app.candidate_name || "Candidat inconnu"
      const candidateTitle = app.title || app.candidate_title || "Développeuse Full Stack Senior"
      const candidateEmail = app.email || app.candidate_email || "Email non disponible"
      const applicationDateRaw = app.application_date || null
      const applicationDate = formatDateSafe(applicationDateRaw)
      const hrRating = app.hr_rating || app.hr_rating || null
      const isRecommended = app.is_recommended || false
      const recommendationPriority = app.recommendation_priority || "normal"
      const recommendedBy = app.recommended_by || null
      const compatibilityPercentage = app.compatibility_percentage || 92
      const quizScore = app.quiz_score || 0

      // DEBUG DÉTAILLÉ des compteurs de skills
      console.log(`🔍 DEBUG RENDU - ${candidateName}:`, {
        id: app.id,
        compatibility_percentage: app.compatibility_percentage,
        matched_skills_count: app.matched_skills_count,
        missing_skills_count: app.missing_skills_count,
        total_job_skills: app.total_job_skills,
        matched_skills: app.matched_skills,
        missing_skills: app.missing_skills,
        raw_app: app,
      })

      console.log(`🔍 Rendu candidature ${candidateName} avec compatibilité ${compatibilityPercentage}%`)

      // Debug quiz section state
      console.log(`🔍 DEBUG QUIZ SECTION ${app.id}:`, {
        element_id: `quiz-section-${app.id}`,
      })

      return `
      <div class="application-item-detailed ${isRecommended ? "has-recommendation" : ""}" data-app-id="${app.id}">
        <div class="candidate-card-header" onclick="toggleCandidateCard(${app.id})">
          <div class="candidate-basic-info">
            <div class="candidate-avatar">${candidateName
              .split(" ")
              .map((n) => n[0])
              .join("")}</div>
            <div class="candidate-details">
              <div class="candidate-name">
                ${candidateName}
                ${
                  isRecommended
                    ? `<span class="recommendation-badge">
                        <i class="fas fa-star"></i> Recommandé
                       </span>`
                    : ""
                }
              </div>
              <div class="candidate-title">${candidateTitle}</div>
            </div>
          </div>
          
        <div class="candidate-scores-section">
          <div class="score-item compatibility">
            <div class="score-icon">
              <i class="fas fa-star-half-alt"></i>
            </div>
            <div class="score-details">
              <span class="score-value">${app.compatibility_percentage || 0}%</span>
              <span class="score-label">Compétences</span>
            </div>
          </div>
          <div class="score-item quiz">
            <div class="score-icon">
              <i class="fas fa-check-circle"></i>
            </div>
            <div class="score-details">
              <span class="score-value">${app.quiz_score || 0}%</span>
              <span class="score-label">Quiz</span>
            </div>
          </div>
        </div>
          <div class="candidate-status-collapsed">
            <div class="status-badge ${app.status}">
              ${getStatusText(app.status)}
            </div>
            <button class="expand-toggle" onclick="event.stopPropagation()">
              <i class="fas fa-chevron-down"></i>
            </button>
          </div>
        </div>

        <div class="candidate-expanded-content" id="expanded-${app.id}">
          <div class="expanded-details-grid">
            <!-- SECTION 1: ANALYSE DES COMPÉTENCES -->
            <div class="detail-section skills-section">
              <h4>
                <i class="fas fa-chart-line"></i> Analyse des compétences
              </h4>
              
              <div class="skills-content">
                <!-- Progress Bar Section -->
                <div class="skills-progress-section">
                  <div class="progress-header">
                    <span class="progress-label">Niveau de compatibilité</span>
                    <span class="progress-percentage">${app.compatibility_percentage || 0}%</span>
                  </div>
                  <div class="progress-bar-container">
                    <div class="progress-bar ${getCompatibilityClass(app.compatibility_percentage || 0)}" 
                         style="width: ${app.compatibility_percentage || 0}%">
                      <div class="progress-bar-fill"></div>
                    </div>
                  </div>
                </div>
                
                <div class="skills-overview">
                  <div class="skills-info-grid">
                    <div class="skills-info-item">
                      <div class="info-icon">
                        <i class="fas fa-check-circle"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Correspondantes</div>
                        <div class="info-value">${app.matched_skills_count || 0}</div>
                      </div>
                    </div>
                    
                    <div class="skills-info-item">
                      <div class="info-icon">
                        <i class="fas fa-times-circle"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Manquantes</div>
                        <div class="info-value">${app.missing_skills_count || 0}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="skills-actions">
                  <div class="skills-actions-row">
                    <button class="btn-compatibility-details" onclick="viewCompatibilityDetails(${app.id})">
                      <i class="fas fa-chart-bar"></i> Détails compatibilité
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- SECTION 2: QUIZ (VISIBLE SEULEMENT SI COMPÉTENCES VALIDÉES) -->
            <div class="detail-section quiz-section ${!app.skills_validated ? 'locked' : ''}" id="quiz-section-${app.id}">
              
              ${!app.skills_validated ? `
                <div class="quiz-validation-overlay">
                  <div class="quiz-validation-number">2</div>
                  <div class="quiz-validation-message">En attente de validation des compétences</div>
                  <button class="btn-validate-skills-overlay" onclick="validateSkillsAndRemoveOverlay(${app.id})" id="validate-btn-overlay-${app.id}">
                    <i class="fas fa-check-double"></i> Valider les compétences
                  </button>
                </div>
              ` : ''}

              <h4>
                <i class="fas fa-chart-bar"></i> Évaluation Quiz
              </h4>
              
              <div class="quiz-content">
                <div class="quiz-overview">
                  <div class="quiz-info-grid">
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-chart-pie"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Score</div>
                        <div class="info-value">${app.quiz_score || 0}%</div>
                      </div>
                    </div>
                    
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-clock"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Durée</div>
                        <div class="info-value">${app.quiz_duration ? formatDuration(app.quiz_duration) : "N/A"}</div>
                      </div>
                    </div>
                    

                    
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-check-double"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Correctes</div>
                        <div class="info-value">${app.quiz_correct_answers || 0}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="quiz-actions">
                  <div class="quiz-actions-row">
                    <button class="btn-generate-quiz" onclick="openCreateQuizModal(${app.candidate_id || app.candidate_profile_id || app.id}, '${candidateName}')">
                      <i class="fas fa-magic"></i> Générer Quiz
                    </button>
                    <button class="btn-view-quiz" onclick="viewQuizResults(${app.id}, '${candidateName}')">
                      <i class="fas fa-eye"></i> Voir Quiz
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- SECTION 3: PROGRAMMATION D'ENTRETIEN -->
            <div class="detail-section interview-section ${!app.quiz_validated ? 'locked' : ''}" id="interview-section-${app.id}">
              
              ${!app.quiz_validated ? `
                <div class="interview-validation-overlay">
                  <div class="interview-validation-number">3</div>
                  <div class="interview-validation-message">En attente de validation du quiz</div>
                  <button class="btn-schedule-interview-overlay" onclick="validateQuizAndRemoveOverlay(${app.id})" id="validate-quiz-btn-overlay-${app.id}">
                    <i class="fas fa-check-double"></i> Valider le quiz
                  </button>
                </div>
              ` : ''}
                
              <h4>
                <i class="fas fa-calendar-alt"></i> Programmation d'entretien
                <span class="interview-status-badge ${getInterviewStatusClass(app.interview_status || 'not_scheduled')}">${getInterviewStatusText(app.interview_status || 'not_scheduled')}</span>
              </h4>
              
              <div class="interview-content">
                <div class="interview-overview">
                  <div class="interview-info-grid">
                    <div class="interview-info-item">
                      <div class="info-icon">
                        <i class="fas fa-calendar-check"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Date prévue</div>
                        <div class="info-value">${app.interview_date ? formatDate(app.interview_date) : 'Non programmé'}</div>
                      </div>
                    </div>
                    
                    <div class="interview-info-item">
                      <div class="info-icon">
                        <i class="fas fa-clock"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Heure</div>
                        <div class="info-value">${app.interview_time || 'Non définie'}</div>
                      </div>
                    </div>
                    

                    
                    <div class="interview-info-item">
                      <div class="info-icon">
                        <i class="fas fa-users"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Type</div>
                        <div class="info-value">${app.interview_type || 'À définir'}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="interview-actions">
                  <div class="interview-actions-row">
                    <button class="btn-schedule-interview" onclick="openScheduleInterviewModal(${app.id}, '${candidateName}')">
                      <i class="fas fa-calendar-plus"></i> Programmer un entretien
                    </button>

                    <button class="btn-reschedule-interview" onclick="rescheduleInterview(${app.id})" ${!app.interview_date ? 'disabled' : ''}>
                      <i class="fas fa-calendar-times"></i> Reprogrammer
                    </button>
                  </div>
                </div>
                
                ${app.interview_notes ? `
                <div class="interview-notes">
                  <h5><i class="fas fa-sticky-note"></i> Notes d'entretien</h5>
                  <p>${app.interview_notes}</p>
                </div>
                ` : ''}
              </div>
            </div>
            

          </div>
          
          <div class="application-actions">
            ${renderCandidateActions(app)}
          </div>
          
          ${
            isRecommended && app.recommendation_comment
              ? `
            <div class="recommendation-comment">
              <h4><i class="fas fa-comment"></i> Commentaire de recommandation</h4>
              <p>${app.recommendation_comment}</p>
            </div>
          `
              : ""
          }
        </div>
      </div>
    `
    })
    .join("")

  // DEBUG: Afficher le HTML final généré
  console.log("🔍 DEBUG HTML FINAL GÉNÉRÉ:")
  console.log(container.innerHTML)

  console.log("✅ Candidatures rendues avec succès")

  // Mettre à jour les compteurs des boutons de filtres
  try {
    updateFilterCounts()
  } catch (error) {
    console.error("❌ Erreur lors de la mise à jour des compteurs:", error)
  }
}

async function validateQuizAndRemoveOverlay(applicationId) {
  console.log(`✅ Validation du quiz pour l'application ${applicationId}`)
  
  try {
    const app = applications.find(a => a.id === applicationId);
    if (!app) {
      console.error("❌ Application non trouvée");
      return;
    }
    
    const candidateName = app.name || app.candidate_name || "Candidat";
    
    showLoading("Validation du quiz en cours...");
    
    setTimeout(() => {
      // Mettre à jour l'état local
      app.quiz_score = app.quiz_score || 0; // Score par défaut si aucun
      
      // Supprimer l'overlay et débloquer la section
      const interviewSection = document.getElementById(`interview-section-${applicationId}`);
      if (interviewSection) {
        interviewSection.classList.remove('locked');
        const overlay = interviewSection.querySelector('.interview-validation-overlay');
        if (overlay) {
          overlay.remove();
        }
      }
      
      hideLoading();
      showNotification(`✅ Quiz validé pour ${candidateName}`, "success");
      
      // Recharger les détails pour afficher le score
      loadJobData(); // ← ICI: Changement de loadJobDetails() à loadJobData()
    }, 1000);
    
  } catch (error) {
    hideLoading();
    console.error("❌ Erreur validation quiz:", error);
    showNotification("Erreur lors de la validation du quiz", "error");
  }
}

function toggleCandidateCard(appId) {
  const expandedContent = document.getElementById(`expanded-${appId}`)
  const toggleButton = document.querySelector(`[data-app-id="${appId}"] .expand-toggle`)
  const cardElement = document.querySelector(`[data-app-id="${appId}"]`)

  if (!expandedContent || !toggleButton) return

  const isExpanded = expandedContent.classList.contains("expanded")

  if (isExpanded) {
    // Fermer la carte
    expandedContent.classList.remove("expanded")
    toggleButton.classList.remove("expanded")
  } else {
    // Ouvrir la carte
    expandedContent.classList.add("expanded")
    toggleButton.classList.add("expanded")

    // Scroll automatique vers la carte si elle n'est PAS TOTALEMENT visible
    setTimeout(() => {
      if (cardElement) {
        const cardRect = cardElement.getBoundingClientRect()
        const windowHeight = window.innerHeight

        // Vérifier si la carte est partiellement ou pas totalement visible
        const isPartiallyVisible = cardRect.top < windowHeight && cardRect.bottom > 0
        const isFullyVisible = cardRect.top >= 0 && cardRect.bottom <= windowHeight

        if (!isFullyVisible) {
          // Calculer la position de scroll optimale pour que la carte soit 100% visible
          let targetScrollY

          if (cardRect.top < 0) {
            // La carte est au-dessus de la vue, scroll vers le haut
            // On veut que le haut de la carte soit visible avec une marge de 50px
            targetScrollY = window.pageYOffset + cardRect.top - 50
          } else if (cardRect.bottom > windowHeight) {
            // La carte est en dessous de la vue, scroll vers le bas
            // On veut que le bas de la carte soit visible avec une marge de 100px
            // La formule: position actuelle + (bas de la carte - hauteur de la fenêtre + marge)
            targetScrollY = window.pageYOffset + (cardRect.bottom - windowHeight + 100)
          }

          // Ajouter un indicateur visuel de scroll
          cardElement.style.transition = "box-shadow 0.3s ease"
          cardElement.style.boxShadow = "0 0 20px rgba(0, 212, 255, 0.3)"

          // Scroll fluide vers la position calculée
          window.scrollTo({
            top: Math.max(0, targetScrollY),
            behavior: "smooth",
          })

          // Retirer l'indicateur visuel après le scroll
          setTimeout(() => {
            cardElement.style.boxShadow = ""
          }, 1500)

          console.log(`🎯 Scroll automatique vers la carte ${appId} (carte pas totalement visible):`, {
            cardTop: cardRect.top,
            cardBottom: cardRect.bottom,
            windowHeight: windowHeight,
            targetScrollY: targetScrollY,
            isPartiallyVisible: isPartiallyVisible,
            isFullyVisible: isFullyVisible,
          })
        } else {
          console.log(`✅ Carte ${appId} déjà totalement visible, pas de scroll nécessaire`)
        }
      }
    }, 100) // Délai pour laisser l'animation CSS se déclencher
  }
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

    // Debug des données reçues
    console.log("🔍 DEBUG COMPATIBILITY API RESPONSE:", {
      status: response.status,
      result: result,
      success: result.success,
      compatibility_percentage: result.compatibility_percentage,
      matched_count: result.matched_count,
      missing_count: result.missing_count,
      total_job_skills: result.total_job_skills,
      matched_skills: result.matched_skills,
      missing_skills: result.missing_skills,
    })

    if (result.success) {
      // Utilisez les données de l'API pour afficher la modal
      showDarkCompatibilityModal(
        result,
        result.compatibility_percentage || 0,
        result.compatibility_source || "calculated",
        result.compatibility_reason || "",
      )
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
function showDarkCompatibilityModal(
  compatibilityData,
  compatibilityPercentage,
  compatibilitySource,
  compatibilityReason,
) {
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
              ${compatibilitySource === "ai" ? '<i class="fas fa-robot" style="color: #10b981; margin-left: 0.5rem;" title="Analyse IA"></i>' : ""}
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
        
        ${
          compatibilitySource === "ai" && compatibilityReason
            ? `
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
        `
            : `
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
                .map((skill) => {
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
                })
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
                .map((skill) => {
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
                })
                .join("")}
            </div>
          </div>
        </div>
        `
        }
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
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
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
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
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
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
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
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
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
    accepted_pending_validation: "accepted_pending_validation",
  }
  return statusTexts[status] || status
}

// Fonction pour initialiser l'état de validation du quiz
function initializeQuizValidationState() {
  console.log("🔧 Initialisation de l'état de validation du quiz")
  
  applications.forEach(app => {
    const interviewSection = document.getElementById(`interview-section-${app.id}`)
    const validateQuizBtn = document.getElementById(`validate-quiz-btn-overlay-${app.id}`)
    
    if (app.quiz_validated) {
      // Si le quiz est déjà validé, retirer l'overlay
      if (interviewSection) {
        interviewSection.classList.remove("locked")
        const overlay = interviewSection.querySelector(".interview-validation-overlay")
        if (overlay) {
          overlay.remove()
        }
      }
      
      if (validateQuizBtn) {
        validateQuizBtn.disabled = true
        validateQuizBtn.innerHTML = '<i class="fas fa-check"></i> Quiz Validé'
      }
    }
  })
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
      body: JSON.stringify({ status: "accepted" }),
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

  const isAdmin = currentUser && currentUser.role === "super_admin"
  const modalTitle = isAdmin ? "Accepter définitivement" : "Accepter la candidature"
  const modalDescription = isAdmin
    ? "En tant qu'administrateur, votre acceptation sera définitive et créera immédiatement l'employé."
    : "Votre acceptation devra être validée par un administrateur avant la création de l'employé."

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
            ${
              isAdmin
                ? `
            <li><i class="fas fa-user-plus"></i> Création automatique de l'employé</li>
            <li><i class="fas fa-briefcase"></i> Attribution du poste</li>
            <li><i class="fas fa-check-circle"></i> Marquage du poste comme pourvu</li>
            <li><i class="fas fa-times-circle"></i> Rejet automatique des autres candidatures</li>
            `
                : `
            <li><i class="fas fa-check-circle"></i> Candidature marquée comme acceptée</li>
            <li><i class="fas fa-user-shield"></i> Envoi pour validation administrateur</li>
            <li><i class="fas fa-clock"></i> En attente d'approbation finale</li>
            `
            }
          </ul>
        </div>
        <div class="info-note">
          <i class="fas fa-info-circle"></i>
          <p>${
            isAdmin
              ? "Cette action est définitive. Le candidat sera intégré en tant qu'employé."
              : "La candidature sera envoyée à l'administrateur pour validation finale avant création de l'employé."
          }</p>
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
    let targetStatus = "accepted"
    if (currentUser && currentUser.role === "recruiter") {
      targetStatus = "accepted_pending_validation"
    }

    const response = await fetch(`/api/accept-application/${applicationId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: targetStatus }),
    })

    const result = await response.json()
    hideLoading()

    if (response.ok && result.success) {
      const message =
        targetStatus === "accepted_pending_validation"
          ? "Candidature acceptée, en attente de validation admin"
          : "Candidat accepté avec succès"

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

// NOUVELLE FONCTION: Mettre à jour les compteurs des boutons de filtres
function updateFilterCounts() {
  console.log("🔢 Mise à jour des compteurs de filtres")

  if (!applications || applications.length === 0) {
    console.log("⚠️ Aucune candidature pour mettre à jour les compteurs")
    return
  }

  // Compter les candidatures par statut
  const counts = {
    all: applications.length,
    pending: applications.filter((app) => app.status === "pending").length,
    reviewed: applications.filter((app) => app.status === "reviewed").length,
    accepted: applications.filter((app) => app.status === "accepted").length,
    rejected: applications.filter((app) => app.status === "rejected").length,
  }

  console.log("📊 Compteurs calculés:", counts)

  // Mettre à jour les boutons de filtres
  const filterButtons = document.querySelectorAll(".filter-btn")
  filterButtons.forEach((btn) => {
    const onclick = btn.getAttribute("onclick")
    if (onclick) {
      if (onclick.includes("'all'")) {
        btn.innerHTML = `<i class="fas fa-filter"></i> Toutes (${counts.all})`
      } else if (onclick.includes("'pending'")) {
        btn.innerHTML = `<i class="fas fa-clock"></i> En attente (${counts.pending})`
      } else if (onclick.includes("'reviewed'")) {
        btn.innerHTML = `<i class="fas fa-eye"></i> Examinées (${counts.reviewed})`
      } else if (onclick.includes("'accepted'")) {
        btn.innerHTML = `<i class="fas fa-check-circle"></i> Acceptées (${counts.accepted})`
      } else if (onclick.includes("'rejected'")) {
        btn.innerHTML = `<i class="fas fa-times-circle"></i> Rejetées (${counts.rejected})`
      }
    }
  })

  // Mettre à jour le titre de la section
  const sectionHeader = document.querySelector(".applications-section .section-header h3")
  if (sectionHeader) {
    sectionHeader.innerHTML = `<i class="fas fa-users"></i> Candidatures (${counts.all})`
  }

  console.log("✅ Compteurs de filtres mis à jour")
}

console.log("✅ Script job-details-enhanced.js chargé complètement avec compatibilité et modal sombre")

// Fonction pour voir les résultats du quiz
async function viewQuizResults(applicationId, candidateName) {
  console.log(`👁️ Affichage résultats quiz pour ${candidateName} (ID: ${applicationId})`)

  try {
    showLoading("Chargement des résultats du quiz...")

    const response = await fetch(`/api/applications/${applicationId}/quiz-results`)
    const result = await response.json()
    hideLoading()

    if (result.success) {
      showQuizResultsModal(result.quiz_data, candidateName, applicationId)
    } else {
      showNotification(result.message || "Erreur lors du chargement des résultats", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur chargement résultats quiz:", error)
    showNotification("Erreur de connexion lors du chargement des résultats", "error")
  }
}

// Fonction pour afficher la modal des résultats du quiz
function showQuizResultsModal(quizData, candidateName, applicationId) {
  console.log("🔍 Affichage modal résultats quiz:", quizData)

  const modal = document.createElement("div")
  modal.className = "modal-overlay quiz-results-modal"
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
      max-width: 800px;
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
          <i class="fas fa-question-circle" style="color: #3b82f6;"></i> 
          Résultats du Quiz - ${candidateName}
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
        <div class="quiz-overview" style="
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
          <div class="quiz-score">
            <div class="score-circle ${getQuizScoreClass(quizData.score || 0)}" style="
              width: 120px;
              height: 120px;
              border-radius: 50%;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              background: conic-gradient(
                ${
                  (quizData.score || 0) >= 75
                    ? "#10b981"
                    : (quizData.score || 0) >= 50
                      ? "#f59e0b"
                      : (quizData.score || 0) >= 25
                        ? "#ef4444"
                        : "#6b7280"
                } 
                ${(quizData.score || 0) * 3.6}deg,
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
                <div style="font-size: 1.5rem; font-weight: 700;">${quizData.score || 0}%</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">Score</div>
              </div>
            </div>
          </div>
          
          <div class="quiz-summary">
            <h4 style="margin: 0 0 1rem 0; color: #f8fafc; display: flex; align-items: center; gap: 0.75rem;">
              <i class="fas fa-chart-bar" style="color: #3b82f6;"></i>
              Résumé du Quiz
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
                ${quizData.correct_answers || 0} réponses correctes
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
                ${quizData.total_questions || 0} questions au total
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
              <i class="fas fa-clock" style="color: #6b7280; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">
                Temps: ${quizData.completion_time || "N/A"}
              </span>
            </div>
          </div>
        </div>
        
        ${
          quizData.questions && quizData.questions.length > 0
            ? `
        <div class="quiz-questions" style="margin-top: 2rem;">
          <h4 style="color: #f8fafc; margin-bottom: 1.5rem;">Détail des questions</h4>
          ${quizData.questions
            .map(
              (question, index) => `
            <div class="question-item" style="
              padding: 1.5rem;
              margin: 1rem 0;
              background: rgba(59, 130, 246, 0.05);
              border: 1px solid rgba(59, 130, 246, 0.2);
              border-radius: 12px;
            ">
              <div class="question-header" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
              ">
                <h5 style="margin: 0; color: #f8fafc;">Question ${index + 1}</h5>
                <span class="question-status ${question.is_correct ? "correct" : "incorrect"}" style="
                  padding: 0.25rem 0.75rem;
                  border-radius: 20px;
                  font-size: 0.8rem;
                  font-weight: 600;
                  color: white;
                  background: ${question.is_correct ? "#10b981" : "#ef4444"};
                ">
                  ${question.is_correct ? "Correct" : "Incorrect"}
                </span>
              </div>
              <p style="color: #f8fafc; margin-bottom: 1rem;">${question.question_text}</p>
              <div class="question-answer">
                <strong style="color: #cbd5e1;">Réponse donnée:</strong> 
                <span style="color: #f8fafc;">${question.user_answer || "Aucune"}</span>
              </div>
              ${
                question.correct_answer
                  ? `
                <div class="question-correct-answer">
                  <strong style="color: #10b981;">Bonne réponse:</strong> 
                  <span style="color: #f8fafc;">${question.correct_answer}</span>
                </div>
              `
                  : ""
              }
            </div>
          `,
            )
            .join("")}
        </div>
        `
            : ""
        }
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

// Fonction helper pour déterminer la classe CSS du score quiz
function getQuizScoreClass(score) {
  if (score >= 75) return "high"
  if (score >= 50) return "medium"
  if (score >= 25) return "low"
  return "very-low"
}

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

async function validateSkillsAnalysis(applicationId, candidateName) {
  console.log(`✅ Validation de l'analyse des compétences pour ${candidateName} (ID: ${applicationId})`)

  try {
      showLoading("Validation en cours...")

      const response = await fetch(`/api/applications/${applicationId}/validate-skills`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              validated: true,
              notes: "Compétences validées par l'équipe RH"
          })
      })

      const result = await response.json()

      if (result.success) {
          // Mettre à jour l'interface utilisateur
          const validateBtn = document.getElementById(`validate-btn-${applicationId}`)
          const validationStatus = document.getElementById(`validation-status-${applicationId}`)
          const quizSection = document.getElementById(`quiz-section-${applicationId}`)

          if (validateBtn) {
              validateBtn.classList.add("validated")
              validateBtn.innerHTML = '<i class="fas fa-check"></i> Validé'
              validateBtn.disabled = true
          }

          if (validationStatus) {
              validationStatus.classList.add("success")
          }

          if (quizSection) {
              quizSection.classList.remove("locked")
              const overlay = quizSection.querySelector(".quiz-validation-overlay")
              if (overlay) {
                  overlay.remove()
              }
          }

          showNotification(`Analyse des compétences validée pour ${candidateName}`, "success")
      } else {
          showNotification(result.message || "Erreur lors de la validation", "error")
      }
  } catch (error) {
      console.error("Erreur lors de la validation des compétences:", error)
      showNotification("Erreur de connexion lors de la validation", "error")
  } finally {
      hideLoading()
  }
}

// Fonction pour enlever seulement l'overlay du quiz (sans valider les compétences)
async function validateSkillsAndRemoveOverlay(applicationId) {
  console.log(`✅ Validation des compétences pour l'application ${applicationId}`)
  
  try {
    // Trouver l'application correspondante
    const app = applications.find(a => a.id === applicationId);
    if (!app) {
      console.error("❌ Application non trouvée");
      return;
    }
    
    const candidateName = app.name || app.candidate_name || "Candidat";
    
    showLoading("Validation des compétences en cours...");
    
    const response = await fetch(`/api/applications/${applicationId}/validate-skills`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        validated: true,
        notes: "Compétences validées par l'équipe RH"
      })
    });
    
    const result = await response.json();
    hideLoading();
    
    if (result.success) {
      // Mettre à jour l'état local
      app.skills_validated = true;
      app.skills_validated_at = new Date().toISOString();
      
      // Mettre à jour l'interface
      const validateBtn = document.getElementById(`validate-btn-${applicationId}`);
      const validationStatus = document.getElementById(`validation-status-${applicationId}`);
      const quizSection = document.getElementById(`quiz-section-${applicationId}`);
      
      if (validateBtn) {
        validateBtn.classList.add("validated");
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Validé';
        validateBtn.disabled = true;
      }
      
      if (validationStatus) {
        validationStatus.classList.add("success");
        validationStatus.style.display = 'block';
      }
      
      if (quizSection) {
        quizSection.classList.remove("locked");
        const overlay = quizSection.querySelector(".quiz-validation-overlay");
        if (overlay) {
          overlay.remove();
        }
      }
      
      showNotification(`✅ Analyse des compétences validée pour ${candidateName}`, "success");
    } else {
      showNotification(result.message || "Erreur lors de la validation", "error");
    }
  } catch (error) {
    hideLoading();
    console.error("❌ Erreur validation compétences:", error);
    showNotification("Erreur de connexion lors de la validation", "error");
  }
}

// Fonction pour valider le quiz et enlever l'overlay de la section entretien
async function validateQuizAndRemoveOverlay(applicationId) {
  console.log(`✅ Validation du quiz pour l'application ${applicationId}`)
  
  try {
    const app = applications.find(a => a.id === applicationId);
    if (!app) {
      console.error("❌ Application non trouvée");
      return;
    }
    
    const candidateName = app.name || app.candidate_name || "Candidat";
    
    showLoading("Validation du quiz en cours...");
    
    // Appel API pour valider le quiz
    const response = await fetch(`/api/applications/${applicationId}/validate-quiz`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        validated: true,
        notes: "Quiz validé par l'équipe RH"
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Mettre à jour l'état local
      app.quiz_validated = true;
      app.quiz_validated_at = new Date().toISOString();
      
      // Supprimer l'overlay et débloquer la section
      const interviewSection = document.getElementById(`interview-section-${applicationId}`);
      if (interviewSection) {
        interviewSection.classList.remove('locked');
        const overlay = interviewSection.querySelector('.interview-validation-overlay');
        if (overlay) {
          overlay.remove();
        }
      }
      
      hideLoading();
      showNotification(`✅ Quiz validé pour ${candidateName}`, "success");
      
      // Mettre à jour l'interface pour refléter la validation
      const validateQuizBtn = document.getElementById(`validate-quiz-btn-overlay-${applicationId}`);
      if (validateQuizBtn) {
        validateQuizBtn.disabled = true;
        validateQuizBtn.innerHTML = '<i class="fas fa-check"></i> Quiz Validé';
      }
      
    } else {
      hideLoading();
      showNotification(result.message || "Erreur lors de la validation", "error");
    }
  } catch (error) {
    hideLoading();
    console.error("❌ Erreur validation quiz:", error);
    showNotification("Erreur de connexion lors de la validation", "error");
  }
}

// Fonction pour initialiser l'état de validation du quiz
function initializeQuizValidationState() {
  console.log("🔧 Initialisation de l'état de validation du quiz")
  
  applications.forEach(app => {
    const interviewSection = document.getElementById(`interview-section-${app.id}`)
    const validateQuizBtn = document.getElementById(`validate-quiz-btn-overlay-${app.id}`)
    
    if (app.quiz_validated) {
      // Si le quiz est déjà validé, retirer l'overlay
      if (interviewSection) {
        interviewSection.classList.remove("locked")
        const overlay = interviewSection.querySelector(".interview-validation-overlay")
        if (overlay) {
          overlay.remove()
        }
      }
      
      if (validateQuizBtn) {
        validateQuizBtn.disabled = true
        validateQuizBtn.innerHTML = '<i class="fas fa-check"></i> Quiz Validé'
      }
    }
  })
}

// Appeler cette fonction après le chargement des applications
setTimeout(() => {
  initializeSkillsValidationState()
  initializeQuizValidationState() // ← Ajouter cette ligne
}, 100)

// Guarded click handler to prevent spamming the open button
function handleOpenCreateQuizClick(buttonEl) {
  if (!buttonEl) return
  if (buttonEl.dataset.loading === "true") return
  // set loading state
  buttonEl.dataset.loading = "true"
  buttonEl.disabled = true
  const originalHtml = buttonEl.innerHTML
  buttonEl.dataset.originalHtml = originalHtml
  buttonEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Ouverture...</span>'
  // open modal (no candidate preselected here)
  openCreateQuizModal()
  // restore the button state after modal is shown
  setTimeout(() => {
    try {
      buttonEl.disabled = false
      buttonEl.dataset.loading = "false"
      if (buttonEl.dataset.originalHtml) {
        buttonEl.innerHTML = buttonEl.dataset.originalHtml
      }
    } catch (e) {}
  }, 600)
}

// Ouvrir le modal de création de quiz
async function openCreateQuizModal(candidateId = null, candidateName = null) {
  console.log("🎯 Ouverture du modal de création de quiz professionnel")
  console.log("👤 Candidat sélectionné:", candidateId, candidateName)

  // Store the candidate ID globally for the form submission
  window.currentQuizCandidateId = candidateId
  window.currentQuizCandidateName = candidateName

  const modal = document.getElementById("createQuizModal")

  if (!modal) {
    console.error("❌ Modal non trouvé")
    return
  }

  // Update modal header to show candidate name if available
  const modalHeader = modal.querySelector(".modal-header h2")
  if (modalHeader && candidateName) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz d'Évaluation pour ${candidateName}`
  } else if (modalHeader) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz d'Évaluation`
  }

  // Afficher le modal
  modal.classList.add("show")

  // Empêcher le scroll du body
  document.body.style.overflow = "hidden"

  // Générer la configuration des compétences (async)
  await generateSkillsQuizConfig()
}

// Fermer le modal de création de quiz
function closeCreateQuizModal() {
  console.log("❌ Fermeture du modal de création de quiz")
  const modal = document.getElementById("createQuizModal")

  if (modal) {
    modal.classList.remove("show")
  }

  // Restaurer le scroll du body
  document.body.style.overflow = "auto"

  // Reset modal header and clear stored candidate info
  const modalHeader = modal.querySelector(".modal-header h2")
  if (modalHeader) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz`
  }

  // Clear stored candidate information
  window.currentQuizCandidateId = null
  window.currentQuizCandidateName = null
}

// Générer la configuration des compétences pour le quiz
async function generateSkillsQuizConfig() {
  console.log("🔧 Génération de la configuration des compétences")
  const container = document.getElementById("skillsQuizConfig")

  if (!container) {
    console.error("❌ Container skillsQuizConfig non trouvé")
    return
  }

  // Afficher un message de chargement
  container.innerHTML =
    '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Chargement des compétences...</p>'

  try {
    // Récupérer les compétences du job
    let jobSkills = []

    if (currentJob && currentJob.id) {
      console.log("🔍 Récupération des compétences pour le job ID:", currentJob.id)
      console.log("🔍 Job complet:", currentJob)

      // Essayer de récupérer depuis les données du job existantes
      if (currentJob.skills && Array.isArray(currentJob.skills)) {
        jobSkills = currentJob.skills
        console.log("✅ Compétences trouvées dans currentJob.skills:", jobSkills)
      } else if (currentJob.required_skills && Array.isArray(currentJob.required_skills)) {
        jobSkills = currentJob.required_skills
        console.log("✅ Compétences trouvées dans currentJob.required_skills:", jobSkills)
      } else if (currentJob.job_skills && Array.isArray(currentJob.job_skills)) {
        jobSkills = currentJob.job_skills
        console.log("✅ Compétences trouvées dans currentJob.job_skills:", jobSkills)
      } else if (currentJob.skills_list && Array.isArray(currentJob.skills_list)) {
        jobSkills = currentJob.skills_list
        console.log("✅ Compétences trouvées dans currentJob.skills_list:", jobSkills)
      }
    }

    // Fallback: essayer de récupérer depuis le DOM
    if (jobSkills.length === 0) {
      console.log("🔍 Fallback: récupération depuis le DOM")
      const skillsContainer = document.getElementById("jobSkillsContainer")
      if (skillsContainer) {
        const skillElements = skillsContainer.querySelectorAll(".skill-tag, .skill-item, [data-skill], .skill")
        jobSkills = Array.from(skillElements)
          .map((el) => {
            return el.textContent?.trim() || el.getAttribute("data-skill") || el.innerText?.trim()
          })
          .filter((skill) => skill && skill.length > 0)
      }
    }

    console.log("🔍 Compétences finales trouvées:", jobSkills)

    if (jobSkills.length === 0) {
      container.innerHTML =
        '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Aucune compétence trouvée pour ce poste. Veuillez d\'abord ajouter des compétences au poste.</p>'
      return
    }

    // Générer le HTML pour chaque compétence
    const skillsHTML = jobSkills
      .map((skill) => {
        // Gérer différents formats de compétences (string ou object)
        let skillName = ""
        if (typeof skill === "string") {
          skillName = skill.trim()
        } else if (skill && typeof skill === "object") {
          // Utiliser skill_name en priorité (structure trouvée dans les données)
          skillName =
            skill.skill_name || skill.name || skill.skill || skill.title || skill.text || "Compétence inconnue"
        } else {
          skillName = String(skill) || "Compétence inconnue"
        }

        // Créer un ID sécurisé pour les inputs
        const skillId = skillName.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase()

        return `
        <div class="skill-quiz-config">
          <div class="skill-quiz-header">
            <span class="skill-quiz-name">${skillName}</span>
          </div>
          <div class="skill-quiz-controls">
            <div class="form-group">
              <label for="questions_${skillId}">Nombre de questions</label>
              <input type="number" id="questions_${skillId}" name="questions_${skillId}" min="0" max="20" value="5" required>
            </div>
            <div class="form-group">
              <label for="difficulty_${skillId}">Niveau de difficulté</label>
              <select id="difficulty_${skillId}" name="difficulty_${skillId}" required>
                <option value="easy">Facile</option>
                <option value="medium" selected>Moyen</option>
                <option value="hard">Difficile</option>
                <option value="expert">Expert</option>
              </select>
            </div>
          </div>
        </div>
      `
      })
      .join("")

    container.innerHTML = skillsHTML
  } catch (error) {
    console.error("❌ Erreur lors de la récupération des compétences:", error)
    container.innerHTML =
      '<p style="color: var(--error-red); text-align: center; padding: 2rem;">Erreur lors du chargement des compétences. Veuillez réessayer.</p>'
  }
}

// Gérer la soumission du formulaire de création de quiz
document.addEventListener("DOMContentLoaded", () => {
  const quizForm = document.getElementById("createQuizForm")

  if (quizForm) {
    quizForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      console.log("📝 Soumission du formulaire de création de quiz")

      // Récupérer les données du formulaire
      const formData = new FormData(quizForm)
      const quizData = {
        title: formData.get("quizTitle"),
        timeLimit: Number.parseInt(formData.get("quizTime")),
        skills: [],
      }

      // Récupérer les compétences du job avec la même logique
      let jobSkills = []

      if (currentJob) {
        if (currentJob.skills && Array.isArray(currentJob.skills)) {
          jobSkills = currentJob.skills
        } else if (currentJob.required_skills && Array.isArray(currentJob.required_skills)) {
          jobSkills = currentJob.required_skills
        } else if (currentJob.job_skills && Array.isArray(currentJob.job_skills)) {
          jobSkills = currentJob.job_skills
        } else if (currentJob.skills_list && Array.isArray(currentJob.skills_list)) {
          jobSkills = currentJob.skills_list
        }

        // Si toujours vide, essayer de récupérer depuis les éléments DOM
        if (jobSkills.length === 0) {
          const skillsContainer = document.getElementById("jobSkillsContainer")
          if (skillsContainer) {
            const skillElements = skillsContainer.querySelectorAll(".skill-tag, .skill-item, [data-skill]")
            jobSkills = Array.from(skillElements)
              .map((el) => {
                return el.textContent?.trim() || el.getAttribute("data-skill") || el.innerText?.trim()
              })
              .filter((skill) => skill && skill.length > 0)
          }
        }
      }

      // Ajouter les configurations de chaque compétence
      jobSkills.forEach((skill) => {
        // Gérer différents formats de compétences (string ou object)
        let skillName = ""
        if (typeof skill === "string") {
          skillName = skill.trim()
        } else if (skill && typeof skill === "object") {
          // Utiliser skill_name en priorité (structure trouvée dans les données)
          skillName =
            skill.skill_name || skill.name || skill.skill || skill.title || skill.text || "Compétence inconnue"
        } else {
          skillName = String(skill) || "Compétence inconnue"
        }

        // Créer un ID sécurisé pour les inputs
        const skillId = skillName.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase()

        const questions = Number.parseInt(formData.get(`questions_${skillId}`)) || 0
        const difficulty = formData.get(`difficulty_${skillId}`) || "medium"

        if (questions > 0) {
          quizData.skills.push({
            name: skillName,
            questions: questions,
            difficulty: difficulty,
          })
        }
      })

      console.log("📊 Données du quiz:", quizData)

      // Get candidate ID from the stored global variable
      const candidateId = window.currentQuizCandidateId || null
      console.log("👤 ID du candidat pour le quiz:", candidateId)

      // Send quiz data to the quiz router
      try {
        const response = await fetch("/api/hr/quiz/create", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: quizData.title,
            time_limit: quizData.timeLimit,
            skills: quizData.skills,
            job_id: currentJob ? currentJob.id || currentJob.job_id : null,
            candidate_id: candidateId,
          }),
        })

        const result = await response.json()

        if (result.success) {
          showNotification("Quiz créé avec succès !", "success")
          closeCreateQuizModal()
        } else {
          showNotification("Erreur lors de la création du quiz", "error")
        }
      } catch (error) {
        console.error("❌ Erreur lors de la création du quiz:", error)
        showNotification("Erreur lors de la création du quiz", "error")
      }
    })
  }
})

// Fermer le modal en cliquant à l'extérieur
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("createQuizModal")

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeCreateQuizModal()
      }
    })
  }
})

// ===== FONCTIONS POUR LA PROGRAMMATION D'ENTRETIEN =====

// Fonction pour obtenir la classe CSS du statut d'entretien
function getInterviewStatusClass(status) {
  const statusClasses = {
    'not_scheduled': 'status-not-scheduled',
    'scheduled': 'status-scheduled',
    'completed': 'status-completed',
    'cancelled': 'status-cancelled',
    'rescheduled': 'status-rescheduled'
  }
  return statusClasses[status] || 'status-not-scheduled'
}

// Fonction pour obtenir le texte du statut d'entretien
function getInterviewStatusText(status) {
  const statusTexts = {
    'not_scheduled': 'Non programmé',
    'scheduled': 'Programmé',
    'completed': 'Terminé',
    'cancelled': 'Annulé',
    'rescheduled': 'Reprogrammé'
  }
  return statusTexts[status] || 'Non programmé'
}

// Fonction pour formater une date
function formatDate(dateString) {
  if (!dateString) return 'Non défini'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch (error) {
    return 'Date invalide'
  }
}

// Fonction pour ouvrir le modal de programmation d'entretien
function openScheduleInterviewModal(applicationId, candidateName) {
  console.log(`📅 Ouverture du modal de programmation d'entretien pour ${candidateName}`)
  
  // Créer le modal
  const modal = document.createElement('div')
  modal.className = 'modal-overlay interview-modal-overlay'
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
      max-width: 600px;
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
          <i class="fas fa-calendar-plus" style="color: #3b82f6;"></i> 
          Programmer un entretien
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
      
      <div class="modal-body" style="padding: 2rem;">
        <div class="candidate-info" style="
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 12px;
          padding: 1rem;
          margin-bottom: 2rem;
        ">
          <h4 style="margin: 0 0 0.5rem 0; color: #f8fafc;">
            <i class="fas fa-user" style="color: #3b82f6; margin-right: 0.5rem;"></i>
            ${candidateName}
          </h4>
          <p style="margin: 0; color: #cbd5e1; font-size: 0.9rem;">
            Application ID: ${applicationId}
          </p>
        </div>
        
        <form id="interview-form" style="display: flex; flex-direction: column; gap: 1.5rem;">
          <div class="form-group">
            <label style="display: block; color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem;">
              <i class="fas fa-calendar" style="color: #3b82f6; margin-right: 0.5rem;"></i>
              Date de l'entretien
            </label>
            <input type="date" id="interview-date" required style="
              width: 100%;
              padding: 0.75rem;
              border: 1px solid rgba(59, 130, 246, 0.3);
              border-radius: 8px;
              background: rgba(15, 23, 42, 0.8);
              color: #f8fafc;
              font-size: 1rem;
            ">
          </div>
          
          <div class="form-group">
            <label style="display: block; color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem;">
              <i class="fas fa-clock" style="color: #3b82f6; margin-right: 0.5rem;"></i>
              Heure de l'entretien
            </label>
            <input type="time" id="interview-time" required style="
              width: 100%;
              padding: 0.75rem;
              border: 1px solid rgba(59, 130, 246, 0.3);
              border-radius: 8px;
              background: rgba(15, 23, 42, 0.8);
              color: #f8fafc;
              font-size: 1rem;
            ">
          </div>
          

          
          <div class="form-group">
            <label style="display: block; color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem;">
              <i class="fas fa-users" style="color: #3b82f6; margin-right: 0.5rem;"></i>
              Type d'entretien
            </label>
            <select id="interview-type" required style="
              width: 100%;
              padding: 0.75rem;
              border: 1px solid rgba(59, 130, 246, 0.3);
              border-radius: 8px;
              background: rgba(15, 23, 42, 0.8);
              color: #f8fafc;
              font-size: 1rem;
            ">
              <option value="">Sélectionner un type</option>
              <option value="premier_contact">Premier contact</option>
              <option value="technique">Entretien technique</option>
              <option value="rh">Entretien RH</option>
              <option value="final">Entretien final</option>
              <option value="autre">Autre</option>
            </select>
          </div>
          
          <div class="form-group">
            <label style="display: block; color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem;">
              <i class="fas fa-sticky-note" style="color: #3b82f6; margin-right: 0.5rem;"></i>
              Notes (optionnel)
            </label>
            <textarea id="interview-notes" rows="3" style="
              width: 100%;
              padding: 0.75rem;
              border: 1px solid rgba(59, 130, 246, 0.3);
              border-radius: 8px;
              background: rgba(15, 23, 42, 0.8);
              color: #f8fafc;
              font-size: 1rem;
              resize: vertical;
            " placeholder="Ajoutez des notes ou instructions pour l'entretien..."></textarea>
          </div>
          
          <div class="form-actions" style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1rem;">
            <button type="button" onclick="this.closest('.modal-overlay').remove()" style="
              padding: 0.75rem 1.5rem;
              border: 1px solid rgba(107, 114, 128, 0.3);
              border-radius: 8px;
              background: transparent;
              color: #9ca3af;
              cursor: pointer;
              font-weight: 600;
            ">Annuler</button>
            <button type="submit" style="
              padding: 0.75rem 1.5rem;
              border: none;
              border-radius: 8px;
              background: linear-gradient(135deg, #3b82f6, #1d4ed8);
              color: white;
              cursor: pointer;
              font-weight: 600;
              box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            ">Programmer l'entretien</button>
          </div>
        </form>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Gérer la soumission du formulaire
  const form = modal.querySelector('#interview-form')
  form.addEventListener('submit', function(e) {
    e.preventDefault()
    scheduleInterview(applicationId, candidateName, form)
  })
}

// Fonction pour programmer l'entretien
function scheduleInterview(applicationId, candidateName, form) {
  const formData = {
    date: form.querySelector('#interview-date').value,
    time: form.querySelector('#interview-time').value,
    type: form.querySelector('#interview-type').value,
    notes: form.querySelector('#interview-notes').value
  }

  console.log(`📅 Programmation d'entretien pour ${candidateName}:`, formData)

  // Ici vous pouvez ajouter l'appel API pour sauvegarder l'entretien
  // await saveInterviewToAPI(applicationId, formData)

  // Fermer le modal
  form.closest('.modal-overlay').remove()

  // Afficher une notification de succès
  showNotification(`Entretien programmé pour ${candidateName}`, "success")

  // Mettre à jour l'affichage (optionnel)
  // updateInterviewDisplay(applicationId, formData)
}

// Fonction pour voir les détails d'un entretien
function viewInterviewDetails(applicationId) {
  console.log(`👁️ Affichage des détails de l'entretien pour l'application ${applicationId}`)
  showNotification("Fonctionnalité en cours de développement", "info")
}

// Fonction pour reprogrammer un entretien
function rescheduleInterview(applicationId) {
  console.log(`🔄 Reprogrammation de l'entretien pour l'application ${applicationId}`)
  showNotification("Fonctionnalité en cours de développement", "info")
}
