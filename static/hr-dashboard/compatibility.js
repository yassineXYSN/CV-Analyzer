console.log("🎯 FRONTEND: Enhanced Compatibility module loaded")

// Enhanced applications loading with better error handling and debugging
async function loadApplicationsWithFilters(statusFilter = "all", compatibilityFilter = "all") {
  console.log("📋 FRONTEND: Loading applications with filters:", { statusFilter, compatibilityFilter })

  try {
    const params = new URLSearchParams()
    if (statusFilter !== "all") params.append("status_filter", statusFilter)
    if (compatibilityFilter !== "all") params.append("compatibility_filter", compatibilityFilter)

    console.log("🌐 FRONTEND: Making API request to /api/applications")
    const response = await fetch(`/api/applications?${params.toString()}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log("📦 FRONTEND: API response received:", result)

    if (result.success) {
      // Process applications with proper compatibility data
      window.applications = (result.applications || []).map((app, index) => {
        const processedApp = {
          ...app,
          compatibility_percentage: typeof app.compatibility_percentage === "number" ? app.compatibility_percentage : 0,
          matched_skills_count: typeof app.matched_skills_count === "number" ? app.matched_skills_count : 0,
          total_job_skills: typeof app.total_job_skills === "number" ? app.total_job_skills : 0,
        }

        console.log(`🔍 FRONTEND: Processed app ${index + 1}:`, {
          id: processedApp.id,
          name: processedApp.candidate_name,
          compatibility: processedApp.compatibility_percentage,
          matched: processedApp.matched_skills_count,
          total: processedApp.total_job_skills,
        })

        return processedApp
      })

      console.log(`✅ FRONTEND: ${window.applications.length} applications loaded with compatibility data`)

      // Log summary of compatibility scores
      const compatibilityScores = window.applications.map((app) => app.compatibility_percentage)
      const avgCompatibility = compatibilityScores.reduce((a, b) => a + b, 0) / compatibilityScores.length
      console.log(`📊 FRONTEND: Compatibility scores: ${compatibilityScores.join(", ")}`)
      console.log(`📊 FRONTEND: Average compatibility: ${avgCompatibility.toFixed(1)}%`)

      renderApplicationsWithCompatibility()
    } else {
      console.error("❌ FRONTEND: Error loading applications:", result.message)
      window.applications = []
      renderApplicationsWithCompatibility()
    }
  } catch (error) {
    console.error("❌ FRONTEND: Network error loading applications:", error)
    window.applications = []
    renderApplicationsWithCompatibility()
  }
}

// Enhanced rendering with better compatibility display
function renderApplicationsWithCompatibility(filter = "all") {
  console.log("📋 FRONTEND: Rendering applications with compatibility, filter:", filter)

  const container = document.getElementById("applicationsContainer")
  if (!container) {
    console.error("❌ FRONTEND: Applications container not found")
    return
  }

  const applications = window.applications || []
  let filteredApps = applications
  if (filter !== "all") {
    filteredApps = applications.filter((app) => app.status === filter)
  }

  console.log(`🎨 FRONTEND: Rendering ${filteredApps.length} applications`)

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
    .map((app) => {
      console.log(`🎯 FRONTEND: Rendering app ${app.id} - Compatibility: ${app.compatibility_percentage}%`)

      return `
        <div class="application-card-enhanced ${app.status}">
          <div class="application-header">
            <div class="applicant-info">
              <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
              <div class="applicant-details">
                <h4>${app.candidate_name}
                  ${
                    app.is_recommended
                      ? `
                    <span class="recommendation-badge ${app.recommendation_priority}" 
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
                </h4>
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

          <!-- Enhanced Compatibility Section -->
          <div class="application-compatibility-section">
            <div class="compatibility-header">
              <div class="compatibility-title">
                <i class="fas fa-chart-pie"></i>
                Compatibilité des compétences
              </div>
              <div class="compatibility-percentage ${getCompatibilityClass(app.compatibility_percentage)}">
                ${app.compatibility_percentage}%
                <i class="fas fa-${getCompatibilityIcon(app.compatibility_percentage)}"></i>
              </div>
            </div>
            
            <div class="compatibility-progress">
              <div class="compatibility-progress-bar ${getCompatibilityClass(app.compatibility_percentage)}" 
                   style="width: ${app.compatibility_percentage}%"></div>
            </div>
          </div>
          
          <div class="application-actions">
            <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
              <i class="fas fa-user"></i> Voir Profil
            </button>
            <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
              <i class="fas fa-info-circle"></i> Détails Poste
            </button>
          </div>
        </div>
      `
    })
    .join("")

  console.log("✅ FRONTEND: Applications rendered with compatibility data")
}

// Rest of the functions remain the same but with enhanced logging
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

// Enhanced compatibility details view
async function viewCompatibilityDetails(applicationId) {
  console.log("🔍 FRONTEND: Viewing compatibility details for application:", applicationId)

  try {
    showLoading("Chargement des détails de compatibilité...")

    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()

    hideLoading()

    if (result.success) {
      console.log("📊 FRONTEND: Compatibility details received:", result)
      showCompatibilityModal(result)
    } else {
      console.error("❌ FRONTEND: Error loading compatibility details:", result.message)
      showNotification("Erreur lors du chargement des détails de compatibilité: " + result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ FRONTEND: Error loading compatibility details:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Enhanced compatibility modal
function showCompatibilityModal(compatibilityData) {
  console.log("🔍 FRONTEND: Showing compatibility modal with data:", compatibilityData)

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

// Helper functions
function getLevelText(level) {
  const levelTexts = {
    beginner: "Débutant",
    intermediate: "Intermédiaire",
    advanced: "Avancé",
    expert: "Expert",
  }
  return levelTexts[level] || level
}

function getFilterText(filter) {
  const filterTexts = {
    all: "",
    pending: "en attente",
    reviewed: "examinée",
    interview_scheduled: "programmée pour entretien",
    interview_completed: "entretien terminé",
    accepted: "acceptée",
    rejected: "rejetée",
  }
  return filterTexts[filter] || filter
}

function getInitials(name) {
  return name
    .split(" ")
    .map((word) => word.charAt(0))
    .join("")
    .toUpperCase()
}

function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    interview_scheduled: "Programmée pour entretien",
    interview_completed: "Entretien terminé",
    accepted: "Acceptée",
    rejected: "Rejetée",
  }
  return statusTexts[status] || status
}

function formatDate(date) {
  const options = { year: "numeric", month: "long", day: "numeric" }
  return new Date(date).toLocaleDateString("fr-FR", options)
}

// Loading and notification helpers
function showLoading(message) {
  const loading = document.createElement("div")
  loading.className = "loading-overlay"
  loading.innerHTML = `
    <div class="loading-content">
      <i class="fas fa-spinner fa-spin"></i>
      <p>${message}</p>
    </div>
  `
  loading.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 30000;
  `
  document.body.appendChild(loading)
}

function hideLoading() {
  const loading = document.querySelector(".loading-overlay")
  if (loading) {
    loading.remove()
  }
}

function showNotification(message, type = "info") {
  console.log(`📢 NOTIFICATION [${type.toUpperCase()}]: ${message}`)
  // Implementation would go here
}

// Make functions available globally
window.loadApplicationsWithFilters = loadApplicationsWithFilters
window.renderApplicationsWithCompatibility = renderApplicationsWithCompatibility
window.viewCompatibilityDetails = viewCompatibilityDetails
window.getCompatibilityClass = getCompatibilityClass
window.getCompatibilityIcon = getCompatibilityIcon

console.log("✅ FRONTEND: Enhanced Compatibility module ready")
