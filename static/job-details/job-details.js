// Global variables
let currentJob = null
let applications = []
let currentUser = null

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

document.addEventListener("DOMContentLoaded", () => {
  loadCurrentUser()
  loadJobData()
})

async function loadCurrentUser() {
  try {
    const response = await fetch("/api/current-user")
    const result = await response.json()

    if (result.success) {
      currentUser = result.user
    } else {
      console.error("Erreur chargement utilisateur:", result.message)
      if (result.message === "Utilisateur non connecté") {
        window.location.href = "/enterprise-login"
      }
    }
  } catch (error) {
    console.error("Erreur réseau chargement utilisateur:", error)
  }
}

function loadJobData() {
  const urlParams = new URLSearchParams(window.location.search)
  const jobId = urlParams.get("id")

  if (jobId) {
    loadJobFromAPI(jobId)
  } else {
    const jobData = localStorage.getItem("selectedJob")
    if (jobData) {
      try {
        currentJob = JSON.parse(jobData)
        displayJobInfo()
        renderApplicationsWithCompatibility()
        setTimeout(() => {
          initializeSkillsValidationState()
        }, 100)
      } catch (error) {
        console.error("Erreur parsing localStorage:", error)
        showError("Erreur lors du chargement des données du poste")
      }
    } else {
      showError("Aucun poste sélectionné. Veuillez retourner au dashboard et sélectionner un poste.")
    }
  }
}

async function loadInterviewDataForApplications() {
  console.log("[v0] Starting to load interview data for applications:", applications.length)

  for (let i = 0; i < applications.length; i++) {
    const app = applications[i]
    console.log("[v0] Processing application ID:", app.id, "for candidate:", app.candidate_profile?.name)

    try {
      // Fetch interview data for this application
      const response = await fetch(`/api/interview/${app.id}`)
      console.log("[v0] API response status for app", app.id, ":", response.status)

      if (response.ok) {
        const result = await response.json()
        console.log("[v0] API result for app", app.id, ":", result)

        if (result.success && result.interview) {
          console.log("[v0] Found interview data for app", app.id, ":", result.interview)

          // Merge interview data with application
          applications[i].interview_date = result.interview.interview_date
          applications[i].start_session = result.interview.start_session
          applications[i].end_session = result.interview.end_session
          applications[i].candidate_name = result.interview.candidate_name || app.candidate_profile?.name
          applications[i].interviewer_name = result.interview.interviewer_name

          // Fetch interview results if completed
          if (result.interview.end_session) {
            console.log("[v0] Interview completed, fetching results for app", app.id)

            const resultsResponse = await fetch(`/api/interview-result/${app.id}`)
            console.log("[v0] Results API response status:", resultsResponse.status)

            if (resultsResponse.ok) {
              const resultsData = await resultsResponse.json()
              console.log("[v0] Results data for app", app.id, ":", resultsData)

              if (resultsData.success && resultsData.result) {
                applications[i].interview_result = {
                  success_rate: resultsData.result.success_rate || 0,
                  dominant_emotion: resultsData.result.dominant_emotion || "Neutre",
                  duration: resultsData.result.duration || "N/A",
                  total_detections: resultsData.result.total_detections || 0,
                  avg_confidence: resultsData.result.avg_confidence || 0,
                }
                console.log("[v0] Merged interview result for app", app.id, ":", applications[i].interview_result)
              }
            } else {
              console.log("[v0] Failed to fetch results for app", app.id, "- status:", resultsResponse.status)
            }
          }
        } else {
          console.log("[v0] No interview data found for app", app.id, "- result:", result)
        }
      } else {
        console.log("[v0] Failed to fetch interview data for app", app.id, "- status:", response.status)
      }
    } catch (error) {
      console.error(`[v0] Erreur lors du chargement des données d'entretien pour l'application ${app.id}:`, error)
    }
  }

  console.log("[v0] Finished loading interview data. Applications with interview data:")
  applications.forEach((app) => {
    if (app.interview_date || app.start_session || app.end_session) {
      console.log("[v0] App", app.id, "has interview data:", {
        interview_date: app.interview_date,
        start_session: app.start_session,
        end_session: app.end_session,
        interview_result: app.interview_result,
      })
    }
  })
}

async function loadJobFromAPI(jobId) {
  try {
    showLoading("Chargement des détails du poste...")

    const response = await fetch(`/api/job-basic/${jobId}`)
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        currentJob = result.job
        applications = result.job.applications || []

        if (!applications || applications.length === 0) {
          try {
            const appsResponse = await fetch(`/api/applications?job_id=${jobId}`)
            const appsResult = await appsResponse.json()
            if (appsResult.success && appsResult.applications) {
              applications = appsResult.applications
            }
          } catch (error) {
            console.error("Erreur récupération candidatures:", error)
          }
        }

        if (applications && applications.length > 0) {
          await calculateCompatibilityForApplications()
          await loadInterviewDataForApplications()
          await loadQuizReviewsForApplications()
        }

        hideLoading()
        displayJobInfo()
        renderApplicationsWithCompatibility()
        updateCompatibilityStats()
        updateFilterCounts()

        setTimeout(() => {
          initializeSkillsValidationState()
          initializeQuizValidationState()
        }, 100)
      } else {
        showError(result.message || "Erreur lors du chargement du poste")
      }
    } else {
      showError("Erreur de connexion au serveur")
    }
  } catch (error) {
    console.error("Erreur critique:", error)
    showError("Erreur lors du chargement des données")
  }
}

async function calculateCompatibilityForApplications() {
  for (let i = 0; i < applications.length; i++) {
    const app = applications[i]
    try {
      const response = await fetch(`/api/application/${app.id}/compatibility`)
      const result = await response.json()

      if (result.success) {
        applications[i].compatibility_percentage = result.compatibility_percentage || result.score || 0
        applications[i].matched_skills_count = result.matched_count || result.matched_skills_count || 0
        applications[i].missing_skills_count = result.missing_count || result.missing_skills_count || 0
        applications[i].total_job_skills = result.total_job_skills || result.total_skills || 0
        applications[i].matched_skills = result.matched_skills || []
        applications[i].missing_skills = result.missing_skills || []

        if (applications[i].matched_skills_count === 0 && applications[i].missing_skills_count === 0) {
          const fallback = calculateCompatibilityFallback(
            applications[i].compatibility_percentage,
            applications[i].total_job_skills || currentJob.skills?.length || 0,
          )
          applications[i].matched_skills_count = fallback.matched
          applications[i].missing_skills_count = fallback.missing
          applications[i].total_job_skills = applications[i].total_job_skills || currentJob.skills?.length || 0
        }
      } else {
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
      const fallback = calculateCompatibilityFallback(app.compatibility_percentage || 0, currentJob.skills?.length || 0)
      applications[i].compatibility_percentage = app.compatibility_percentage || 0
      applications[i].matched_skills_count = fallback.matched
      applications[i].missing_skills_count = fallback.missing
      applications[i].total_job_skills = currentJob.skills?.length || 0
    }
  }
}

function calculateCompatibilityFallback(compatibilityPercentage, totalSkills) {
  if (!totalSkills || totalSkills === 0) return { matched: 0, missing: 0 }

  const matched = Math.round((compatibilityPercentage / 100) * totalSkills)
  const missing = totalSkills - matched

  return { matched, missing }
}

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
  }
}

function displayJobInfo() {
  if (!currentJob) return

  const elements = {
    jobTitle: currentJob.title || "Titre non disponible",
    jobDepartment: currentJob.department_name || "Département non spécifié",
    jobDescription: currentJob.description || "Description non disponible",
    jobResponsibilities: currentJob.responsibilities || "Aucune responsabilité spécifiée",
    jobType: (currentJob.employment_type || "").toUpperCase(),
    jobPriority: (currentJob.priority || "").toUpperCase(),
    jobDeadline: currentJob.deadline ? formatDateSafe(currentJob.deadline) : "Non définie",
    jobStatus: (currentJob.status || "").toUpperCase(),
    jobSalary: getSalaryText(),
    contractType: (currentJob.employment_type || "").toUpperCase(),
    jobCreated: formatDateSafe(currentJob.created_at),
    assignedEmployee: currentJob.assigned_employee_name || "Non assigné",
    jobApplications: getApplicationsCount(),
    daysRemaining: getDaysRemaining(),
  }

  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id)
    if (element) {
      if (id === "jobStatus") {
        element.textContent = value
        element.className = `status-badge ${currentJob.status || "draft"}`
      } else {
        element.textContent = value
      }
    }
  })

  renderJobSkills()
}

function getSalaryText() {
  if (currentJob.salary_min && currentJob.salary_max) {
    return `${currentJob.salary_min} - ${currentJob.salary_max} TND`
  } else if (currentJob.salary_min) {
    return `${currentJob.salary_min}+ TND`
  }
  return "Non spécifié"
}

function getApplicationsCount() {
  return typeof currentJob.applications_count === "number" && !isNaN(currentJob.applications_count)
    ? currentJob.applications_count
    : Array.isArray(applications)
      ? applications.length
      : 0
}

function getDaysRemaining() {
  let days = currentJob.days_remaining
  if (days === null || days === undefined) {
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
      }
    }
  }
  return days !== null && days !== undefined ? days : "--"
}

function renderJobSkills() {
  const skillsContainer = document.getElementById("jobSkillsContainer")
  if (!skillsContainer) return

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

  if (!Array.isArray(currentJob.skills)) {
    skillsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-exclamation-triangle"></i>
          <h4>Erreur de données</h4>
          <p>Format des compétences invalide. Veuillez contacter l'administrateur.</p>
        </div>
      `
    return
  }

  const validSkills = currentJob.skills.filter((skill) => skill && typeof skill === "object")

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

  const count = validSkills.length
  const singleClass = count === 1 ? ' single-skill' : ''
  const densityClass = count <= 6 ? ' skills-few' : (count <= 24 ? ' skills-many' : ' skills-tons')
  skillsContainer.innerHTML = `
      <div class="skills-grid${singleClass}${densityClass}">
        ${validSkills
          .map((skill) => {
            const skillName = skill.name || skill.skill_name || skill.skill || "Compétence non spécifiée"
            const skillLevel = skill.level || skill.skill_level || skill.experience || "N/A"
            const isRequired =
              skill.required !== undefined ? skill.required : skill.is_required !== undefined ? skill.is_required : true

            let formattedLevel = "N/A"
            if (skillLevel && typeof skillLevel === "string" && skillLevel.length > 0) {
              formattedLevel = skillLevel.charAt(0).toUpperCase() + skillLevel.slice(1)
            }

            return `
                <div class="skill-item">
                  <div class="skill-name" data-tooltip="${skillName}">${skillName}</div>
                  <div class="skill-level">${formattedLevel}</div>
                  ${
                    isRequired
                      ? `<span class=\"skill-required-badge\">Requis</span>`
                      : `<span class=\"skill-optional-badge\">Optionnel</span>`
                  }
                  <div class="skill-collapsible"></div>
                </div>
              `
          })
          .join("")}
      </div>
    `
}

function initializeSkillsValidationState() {
  applications.forEach((app) => {
    const quizSection = document.getElementById(`quiz-section-${app.id}`)
    const validateBtn = document.getElementById(`validate-btn-${app.id}`)
    const validationStatus = document.getElementById(`validation-status-${app.id}`)

    if (app.skills_validated) {
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
  const container = document.getElementById("applicationsList")
  if (!container) return

  let filteredApplications = applications
  if (filter !== "all") {
    filteredApplications = applications.filter((app) => app.status === filter)
  }

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

  const isDeptHead = currentUser && currentUser.role === "department_head"

  container.innerHTML = filteredApplications
    .map((app) => {
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
            <div class="detail-section quiz-section ${!app.skills_validated ? "locked" : ""}" id="quiz-section-${app.id}">
              
              ${
                !app.skills_validated
                  ? `
                <div class="quiz-validation-overlay">
                  <div class="quiz-validation-number">2</div>
                  <div class="quiz-validation-message">En attente de validation des compétences</div>
                  ${isDeptHead ? '' : `
                  <button class="btn-validate-skills-overlay" onclick="validateSkillsAndRemoveOverlay(${app.id})" id="validate-btn-overlay-${app.id}">
                    <i class="fas fa-check-double"></i> Valider les compétences
                  </button>
                  `}
                </div>
              `
                  : ""
              }

              <h4>
                <i class="fas fa-chart-bar"></i> Évaluation Quiz
              </h4>
              
              <div class="quiz-content">
                <div class="quiz-overview">
                  <!-- Debug: Log quiz data -->
                  <script>console.log('Quiz data for ${candidateName}:', ${JSON.stringify({
                    quiz_score: app.quiz_score,
                    quiz_duration: app.quiz_duration,
                    quiz_correct_answers: app.quiz_correct_answers,
                    quiz_total_questions: app.quiz_total_questions,
                  })});</script>
                  <div class="quiz-info-grid">
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-chart-pie"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Score</div>
                        <div class="info-value">${!app.quiz_id ? "en attente de generation de quiz" : !app.quiz_score ? "en attente du condidat" : app.quiz_score + "%"}</div>
                      </div>
                    </div>
                    
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-clock"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Durée</div>
                        <div class="info-value">${!app.quiz_id ? "en attente de generation de quiz" : !app.quiz_duration ? "en attente du condidat" : formatDuration(app.quiz_duration)}</div>
                      </div>
                    </div>
                    
                    <div class="quiz-info-item">
                      <div class="info-icon">
                        <i class="fas fa-check-double"></i>
                      </div>
                      <div class="info-content">
                        <div class="info-label">Correctes</div>
                        <div class="info-value">${!app.quiz_id ? "en attente de generation de quiz" : !app.quiz_correct_answers ? "en attente du condidat" : app.quiz_correct_answers}</div>
                      </div>
                    </div>
                  </div>
                  
                  <script>console.log('DEBUG: Quiz data for ${candidateName}:', {
                    quiz_id: ${app.quiz_id || "null"},
                    quiz_score: ${app.quiz_score || "null"},
                    quiz_duration: ${app.quiz_duration || "null"},
                    quiz_correct_answers: ${app.quiz_correct_answers || "null"},
                    quiz_total_questions: ${app.quiz_total_questions || "null"}
                  });</script>
                </div>
                
                <div class="quiz-actions">
                  <div class="quiz-actions-row">
                    ${!app.quiz_id && !isDeptHead ? `
                      <button class="btn-generate-quiz" onclick="openCreateQuizModal(${app.candidate_id || app.candidate_profile_id || app.id}, '${candidateName}')">
                        <i class="fas fa-magic"></i> Générer Quiz
                      </button>
                    `
                        : ""
                    }
                    ${
                      app.quiz_id
                        ? `
                      <button class="btn-view-quiz" onclick="viewQuizResults(${app.id}, '${candidateName}')">
                        <i class="fas fa-eye"></i> Voir Quiz
                      </button>
                      <br>
                      ${app.quiz_score && app.quiz_score > 0 ? `
                        <button class="btn-analyze-ai" onclick="viewAIAnalysis(${app.id}, '${candidateName}')">
                          <i class="fas fa-robot"></i> ${app.has_quiz_review ? 'Voir analyse' : 'Analyse IA'}
                        </button>
                      ` : ''}
                    ` : ''}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- SECTION 3: INTERVIEW (VISIBLE SEULEMENT SI QUIZ VALIDÉ) -->
            <div class="detail-section interview-section ${!app.quiz_validated ? "locked" : ""}" id="interview-section-${app.id}">
              
              ${
                !app.quiz_validated
                  ? `
                <div class="interview-validation-overlay">
                  <div class="interview-validation-number">3</div>
                  <div class="interview-validation-message">
                    ${isQuizValid(app.quiz_score) 
                      ? "En attente de validation du quiz" 
                      : "Le candidat n'a pas encore complété le quiz"
                    }
                  </div>
                  ${isDeptHead ? '' : `
                  <button class="btn-validate-quiz-overlay ${!isQuizValid(app.quiz_score) ? 'disabled' : ''}" 
                          onclick="validateQuizAndRemoveOverlay(${app.id})" 
                          id="validate-quiz-btn-overlay-${app.id}"
                          ${!isQuizValid(app.quiz_score) ? 'disabled' : ''}>
                    <i class="fas fa-check-double"></i> 
                    ${isQuizValid(app.quiz_score) ? 'Valider le quiz' : 'Quiz non complété'}
                  </button>
                  `}
                </div>
              `
                  : ""
              }

              <h4>
                <i class="fas fa-calendar-alt"></i> Interview
              </h4>
              
              <div class="interview-content">
                ${getInterviewContent(app)}
              </div>
            </div>

          </div>
          
          <div class="application-actions">
            ${renderCandidateActions(app)}
          </div>
          
          ${""}
        </div>
      </div>
    `
    })
    .join("")

  updateFilterCounts()
}

function toggleCandidateCard(appId) {
  const expandedContent = document.getElementById(`expanded-${appId}`)
  const toggleButton = document.querySelector(`[data-app-id="${appId}"] .expand-toggle`)
  const cardElement = document.querySelector(`[data-app-id="${appId}"]`)

  if (!expandedContent || !toggleButton) return

  const isExpanded = expandedContent.classList.contains("expanded")

  if (isExpanded) {
    expandedContent.classList.remove("expanded")
    toggleButton.classList.remove("expanded")
  } else {
    expandedContent.classList.add("expanded")
    toggleButton.classList.add("expanded")

    setTimeout(() => {
      if (cardElement) {
        const cardRect = cardElement.getBoundingClientRect()
        const windowHeight = window.innerHeight
        const isFullyVisible = cardRect.top >= 0 && cardRect.bottom <= windowHeight

        if (!isFullyVisible) {
          let targetScrollY
          if (cardRect.top < 0) {
            targetScrollY = window.pageYOffset + cardRect.top - 50
          } else if (cardRect.bottom > windowHeight) {
            targetScrollY = window.pageYOffset + (cardRect.bottom - windowHeight + 100)
          }

          cardElement.style.transition = "box-shadow 0.3s ease"
          cardElement.style.boxShadow = "0 0 20px rgba(0, 212, 255, 0.3)"

          window.scrollTo({
            top: Math.max(0, targetScrollY),
            behavior: "smooth",
          })

          setTimeout(() => {
            cardElement.style.boxShadow = ""
          }, 1500)
        }
      }
    }, 100)
  }
}

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

async function viewCompatibilityDetails(applicationId) {
  try {
    showLoading("Chargement des détails de compatibilité...")

    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()

    hideLoading()

    if (result.success) {
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
    console.error("Erreur chargement détails compatibilité:", error)
    showNotification("Erreur de connexion", "error")
  }
}

function showDarkCompatibilityModal(
  compatibilityData,
  compatibilityPercentage,
  compatibilitySource,
  compatibilityReason,
) {
  console.log("[Compatibility Modal] Creating modal with data:", compatibilityData)
  console.log("[Compatibility Modal] Percentage:", compatibilityPercentage)
  
  // Check if modal already exists and remove it
  const existingModal = document.querySelector('.compatibility-modal-overlay')
  if (existingModal) {
    console.log("[Compatibility Modal] Removing existing modal")
    existingModal.remove()
  }
  
  const modal = document.createElement("div")
  modal.className = "modal-overlay compatibility-modal-overlay"
  // Remove inline styles to let CSS take precedence

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
                    <span class="skill-name" data-tooltip="${skill.name || skill.skill_name || 'Compétence non spécifiée'}" style="
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
                    <span class="skill-name" data-tooltip="${skill.name || skill.skill_name || 'Compétence non spécifiée'}" style="
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

  console.log("[Compatibility Modal] Adding modal to DOM")
  document.body.appendChild(modal)
  console.log("[Compatibility Modal] Modal added to DOM, checking visibility")
  console.log("[Compatibility Modal] Modal element:", modal)
  console.log("[Compatibility Modal] Modal computed style:", window.getComputedStyle(modal))
  
  // Force modal to be visible
  setTimeout(() => {
    console.log("[Compatibility Modal] Checking modal visibility after timeout")
    modal.style.display = 'flex'
    modal.style.opacity = '1'
    modal.style.visibility = 'visible'
    console.log("[Compatibility Modal] Modal style after force show:", modal.style.cssText)
  }, 100)

  // Close modal when clicking outside
  modal.addEventListener("click", (e) => {
    console.log("[Compatibility Modal] Modal clicked, target:", e.target)
    if (e.target === modal) {
      console.log("[Compatibility Modal] Closing modal")
      modal.remove()
    }
  })
}

function getLevelText(level) {
  const levelTexts = {
    beginner: "Débutant",
    intermediate: "Intermédiaire",
    advanced: "Avancé",
    expert: "Expert",
  }
  return levelTexts[level] || level
}

function renderCandidateActions(app) {
  const candidateName = app.name || app.candidate_name || "Candidat inconnu"
  const candidateId = app.candidate_id || app.candidate_profile_id || app.id

  if (currentUser && currentUser.role === "department_head") {
    // Pour les chefs de département : toujours afficher "Voir profil"
    const parts = []
    if ((app.status === "pending" || app.status === "reviewed") && !app.is_recommended) {
      const safeCandidateName = String(candidateName).replace(/'/g, "\\'").replace(/"/g, '\\"')
      const safeJobTitle = String((currentJob && (currentJob.title || currentJob.job_title)) || "Poste").replace(/'/g, "\\'").replace(/"/g, '\\"')
      parts.push(`
      <button class="btn-action recommend" onclick="showRecommendModal(${app.id}, '${safeCandidateName}', '${safeJobTitle}')">
        <i class="fas fa-thumbs-up"></i> Recommander
      </button>
    `)
    }
    if (app.is_recommended) {
      parts.push(`
      <button class="btn-action recommend" onclick="showRecommendationDetails(${app.id})">
        <i class="fas fa-comment"></i> Commentaire
      </button>
    `)
    }
    parts.push(`
      <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
        <i class="fas fa-info-circle"></i> Voir profil
      </button>
    `)
    return parts.join("\n")
  }

  // Pour les recruteurs
  if (currentUser && currentUser.role === "recruiter") {
    const parts = []
    
    if (app.status === "pending") {
      parts.push(`
      <button class="btn-action review" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-eye"></i> Examiner
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
        <i class="fas fa-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
      `)
    } else if (app.status === "reviewed") {
      parts.push(`
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
        <i class="fas fa-check-circle"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
      `)
    } else if (app.status === "interview_scheduled") {
      parts.push(`
      <button class="btn-action complete" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-check-double"></i> Entretien terminé
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
        <i class="fas fa-user-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
      `)
    } else if (app.status === "accepted_pending_validation") {
      parts.push(`
      <span class="status-badge pending-validation">
        <i class="fas fa-clock"></i> En attente validation admin
      </span>
      `)
    }
    
    // Ajouter le bouton de recommandation si le candidat est recommandé
    if (app.is_recommended) {
      parts.push(`
      <button class="btn-action recommend" onclick="showRecommendationDetails(${app.id})">
        <i class="fas fa-comment"></i> Commentaire
      </button>
      `)
    }
    
    // Toujours ajouter le bouton voir profil
    parts.push(`
    <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
      <i class="fas fa-info-circle"></i> Voir profil
    </button>
    `)
    
    return parts.join("\n")
  }

  // Pour les administrateurs
  if (currentUser && currentUser.role === "admin") {
    const parts = []
    
    if (app.status === "accepted_pending_validation") {
      parts.push(`
      <button class="btn-action validate" onclick="showAdminValidationModal(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-user-shield"></i> Valider
      </button>
      `)
    } else if (app.status === "pending" || app.status === "reviewed" || app.status === "interview_scheduled") {
      parts.push(`
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${candidateName}', '${currentJob.title}', '${currentJob.department_name || currentJob.department || "Département"}')">
        <i class="fas fa-check"></i> Accepter définitivement
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${candidateName}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
      `)
    }
    
    // Ajouter le bouton de recommandation si le candidat est recommandé
    if (app.is_recommended) {
      parts.push(`
      <button class="btn-action recommend" onclick="showRecommendationDetails(${app.id})">
        <i class="fas fa-comment"></i> Commentaire
      </button>
      `)
    }
    
    // Toujours ajouter le bouton voir profil
    parts.push(`
    <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
      <i class="fas fa-info-circle"></i> Voir profil
    </button>
    `)
    
    return parts.join("\n")
  }

  // Pour tous les autres cas
  return `
  <button class="btn-action info" onclick="viewCandidateProfile(${candidateId})">
    <i class="fas fa-info-circle"></i> Voir profil
  </button>
`
}

// Affiche un modal léger avec le commentaire de recommandation
function showRecommendationDetails(applicationId) {
  try {
    const app = (Array.isArray(applications) ? applications : []).find(a => String(a.id) === String(applicationId))
    const comment = (app && app.recommendation_comment) || "Aucun commentaire saisi"
    const priority = (app && app.recommendation_priority) || "normal"

    const overlay = document.createElement('div')
    overlay.className = 'recommend-modal-overlay'
    // Fallback inline styles in case CSS isn't loaded yet
    overlay.style.position = 'fixed'
    overlay.style.top = '0'
    overlay.style.left = '0'
    overlay.style.width = '100%'
    overlay.style.height = '100%'
    overlay.style.display = 'flex'
    overlay.style.alignItems = 'center'
    overlay.style.justifyContent = 'center'
    overlay.style.zIndex = '30000'
    overlay.style.background = overlay.style.background || 'rgba(0,0,0,0.75)'

    overlay.innerHTML = `
      <div class="recommend-modal" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h3><i class="fas fa-comment"></i> Commentaire de recommandation</h3>
          <button class="modal-close" onclick="this.closest('.recommend-modal-overlay').remove()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="recommendation-comment">
            <p><strong>Priorité:</strong> <span class="recommendation-badge ${priority}">${priority}</span></p>
            <p>${comment}</p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-confirm" onclick="this.closest('.recommend-modal-overlay').remove()"><i class="fas fa-check"></i> Fermer</button>
        </div>
      </div>
    `

    // Close on backdrop click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove()
      }
    })

    document.body.appendChild(overlay)
  } catch (e) {
    console.error('Erreur lors de l\'affichage du commentaire de recommandation:', e)
    if (typeof showNotification === 'function') {
      showNotification("Impossible d'afficher le commentaire de recommandation", 'error')
    }
  }
}

// Copie du modal de recommandation du dashboard pour un rendu identique
function showRecommendModal(applicationId, candidateName, jobTitle) {
  if (!currentUser || currentUser.role !== "department_head") {
    showNotification("Seuls les chefs de département peuvent recommander des candidatures", "warning")
    return
  }

  const existingModal = document.querySelector(".recommend-modal-overlay")
  if (existingModal) existingModal.remove()

  const modal = document.createElement("div")
  modal.className = "modal-overlay recommend-modal-overlay"
  modal.style.cssText = `
position: fixed; top: 0; left: 0; width: 100%; height: 100%;
background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(10px);
display: flex; align-items: center; justify-content: center;
z-index: 25000; padding: 2rem; opacity: 0; transition: opacity 0.3s ease;`

  modal.innerHTML = `
<div class="modal-content recommend-modal" style="
background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
border: 2px solid rgba(243, 156, 18, 0.4);
border-radius: 20px; max-width: 550px; width: 95%; max-height: 85vh;
overflow: hidden; display: flex; flex-direction: column;
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
transform: scale(0.95); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);">
  <div class="modal-header" style="flex-shrink: 0; background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 1.5rem 2rem; border-bottom: none; position: relative; border-radius: 20px 20px 0 0;">
    <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.75rem;">
      <i class="fas fa-thumbs-up" style="color: #f39c12;"></i>
      Recommander cette candidature
    </h3>
    <button class="modal-close" onclick="closeRecommendModal()" style="position: absolute; top: 1.5rem; right: 1.5rem; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); font-size: 1.2rem;">&times;</button>
  </div>
  <div class="modal-body" style="flex: 1; overflow-y: auto; overflow-x: hidden; padding: 2rem; background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);">
    <div class="candidate-info-modal" style="display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05)); border: 1px solid rgba(243, 156, 18, 0.3); border-radius: 16px; margin-bottom: 2rem; position: relative; overflow: hidden;">
      <div class="candidate-avatar-modal" style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #f39c12, #e67e22); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.5rem; flex-shrink: 0; box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);">${(candidateName || '').split(' ').map(n=>n[0]).join('')}</div>
      <div>
        <h4 style="color: #f8fafc; margin: 0 0 0.5rem 0; font-size: 1.25rem; font-weight: 700;">${candidateName}</h4>
        <p style="color: #cbd5e1; margin: 0.25rem 0; font-size: 0.95rem;"><strong>Poste:</strong> ${jobTitle}</p>
        <p style="color: #cbd5e1; margin: 0.25rem 0; font-size: 0.95rem;"><strong>Votre rôle:</strong> Chef de département</p>
      </div>
    </div>
    <div class="form-group" style="margin-bottom: 2rem;">
      <label class="form-label" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; color: #f1f5f9; font-weight: 600; font-size: 0.95rem;">
        <i class="fas fa-comment" style="color: #f39c12;"></i>
        Commentaire de recommandation *
      </label>
      <textarea id="recommendationComment" class="form-textarea" placeholder="Expliquez pourquoi vous recommandez ce candidat (compétences, expérience, adéquation au poste...)..." rows="4" required style="width: 100%; padding: 1rem; border: 2px solid rgba(203, 213, 225, 0.3); border-radius: 12px; font-size: 0.95rem; transition: all 0.3s; background: rgba(248, 250, 252, 0.95); color: #1e293b; font-weight: 500; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); font-family: inherit; resize: vertical; line-height: 1.5;"></textarea>
      <small class="form-help" style="color: #cbd5e1; font-size: 0.85rem; margin-top: 0.5rem; font-style: italic; display: flex; align-items: center; gap: 0.5rem;">💡 Ce commentaire sera visible par les recruteurs et super admins</small>
    </div>
    <div class="form-group" style="margin-bottom: 2rem;">
      <label class="form-label" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; color: #f1f5f9; font-weight: 600; font-size: 0.95rem;">
        <i class="fas fa-flag" style="color: #f39c12;"></i>
        Niveau de priorité de votre recommandation
      </label>
      <select id="recommendationPriority" class="form-select" style="width: 100%; padding: 1rem; border: 2px solid rgba(203, 213, 225, 0.3); border-radius: 12px; font-size: 0.95rem; transition: all 0.3s; background: rgba(248, 250, 252, 0.95); color: #1e293b; font-weight: 500; box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1); cursor: pointer;">
        <option value="normal">📋 Recommandation normale</option>
        <option value="high">⭐ Recommandation forte</option>
        <option value="urgent">🔥 Recommandation urgente</option>
      </select>
      <small class="form-help" style="color: #cbd5e1; font-size: 0.85rem; margin-top: 0.5rem; font-style: italic; display: flex; align-items: center; gap: 0.5rem;">💡 Choisissez le niveau selon l'adéquation du candidat</small>
    </div>
    <div class="recommendation-info" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05)); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px; padding: 1.5rem; margin-top: 2rem; position: relative;">
      <h5 style="margin: 0 0 1rem 0; color: #f8fafc; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">
        <i class="fas fa-info-circle" style="color: #3b82f6;"></i>
        Cette action va :
      </h5>
      <ul style="margin: 0; padding-left: 1.5rem; list-style: none;">
        <li style="margin: 0.75rem 0; color: #cbd5e1; font-weight: 500; display: flex; align-items: center; gap: 0.75rem;"><i class="fas fa-star" style="color: #f59e0b; width: 20px; font-size: 1rem;"></i> Marquer la candidature comme recommandée</li>
        <li style="margin: 0.75rem 0; color: #cbd5e1; font-weight: 500; display: flex; align-items: center; gap: 0.75rem;"><i class="fas fa-bell" style="color: #17a2b8; width: 20px; font-size: 1rem;"></i> Notifier les recruteurs et super admins</li>
        <li style="margin: 0.75rem 0; color: #cbd5e1; font-weight: 500; display: flex; align-items: center; gap: 0.75rem;"><i class="fas fa-arrow-up" style="color: #28a745; width: 20px; font-size: 1rem;"></i> Donner une priorité élevée à cette candidature</li>
        <li style="margin: 0.75rem 0; color: #cbd5e1; font-weight: 500; display: flex; align-items: center; gap: 0.75rem;"><i class="fas fa-user-tie" style="color: #007bff; width: 20px; font-size: 1rem;"></i> Associer votre nom à cette recommandation</li>
      </ul>
    </div>
  </div>
  <div class="modal-footer" style="flex-shrink: 0; display: flex; justify-content: flex-end; gap: 1rem; padding: 1.5rem 2rem; border-top: 1px solid rgba(59, 130, 246, 0.2); background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 0 0 20px 20px;">
    <button class="btn-secondary" onclick="closeRecommendModal()" style="padding: 0.875rem 1.75rem; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem; background: linear-gradient(135deg, #64748b, #475569); color: white; border: 1px solid rgba(100, 116, 139, 0.3);"><i class="fas fa-times"></i> Annuler</button>
    <button class="btn-primary recommend" onclick="confirmRecommendation(${applicationId})" style="padding: 0.875rem 1.75rem; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem; background: linear-gradient(135deg, #f39c12, #e67e22); color: white; border: 1px solid rgba(243, 156, 18, 0.3); box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);"><i class="fas fa-thumbs-up"></i> Confirmer la recommandation</button>
  </div>
</div>`

  document.body.appendChild(modal)
  document.body.style.overflow = "hidden"
  requestAnimationFrame(() => {
    modal.style.opacity = "1"
    const modalContent = modal.querySelector(".recommend-modal")
    if (modalContent) modalContent.style.transform = "scale(1)"
  })
  modal.addEventListener("click", (e) => { if (e.target === modal) closeRecommendModal() })
}

function closeRecommendModal() {
  const modal = document.querySelector(".recommend-modal-overlay")
  if (!modal) return
  modal.style.opacity = "0"
  const modalContent = modal.querySelector(".recommend-modal")
  if (modalContent) modalContent.style.transform = "scale(0.95)"
  setTimeout(() => { if (modal.parentElement) modal.remove(); document.body.style.overflow = "auto" }, 300)
}

async function confirmRecommendation(applicationId) {
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
      showNotification("Le commentaire de recommandation est obligatoire", "warning"); commentElement.focus(); return
    }
    if (comment.length < 10) {
      showNotification("Le commentaire doit contenir au moins 10 caractères", "warning"); commentElement.focus(); return
    }
    closeRecommendModal(); showLoading("Traitement de votre recommandation...")
    const response = await fetch(`/api/applications/${applicationId}/recommend`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ comment, priority }) })
    const result = await response.json(); hideLoading()
    if (response.ok && (result.success || result.message)) {
      showNotification(`✅ ${result.message || "Candidature recommandée avec succès"}`, "success")
      if (result.recommended_by || result.recommendation_comment) {
        showNotification("🎯 Les recruteurs et super admins ont été notifiés de votre recommandation", "info")
      }
      setTimeout(() => { loadJobData && loadJobData() }, 600)
    } else {
      showNotification(result.message || "Erreur lors de la recommandation", "error")
    }
  } catch (error) {
    console.error("❌ Erreur réseau recommandation candidature:", error)
    hideLoading(); showNotification("❌ Erreur de connexion lors de la recommandation", "error")
  }
}

function goBackToDashboard() {
  window.location.href = "/dashboard"
}

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

function initializeQuizValidationState() {
  applications.forEach((app) => {
    const interviewSection = document.getElementById(`interview-section-${app.id}`)
    const validateQuizBtn = document.getElementById(`validate-quiz-btn-overlay-${app.id}`)

    if (app.quiz_validated) {
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
function showAdminValidationModal(applicationId, candidateName, jobTitle) {
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

async function confirmAdminValidation(applicationId) {
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
    console.error("Erreur validation admin:", error)
    showNotification("Erreur de connexion lors de la validation", "error")
  }
}

function showRecommendConfirmation(applicationId, candidateName, jobTitle) {
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
          <label for="recommendationComment_${applicationId}">Commentaire de recommandation :</label>
          <textarea id="recommendationComment_${applicationId}" placeholder="Expliquez pourquoi vous recommandez ce candidat..." rows="3" required></textarea>
          
          <label for="recommendationPriority_${applicationId}">Niveau de recommandation :</label>
          <select id="recommendationPriority_${applicationId}">
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

async function confirmRecommendApplication(applicationId) {
  try {
    const commentElement = document.getElementById(`recommendationComment_${applicationId}`)
    const priorityElement = document.getElementById(`recommendationPriority_${applicationId}`)

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
      showNotification(`✅ ${result.message || "Candidature recommandée avec succès"}`, "success")

      setTimeout(async () => {
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)

      setTimeout(() => {
        showNotification("🎯 Les recruteurs et super admins ont été notifiés de votre recommandation", "info")
      }, 2000)
    } else {
      showNotification(`❌ ${result.message}`, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("Erreur réseau recommandation candidature:", error)
    showNotification("❌ Erreur de connexion lors de la recommandation", "error")
  }
}

function showAcceptConfirmation(applicationId, candidateName, jobTitle, departmentName) {
  const isAdmin = currentUser && currentUser.role === "admin"
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

function showRejectConfirmation(applicationId, candidateName, jobTitle) {
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

function handleEscapeKey(e) {
  if (e.key === "Escape") {
    closeConfirmationModal()
  }
}

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

async function confirmAcceptApplication(applicationId) {
  try {
    closeConfirmationModal()
    showLoading("Traitement de l'acceptation...")

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
    console.error("Erreur réseau ou système:", error)
    hideLoading()
    showNotification("Erreur inattendue lors de la communication avec le serveur", "error")
  }
}

async function confirmRejectApplication(applicationId) {
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
      showNotification(result.message || "Candidature rejetée", "success")

      setTimeout(async () => {
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)
    } else {
      showNotification(result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("Erreur réseau rejet candidature:", error)
    showNotification("Erreur de connexion lors du rejet", "error")
  }
}

async function updateApplicationStatus(applicationId, newStatus) {
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
      showNotification(result.message, "success")

      setTimeout(async () => {
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)
    } else {
      showNotification(result.message, "error")
    }
  } catch (error) {
    console.error("Erreur réseau mise à jour statut:", error)
    showNotification("Erreur de connexion", "error")
  }
}

function filterApplications(filter) {
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

function viewCandidateProfile(candidateId) {
  window.location.href = `/candidate-profile/${candidateId}`
}

function showLoading(message) {
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

function updateFilterCounts() {
  // Initialiser les compteurs à 0 par défaut
  const counts = {
    all: 0,
    pending: 0,
    reviewed: 0,
    accepted: 0,
    rejected: 0,
  }

  // Mettre à jour les compteurs si des candidatures existent
  if (applications && applications.length > 0) {
    counts.all = applications.length
    counts.pending = applications.filter((app) => app.status === "pending").length
    counts.reviewed = applications.filter((app) => app.status === "reviewed").length
    counts.accepted = applications.filter((app) => app.status === "accepted").length
    counts.rejected = applications.filter((app) => app.status === "rejected").length
  }

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

  const sectionHeader = document.querySelector(".applications-section .section-header h3")
  if (sectionHeader) {
    sectionHeader.innerHTML = `<i class="fas fa-users"></i> Candidatures (${counts.all})`
  }
}

async function viewQuizResults(applicationId, candidateName) {
  try {


    window.location.href = `/quiz-preview/${applicationId}`  } catch (error) {
    console.error("Erreur ouverture aperçu quiz:", error)
    showNotification("Erreur lors de l'ouverture de l'aperçu du quiz", "error")
  }
}

async function loadQuizReviewsForApplications() {
  console.log("[Quiz Reviews] Starting to load quiz reviews for applications:", applications.length)

  for (let i = 0; i < applications.length; i++) {
    const app = applications[i]
    console.log("[Quiz Reviews] Processing application ID:", app.id, "for candidate:", app.candidate_profile?.name)

    try {
      // Fetch quiz review data for this application
      const response = await fetch(`/api/applications/${app.id}/quiz-review`)
      console.log("[Quiz Reviews] Response status for app", app.id, ":", response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log("[Quiz Reviews] Response data for app", app.id, ":", data)
        
        if (data.success) {
          // Add quiz review information to the application object
          app.has_quiz_review = data.has_review
          app.quiz_review = data.quiz_review
          app.quiz_review_date = data.quiz_review_date
          console.log("[Quiz Reviews] Application", app.id, "has review:", data.has_review)
        } else {
          app.has_quiz_review = false
          app.quiz_review = null
          app.quiz_review_date = null
          console.log("[Quiz Reviews] Application", app.id, "failed to load review:", data.message)
        }
      } else {
        app.has_quiz_review = false
        app.quiz_review = null
        app.quiz_review_date = null
        console.log("[Quiz Reviews] Application", app.id, "HTTP error:", response.status)
      }
    } catch (error) {
      console.error("[Quiz Reviews] Error fetching quiz review for application", app.id, ":", error)
      app.has_quiz_review = false
      app.quiz_review = null
      app.quiz_review_date = null
    }
  }
  
  console.log("[Quiz Reviews] Completed loading quiz reviews for all applications")
  console.log("[Quiz Reviews] Final applications data:", applications.map(app => ({
    id: app.id,
    has_quiz_review: app.has_quiz_review,
    quiz_review_exists: !!app.quiz_review
  })))
  
  // Update button texts based on loaded data
  applications.forEach(app => {
    if (app.quiz_score && app.quiz_score > 0) {
      updateAnalyzeButtonText(app.id, app.has_quiz_review)
    }
  })
}

async function viewAIAnalysis(applicationId, candidateName) {
  console.log("[viewAIAnalysis] Called with applicationId:", applicationId, "candidateName:", candidateName)
  console.log("[viewAIAnalysis] Available applications:", applications.length)
  
  // Get the button for loading state
  const button = document.querySelector(`button[onclick*="viewAIAnalysis(${applicationId}"]`)
  const originalButtonContent = button ? button.innerHTML : ''
  
  try {
    // Find the application in our loaded data
    const app = applications.find(a => a.id === applicationId)
    console.log("[viewAIAnalysis] Found app:", app)
    console.log("[viewAIAnalysis] App has_quiz_review:", app?.has_quiz_review)
    console.log("[viewAIAnalysis] App quiz_review:", app?.quiz_review ? "EXISTS" : "NULL")
    
    if (app && app.has_quiz_review && app.quiz_review) {
      console.log("[viewAIAnalysis] Showing modal with existing review")
      // Show existing review in a modal using already loaded data
      showAIAnalysisModal(app.quiz_review, app.quiz_review_date, candidateName)
    } else {
      console.log("[viewAIAnalysis] No review exists in loaded data, checking API directly")
      
      // Show loading state while checking API
      if (button) {
        button.disabled = true
        button.innerHTML = '<i class="fas fa-circle-notch spinning"></i> Vérification...'
        button.style.opacity = '0.7'
      }
      
      // Fallback: Check API directly in case data wasn't loaded properly
      try {
        const response = await fetch(`/api/applications/${applicationId}/quiz-review`)
        const data = await response.json()
        
        if (data.success && data.has_review) {
          console.log("[viewAIAnalysis] Found review via API, showing modal")
          // Reset button state
          if (button) {
            button.disabled = false
            button.innerHTML = originalButtonContent
            button.style.opacity = '1'
          }
          showAIAnalysisModal(data.quiz_review, data.quiz_review_date, candidateName)
        } else {
          console.log("[viewAIAnalysis] No review exists, generating one automatically")
          // No review exists, generate one automatically using the same logic as quiz preview
          await generateAIAnalysis(applicationId, candidateName)
        }
      } catch (apiError) {
        console.error("[viewAIAnalysis] API fallback error:", apiError)
        showNotification("Erreur lors de la récupération de l'analyse IA", "error")
        
        // Reset button state on error
        if (button) {
          button.disabled = false
          button.innerHTML = originalButtonContent
          button.style.opacity = '1'
        }
      }
    }
  } catch (error) {
    console.error("Erreur lors de la récupération de l'analyse IA:", error)
    showNotification("Erreur lors de la récupération de l'analyse IA", "error")
    
    // Reset button state on error
    if (button) {
      button.disabled = false
      button.innerHTML = originalButtonContent
      button.style.opacity = '1'
    }
  }
}

function showAIAnalysisModal(review, reviewDate, candidateName) {
  console.log("[AI Analysis Modal] Creating modal for:", candidateName)
  console.log("[AI Analysis Modal] Review exists:", !!review)
  console.log("[AI Analysis Modal] Review content:", review)
  console.log("[AI Analysis Modal] Review date:", reviewDate)
  
  // Check if modal already exists and remove it
  const existingModal = document.querySelector('.ai-analysis-modal')
  if (existingModal) {
    console.log("[AI Analysis Modal] Removing existing modal")
    existingModal.remove()
  }
  
  const modal = document.createElement("div")
  modal.className = "modal-overlay ai-analysis-modal"
  // Remove inline styles to let CSS take precedence
  
  const modalContent = document.createElement("div")
  modalContent.className = "ai-analysis-modal-content"
  modalContent.style.cssText = `
    background: #1e293b;
    border-radius: 16px;
    padding: 2rem;
    max-width: 90%;
    max-height: 90%;
    overflow-y: auto;
    border: 1px solid #475569;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
    position: relative;
  `
  
  const header = document.createElement("div")
  header.style.cssText = `
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #475569;
  `
  
  const title = document.createElement("h2")
  title.textContent = `Analyse IA - ${candidateName}`
  title.style.cssText = `
    color: #f1f5f9;
    margin: 0;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  `
  title.innerHTML = `<i class="fas fa-robot"></i> Analyse IA - ${candidateName}`
  
  const closeBtn = document.createElement("button")
  closeBtn.innerHTML = '<i class="fas fa-times"></i>'
  closeBtn.style.cssText = `
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem;
    cursor: pointer;
    font-size: 1rem;
  `
  closeBtn.onclick = () => document.body.removeChild(modal)
  
  const reviewDateElement = document.createElement("div")
  reviewDateElement.textContent = `Analyse générée le ${new Date(reviewDate).toLocaleDateString('fr-FR')}`
  reviewDateElement.style.cssText = `
    color: #94a3b8;
    font-size: 0.9rem;
    font-style: italic;
    margin-bottom: 1rem;
    text-align: center;
  `
  
  const content = document.createElement("div")
  content.style.cssText = `
    color: #e2e8f0;
    line-height: 1.6;
    white-space: pre-wrap;
    font-size: 0.95rem;
    background: #0f172a;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #334155;
  `
  content.textContent = review
  
  header.appendChild(title)
  header.appendChild(closeBtn)
  modalContent.appendChild(header)
  modalContent.appendChild(reviewDateElement)
  modalContent.appendChild(content)
  modal.appendChild(modalContent)
  
  console.log("[AI Analysis Modal] Adding modal to DOM")
  document.body.appendChild(modal)
  console.log("[AI Analysis Modal] Modal added to DOM, checking visibility")
  console.log("[AI Analysis Modal] Modal element:", modal)
  console.log("[AI Analysis Modal] Modal computed style:", window.getComputedStyle(modal))
  
  // Force modal to be visible
  setTimeout(() => {
    console.log("[AI Analysis Modal] Checking modal visibility after timeout")
    modal.style.display = 'flex'
    modal.style.opacity = '1'
    modal.style.visibility = 'visible'
    console.log("[AI Analysis Modal] Modal style after force show:", modal.style.cssText)
  }, 100)
  
  // Close modal when clicking outside
  modal.onclick = (e) => {
    console.log("[AI Analysis Modal] Modal clicked, target:", e.target)
    if (e.target === modal) {
      console.log("[AI Analysis Modal] Closing modal")
      document.body.removeChild(modal)
    }
  }
}

// Test function to verify modal works
function testAIModal() {
  console.log("[TEST] Testing AI Modal")
  showAIAnalysisModal("This is a test review content. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", "2024-01-15T10:30:00Z", "Test Candidate")
}

// Test function for compatibility modal
function testCompatibilityModal() {
  console.log("[TEST] Testing Compatibility Modal")
  const testData = {
    matched_count: 8,
    missing_count: 3,
    total_job_skills: 11,
    matched_skills: [
      { skill_name: "JavaScript", level: "advanced", is_required: true },
      { skill_name: "React", level: "intermediate", is_required: true },
      { skill_name: "Node.js", level: "intermediate", is_required: false }
    ],
    missing_skills: [
      { skill_name: "Python", level: "beginner", is_required: true },
      { skill_name: "Docker", level: "intermediate", is_required: false }
    ]
  }
  showDarkCompatibilityModal(testData, 75, "ai", "This candidate shows strong technical skills with excellent JavaScript and React experience. The missing Python skills can be developed through training.")
}

// Test function for AI analysis generation
function testAIGeneration(applicationId = 1) {
  console.log("[TEST] Testing AI Analysis Generation for application:", applicationId)
  generateAIAnalysis(applicationId, "Test Candidate")
}

// Test function for loading state
function testLoadingState(applicationId = 1) {
  console.log("[TEST] Testing Loading State for application:", applicationId)
  const button = document.querySelector(`button[onclick*="viewAIAnalysis(${applicationId}"]`)
  if (button) {
    button.disabled = true
    button.innerHTML = '<i class="fas fa-circle-notch spinning"></i> Test Loading...'
    button.style.opacity = '0.7'
    
    // Reset after 3 seconds
    setTimeout(() => {
      button.disabled = false
      button.innerHTML = '<i class="fas fa-robot"></i> Analyse IA'
      button.style.opacity = '1'
    }, 3000)
  } else {
    console.log("[TEST] Button not found for application:", applicationId)
  }
}

// Function to generate AI analysis automatically (same logic as quiz preview)
async function generateAIAnalysis(applicationId, candidateName) {
  console.log("[generateAIAnalysis] Starting AI analysis generation for application:", applicationId)
  
  // Get the button and show loading state
  const button = document.querySelector(`button[onclick*="viewAIAnalysis(${applicationId}"]`)
  const originalButtonContent = button ? button.innerHTML : ''
  
  try {
    // Show loading state on button
    if (button) {
      button.disabled = true
      button.innerHTML = '<i class="fas fa-circle-notch spinning"></i> Génération...'
      button.style.opacity = '0.7'
    }
    
    // Show loading notification
    showNotification("Génération de l'analyse IA en cours...", "info")
    
    // Make request to AI analysis endpoint (same as quiz preview)
    const response = await fetch(`/api/applications/${applicationId}/ai-analyze-quiz`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    const data = await response.json()
    console.log("[generateAIAnalysis] AI analysis response:", data)
    
    if (data.success) {
      console.log("[generateAIAnalysis] AI analysis successful, showing modal")
      // Show the generated review in a modal
      showAIAnalysisModal(data.quiz_review, new Date().toISOString(), candidateName)
      
      // Update the application data in our loaded applications
      const app = applications.find(a => a.id === applicationId)
      if (app) {
        app.has_quiz_review = true
        app.quiz_review = data.quiz_review
        app.quiz_review_date = new Date().toISOString()
        console.log("[generateAIAnalysis] Updated application data with new review")
      }
      
      // Update the button text to show "Voir analyse"
      updateAnalyzeButtonText(applicationId, true)
      
      showNotification("Analyse IA générée avec succès!", "success")
    } else {
      console.error("[generateAIAnalysis] AI analysis failed:", data.message)
      showNotification(`Erreur lors de la génération de l'analyse IA: ${data.message || 'Erreur inconnue'}`, "error")
      
      // Reset button to original state on error
      if (button) {
        button.disabled = false
        button.innerHTML = originalButtonContent
        button.style.opacity = '1'
      }
    }
  } catch (error) {
    console.error("[generateAIAnalysis] Error during AI analysis:", error)
    showNotification("Erreur lors de la génération de l'analyse IA", "error")
    
    // Reset button to original state on error
    if (button) {
      button.disabled = false
      button.innerHTML = originalButtonContent
      button.style.opacity = '1'
    }
  }
}

// Function to update the analyze button text
function updateAnalyzeButtonText(applicationId, hasReview) {
  const button = document.querySelector(`button[onclick*="viewAIAnalysis(${applicationId}"]`)
  if (button) {
    const icon = button.querySelector('i')
    if (icon) {
      button.innerHTML = `<i class="fas fa-robot"></i> ${hasReview ? 'Voir analyse' : 'Analyse IA'}`
    }
  }
}

// Make test functions globally available
window.testAIModal = testAIModal
window.testCompatibilityModal = testCompatibilityModal
window.testAIGeneration = testAIGeneration
window.testLoadingState = testLoadingState

function showQuizResultsModal(quizData, candidateName, applicationId) {
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

function getQuizScoreClass(score) {
  if (score >= 75) return "high"
  if (score >= 50) return "medium"
  if (score >= 25) return "low"
  return "very-low"
}

async function validateSkillsAndRemoveOverlay(applicationId) {
  try {
    const app = applications.find((a) => a.id === applicationId)
    if (!app) {
      console.error("Application non trouvée")
      return
    }

    const candidateName = app.name || app.candidate_name || "Candidat"

    showLoading("Validation des compétences en cours...")

    const response = await fetch(`/api/applications/${applicationId}/validate-skills`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        validated: true,
        notes: "Compétences validées par l'équipe RH",
      }),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      app.skills_validated = true
      app.skills_validated_at = new Date().toISOString()

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
        validationStatus.style.display = "block"
      }

      if (quizSection) {
        quizSection.classList.remove("locked")
        const overlay = quizSection.querySelector(".quiz-validation-overlay")
        if (overlay) {
          overlay.remove()
        }
      }

      showNotification(`✅ Analyse des compétences validée pour ${candidateName}`, "success")
    } else {
      showNotification(result.message || "Erreur lors de la validation", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("Erreur validation compétences:", error)
    showNotification("Erreur de connexion lors de la validation", "error")
  }
}

function isQuizValid(quizScore) {
  return quizScore && quizScore > 0 && quizScore !== null && quizScore !== undefined;
}

function showQuizValidationError() {
  showNotification("❌ Impossible de valider le quiz : le candidat n'a pas encore complété le quiz ou n'a pas de score valide.", "error");
}

async function validateQuizAndRemoveOverlay(applicationId) {
  try {
    const app = applications.find((a) => a.id === applicationId)
    if (!app) {
      console.error("Application non trouvée")
      return
    }
    
    // Vérifier que le quiz a un score valide
    if (!isQuizValid(app.quiz_score)) {
      showNotification("❌ Impossible de valider le quiz : le candidat n'a pas encore complété le quiz ou n'a pas de score valide.", "error");
      return;
    }
    
    const candidateName = app.name || app.candidate_name || "Candidat";
    
    showLoading("Validation du quiz en cours...");
    
    const response = await fetch(`/api/applications/${applicationId}/validate-quiz`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        validated: true,
        notes: "Quiz validé par l'équipe RH",
      }),
    })

    const result = await response.json()

    if (result.success) {
      app.quiz_validated = true
      app.quiz_validated_at = new Date().toISOString()

      const interviewSection = document.getElementById(`interview-section-${applicationId}`)
      if (interviewSection) {
        interviewSection.classList.remove("locked")
        const overlay = interviewSection.querySelector(".interview-validation-overlay")
        if (overlay) {
          overlay.remove()
        }
      }

      hideLoading()
      showNotification(`✅ Quiz validé pour ${candidateName}`, "success")

      const validateQuizBtn = document.getElementById(`validate-quiz-btn-overlay-${applicationId}`)
      if (validateQuizBtn) {
        validateQuizBtn.disabled = true
        validateQuizBtn.innerHTML = '<i class="fas fa-check"></i> Quiz Validé'
      }
    } else {
      hideLoading()
      showNotification(result.message || "Erreur lors de la validation", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("Erreur validation quiz:", error)
    showNotification("Erreur de connexion lors de la validation", "error")
  }
}

function handleOpenCreateQuizClick(buttonEl) {
  if (!buttonEl) return
  if (buttonEl.dataset.loading === "true") return

  buttonEl.dataset.loading = "true"
  buttonEl.disabled = true
  const originalHtml = buttonEl.innerHTML
  buttonEl.dataset.originalHtml = originalHtml
  buttonEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Ouverture...</span>'

  openCreateQuizModal()

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

async function openCreateQuizModal(candidateId = null, candidateName = null) {
  window.currentQuizCandidateId = candidateId
  window.currentQuizCandidateName = candidateName

  const modal = document.getElementById("createQuizModal")

  if (!modal) {
    console.error("Modal non trouvé")
    return
  }

  const modalHeader = modal.querySelector(".modal-header h2")
  if (modalHeader && candidateName) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz d'Évaluation pour ${candidateName}`
  } else if (modalHeader) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz d'Évaluation`
  }

  modal.classList.add("show")
  document.body.style.overflow = "hidden"

  await generateSkillsQuizConfig()
}

function closeCreateQuizModal() {
  const modal = document.getElementById("createQuizModal")

  if (modal) {
    modal.classList.remove("show")
  }

  document.body.style.overflow = "auto"

  const modalHeader = modal.querySelector(".modal-header h2")
  if (modalHeader) {
    modalHeader.innerHTML = `<i class="fas fa-question-circle"></i> Créer un Quiz`
  }

  window.currentQuizCandidateId = null
  window.currentQuizCandidateName = null
}

async function generateSkillsQuizConfig() {
  const container = document.getElementById("skillsQuizConfig")

  if (!container) {
    console.error("Container skillsQuizConfig non trouvé")
    return
  }

  container.innerHTML =
    '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Chargement des compétences...</p>'

  try {
    let jobSkills = []

    if (currentJob && currentJob.id) {
      if (currentJob.skills && Array.isArray(currentJob.skills)) {
        jobSkills = currentJob.skills
      } else if (currentJob.required_skills && Array.isArray(currentJob.required_skills)) {
        jobSkills = currentJob.required_skills
      } else if (currentJob.job_skills && Array.isArray(currentJob.job_skills)) {
        jobSkills = currentJob.job_skills
      } else if (currentJob.skills_list && Array.isArray(currentJob.skills_list)) {
        jobSkills = currentJob.skills_list
      }
    }

    if (jobSkills.length === 0) {
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

    if (jobSkills.length === 0) {
      container.innerHTML =
        '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Aucune compétence trouvée pour ce poste. Veuillez d\'abord ajouter des compétences au poste.</p>'
      return
    }

    const skillsHTML = jobSkills
      .map((skill) => {
        let skillName = ""
        if (typeof skill === "string") {
          skillName = skill.trim()
        } else if (skill && typeof skill === "object") {
          skillName =
            skill.skill_name || skill.name || skill.skill || skill.title || skill.text || "Compétence inconnue"
        } else {
          skillName = String(skill) || "Compétence inconnue"
        }

        const skillId = skillName.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase()

        return `
        <div class="skill-quiz-config">
          <div class="skill-quiz-header">
            <span class="skill-quiz-name">${skillName}</span>
          </div>
          <div class="skill-quiz-controls">
            <div class="form-group">
              <label for="questions_${skillId}">Nombre de questions</label>
              <div class="salary-range">
                <input type="number" id="questions_${skillId}" name="questions_${skillId}" min="0" max="20" value="5" required>
              </div>
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
    console.error("Erreur lors de la récupération des compétences:", error)
    container.innerHTML =
      '<p style="color: var(--error-red); text-align: center; padding: 2rem;">Erreur lors du chargement des compétences. Veuillez réessayer.</p>'
  }
}

function showQuizGenerationPopup() {
  // Create popup overlay
  const popupOverlay = document.createElement('div')
  popupOverlay.className = 'quiz-generation-popup-overlay'
  popupOverlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
    animation: fadeIn 0.3s ease;
  `

  // Create popup content
  const popupContent = document.createElement('div')
  popupContent.className = 'quiz-generation-popup-content'
  popupContent.style.cssText = `
    background: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    text-align: center;
    max-width: 400px;
    width: 90%;
    animation: slideIn 0.3s ease;
  `

  popupContent.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <i class="fas fa-clock" style="font-size: 3rem; color: #3b82f6; margin-bottom: 1rem;"></i>
      <h3 style="margin: 0 0 1rem 0; color: #1f2937; font-size: 1.5rem;">Génération du Quiz</h3>
      <p style="margin: 0; color: #6b7280; line-height: 1.6;">
        La création peut prendre 5 à 10 secondes par compétence sélectionnée.
      </p>
    </div>
    <div style="display: flex; justify-content: center; gap: 1rem;">
      <button id="continueQuizGeneration" style="
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
      ">
        <i class="fas fa-check"></i> Continuer
      </button>
      <button id="cancelQuizGeneration" style="
        background: #f3f4f6;
        color: #6b7280;
        border: 1px solid #d1d5db;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
      ">
        <i class="fas fa-times"></i> Annuler
      </button>
    </div>
  `

  // Add CSS animations
  const style = document.createElement('style')
  style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes slideIn {
      from { transform: translateY(-20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    .quiz-generation-popup-content button:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  `
  document.head.appendChild(style)

  popupOverlay.appendChild(popupContent)
  document.body.appendChild(popupOverlay)

  // Handle continue button
  const continueBtn = document.getElementById('continueQuizGeneration')
  const cancelBtn = document.getElementById('cancelQuizGeneration')

  continueBtn.addEventListener('click', () => {
    document.body.removeChild(popupOverlay)
    document.head.removeChild(style)
    // Continue with quiz generation
    proceedWithQuizGeneration()
  })

  cancelBtn.addEventListener('click', () => {
    document.body.removeChild(popupOverlay)
    document.head.removeChild(style)
    // Reset form state
    const quizForm = document.getElementById("createQuizForm")
    if (quizForm) {
      quizForm.dataset.submitting = "false"
      const submitBtn = quizForm.querySelector(".quiz-create-btn, .btn-primary")
      if (submitBtn) {
        submitBtn.disabled = false
        submitBtn.innerHTML = '<i class="fas fa-magic"></i> Générer le Quiz'
      }
    }
  })

  // Close on overlay click
  popupOverlay.addEventListener('click', (e) => {
    if (e.target === popupOverlay) {
      document.body.removeChild(popupOverlay)
      document.head.removeChild(style)
      // Reset form state
      const quizForm = document.getElementById("createQuizForm")
      if (quizForm) {
        quizForm.dataset.submitting = "false"
        const submitBtn = quizForm.querySelector(".quiz-create-btn, .btn-primary")
        if (submitBtn) {
          submitBtn.disabled = false
          submitBtn.innerHTML = '<i class="fas fa-magic"></i> Générer le Quiz'
        }
      }
    }
  })
}

async function proceedWithQuizGeneration() {
  const quizForm = document.getElementById("createQuizForm")
  if (!quizForm) return

  const submitBtn = quizForm.querySelector(".quiz-create-btn, .btn-primary")
  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : null
  if (submitBtn) {
    submitBtn.disabled = true
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Création…'
  }

  const formData = new FormData(quizForm)
  const quizData = {
    title: formData.get("quizTitle"),
    timeLimit: Number.parseInt(formData.get("quizTime")) || 45,
    skills: [],
  }

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

  jobSkills.forEach((skill) => {
    let skillName = ""
    if (typeof skill === "string") {
      skillName = skill.trim()
    } else if (skill && typeof skill === "object") {
      skillName =
        skill.skill_name || skill.name || skill.skill || skill.title || skill.text || "Compétence inconnue"
    } else {
      skillName = String(skill) || "Compétence inconnue"
    }

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

  if (!quizData.title || !quizData.timeLimit || Number.isNaN(quizData.timeLimit)) {
    showNotification("Veuillez renseigner le titre et le temps limite.", "error")
    if (submitBtn) {
      submitBtn.disabled = false
      if (originalBtnHtml) submitBtn.innerHTML = originalBtnHtml
    }
    quizForm.dataset.submitting = "false"
    return
  }
  if (quizData.skills.length === 0) {
    showNotification("Veuillez configurer au moins une compétence avec des questions.", "error")
    if (submitBtn) {
      submitBtn.disabled = false
      if (originalBtnHtml) submitBtn.innerHTML = originalBtnHtml
    }
    quizForm.dataset.submitting = "false"
    return
  }

  const formControls = quizForm.querySelectorAll("input, select, textarea, button")
  formControls.forEach((el) => {
    if (el !== submitBtn) el.disabled = true
  })

  const candidateId = window.currentQuizCandidateId || null

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
      
      // Refresh the page to show updated quiz data
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    } else {
      showNotification("Erreur lors de la création du quiz", "error")
    }
  } catch (error) {
    console.error("Erreur lors de la création du quiz:", error)
    showNotification("Erreur lors de la création du quiz", "error")
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false
      if (originalBtnHtml) submitBtn.innerHTML = originalBtnHtml
    }
    formControls.forEach((el) => {
      if (el !== submitBtn) el.disabled = false
    })
    quizForm.dataset.submitting = "false"
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const quizForm = document.getElementById("createQuizForm")

  if (quizForm) {
    quizForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      if (quizForm.dataset.submitting === "true") {
        return
      }

      // Show popup before starting quiz generation
      showQuizGenerationPopup()
    })
  }
})

function getInterviewStatusClass(status) {
  const statusClasses = {
    not_scheduled: "status-not-scheduled",
    scheduled: "status-scheduled",
    completed: "status-completed",
    cancelled: "status-cancelled",
    rescheduled: "status-rescheduled",
    passed: "status-passed",
    failed: "status-failed",
  }
  return statusClasses[status] || "status-not-scheduled"
}

function getInterviewStatusText(status) {
  const statusTexts = {
    not_scheduled: "Non programmé",
    scheduled: "Programmé",
    completed: "Terminé",
    cancelled: "Annulé",
    rescheduled: "Reprogrammé",
    passed: "Réussi",
    failed: "Échoué",
  }
  return statusTexts[status] || "Non programmé"
}

function viewInterviewResults(applicationId) {
  window.open(`/interview-results?application_id=${applicationId}`, "_blank")
}

function formatDate(dateString) {
  if (!dateString) return "Non défini"
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString("fr-FR", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  } catch (error) {
    return "Date invalide"
  }
}

// Available time slots (same as dashboard)
const availableSlots = {
  "09:00": "09:00 - 10:00",
  "10:00": "10:00 - 11:00",
  "11:00": "11:00 - 12:00",
  "14:00": "14:00 - 15:00",
  "15:00": "15:00 - 16:00",
  "16:00": "16:00 - 17:00",
};

// Selected slots for each candidate
const selectedSlotsByCandidate = {};
let currentDay = null;
let currentAppId = null;
let currentCandidateId = null;

function openScheduleInterviewModal(applicationId, candidateName) {
  currentAppId = applicationId;
  currentCandidateId = applicationId; // Using applicationId as candidateId for simplicity

  if (!selectedSlotsByCandidate[currentCandidateId]) {
    selectedSlotsByCandidate[currentCandidateId] = [];
  }
  const modal = document.createElement("div")
  modal.className = "modal-overlay interview-modal-overlay"
  modal.id = "schedulerModal"
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  `

  modal.innerHTML = `
    <div class="scheduler-container" style="
      background: var(--card);
      border-radius: 16px;
      padding: 2rem;
      width: 90%;
      max-width: 600px;
      border: 1px solid var(--border-color);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      max-height: 80vh;
      overflow-y: auto;
    ">
      <div class="header" style="
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
      ">
        <h1 style="
          color: var(--text-primary);
          font-size: 1.5rem;
          font-weight: 600;
          margin: 0 0 0.5rem 0;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        ">
          <i class="fas fa-calendar-alt"></i> Programmer un entretien
        </h1>
        <p id="candidate-info" style="
          color: var(--text-secondary);
          margin: 0;
          font-size: 0.95rem;
        ">Planification d'entretien pour ${candidateName}</p>
      </div>
      
      <div class="content">
        <div class="day-picker" style="margin-bottom: 1rem;">
          <label for="daySelect" style="
            display: block;
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 0.5rem;
          ">
            <i class="fas fa-calendar-alt"></i> Choisir un jour :
          </label>
          <input type="date" id="daySelect" style="
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 0.95rem;
          ">
        </div>
        
        <p class="selection-limit" style="
          color: var(--text-secondary);
          font-size: 0.9rem;
          margin-bottom: 1rem;
          font-style: italic;
        ">Vous ne pouvez sélectionner que 3 créneaux par jour.</p>
        
        <div id="timeSlotsContainer" class="time-slots-grid" style="
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
          margin-bottom: 1rem;
        "></div>
        
        <div id="selected-slots" class="selected-slots" style="
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: 1rem;
        ">
          <h3 style="
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
          ">
            <i class="fas fa-check-circle"></i> Créneaux sélectionnés
          </h3>
          <div id="selected-list" style="
            color: var(--text-secondary);
            font-size: 0.9rem;
          ">Aucun créneau sélectionné</div>
        </div>
        
        <div class="actions" style="
          display: flex;
          gap: 1rem;
          justify-content: flex-end;
          padding-top: 1rem;
          border-top: 1px solid var(--border-color);
        ">
          <button class="btn btn-secondary" onclick="closeScheduler()" style="
            padding: 0.75rem 1.5rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
          ">
            <i class="fas fa-arrow-left"></i> Retour
          </button>
          <button class="btn btn-primary" onclick="confirmSchedule()" style="
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-dark));
            color: white;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
          ">
            <i class="fas fa-paper-plane"></i> Envoyer
          </button>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Initialize the scheduler
  const today = new Date().toISOString().split("T")[0];
  const dayInput = document.getElementById("daySelect");
  dayInput.setAttribute("min", today);
  dayInput.value = today;
  dayInput.addEventListener("change", showTimeSlots);

  showTimeSlots();
}

function closeScheduler() {
  const modal = document.getElementById("schedulerModal");
  if (modal) {
    modal.remove();
  }
}

function showTimeSlots() {
  currentDay = document.getElementById("daySelect").value;
  const container = document.getElementById("timeSlotsContainer");
  container.innerHTML = "";

  Object.keys(availableSlots).forEach((time) => {
    const div = document.createElement("div");
    div.classList.add("time-slot");
    div.style.cssText = `
      padding: 0.75rem;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      background: var(--bg-secondary);
      color: var(--text-primary);
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.9rem;
    `;
    div.textContent = availableSlots[time];
    div.onclick = () => toggleTimeSlot(time, div);
    container.appendChild(div);
  });
}

function toggleTimeSlot(time, element) {
  const candidateSlots = selectedSlotsByCandidate[currentCandidateId] || [];
  const slotKey = `${currentDay} ${time}`;
  
  if (candidateSlots.includes(slotKey)) {
    // Remove slot
    const index = candidateSlots.indexOf(slotKey);
    candidateSlots.splice(index, 1);
    element.style.background = "var(--bg-secondary)";
    element.style.borderColor = "var(--border-color)";
    element.style.color = "var(--text-primary)";
  } else {
    // Add slot (max 3)
    if (candidateSlots.length >= 3) {
      showNotification("Vous ne pouvez sélectionner que 3 créneaux maximum", "warning");
      return;
    }
    candidateSlots.push(slotKey);
    element.style.background = "linear-gradient(135deg, var(--primary-blue), var(--primary-blue-dark))";
    element.style.borderColor = "var(--primary-blue)";
    element.style.color = "white";
  }
  
  updateSelectedSlotsDisplay();
}

function updateSelectedSlotsDisplay() {
  const candidateSlots = selectedSlotsByCandidate[currentCandidateId] || [];
  const selectedList = document.getElementById("selected-list");
  
  if (candidateSlots.length === 0) {
    selectedList.textContent = "Aucun créneau sélectionné";
    selectedList.style.color = "var(--text-secondary)";
  } else {
    selectedList.innerHTML = candidateSlots.map(slot => {
      const [date, time] = slot.split(" ");
      const formattedDate = new Date(date).toLocaleDateString("fr-FR");
      return `<div style="margin-bottom: 0.25rem;">${formattedDate} - ${availableSlots[time]}</div>`;
    }).join("");
    selectedList.style.color = "var(--text-primary)";
  }
}

function confirmSchedule() {
  const candidateSlots = selectedSlotsByCandidate[currentCandidateId] || [];
  if (candidateSlots.length === 0) {
    showNotification("Veuillez sélectionner au moins un créneau.", "warning");
    return;
  }

  sendInterviewNotification(currentAppId, currentCandidateId, candidateSlots);
  closeScheduler();
}

function sendInterviewNotification(applicationId, candidateId, slots) {
  // Validate slots format (e.g., "YYYY-MM-DD HH:MM")
  const slotRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/;
  if (!Array.isArray(slots) || slots.length === 0 || !slots.every(s => typeof s === 'string' && slotRegex.test(s))) {
    console.error("Invalid slots format. Expected format: YYYY-MM-DD HH:MM");
    showNotification("Erreur: Les créneaux doivent être au format YYYY-MM-DD HH:MM", "error");
    return Promise.reject(new Error("Invalid slots format"));
  }

  // Validate currentUser
  const recruiterId = currentUser ? currentUser.id : null;
  if (!recruiterId) {
    console.error("No current user or recruiter_id found");
    showNotification("Erreur: Utilisateur non connecté", "error");
    return Promise.reject(new Error("No current user"));
  }

  // Log the payload for debugging
  const payload = {
    application_id: applicationId,
    candidate_id: candidateId,
    slots: slots,
    recruiter_id: recruiterId
  };
  console.log("Request payload:", payload);

  return fetch(`/api/schedule-interview/${applicationId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((res) => {
      if (!res.ok) {
        return res.json().then((data) => {
          throw new Error(data.message || data.detail || `HTTP error! status: ${res.status}`);
        });
      }
      return res.json();
    })
    .then((data) => {
      if (!data.success) {
        console.error(`❌ FRONTEND: Failed to send notification: ${data.message || data.detail}`);
        showNotification(`Erreur: ${data.message || data.detail || "Échec de l'envoi de la notification"}`, "error");
        throw new Error(data.message || data.detail || "Failed to send notification");
      }
      showNotification("✅ Notification d'entretien envoyée avec succès", "success");
      return data;
    })
    .catch((err) => {
      console.error("❌ FRONTEND: Error during API call:", err);
      showNotification(`Erreur serveur: ${err.message || "Veuillez réessayer plus tard"}`, "error");
      throw err;
    });
}


function viewInterviewDetails(applicationId) {
  showNotification("Fonctionnalité en cours de développement", "info")
}

function rescheduleInterview(applicationId) {
  showNotification("Fonctionnalité en cours de développement", "info")
}

function getInterviewStatusBadge(app) {
  const now = new Date()
  const interviewDate = app.interview_date ? new Date(app.interview_date) : null

  if (app.end_session) {
    const successRate = app.interview_result?.success_rate || 0
    return `<span class="interview-status-badge ${getInterviewStatusClass('completed')} ${successRate >= 50 ? "success" : "failure"}">
      ${getInterviewStatusText('completed')} (${successRate}%)
    </span>`
  } else if (app.start_session) {
    return `<span class="interview-status-badge ${getInterviewStatusClass('scheduled')}">
      ${getInterviewStatusText('scheduled')}
    </span>`
  } else if (app.interview_date && interviewDate && interviewDate < now) {
    return `<span class="interview-status-badge ${getInterviewStatusClass('cancelled')}">
      En retard
    </span>`
  } else if (app.interview_date) {
    return `<span class="interview-status-badge ${getInterviewStatusClass('scheduled')}">
      ${getInterviewStatusText('scheduled')}
    </span>`
  } else {
    return `<span class="interview-status-badge ${getInterviewStatusClass('not_scheduled')}">
      ${getInterviewStatusText('not_scheduled')}
    </span>`
  }
}

function getInterviewContent(app) {
  console.log("[v0] Generating interview content for app", app.id, "with data:", {
    interview_date: app.interview_date,
    start_session: app.start_session,
    end_session: app.end_session,
    interview_result: app.interview_result,
  })

  const now = new Date()
  const candidateName = app.candidate_profile?.name || app.candidate_name || "N/A"
  const isDeptHead = currentUser?.role === "department_head"

  // Check if interview data exists - show basic info grid like old file
  if (!app.interview_date && !app.start_session && !app.end_session) {
    console.log("[v0] No interview data found for app", app.id, "- showing no data message")
    return `
      <div class="interview-overview">
        <div class="interview-info-grid">
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-calendar-check"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Date prévue</div>
              <div class="info-value">Non programmé</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Heure</div>
              <div class="info-value">Non définie</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-users"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Type</div>
              <div class="info-value">À définir</div>
            </div>
          </div>
        </div>
      </div>
      
      ${isDeptHead ? '' : `
      <div class="interview-actions">
        <div class="interview-actions-row">
          <button class="btn-schedule-interview" onclick="openScheduleInterviewModal(${app.id}, '${candidateName}')">
            <i class="fas fa-calendar-plus"></i> Programmer un entretien
          </button>

          <button class="btn-reschedule-interview" onclick="rescheduleInterview(${app.id})" disabled>
            <i class="fas fa-calendar-times"></i> Reprogrammer
          </button>
        </div>
      </div>
      `}`
  }

  const interviewDate = app.interview_date ? new Date(app.interview_date) : null
  const timeDiff = interviewDate ? interviewDate - now : 0

  // Completed interview - show results with exact old file structure
  if (app.end_session && app.interview_result) {
    console.log("[v0] Showing completed interview results for app", app.id)
    return `
      <div class="interview-overview">
        <div class="interview-info-grid">
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-calendar-check"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Date prévue</div>
              <div class="info-value">${formatDateSafe(app.interview_date)}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Heure</div>
              <div class="info-value">${app.interview_time || 'Terminé'}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-users"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Type</div>
              <div class="info-value">${app.interview_type || 'Terminé'}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-percentage"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Résultat</div>
              <div class="info-value ${app.interview_result.success_rate >= 60 ? "success" : "failure"}">${app.interview_result.success_rate}%</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="interview-actions">
        <div class="interview-actions-row">
          <button class="btn-view-interview" onclick="viewInterviewResults(${app.id})">
            <i class="fas fa-chart-line"></i> Voir les résultats détaillés
          </button>
        </div>
      </div>
      
      ${app.interview_notes ? `
      <div class="interview-notes">
        <h5><i class="fas fa-sticky-note"></i> Notes d'entretien</h5>
        <p>${app.interview_notes}</p>
      </div>
      ` : ''}`
  }

  // Started interview
  else if (app.start_session) {
    console.log("[v0] Showing started interview for app", app.id)
    return `
      <div class="interview-overview">
        <div class="interview-info-grid">
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-calendar-check"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Date prévue</div>
              <div class="info-value">${formatDateSafe(app.interview_date)}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Heure</div>
              <div class="info-value">${app.interview_time || 'En cours'}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-users"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Type</div>
              <div class="info-value">${app.interview_type || 'En cours'}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="interview-actions">
        <div class="interview-actions-row">
          <a href="/interview/${app.id}" class="btn-join-interview">
            <i class="fas fa-video"></i> Rejoindre l'entretien
          </a>
        </div>
      </div>
      
      ${app.interview_notes ? `
      <div class="interview-notes">
        <h5><i class="fas fa-sticky-note"></i> Notes d'entretien</h5>
        <p>${app.interview_notes}</p>
      </div>
      ` : ''}`
  }

  // Upcoming interview
  else if (app.interview_date && timeDiff > 0) {
    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((timeDiff / (1000 * 60 * 60)) % 24)
    const minutes = Math.floor((timeDiff / (1000 * 60)) % 60)

    return `
      <div class="interview-overview">
        <div class="interview-info-grid">
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-calendar-check"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Date prévue</div>
              <div class="info-value">${formatDateSafe(app.interview_date)}</div>
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
          ${
            timeDiff <= 3600000
              ? `
            <a href="/interview/${app.id}" class="btn-start-session">
              <i class="fas fa-play"></i> Démarrer l'entretien
            </a>
          `
              : `
            <button class="btn-waiting" disabled>
              <i class="fas fa-hourglass-half"></i> En attente (${days}j ${hours}h ${minutes}m)
            </button>
          `
          }
          ${isDeptHead ? '' : `
          <button class="btn-reschedule-interview" onclick="rescheduleInterview(${app.id})">
            <i class="fas fa-calendar-times"></i> Reprogrammer
          </button>
          `}
        </div>
      </div>
      
      ${app.interview_notes ? `
      <div class="interview-notes">
        <h5><i class="fas fa-sticky-note"></i> Notes d'entretien</h5>
        <p>${app.interview_notes}</p>
      </div>
      ` : ''}`
  }

  // Overdue interview
  else if (app.interview_date && timeDiff <= 0) {
    return `
      <div class="interview-overview">
        <div class="interview-info-grid">
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-calendar-check"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Date prévue</div>
              <div class="info-value">${formatDateSafe(app.interview_date)}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Heure</div>
              <div class="info-value">${app.interview_time || 'En retard'}</div>
            </div>
          </div>
          
          <div class="interview-info-item">
            <div class="info-icon">
              <i class="fas fa-users"></i>
            </div>
            <div class="info-content">
              <div class="info-label">Type</div>
              <div class="info-value">${app.interview_type || 'En retard'}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="interview-actions">
        <div class="interview-actions-row">
          <a href="/interview/${app.id}" class="btn-start-overdue">
            <i class="fas fa-play"></i> Démarrer maintenant
          </a>
          ${isDeptHead ? '' : `
          <button class="btn-reschedule-interview" onclick="rescheduleInterview(${app.id})">
            <i class="fas fa-calendar-times"></i> Reprogrammer
          </button>
          `}
        </div>
      </div>
      
      ${app.interview_notes ? `
      <div class="interview-notes">
        <h5><i class="fas fa-sticky-note"></i> Notes d'entretien</h5>
        <p>${app.interview_notes}</p>
      </div>
      ` : ''}`
  }

  // Fallback - no interview scheduled
  return `
    <div class="interview-overview">
      <div class="interview-info-grid">
        <div class="interview-info-item">
          <div class="info-icon">
            <i class="fas fa-calendar-check"></i>
          </div>
          <div class="info-content">
            <div class="info-label">Date prévue</div>
            <div class="info-value">Non programmé</div>
          </div>
        </div>
        
        <div class="interview-info-item">
          <div class="info-icon">
            <i class="fas fa-clock"></i>
          </div>
          <div class="info-content">
            <div class="info-label">Heure</div>
            <div class="info-value">Non définie</div>
          </div>
        </div>
        
        <div class="interview-info-item">
          <div class="info-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="info-content">
            <div class="info-label">Type</div>
            <div class="info-value">À définir</div>
          </div>
        </div>
      </div>
    </div>
    
    ${isDeptHead ? '' : `
    <div class="interview-actions">
      <div class="interview-actions-row">
        <button class="btn-schedule-interview" onclick="openScheduleInterviewModal(${app.id}, '${candidateName}')">
          <i class="fas fa-calendar-plus"></i> Programmer un entretien
        </button>

        <button class="btn-reschedule-interview" onclick="rescheduleInterview(${app.id})" disabled>
          <i class="fas fa-calendar-times"></i> Reprogrammer
        </button>
      </div>
    </div>
    `}`
}
function viewDetailedInterviewResults(applicationId) {
  // Open interview results in new window
  window.open(`/interview-results?application_id=${applicationId}`, "_blank")
}

function updateScoreCircle(element, percentage) {
  if (element) {
    element.style.setProperty("--score-angle", `${percentage * 3.6}deg`)
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const scoreCircles = document.querySelectorAll(".score-circle")
  scoreCircles.forEach((circle) => {
    const percentageElement = circle.querySelector(".score-percentage")
    if (percentageElement) {
      const percentage = Number.parseInt(percentageElement.textContent)
      updateScoreCircle(circle, percentage)
    }
  })
})
