// ==================== GESTION AVANCÉE DES PERMISSIONS ====================

// Déclaration des variables nécessaires
const currentUser = null // Cette variable devrait être définie ailleurs dans votre code
const showNotification = null // Cette fonction devrait être définie ailleurs dans votre code
const openDepartmentModal = null // Cette fonction devrait être définie ailleurs dans votre code
const openJobModal = null // Cette fonction devrait être définie ailleurs dans votre code

// Fonction pour vérifier les permissions selon le rôle
function checkPermission(action) {
  if (!currentUser) {
    console.warn("🚫 PERMISSIONS: Utilisateur non connecté")
    return false
  }

  const permissions = {
    super_admin: {
      create_department: true,
      create_job: true,
      create_user: true,
      manage_all_applications: true,
      view_all_departments: true,
      manage_company_profile: true,
    },
    department_head: {
      create_department: false,
      create_job: true, // Seulement dans ses départements
      create_user: false,
      manage_all_applications: false, // Seulement ses départements
      view_all_departments: false, // Seulement ses départements
      manage_company_profile: false,
    },
    recruiter: {
      create_department: false,
      create_job: false,
      create_user: false,
      manage_all_applications: true,
      view_all_departments: true,
      manage_company_profile: false,
    },
  }

  const userPermissions = permissions[currentUser.role]
  if (!userPermissions) {
    console.warn(`🚫 PERMISSIONS: Rôle inconnu: ${currentUser.role}`)
    return false
  }

  const hasPermission = userPermissions[action] || false
  console.log(`🔐 PERMISSIONS: ${currentUser.role} - ${action}: ${hasPermission ? "✅" : "❌"}`)

  return hasPermission
}

// Fonction pour masquer/afficher les éléments selon les permissions
function applyPermissionBasedVisibility() {
  if (!currentUser) return

  console.log("🔐 PERMISSIONS: Application de la visibilité basée sur les permissions")

  // Masquer la section d'assignation de manager pour les non-super-admin
  if (!checkPermission("create_user")) {
    const managerToggleContainer = document.getElementById("managerToggleContainer")
    if (managerToggleContainer) {
      managerToggleContainer.style.display = "none"
      console.log("🚫 PERMISSIONS: Section assignation manager masquée")
    }
  }

  // Masquer les boutons de création selon le rôle
  if (!checkPermission("create_department")) {
    const createDeptAction = document.getElementById("createDeptAction")
    if (createDeptAction) {
      createDeptAction.style.display = "none"
      console.log("🚫 PERMISSIONS: Action création département masquée")
    }
  }

  if (!checkPermission("create_job")) {
    const createJobAction = document.getElementById("createJobAction")
    if (createJobAction) {
      createJobAction.style.display = "none"
      console.log("🚫 PERMISSIONS: Action création poste masquée")
    }
  }
}

// Fonction pour vérifier avant d'ouvrir les modals
function openDepartmentModalWithPermission() {
  if (!checkPermission("create_department")) {
    showNotification("Vous n'avez pas les permissions pour créer des départements", "warning")
    return
  }
  openDepartmentModal()
}

function openJobModalWithPermission(preselectedDeptId = null) {
  if (!checkPermission("create_job")) {
    showNotification("Vous n'avez pas les permissions pour créer des postes", "warning")
    return
  }
  openJobModal(preselectedDeptId)
}

// Fonction pour afficher un résumé des permissions utilisateur
function displayUserPermissions() {
  if (!currentUser) return

  const permissions = [
    { key: "create_department", label: "Créer des départements" },
    { key: "create_job", label: "Créer des postes" },
    { key: "create_user", label: "Créer des utilisateurs" },
    { key: "manage_all_applications", label: "Gérer toutes les candidatures" },
    { key: "view_all_departments", label: "Voir tous les départements" },
  ]

  console.log(`👤 PERMISSIONS pour ${currentUser.first_name} ${currentUser.last_name} (${currentUser.role}):`)
  permissions.forEach((perm) => {
    const hasPermission = checkPermission(perm.key)
    console.log(`   ${hasPermission ? "✅" : "❌"} ${perm.label}`)
  })
}

// Intégrer les vérifications de permissions dans l'initialisation
document.addEventListener("DOMContentLoaded", () => {
  // Attendre que l'utilisateur soit chargé avant d'appliquer les permissions
  setTimeout(() => {
    if (currentUser) {
      applyPermissionBasedVisibility()
      displayUserPermissions()
    }
  }, 1000)
})
