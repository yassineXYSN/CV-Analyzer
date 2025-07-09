// Variables globales
let currentEmployee = null
let notes = []

// Charger les données du candidat au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  loadPersonData(); // 👈 gère candidat ou employé
  initializeCircleProgress();
  loadNotes();
});


// Charger les données du candidat depuis l'URL
function loadCandidateData() {
  const urlParams = new URLSearchParams(window.location.search);
  const candidateId = urlParams.get("candidate_id");

  if (candidateId) {
    loadCandidateFromAPI(candidateId);
  } else {
    showNotification("Aucun candidat sélectionné", "error");
  }
}
function loadPersonData() {
  const urlParams = new URLSearchParams(window.location.search);
  const candidateId = urlParams.get("candidate_id");
  const employeeId = urlParams.get("id");

  if (candidateId) {
    loadCandidateFromAPI(candidateId);
  } else if (employeeId) {
    loadEmployeeFromAPI(employeeId);
  } else {
    showNotification("Aucun profil à afficher", "error");
  }
}

// Charger le candidat depuis l'API


// Afficher les informations du candidat
function displayCandidateInfo(candidate) {

const nameEl = document.getElementById("employeeName");
  if (!nameEl) {
    console.warn("⛔ DOM non prêt, employeeName introuvable");
    return;
  }

  const educationList = document.getElementById("employeeEducationList");
const langList = document.getElementById("employeeLanguagesList");
const certList = document.getElementById("employeeCertificatesList");

  // Informations principales
  document.getElementById("employeeName").textContent = `${candidate.first_name} ${candidate.last_name}`;
  document.getElementById("employeePosition").textContent = candidate.title || "Candidat";
  document.getElementById("employeeEmail").textContent = candidate.email;
  document.getElementById("employeePhone").textContent = candidate.phone || "Non renseigné";
  document.getElementById("employeeId").textContent = `CAND${candidate.id}`;

  // Avatar avec initiales
  const avatar = document.getElementById("employeeAvatar");
const firstInitial = candidate.first_name ? candidate.first_name[0].toUpperCase() : "?"
const lastInitial  = candidate.last_name ? candidate.last_name[0].toUpperCase() : "?"
avatar.textContent = `${firstInitial}${lastInitial}`

  // Département (spécifique aux candidats)
  document.getElementById("employeeDepartment").textContent = "Candidat externe";
  document.getElementById("employeeHireDate").textContent = "Non embauché";

  // Profil et analyse IA
  document.getElementById("employeeProfileText").textContent = candidate.profile || "Aucune présentation disponible";
  
  if (candidate.analyse) {
    document.getElementById("employeeAnalysis").textContent = candidate.analyse;
  } else {
    document.getElementById("employeeAnalysis").textContent = "Aucune analyse IA disponible";
  }

  // Compétences
  const skillsList = document.getElementById("employeeSkillsList");
  skillsList.innerHTML = ""; // Clear existing skills

  let parsedSkills = []

try {
  parsedSkills = typeof candidate.skills === "string"
    ? JSON.parse(candidate.skills)
    : candidate.skills
} catch (e) {
  console.warn("Erreur parsing skills", e)
}

if (parsedSkills.length > 0) {
  parsedSkills.forEach(skill => {
    const skillItem = document.createElement("div")
    skillItem.className = "skill-item"

    if (typeof skill === "string") {
      const parts = skill.split(":")
      const name = parts[0].trim()
      const percent = parts[1] ? parseInt(parts[1]) : 75

      skillItem.innerHTML = `
        <span class="skill-name">${name}</span>
        <div class="skill-bar"><div class="skill-progress" style="width: ${percent}%"></div></div>
        <span class="skill-level">${percent}%</span>
      `
    }

    document.getElementById("employeeSkillsList").appendChild(skillItem)
  })
}

// ✅ Ce bloc est maintenant *en dehors* du if
const educationData = parseJsonSafe(candidate.education);
const langData = parseJsonSafe(candidate.languages);
const certData = parseJsonSafe(candidate.certificates);

console.log("🎓 Éducation :", educationData);
console.log("🌍 Langues :", langData);
console.log("📜 Certificats :", certData);

// Éducation
educationList.innerHTML = "";
if (Array.isArray(educationData) && educationData.length > 0) {
  educationData.forEach(item => {
    const li = document.createElement("li");
    li.textContent = `${item.degree} - ${item.institution} (${item.years})`;
    educationList.appendChild(li);
  });
} else {
  educationList.innerHTML = "<li>Aucune information</li>";
}

// Langues
langList.innerHTML = "";
if (Array.isArray(langData) && langData.length > 0) {
  langData.forEach(lang => {
    const li = document.createElement("li");
    li.textContent = lang;
    langList.appendChild(li);
  });
} else {
  langList.innerHTML = "<li>Aucune langue renseignée</li>";
}

// Certificats
certList.innerHTML = "";
if (Array.isArray(certData) && certData.length > 0) {
  certData.forEach(cert => {
    const li = document.createElement("li");
    li.textContent = cert;
    certList.appendChild(li);
  });
} else {
  certList.innerHTML = "<li>Aucun certificat disponible</li>";
}

  // Statistiques simulées pour l'affichage

}

// Obtenir le nom du département (simulé)
function getDepartmentName(departmentId) {
  const departments = {
    1: "Développement",
    2: "Ressources Humaines",
    3: "Marketing",
    4: "Ventes",
    5: "Support",
  }
  return departments[departmentId] || "Département inconnu"
}

// Initialiser les cercles de progression
function initializeCircleProgress() {
  const circles = document.querySelectorAll(".circle-progress")
  circles.forEach((circle) => {
    const percentage = circle.getAttribute("data-percentage")
    circle.style.setProperty("--percentage", percentage)
  })
}

// Fonction pour retourner au dashboard
function goBackToDashboard() {
  window.location.href = "/dashboard"
}

function addSkill() {
  const skillName = prompt("Nom de la compétence:")
  const skillLevel = prompt("Niveau (0-100):")

  if (skillName && skillLevel && !isNaN(skillLevel)) {
    const skillsList = document.getElementById("skillsList")
    const skillItem = document.createElement("div")
    skillItem.className = "skill-item"
    skillItem.innerHTML = `
            <span class="skill-name">${skillName}</span>
            <div class="skill-bar">
                <div class="skill-progress" style="width: ${skillLevel}%"></div>
            </div>
            <span class="skill-level">${skillLevel}%</span>
        `
    skillsList.appendChild(skillItem)
    showNotification("Compétence ajoutée avec succès !", "success")
  }
}

function uploadDocument() {
  showNotification("Fonction d'upload en cours de développement", "info")
}

function viewDocument(type) {
  showNotification(`Ouverture du document: ${type}`, "info")
}

function downloadDocument(type) {
  showNotification(`Téléchargement du document: ${type}`, "info")
}

// Gestion des notes
function addNote() {
  document.getElementById("noteModal").classList.add("show")
  document.body.style.overflow = "hidden"
}

function closeNoteModal() {
  document.getElementById("noteModal").classList.remove("show")
  document.body.style.overflow = "auto"
  document.getElementById("noteForm").reset()
}

function saveNote() {
  const noteContent = document.getElementById("noteContent").value.trim()

  if (!noteContent) {
    showNotification("Veuillez saisir une note", "error")
    return
  }

  const note = {
    id: Date.now(),
    content: noteContent,
    author: "Sarah Johnson", // Utilisateur actuel
    date: new Date().toLocaleDateString("fr-FR"),
    timestamp: new Date(),
  }

  notes.unshift(note)
  saveNotes()
  renderNotes()
  closeNoteModal()
  showNotification("Note ajoutée avec succès !", "success")
}

function loadNotes() {
  const savedNotes = localStorage.getItem(`notes_${currentEmployee?.id}`)
  if (savedNotes) {
    notes = JSON.parse(savedNotes)
    renderNotes()
  }
}

function saveNotes() {
  localStorage.setItem(`notes_${currentEmployee.id}`, JSON.stringify(notes))
}

function renderNotes() {
  const notesList = document.getElementById("notesList")

  if (notes.length === 0) {
    notesList.innerHTML = `
            <div class="note-item">
                <div class="note-header">
                    <span class="note-author">Système</span>
                    <span class="note-date">${new Date().toLocaleDateString("fr-FR")}</span>
                </div>
                <p class="note-content">Aucune note disponible pour cet employé.</p>
            </div>
        `
    return
  }

  notesList.innerHTML = notes
    .map(
      (note) => `
        <div class="note-item">
            <div class="note-header">
                <span class="note-author">${note.author}</span>
                <span class="note-date">${note.date}</span>
            </div>
            <p class="note-content">${note.content}</p>
        </div>
    `,
    )
    .join("")
}

// Système de notifications
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

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 4000)
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

// Ajouter les animations CSS
const style = document.createElement("style")
style.textContent = `
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
document.head.appendChild(style)

async function loadCandidateFromAPI(candidateId) {
  try {
    const res = await fetch(`/api/candidate/${candidateId}`)
    const data = await res.json()

    if (!data.success) throw new Error(data.message)
    const c = data.candidate
    console.log("📦 Données reçues du candidat :", c);

    currentEmployee = {
      id: c.id,
      first_name: c.first_name,
      last_name: c.last_name,
      email: c.email,
      phone: c.phone,
      position: c.title || "Candidat",
      department_name: "Candidat externe",
      hire_date: null,
      employee_id: `CAND${c.id}`,
      profile: c.profile || "",
      linkedin: c.linkedin,
      address: c.address
    }

displayEmployeeInfo(currentEmployee)




    // Compétences
    clearSkills()
    if (Array.isArray(c.skills)) {
      c.skills.forEach(s => addSkillToUI(s))
    } else {
      try {
        JSON.parse(c.skills).forEach(s => addSkillToUI(s))
      } catch {}
    }

    // Facultatif : afficher l’analyse
    if (c.analyse) {
      const analyseEl = document.getElementById("employeeAnalysis")
      if (analyseEl) analyseEl.textContent = c.analyse
    }

    // Facultatif : afficher le CV résumé ou profil texte
    const profileEl = document.getElementById("employeeProfileText")
    if (profileEl && c.profile) {
      profileEl.textContent = c.profile
    }
setTimeout(() => displayCandidateInfo(c), 0);

  } catch (err) {
    console.error("Erreur chargement candidat:", err)
    showNotification("Erreur lors du chargement du profil candidat", "error")
  }
}
function clearSkills() {
  const list = document.getElementById("employeeSkillsList")
  if (list) list.innerHTML = ""
}
function addSkillToUI(skill) {
  const list = document.getElementById("employeeSkillsList")
  if (!list || !skill) return

  const div = document.createElement("div")
  div.className = "skill-item"
  div.innerHTML = `
    <span class="skill-name">${skill}</span>
    <div class="skill-bar"><div class="skill-progress" style="width: 75%"></div></div>
    <span class="skill-level">75%</span>
  `
  list.appendChild(div)
}
function displayEmployeeInfo(employee) {
  if (!employee) return;

  const name = `${employee.first_name || "?"} ${employee.last_name || ""}`
  document.getElementById("employeeName").textContent = name
  document.getElementById("employeePosition").textContent = employee.position || "Candidat"
  document.getElementById("employeeEmail").textContent = employee.email || "Non renseigné"
  document.getElementById("employeePhone").textContent = employee.phone || "Non renseigné"
  document.getElementById("employeeId").textContent = employee.employee_id || "CAND?"

  // Initiales dans l’avatar
  const avatar = document.getElementById("employeeAvatar")
  const fi = employee.first_name ? employee.first_name[0].toUpperCase() : "?"
  const li = employee.last_name ? employee.last_name[0].toUpperCase() : "?"
  avatar.textContent = `${fi}${li}`

  document.getElementById("employeeDepartment").textContent = employee.department_name || "Candidat externe"
  document.getElementById("employeeHireDate").textContent = employee.hire_date || "Non embauché"
}

async function loadEmployeeFromAPI(employeeId) {
  try {
    const res = await fetch(`/api/employee/${employeeId}`)
    const data = await res.json()

    if (!data.success) throw new Error(data.message)
    const e = data.employee

    currentEmployee = {
      id: e.id,
      first_name: e.first_name,
      last_name: e.last_name,
      email: e.email,
      phone: e.phone,
      position: e.position || "Employé",
      department_name: e.department_name || "Département inconnu",
      hire_date: e.hire_date || "Non précisé",
      employee_id: e.employee_id || `EMP${e.id}`,
      skills: e.skills || [],
      // Ajout des données manquantes
      education: e.education || [],
      languages: e.languages || [],
      certificates: e.certificates || [],
      profile: e.profile || "",
      analyse: e.analyse || ""
    }

    // Afficher TOUTES les données
    displayEmployeeInfo(currentEmployee)
    displayEmployeeDetails(currentEmployee) // Nouvelle fonction

    // Afficher les compétences (skills = ["Python: 80%", ...])
    const container = document.getElementById("employeeSkillsList")
    container.innerHTML = ""
    if (Array.isArray(currentEmployee.skills)) {
      currentEmployee.skills.forEach((skill) => {
        const div = document.createElement("div")
        div.className = "skill-item"

        const [name, percentText] = skill.split(":")
        const percent = percentText ? parseInt(percentText) : 75

        div.innerHTML = `
          <span class="skill-name">${name.trim()}</span>
          <div class="skill-bar"><div class="skill-progress" style="width: ${percent}%"></div></div>
          <span class="skill-level">${percent}%</span>
        `
        container.appendChild(div)
      })
    }

    // Afficher un texte de présentation fictif
    document.getElementById("employeeProfileText").textContent =
      `Employé dans le poste de ${currentEmployee.position}. Adresse : ${currentEmployee.address}`

  } catch (e) {
    console.error("Erreur chargement employé:", e)
    showNotification("Impossible de charger le profil employé", "error")
  }
}

function displayEmployeeDetails(employee) {
  // Éducation
  const educationList = document.getElementById("employeeEducationList");
  educationList.innerHTML = "";
  if (Array.isArray(employee.education) && employee.education.length > 0) {
    employee.education.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.degree} - ${item.institution} (${item.years})`;
      educationList.appendChild(li);
    });
  } else {
    educationList.innerHTML = "<li>Aucune information</li>";
  }

  // Langues
  const langList = document.getElementById("employeeLanguagesList");
  langList.innerHTML = "";
  if (Array.isArray(employee.languages) && employee.languages.length > 0) {
    employee.languages.forEach(lang => {
      const li = document.createElement("li");
      li.textContent = lang;
      langList.appendChild(li);
    });
  } else {
    langList.innerHTML = "<li>Aucune langue renseignée</li>";
  }

  // Certificats
  const certList = document.getElementById("employeeCertificatesList");
  certList.innerHTML = "";
  if (Array.isArray(employee.certificates) && employee.certificates.length > 0) {
    employee.certificates.forEach(cert => {
      const li = document.createElement("li");
      li.textContent = cert;
      certList.appendChild(li);
    });
  } else {
    certList.innerHTML = "<li>Aucun certificat disponible</li>";
  }

  // Profil et analyse
  document.getElementById("employeeProfileText").textContent = employee.profile || "Aucune présentation disponible";
  document.getElementById("employeeAnalysis").textContent = employee.analyse || "Aucune analyse IA disponible";
}

function parseJsonSafe(value) {
  try {
    const once = typeof value === "string" ? JSON.parse(value) : value;
    return typeof once === "string" ? JSON.parse(once) : once;
  } catch (e) {
    console.warn("Erreur de parsing JSON :", e);
    return [];
  }
}