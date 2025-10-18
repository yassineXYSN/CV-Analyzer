// Global variables

let currentJob = null

let applications = []

let currentUser = null



// Fonction pour convertir une Date en format datetime-local

function toLocalDatetimeValue(date) {

  if (!date) return ''

  // Use local date methods to avoid timezone issues

  const year = date.getFullYear()

  const month = String(date.getMonth() + 1).padStart(2, '0')

  const day = String(date.getDate()).padStart(2, '0')

  const hours = String(date.getHours()).padStart(2, '0')

  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}`

}



// Fonction pour convertir une Date en ISO string avec timezone local

function toLocalISOString(date) {

  if (!date) return ''

  // Get timezone offset in minutes

  const offset = date.getTimezoneOffset()

  const offsetHours = Math.floor(Math.abs(offset) / 60)

  const offsetMinutes = Math.abs(offset) % 60

  const offsetSign = offset <= 0 ? '+' : '-'

  const offsetStr = `${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`

  

  // Format as ISO string with local timezone

  const year = date.getFullYear()

  const month = String(date.getMonth() + 1).padStart(2, '0')

  const day = String(date.getDate()).padStart(2, '0')

  const hours = String(date.getHours()).padStart(2, '0')

  const minutes = String(date.getMinutes()).padStart(2, '0')

  const seconds = String(date.getSeconds()).padStart(2, '0')

  

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${offsetStr}`

}



// Helper: clef de date locale (AAAA-MM-JJ) sans décalage de fuseau

function toLocalDateKey(date) {

  if (!date) return ''

  const y = date.getFullYear()

  const m = String(date.getMonth() + 1).padStart(2, '0')

  const d = String(date.getDate()).padStart(2, '0')

  return `${y}-${m}-${d}`

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

  // SUPPRIMÉ: loadBlockedSlots() - sera chargé dans initPermanentCalendar()

  const btn = document.getElementById("openScheduleModalBtn")

  if (btn) btn.addEventListener("click", openScheduleModal)

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



function clearInlineSlots() {

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s) s.value = ""

    if (e) e.value = ""

  }

  

  // Réinitialiser les sélections du calendrier

  selectedDays.clear()

  const allDays = document.querySelectorAll('.calendar-day')

  allDays.forEach(day => {

    day.classList.remove('selected', 'disabled')

  })

}



async function saveInlineSlots() {

  const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

  const inputs = []

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s && e && s.value && e.value) {

      const start = new Date(s.value)

      const end = new Date(e.value)

      if (end <= start) {

        showNotification(`Créneau ${i}: fin doit être après début`, 'error')

        return

      }

      inputs.push({ start, end })

    }

  }

  if (!inputs.length) {

    showNotification('Veuillez saisir au moins un créneau.', 'info')

    return

  }

  // Vérification des conflits d'horaires (même jour OK, même heure NOK)

  const hasTimeConflict = (a, b) => {

    // Vérifier si c'est le même jour

    const sameDay = a.start.toDateString() === b.start.toDateString()

    if (!sameDay) return false

    

    // Si c'est le même jour, vérifier le chevauchement d'horaires

    return a.start < b.end && a.end > b.start

  }

  

  for (let i = 0; i < inputs.length; i++) {

    for (let j = i + 1; j < inputs.length; j++) {

      if (hasTimeConflict(inputs[i], inputs[j])) {

        const dateA = inputs[i].start.toLocaleDateString('fr-FR')

        const timeA = inputs[i].start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

        const timeB = inputs[j].start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

        showNotification(`Conflit d'horaires le ${dateA}: ${timeA} et ${timeB} se chevauchent.`, 'error')

        return

      }

    }

  }

  try {

    const payload = {

      job_id: Number(jobId),

      slots: inputs.map(s => ({ start_time: toLocalISOString(s.start), end_time: toLocalISOString(s.end) }))

    }

    const res = await fetch('/api/hr/interview-slots', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(payload)

    })

    const txt = await res.text()

    if (!res.ok) throw new Error(txt || 'Erreur lors de la sauvegarde des créneaux')

    showNotification('Créneaux enregistrés avec succès! Email d\'invitation envoyé automatiquement.', 'success')

    clearInlineSlots()

  } catch (e) {

    showNotification(e.message || 'Erreur serveur', 'error')

  }

}



// Variables globales pour les créneaux confirmés

let confirmedSlots = [];

let savedSlotIds = [];

// Variable supprimée - la logique de verrouillage est maintenant gérée par candidat



// Fonction pour vérifier l'état des créneaux d'un candidat spécifique

async function checkCandidateSlotsStatus(candidateId) {

  try {

    const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

    console.log(`[DEBUG] Vérification des créneaux pour le candidat ${candidateId} dans le job ${jobId}`)

    

    const slotsRes = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

    const slotsData = await slotsRes.json()

    console.log(`[DEBUG] Tous les créneaux du job:`, slotsData)

    

    // Filtrer les créneaux confirmés pour ce candidat spécifique

    const confirmedSlotsForCandidate = slotsData.filter(slot => 

      slot.is_confirmed && slot.application_id == candidateId

    )

    console.log(`[DEBUG] Créneaux confirmés pour le candidat ${candidateId}:`, confirmedSlotsForCandidate)

    

    return {

      hasConfirmedSlots: confirmedSlotsForCandidate.length > 0,

      confirmedSlots: confirmedSlotsForCandidate

    }

  } catch (error) {

    console.error('Erreur lors de la vérification des créneaux du candidat:', error)

    return { hasConfirmedSlots: false, confirmedSlots: [] }

  }

}



// Fonction pour mettre à jour le bouton d'un candidat spécifique

async function updateCandidateButton(candidateId) {

  console.log(`[DEBUG] Mise à jour du bouton pour le candidat ${candidateId}`)

  

  const button = document.getElementById(`schedule-btn-${candidateId}`)

  const textSpan = document.getElementById(`schedule-text-${candidateId}`)

  const icon = button?.querySelector('i')

  

  if (!button) {

    console.log(`[DEBUG] Bouton non trouvé pour le candidat ${candidateId} (ID: schedule-btn-${candidateId})`)

    return

  }

  

  if (!textSpan) {

    console.log(`[DEBUG] TextSpan non trouvé pour le candidat ${candidateId} (ID: schedule-text-${candidateId})`)

    return

  }

  

  if (!icon) {

    console.log(`[DEBUG] Icône non trouvée pour le candidat ${candidateId}`)

    return

  }

  

  const status = await checkCandidateSlotsStatus(candidateId)

  console.log(`[DEBUG] Statut pour le candidat ${candidateId}:`, status)

  

  // Vérifier le statut de l'application dans le tableau

  const application = applications?.find(app => app.id == candidateId)

  const isInterviewScheduled = application?.status === 'interview_scheduled'

  

  if (status.hasConfirmedSlots) {

    // Le candidat a des créneaux confirmés

    console.log(`[DEBUG] Candidat ${candidateId} a des créneaux confirmés - Mise à jour du bouton`)

    icon.className = 'fas fa-calendar-check'

    

    if (isInterviewScheduled) {

      // Si le statut de l'application est interview_scheduled, le candidat a confirmé

      textSpan.textContent = 'Entretien confirmé'

      console.log(`[DEBUG] Bouton mis à jour pour le candidat ${candidateId}: Entretien confirmé`)

    } else {

      // Sinon, c'est juste des créneaux en attente de confirmation du candidat

      textSpan.textContent = 'Créneaux en attente'

      console.log(`[DEBUG] Bouton mis à jour pour le candidat ${candidateId}: Créneaux en attente`)

    }

    

    button.onclick = () => showConfirmedSlotsModal(status.confirmedSlots)

  } else {

    // Le candidat n'a pas de créneaux confirmés

    console.log(`[DEBUG] Candidat ${candidateId} n'a pas de créneaux confirmés - Mise à jour du bouton`)

    icon.className = 'fas fa-calendar-plus'

    textSpan.textContent = 'Programmer un entretien'

    button.onclick = () => openScheduleInterviewModal(candidateId, 'Candidat')

    console.log(`[DEBUG] Bouton mis à jour pour le candidat ${candidateId}: Programmer un entretien`)

  }

}



// Ces fonctions ne sont plus nécessaires car la confirmation est automatique



// Fonction supprimée - la logique de verrouillage est maintenant gérée par candidat individuellement



// Fonction pour verrouiller le calendrier

// Fonction supprimée - la logique de verrouillage est maintenant gérée par candidat individuellement



// Fonction de test pour forcer la mise à jour de tous les boutons

async function forceUpdateAllButtons() {

  console.log(`[DEBUG] Force update de tous les boutons`)

  

  if (applications && applications.length > 0) {

    console.log(`[DEBUG] Mise à jour forcée de ${applications.length} candidats`)

    for (const app of applications) {

      console.log(`[DEBUG] Mise à jour forcée du candidat ${app.id}`)

      await updateCandidateButton(app.id)

    }

  } else {

    console.log(`[DEBUG] Aucune application trouvée pour la mise à jour forcée`)

  }

}



// Fonction pour marquer les créneaux de temps occupés dans le modal

function markOccupiedTimeSlots(modal, dateString) {

  console.log(`[DEBUG] markOccupiedTimeSlots appelée pour la date: ${dateString}`)

  console.log(`[DEBUG] blockedSlots:`, blockedSlots)

  console.log(`[DEBUG] confirmedSlots:`, confirmedSlots)

  

  const presetBtns = modal.querySelectorAll('.preset-btn')

  console.log(`[DEBUG] Boutons prédéfinis trouvés: ${presetBtns.length}`)

  

  presetBtns.forEach(btn => {

    const startTime = btn.dataset.start

    const endTime = btn.dataset.end

    console.log(`[DEBUG] Vérification du créneau: ${startTime} - ${endTime}`)

    

    // Créer les dates de début et fin pour ce créneau

    const [year, month, day] = dateString.split('-').map(Number)

    const [startHour, startMinute] = startTime.split(':').map(Number)

    const [endHour, endMinute] = endTime.split(':').map(Number)

    

    const startDateTime = new Date(year, month - 1, day, startHour, startMinute, 0)

    const endDateTime = new Date(year, month - 1, day, endHour, endMinute, 0)

    

    // Vérifier les conflits avec les créneaux bloqués (réservés par d'autres candidats) - seulement pour la date courante

    const hasConflictWithBlocked = blockedSlots && blockedSlots.some(blockedSlot => {

      const blockedStart = new Date(blockedSlot.start_time)

      const blockedEnd = new Date(blockedSlot.end_time)

      

      // Vérifier que le créneau bloqué est sur la même date

      const blockedDate = toLocalDateKey(blockedStart)

      const currentDate = toLocalDateKey(startDateTime)

      

      if (blockedDate !== currentDate) {

        return false // Ignorer les créneaux d'autres dates

      }

      

      const conflict = startDateTime < blockedEnd && endDateTime > blockedStart

      if (conflict) {

        console.log(`[DEBUG] Conflit avec créneau bloqué:`, blockedSlot)

      }

      return conflict

    })

    

    // Vérifier les conflits avec les créneaux réservés par le même agent HR (seulement pour la date courante)

    const hasConflictWithReserved = confirmedSlots && confirmedSlots.some(reservedSlot => {

      const reservedStart = new Date(reservedSlot.start_time)

      const reservedEnd = new Date(reservedSlot.end_time)

      

      // Vérifier que le créneau réservé est sur la même date

      const reservedDate = toLocalDateKey(reservedStart)

      const currentDate = toLocalDateKey(startDateTime)

      

      if (reservedDate !== currentDate) {

        return false // Ignorer les créneaux d'autres dates

      }

      

      const conflict = startDateTime < reservedEnd && endDateTime > reservedStart

      if (conflict) {

        console.log(`[DEBUG] Conflit avec créneau réservé:`, reservedSlot)

      }

      return conflict

    })

    

    // Vérifier les conflits avec les créneaux déjà sélectionnés par le même candidat (seulement pour la date courante)

    const hasConflictWithCandidateSlots = currentCandidateId && selectedSlotsByCandidate[currentCandidateId] && selectedSlotsByCandidate[currentCandidateId].some(candidateSlot => {

      const candidateStart = new Date(candidateSlot.start)

      const candidateEnd = new Date(candidateSlot.end)

      

      // Vérifier que le créneau du candidat est sur la même date

      const candidateDate = toLocalDateKey(candidateStart)

      const currentDate = toLocalDateKey(startDateTime)

      

      if (candidateDate !== currentDate) {

        return false // Ignorer les créneaux d'autres dates

      }

      

      const conflict = startDateTime < candidateEnd && endDateTime > candidateStart

      if (conflict) {

        console.log(`[DEBUG] Conflit avec créneau du candidat:`, candidateSlot)

      }

      return conflict

    })

    

    // Vérifier les conflits avec les créneaux actuellement sélectionnés dans le modal (pas encore sauvegardés)

    const hasConflictWithModalSlots = (() => {

      const selectedList = modal.querySelector('.selected-times-list')

      if (!selectedList) {

        console.log(`[DEBUG] selectedList non trouvé`)

        return false

      }

      

      const selectedItems = selectedList.querySelectorAll('.selected-time-chip')

      console.log(`[DEBUG] selectedItems trouvés: ${selectedItems.length}`)

      

      return Array.from(selectedItems).some(item => {

        const span = item.querySelector('span')

        if (!span) return false

        

        const timeText = span.textContent

        console.log(`[DEBUG] Vérification item: ${timeText}`)

        

        if (!timeText || !timeText.includes(' - ')) return false

        

        const [startTimeText, endTimeText] = timeText.split(' - ')

        console.log(`[DEBUG] Parsed: ${startTimeText}-${endTimeText}`)

        

        if (!startTimeText || !endTimeText) return false

        

        // Convertir les heures du modal en dates

        const [startHour, startMinute] = startTimeText.split(':').map(Number)

        const [endHour, endMinute] = endTimeText.split(':').map(Number)

        

        const modalStartDateTime = new Date(year, month - 1, day, startHour, startMinute, 0)

        const modalEndDateTime = new Date(year, month - 1, day, endHour, endMinute, 0)

        

        const conflict = startDateTime < modalEndDateTime && endDateTime > modalStartDateTime

        if (conflict) {

          console.log(`[DEBUG] Conflit avec créneau du modal: ${startTimeText}-${endTimeText}`)

        }

        return conflict

      })

    })()

    

    console.log(`[DEBUG] Créneau ${startTime}-${endTime}: blocked=${hasConflictWithBlocked}, reserved=${hasConflictWithReserved}, candidate=${hasConflictWithCandidateSlots}, modal=${hasConflictWithModalSlots}`)

    

    // Marquer le bouton selon le type de conflit

    if (hasConflictWithBlocked) {

      btn.classList.add('occupied')

      btn.title = 'Ce créneau est réservé par un autre candidat'

      btn.disabled = true

      console.log(`[DEBUG] Bouton marqué comme occupé: ${startTime}-${endTime}`)

    } else if (hasConflictWithReserved) {

      btn.classList.add('reserved-by-me')

      btn.title = 'Ce créneau est réservé par vous'

      btn.disabled = true

      console.log(`[DEBUG] Bouton marqué comme réservé par moi: ${startTime}-${endTime}`)

    } else if (hasConflictWithCandidateSlots || hasConflictWithModalSlots) {

      btn.classList.add('selected-by-candidate')

      btn.title = 'Ce créneau est déjà sélectionné par ce candidat'

      btn.disabled = true

      console.log(`[DEBUG] Bouton marqué comme sélectionné par le candidat: ${startTime}-${endTime}`)

    }

  })

}



// Fonction pour afficher le modal des créneaux confirmés

function showConfirmedSlotsModal(confirmedSlots) {

  console.log("[DEBUG] showConfirmedSlotsModal appelée avec:", confirmedSlots)

  

  // Créer le modal s'il n'existe pas

  let modal = document.getElementById('confirmedSlotsModal')

  if (!modal) {

    console.log("[DEBUG] Création du modal confirmedSlotsModal")

    modal = createConfirmedSlotsModal()

    document.body.appendChild(modal)

  } else {

    console.log("[DEBUG] Modal confirmedSlotsModal existe déjà")

  }

  

  // Générer le calendrier professionnel

  console.log("[DEBUG] Génération du calendrier avec les créneaux:", confirmedSlots)

  // Classifier les créneaux
  const status = (slot) => (slot.status || '').toString().toLowerCase()
  const isConfirmed = (slot) => status(slot) === 'reserved' || status(slot) === 'confirmed'
  const isPending = (slot) => status(slot) === 'free'

  const pendingSlots = (confirmedSlots || []).filter(isPending)
  const confirmedSlotsArr = (confirmedSlots || []).filter(isConfirmed)

  // Mettre à jour les statistiques
  const totalCount = modal.querySelector('#totalSlotsCount')
  const pendingCount = modal.querySelector('#pendingSlotsCount')
  const confirmedCount = modal.querySelector('#confirmedSlotsCount')
  const pendingTabBadge = modal.querySelector('#pendingTabBadge')
  const confirmedTabBadge = modal.querySelector('#confirmedTabBadge')

  if (totalCount) totalCount.textContent = confirmedSlots.length
  if (pendingCount) pendingCount.textContent = pendingSlots.length
  if (confirmedCount) confirmedCount.textContent = confirmedSlotsArr.length
  if (pendingTabBadge) pendingTabBadge.textContent = pendingSlots.length
  if (confirmedTabBadge) confirmedTabBadge.textContent = confirmedSlotsArr.length

  // Remplir les grilles
  const pendingGrid = modal.querySelector('#pendingSlotsGrid')
  const confirmedGrid = modal.querySelector('#confirmedSlotsGrid')

  if (pendingGrid) {
    pendingGrid.innerHTML = pendingSlots.map(slot => createSlotCard(slot, 'pending')).join('')
  }

  if (confirmedGrid) {
    confirmedGrid.innerHTML = confirmedSlotsArr.map(slot => createSlotCard(slot, 'confirmed')).join('')
  }

  // Afficher l'onglet par défaut
  const defaultTab = pendingSlots.length > 0 ? 'pending' : 'confirmed'
  switchSlotsTab(defaultTab)

  

  // Afficher le modal

  console.log("[DEBUG] Affichage du modal confirmedSlotsModal")

  modal.style.display = 'block'

  modal.classList.add('show')

  console.log("[DEBUG] Modal affiché avec style:", modal.style.display)

}



// Variables globales pour le calendrier confirmé

let confirmedCalendarCurrentDate = new Date()

let globalConfirmedSlots = []



// Variables globales pour les créneaux bloqués

let blockedSlots = []

let busyDays = new Set()

let partiallyOccupiedDays = new Set()



// Fonction pour générer le calendrier professionnel des créneaux confirmés

function generateConfirmedCalendar(confirmedSlots) {

  console.log("[DEBUG] generateConfirmedCalendar appelée avec:", confirmedSlots)

  

  const calendarDays = document.getElementById('confirmedCalendarDays')

  const calendarHeader = document.querySelector('.calendar-header-confirmed h3')

  

  console.log("[DEBUG] Éléments DOM trouvés:")

  console.log("  - confirmedCalendarDays:", calendarDays)

  console.log("  - calendar-header-confirmed h3:", calendarHeader)

  

  if (!calendarDays || !calendarHeader) {

    console.log("[DEBUG] Éléments DOM manquants, arrêt de la génération du calendrier")

    return

  }

  

  // Stocker les créneaux confirmés globalement pour la navigation

  if (confirmedSlots) {

    globalConfirmedSlots = confirmedSlots

  }

  

  // Utiliser la date courante du calendrier confirmé

  const currentMonth = confirmedCalendarCurrentDate.getMonth()

  const currentYear = confirmedCalendarCurrentDate.getFullYear()

  

  // Mettre à jour le titre avec le mois et l'année

  const monthNames = [

    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',

    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'

  ]

  calendarHeader.innerHTML = `<i class="fas fa-calendar-alt"></i> ${monthNames[currentMonth]} ${currentYear} - Créneaux confirmés`

  

  // Premier jour du mois

  const firstDay = new Date(currentYear, currentMonth, 1)

  const lastDay = new Date(currentYear, currentMonth + 1, 0)

  

  // Jours de la semaine (0 = dimanche, 1 = lundi, etc.)

  const startDay = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1 // Convertir pour commencer par lundi

  

  // Créer des Sets des dates selon le statut

  const confirmedDates = new Set()

  const reservedDates = new Set()

  const pendingDates = new Set()

  const slotsToUse = confirmedSlots || globalConfirmedSlots

  if (slotsToUse) {

    slotsToUse.forEach(slot => {

      const slotDate = new Date(slot.start_time)

      const dateKey = toLocalDateKey(slotDate)

      confirmedDates.add(dateKey)

      const status = (slot.status || '').toString().toLowerCase()

      if (status === 'reserved') reservedDates.add(dateKey)

      else pendingDates.add(dateKey)

    })

  }

  

  // Vider le calendrier

  calendarDays.innerHTML = ''

  

  // Ajouter les jours vides du début du mois

  for (let i = 0; i < startDay; i++) {

    const emptyDay = document.createElement('div')

    emptyDay.className = 'calendar-day-confirmed empty'

    calendarDays.appendChild(emptyDay)

  }

  

  // Ajouter tous les jours du mois

  for (let day = 1; day <= lastDay.getDate(); day++) {

    const dayElement = document.createElement('div')

    dayElement.className = 'calendar-day-confirmed'

    

    const currentDate = new Date(currentYear, currentMonth, day)

    const dateKey = toLocalDateKey(currentDate)

    

    // Numéro du jour

    const dayNumber = document.createElement('div')

    dayNumber.className = 'day-number'

    dayNumber.textContent = day

    dayElement.appendChild(dayNumber)

    

    // Vérifier si c'est aujourd'hui

    const today = new Date()

    if (currentDate.toDateString() === today.toDateString()) {

      dayElement.classList.add('today')

    }

    

    // Vérifier si ce jour a des créneaux confirmés et réserver l'aspect selon statut

    if (confirmedDates.has(dateKey)) {

      dayElement.classList.add('has-confirmed-slots')

      if (reservedDates.has(dateKey)) {

        dayElement.classList.add('has-reserved-slots')

      } else if (pendingDates.has(dateKey)) {

        dayElement.classList.add('has-pending-slots')

      }

      

      // Ajouter les créneaux de ce jour

      const daySlots = slotsToUse.filter(slot => {

        const slotDateKey = toLocalDateKey(new Date(slot.start_time))

        return slotDateKey === dateKey

      })

      

      const slotsContainer = document.createElement('div')

      slotsContainer.className = 'day-slots'

      

      daySlots.forEach(slot => {

        const startTime = new Date(slot.start_time)

        const endTime = new Date(slot.end_time)

        const timeStr = `${startTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}-${endTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`

        

        const slotElement = document.createElement('div')

        const status = (slot.status || '').toString().toLowerCase()

        slotElement.className = `day-slot ${status === 'reserved' ? 'selected' : 'pending'}`

        slotElement.textContent = timeStr

        slotsContainer.appendChild(slotElement)

      })

      

      dayElement.appendChild(slotsContainer)

    }

    

    calendarDays.appendChild(dayElement)

  }

}



// Fonctions de navigation pour le calendrier confirmé

function previousMonthConfirmed() {

  confirmedCalendarCurrentDate.setMonth(confirmedCalendarCurrentDate.getMonth() - 1)

  generateConfirmedCalendar(globalConfirmedSlots)

}



function nextMonthConfirmed() {

  confirmedCalendarCurrentDate.setMonth(confirmedCalendarCurrentDate.getMonth() + 1)

  generateConfirmedCalendar(globalConfirmedSlots)

}



// Fonction pour créer le modal des créneaux confirmés

function createConfirmedSlotsModal() {

  const modal = document.createElement('div')

  modal.id = 'confirmedSlotsModal'

  modal.className = 'modal modern-modal-overlay'

  modal.style.display = 'none'

  

  modal.innerHTML = `

    <div class="modal-content confirmed-slots-modal">

      <div class="modal-header modern-header">

        <div class="header-content">

          <div class="header-icon">

            <i class="fas fa-calendar-check"></i>

          </div>

          <div class="header-text">

            <h2>Gestion des créneaux d'entretien</h2>

            <p class="header-subtitle">Vue d'ensemble des créneaux réservés et confirmés</p>

          </div>

        </div>

        <button class="close-btn modern-close" onclick="closeConfirmedSlotsModal()">

          <i class="fas fa-times"></i>

        </button>

      </div>

      <div class="modal-body confirmed-slots-body">

        <!-- Statistiques résumées -->
        <div class="slots-summary-cards">
          <div class="summary-card total">
            <div class="summary-icon">
              <i class="fas fa-layer-group"></i>
            </div>
            <div class="summary-content">
              <div class="summary-number" id="totalSlotsCount">0</div>
              <div class="summary-label">Total créneaux</div>
            </div>
          </div>
          <div class="summary-card pending">
            <div class="summary-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="summary-content">
              <div class="summary-number" id="pendingSlotsCount">0</div>
              <div class="summary-label">En attente</div>
            </div>
          </div>
          <div class="summary-card confirmed">
            <div class="summary-icon">
              <i class="fas fa-check-circle"></i>
            </div>
            <div class="summary-content">
              <div class="summary-number" id="confirmedSlotsCount">0</div>
              <div class="summary-label">Confirmés</div>
            </div>
          </div>
        </div>

        <!-- Navigation par onglets -->
        <div class="slots-tabs">
          <button class="tab-button active" data-tab="pending" onclick="switchSlotsTab('pending')">
            <i class="fas fa-user-clock"></i>
            <span>Créneaux en attente</span>
            <div class="tab-badge" id="pendingTabBadge">0</div>
          </button>
          <button class="tab-button" data-tab="confirmed" onclick="switchSlotsTab('confirmed')">
            <i class="fas fa-check-circle"></i>
            <span>Entretiens confirmés</span>
            <div class="tab-badge" id="confirmedTabBadge">0</div>
          </button>
        </div>

        <!-- Contenu des onglets -->
        <div class="slots-content">
          <div class="tab-panel active" id="pendingPanel">
            <div class="panel-header">
              <h3><i class="fas fa-user-clock"></i> Créneaux en attente</h3>
              <p>Créneaux réservés par l'agent RH, en attente de confirmation du candidat</p>
            </div>
            <div class="slots-grid" id="pendingSlotsGrid">
              <!-- Les créneaux en attente seront insérés ici -->
            </div>
          </div>
          <div class="tab-panel" id="confirmedPanel">
            <div class="panel-header">
              <h3><i class="fas fa-check-circle"></i> Entretiens confirmés</h3>
              <p>Créneaux acceptés par les candidats</p>
            </div>
            <div class="slots-grid" id="confirmedSlotsGrid">
              <!-- Les créneaux confirmés seront insérés ici -->
            </div>
          </div>
        </div>

        <!-- Actions du modal -->
        <div class="modal-actions">
          <button class="btn-secondary" onclick="closeConfirmedSlotsModal()">
            <i class="fas fa-times"></i>
            <span>Fermer</span>
          </button>
        </div>

      </div>

    </div>

  `

  

  return modal

}

// Fonction pour basculer entre les onglets
function switchSlotsTab(tabName) {
  // Désactiver tous les onglets
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'))
  document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'))
  
  // Activer l'onglet sélectionné
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active')
  document.getElementById(`${tabName}Panel`).classList.add('active')
}

// Fonction pour créer une carte de créneau (pour le modal des créneaux confirmés)
function createSlotCard(slot, type) {
  const startDate = new Date(slot.start_time)
  const endDate = new Date(slot.end_time)
  
  const dateStr = startDate.toLocaleDateString('fr-FR', { 
    weekday: 'long', 
    day: 'numeric', 
    month: 'long' 
  })
  const timeStr = `${startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} - ${endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
  
  const statusClass = type === 'confirmed' ? 'confirmed' : 'pending'
  const statusIcon = type === 'confirmed' ? 'fas fa-check-circle' : 'fas fa-clock'
  const statusText = type === 'confirmed' ? 'Confirmé' : 'En attente'
  
  return `
    <div class="slot-card ${statusClass}">
      <div class="slot-date">
        <div class="date-day">${startDate.getDate()}</div>
        <div class="date-month">${startDate.toLocaleDateString('fr-FR', { month: 'short' })}</div>
      </div>
      <div class="slot-info">
        <div class="slot-time">${timeStr}</div>
        <div class="slot-weekday">${startDate.toLocaleDateString('fr-FR', { weekday: 'long' })}</div>
        <div class="slot-status">
          <i class="${statusIcon}"></i>
          <span>${statusText}</span>
        </div>
      </div>
    </div>
  `
}

// Fonction pour créer une carte de créneau d'entretien (avec bouton de suppression)
function createInterviewSlotCard(slot, index) {
  const startDate = new Date(slot.start_time)
  const endDate = new Date(slot.end_time)
  
  const timeStr = `${startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} - ${endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
  
  return `
    <div class="slot-card">
      <button class="slot-delete-btn" onclick="deleteInterviewSlot(${slot.id || index})" title="Supprimer ce créneau">
        <i class="fas fa-times"></i>
      </button>
      <div class="slot-header">
        <div class="slot-number">${index + 1}</div>
        <div class="slot-title">Créneau ${index + 1}</div>
      </div>
      <div class="slot-inputs">
        <div class="input-group">
          <label>Heure de début</label>
          <input type="time" class="slot-input" value="${startDate.toTimeString().slice(0, 5)}" onchange="updateSlotTime(${slot.id || index}, 'start', this.value)">
        </div>
        <div class="input-group">
          <label>Heure de fin</label>
          <input type="time" class="slot-input" value="${endDate.toTimeString().slice(0, 5)}" onchange="updateSlotTime(${slot.id || index}, 'end', this.value)">
        </div>
      </div>
      <div class="slot-status free">
        <i class="fas fa-check-circle"></i>
        <span>Disponible</span>
      </div>
    </div>
  `
}

// Fonction pour vider un créneau d'entretien
function clearInterviewSlot(slotId) {
  if (!slotId || slotId === 'null') {
    console.warn('ID de créneau invalide:', slotId)
    return
  }

  if (confirm('Êtes-vous sûr de vouloir vider ce créneau d\'entretien ?')) {
    console.log('Vidage du créneau d\'entretien:', slotId)
    
    // Vider les inputs du créneau
    const startInput = document.getElementById(`slot${slotId}_start`)
    const endInput = document.getElementById(`slot${slotId}_end`)
    const statusElement = document.getElementById(`slot${slotId}_status`)
    
    if (startInput) startInput.value = ''
    if (endInput) endInput.value = ''
    
    // Remettre le statut à "Disponible"
    if (statusElement) {
      statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Disponible</span>'
      statusElement.className = 'slot-status'
    }
    
    // Animation de feedback
    const slotCard = document.querySelector(`[onclick="clearInterviewSlot(${slotId})"]`)?.closest('.slot-card')
    if (slotCard) {
      slotCard.style.transition = 'all 0.3s ease'
      slotCard.style.transform = 'scale(0.95)'
      slotCard.style.backgroundColor = '#fef2f2'
      
      setTimeout(() => {
        slotCard.style.transform = 'scale(1)'
        slotCard.style.backgroundColor = ''
      }, 300)
    }
  }
}

// Fonction pour mettre à jour les numéros des créneaux d'entretien
function updateInterviewSlotNumbers() {
  const slotCards = document.querySelectorAll('.slots-grid .slot-card')
  slotCards.forEach((card, index) => {
    const numberElement = card.querySelector('.slot-number')
    const titleElement = card.querySelector('.slot-title')
    if (numberElement) numberElement.textContent = index + 1
    if (titleElement) titleElement.textContent = `Créneau ${index + 1}`
  })
}

// Fonction pour mettre à jour l'heure d'un créneau
function updateSlotTime(slotId, type, time) {
  console.log(`Mise à jour ${type} du créneau ${slotId}:`, time)
  // Ici vous pouvez ajouter la logique pour mettre à jour l'heure
}

// Fonction pour mettre à jour les compteurs de créneaux
function updateSlotCounters() {
  const pendingSlots = document.querySelectorAll('#pendingSlotsGrid .slot-card').length
  const confirmedSlots = document.querySelectorAll('#confirmedSlotsGrid .slot-card').length
  const totalSlots = pendingSlots + confirmedSlots

  const pendingCount = document.querySelector('#pendingSlotsCount')
  const confirmedCount = document.querySelector('#confirmedSlotsCount')
  const totalCount = document.querySelector('#totalSlotsCount')
  const pendingTabBadge = document.querySelector('#pendingTabBadge')
  const confirmedTabBadge = document.querySelector('#confirmedTabBadge')

  if (pendingCount) pendingCount.textContent = pendingSlots
  if (confirmedCount) confirmedCount.textContent = confirmedSlots
  if (totalCount) totalCount.textContent = totalSlots
  if (pendingTabBadge) pendingTabBadge.textContent = pendingSlots
  if (confirmedTabBadge) confirmedTabBadge.textContent = confirmedSlots
}

// Fonction pour fermer le modal des créneaux confirmés

function closeConfirmedSlotsModal() {

  const modal = document.getElementById('confirmedSlotsModal')

  if (modal) {

    modal.style.display = 'none'

    modal.classList.remove('show')

  }

}



// Fonction pour charger les créneaux confirmés (simplifiée)

async function loadConfirmedSlots() {

  const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

  

  try {

    const res = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

    const slots = await res.json()

    

    const confirmed = slots.filter(slot => slot.is_confirmed)

    

    // Stocker les créneaux confirmés dans la variable globale

    confirmedSlots = confirmed

    

    // Mettre à jour l'affichage du calendrier

    updateCalendarDayStates()

    // Afficher les heures déjà sélectionnées

    showSelectedHours()

    setTimeout(() => showSelectedHours(), 200)

    setTimeout(() => showSelectedHours(), 500)

    

  } catch (e) {

    console.error('Erreur lors du chargement des créneaux confirmés:', e)

  }

}



// Fonction pour charger tous les créneaux bloqués (réservés par d'autres candidats)

// VERSION MODIFIÉE - Seuls les jours avec TOUS les créneaux occupés sont marqués comme busy

async function loadBlockedSlots() {

  const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

  

  try {

    const res = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

    const slots = await res.json()

    

    // Filtrer les créneaux qui sont réservés par des candidats (pas libres)

    const reserved = slots.filter(slot => slot.status === 'RESERVED' || slot.status === 'CONFIRMED')

    

    // Stocker les créneaux bloqués

    blockedSlots = reserved

    

    // Analyser les jours pour déterminer leur niveau d'occupation

    busyDays.clear()

    partiallyOccupiedDays.clear()

    const daySlotCounts = new Map()

    

    // Compter TOUS les créneaux (réservés + confirmés) par jour

    // Utiliser seulement les données de l'API pour éviter les incohérences

    const allOccupiedSlots = slots.filter(slot => slot.status === 'RESERVED' || slot.status === 'CONFIRMED' || slot.is_confirmed)

    

    allOccupiedSlots.forEach(slot => {

      const slotDate = new Date(slot.start_time)

      const dateKey = toLocalDateKey(slotDate)

      daySlotCounts.set(dateKey, (daySlotCounts.get(dateKey) || 0) + 1)

    })

    

    // Marquer les jours selon leur niveau d'occupation

    daySlotCounts.forEach((count, dateKey) => {

      if (count >= 4) {

        // Jour complètement occupé (rouge) - 4 créneaux maximum atteints

        busyDays.add(dateKey)

      } else if (count > 0) {

        // Jour partiellement occupé (jaune) - au moins un créneau est pris

        partiallyOccupiedDays.add(dateKey)

      }

    })

    

    // Mettre à jour l'affichage du calendrier immédiatement

    updateCalendarDayStates()

    // Afficher les heures déjà sélectionnées

    showSelectedHours()

    setTimeout(() => showSelectedHours(), 200)

    setTimeout(() => showSelectedHours(), 500)

    

  } catch (e) {

    console.error('Erreur lors du chargement des créneaux bloqués:', e)

  }

}



// Cette fonction n'est plus nécessaire



// Modifier la fonction saveInlineSlots pour créer ET confirmer automatiquement

async function saveInlineSlotsWithIds() {

  const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

  console.log(`[DEBUG] saveInlineSlotsWithIds - currentCandidateId: ${currentCandidateId}, jobId: ${jobId}`)

  console.log(`[DEBUG] currentAppId: ${currentAppId}`)

  const inputs = []

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s && e && s.value && e.value) {

      const start = new Date(s.value)

      const end = new Date(e.value)

      if (end <= start) {

        showNotification(`Créneau ${i}: fin doit être après début`, 'error')

        return

      }

      inputs.push({ start, end })

    }

  }

  if (!inputs.length) {

    showNotification('Veuillez saisir au moins un créneau.', 'info')

    return

  }

  

  // Vérifier la limite de 4 créneaux par candidat

  if (currentCandidateId) {

    const existingSlots = selectedSlotsByCandidate[currentCandidateId] || []

    const totalSlots = existingSlots.length + inputs.length

    if (totalSlots > 4) {

      showNotification(`Ce candidat ne peut pas avoir plus de 4 créneaux. Actuellement: ${existingSlots.length}, ajoutés: ${inputs.length}.`, 'error')

      return

    }

  }

  

  // Vérification des conflits d'horaires (même jour OK, même heure NOK)

  const hasTimeConflict = (a, b) => {

    // Vérifier si c'est le même jour

    const sameDay = a.start.toDateString() === b.start.toDateString()

    if (!sameDay) return false

    

    // Si c'est le même jour, vérifier le chevauchement d'horaires

    return a.start < b.end && a.end > b.start

  }

  

  for (let i = 0; i < inputs.length; i++) {

    for (let j = i + 1; j < inputs.length; j++) {

      if (hasTimeConflict(inputs[i], inputs[j])) {

        showNotification(`Conflit d'horaires entre les créneaux ${i + 1} et ${j + 1}`, 'error')

        return

      }

    }

  }

  

  try {

    // 1. Créer les créneaux

    const payload = {

      job_id: Number(jobId),

      application_id: currentCandidateId ? Number(currentCandidateId) : null,

      slots: inputs.map(s => ({ start_time: toLocalISOString(s.start), end_time: toLocalISOString(s.end) }))

    }

    console.log(`[DEBUG] Payload de création des créneaux:`, payload)

    const res = await fetch('/api/hr/interview-slots', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(payload)

    })

    const result = await res.json()

    console.log(`[DEBUG] Réponse de création des créneaux:`, result)

    if (!res.ok) throw new Error(result.detail || 'Erreur lors de la sauvegarde des créneaux')

    

    // 2. Confirmer automatiquement les créneaux créés

    if (result.created && result.created.length > 0) {

      const confirmPayload = {

        job_id: Number(jobId),

        application_id: currentCandidateId ? Number(currentCandidateId) : null,

        slot_ids: result.created

      }

      console.log(`[DEBUG] Payload de confirmation des créneaux:`, confirmPayload)

      

      const confirmRes = await fetch('/api/hr/interview-slots/confirm', {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify(confirmPayload)

      })

      

      if (confirmRes.ok) {

        showNotification('Créneaux créés et confirmés avec succès ! En attente de la réponse du candidat.', 'success')

        

        // 3. Mettre à jour l'interface immédiatement

        const confirmResult = await confirmRes.json()

        console.log(`[DEBUG] Réponse de confirmation des créneaux:`, confirmResult)

        if (confirmResult.confirmed_slots) {

          // Les créneaux sont maintenant confirmés

          

          // Stocker les créneaux pour ce candidat

          if (currentCandidateId) {

            selectedSlotsByCandidate[currentCandidateId] = inputs.map((slot, index) => ({

              start: slot.start,

              end: slot.end,

              id: result.created[index]

            }))

            console.log(`[DEBUG] Créneaux stockés pour le candidat ${currentCandidateId}:`, selectedSlotsByCandidate[currentCandidateId])

          }

          

          // Mettre à jour le bouton du candidat

          console.log(`[DEBUG] currentCandidateId lors de la sauvegarde: ${currentCandidateId}`)

          if (currentCandidateId) {

            console.log(`[DEBUG] Mise à jour du bouton pour le candidat ${currentCandidateId} après sauvegarde`)

            await updateCandidateButton(currentCandidateId)

          } else {

            console.log(`[DEBUG] currentCandidateId n'est pas défini, mise à jour de tous les boutons`)

            // Fallback: mettre à jour tous les boutons des candidats

            const allButtons = document.querySelectorAll('[id^="schedule-btn-"]')

            console.log(`[DEBUG] Boutons trouvés: ${allButtons.length}`)

            

            for (const button of allButtons) {

              const candidateId = button.id.replace('schedule-btn-', '')

              console.log(`[DEBUG] Mise à jour du bouton pour le candidat: ${candidateId}`)

              if (candidateId) {

                await updateCandidateButton(candidateId)

              }

            }

            

            // Aussi mettre à jour tous les candidats de la liste actuelle

            if (applications && applications.length > 0) {

              console.log(`[DEBUG] Mise à jour de tous les candidats de la liste: ${applications.length}`)

              for (const app of applications) {

                await updateCandidateButton(app.id)

              }

            }

          }

          

          // Récupérer les créneaux confirmés pour les afficher

          const slotsRes = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

          const slotsData = await slotsRes.json()

          const confirmedSlotsData = slotsData.filter(slot => slot.is_confirmed)

          

          // Mettre à jour les créneaux confirmés

          confirmedSlots = confirmedSlotsData

          

          // Recharger les créneaux bloqués pour mettre à jour la coloration AVANT updateCalendarDayStates

          await loadBlockedSlots()

          

          // Attendre un petit délai pour s'assurer que les données sont bien mises à jour

          setTimeout(() => {

            updateCalendarDayStates()

          }, 100)

          

          // Force update de tous les boutons après un délai pour s'assurer que tout est bien mis à jour

          setTimeout(async () => {

            console.log(`[DEBUG] Force update après sauvegarde`)

            await forceUpdateAllButtons()

          }, 1000)

          

          // Recharger les applications pour mettre à jour les boutons

          setTimeout(() => {

            loadApplications()

          }, 1000)

          

          // Informer l'utilisateur que l'email a été envoyé automatiquement

          if (currentCandidateId) {

            showNotification('Créneaux confirmés et email d\'invitation envoyé automatiquement au candidat !', 'success')

          }

        }

      } else {

        showNotification('Créneaux créés mais erreur lors de la confirmation', 'warning')

      }

    }

    

    clearInlineSlots()

    closeScheduleModal()

    

  } catch (e) {

    showNotification(e.message || 'Erreur serveur', 'error')

  }

}



function openScheduleModal() {

  // Ne plus bloquer l'accès - permettre la sélection pour tous les candidats

  // Réinitialiser currentCandidateId pour le modal global

  currentCandidateId = null

  currentAppId = null

  

  const modal = document.getElementById('scheduleInterviewModal')

  if (!modal) return

  modal.style.display = 'block'

  modal.classList.add('show')

  initGoogleSection()

  bindSlotInputsForGoogle()

}



function closeScheduleModal() {

  const modal = document.getElementById('scheduleInterviewModal')

  if (!modal) return

  modal.style.display = 'none'

  modal.classList.remove('show')

}



function clearModalSlots() { clearInlineSlots() }

async function saveModalSlots() { 

  await saveInlineSlotsWithIds(); 

  closeScheduleModal(); 

}



// Variables globales pour le calendrier Google

let googleCalendarEmbedded = false;

let currentCalendarView = 'month';

let selectedCalendarId = null;



// Variables globales pour le calendrier permanent

let currentDate = new Date();

// selectedDays n'est plus utilisé pour contraindre la sélection; on dérive l'état depuis les inputs de créneaux

let selectedDays = new Set();

let calendarInitialized = false;



// Helper global: compter les créneaux remplis (start & end) pour le candidat courant

function getFilledSlotsCount() {

  // Si on est dans le contexte d'un candidat spécifique, compter ses créneaux

  if (currentCandidateId && selectedSlotsByCandidate[currentCandidateId]) {

    return selectedSlotsByCandidate[currentCandidateId].length

  }

  

  // Sinon, compter les créneaux globaux (pour compatibilité)

  let filled = 0

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s && e && s.value && e.value) filled++

  }

  return filled

}



// Helper: vérifier s'il existe un créneau pour une date donnée (AAAA-MM-JJ)

function hasSlotOnDate(dateString) {

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    if (s && s.value) {

      const d = new Date(s.value)

      const k = d.toISOString().split('T')[0]

      if (k === dateString) return true

    }

  }

  return false

}



async function initGoogleSection() {

  const statusBadge = document.getElementById('googleStatusBadge')

  const btn = document.getElementById('btnConnectGoogle')

  const sel = document.getElementById('googleCalendarSelect')

  const info = document.getElementById('googleConflictInfo')

  const calendarContainer = document.getElementById('googleCalendarContainer')

  

  // Only require elements that are guaranteed to exist in the modal
  // If status badge doesn't exist, we still continue to show the info message and calendar container handling
  if (!info || !calendarContainer) return

  

  // Vérifier les paramètres URL pour les erreurs ou succès

  const urlParams = new URLSearchParams(window.location.search)

  const connected = urlParams.get('connected')

  const error = urlParams.get('error')

  

  // Afficher les messages d'erreur ou de succès

  if (error) {

    let errorMessage = ''

    switch (error) {

      case 'session_expired':

        errorMessage = 'Session expirée. Veuillez vous reconnecter.'

        break

      case 'not_authenticated':

        errorMessage = 'Vous devez être connecté pour utiliser Google Calendar.'

        break

      case 'google_auth_failed':

        errorMessage = 'Échec de l\'authentification Google. Veuillez réessayer.'

        break

      case 'google_callback_error':

        errorMessage = 'Erreur lors de la connexion à Google Calendar.'

        break

      default:

        errorMessage = 'Erreur lors de la connexion Google Calendar.'

    }

    

    // Afficher l'erreur dans le badge

    statusBadge.textContent = 'Erreur'

    statusBadge.className = 'error'

    statusBadge.title = errorMessage

    

    console.error('Google Calendar Error:', errorMessage)

    

    // Nettoyer l'URL

    const newUrl = window.location.pathname

    window.history.replaceState({}, document.title, newUrl)

  }

  

  try {

    // Récupérer le token JWT depuis localStorage

    const accessToken = localStorage.getItem('hr_access_token')

    if (!accessToken) {

      console.error('No HR access token found')

      if (statusBadge) {
        statusBadge.textContent = ''
        statusBadge.className = ''
        statusBadge.title = ''
      }

      if (btn) btn.style.display = 'inline-block'

      if (sel) sel.style.display = 'none'

      calendarContainer.style.display = 'none'

      info.textContent = ''

      return

    }

    

    const response = await fetch('/api/hr/google/status', {

      headers: {

        'Authorization': `Bearer ${accessToken}`

      }

    })

    

    if (!response.ok) {

      throw new Error(`HTTP ${response.status}: ${response.statusText}`)

    }

    

    const s = await response.json()

    if (s.connected) {

      if (statusBadge) {
        statusBadge.textContent = ''
        statusBadge.className = ''
        statusBadge.title = ''
      }

      if (btn) btn.style.display = 'none'

      if (sel) sel.style.display = 'inline-block'

      calendarContainer.style.display = 'block'

      

      try {

        const listResponse = await fetch('/api/hr/google/calendar-list', {

          headers: {

            'Authorization': `Bearer ${accessToken}`

          }

        })

        

        if (!listResponse.ok) {

          throw new Error(`HTTP ${listResponse.status}: ${listResponse.statusText}`)

        }

        

        const list = await listResponse.json()

      if (list.success) {

        if (sel) {
          sel.innerHTML = list.calendars.map(c=>`<option value="${c.id}">${c.summary}</option>`).join('')
        }

        selectedCalendarId = list.calendars[0]?.id

        loadGoogleCalendarEmbed()

        } else {

          console.error('Failed to load calendar list:', list)

        }

      } catch (listError) {

        console.error('Error loading calendar list:', listError)

        info.textContent = 'Erreur lors du chargement des calendriers'

        info.style.color = '#c0392b'

      }

      

      await checkGoogleConflicts()

    } else {

      if (statusBadge) {
        statusBadge.textContent = ''
        statusBadge.className = ''
        statusBadge.title = ''
      }

      if (btn) btn.style.display = 'inline-block'

      if (sel) sel.style.display = 'none'

      calendarContainer.style.display = 'none'

      info.textContent = ''

    }

    

    // Toujours initialiser le calendrier permanent

    initPermanentCalendar()

  } catch (e) {

    console.error('Error initializing Google section:', e)

    if (statusBadge) {
      statusBadge.textContent = ''
      statusBadge.className = ''
      statusBadge.title = ''
    }

    if (btn) btn.style.display = 'inline-block'

    if (sel) sel.style.display = 'none'

    calendarContainer.style.display = 'none'

    info.textContent = 'Erreur de connexion au serveur'

    info.style.color = '#c0392b'

  }

}



function loadGoogleCalendarEmbed() {

  const calendarEmbed = document.getElementById('googleCalendarEmbed')

  if (!calendarEmbed || !selectedCalendarId) return

  

  // Afficher l'état de chargement

  calendarEmbed.innerHTML = `

    <div class="calendar-loading">

      <i class="fas fa-spinner"></i>

      Chargement du calendrier Google...

    </div>

  `

  

  // Créer l'URL d'embed du calendrier Google

  const calendarUrl = `https://calendar.google.com/calendar/embed?src=${selectedCalendarId}&ctz=Europe%2FParis&mode=${currentCalendarView}&showTitle=0&showNav=1&showDate=1&showTabs=1&showCalendars=0&showTz=0`

  

  // Créer l'iframe

  const iframe = document.createElement('iframe')

  iframe.src = calendarUrl

  iframe.style.width = '100%'

  iframe.style.height = '400px'

  iframe.style.border = 'none'

  iframe.style.borderRadius = '8px'

  

  // Remplacer le contenu de chargement par l'iframe

  setTimeout(() => {

    calendarEmbed.innerHTML = ''

    calendarEmbed.appendChild(iframe)

    googleCalendarEmbedded = true

  }, 1000)

}



function refreshGoogleCalendar() {

  if (googleCalendarEmbedded) {

    loadGoogleCalendarEmbed()

  }

}



function toggleCalendarView() {

  const viewText = document.getElementById('calendarViewText')

  if (currentCalendarView === 'month') {

    currentCalendarView = 'week'

    viewText.textContent = 'Vue hebdomadaire'

  } else {

    currentCalendarView = 'month'

    viewText.textContent = 'Vue mensuelle'

  }

  loadGoogleCalendarEmbed()

}



// Gestionnaire pour le changement de calendrier

document.addEventListener('DOMContentLoaded', function() {

  const calendarSelect = document.getElementById('googleCalendarSelect')

  if (calendarSelect) {

    calendarSelect.addEventListener('change', function() {

      selectedCalendarId = this.value

      loadGoogleCalendarEmbed()

    })

  }

  

  // Initialiser le calendrier permanent immédiatement

  setTimeout(() => {

    initPermanentCalendar()

  }, 100)

  

  // Afficher les heures déjà sélectionnées après un délai plus long

  setTimeout(() => {

    showSelectedHours()

  }, 1000)

})



// Fonctions pour le calendrier permanent

async function initPermanentCalendar() {

  if (calendarInitialized) return

  

  // Rendre le calendrier d'abord

  renderCalendar()

  

  // Charger les données

  await Promise.all([

    loadBlockedSlots(),

    loadConfirmedSlots()

  ])

  

  // Re-rendre le calendrier APRÈS avoir chargé les données

  renderCalendar()

  updateCalendarDayStates()

  

  // Afficher les heures déjà sélectionnées

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

  setTimeout(() => showSelectedHours(), 1000)

  

  calendarInitialized = true

}



function renderCalendar() {

  const calendarDays = document.getElementById('calendarDays')

  const currentMonthYear = document.getElementById('currentMonthYear')

  

  if (!calendarDays || !currentMonthYear) return

  

  // Mettre à jour le titre

  const monthNames = [

    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',

    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'

  ]

  currentMonthYear.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`

  

  // Calculer le premier jour du mois et le nombre de jours

  const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)

  const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0)

  const startDate = new Date(firstDay)

  startDate.setDate(startDate.getDate() - (firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1))

  

  // Générer les jours

  calendarDays.innerHTML = ''

  

  for (let i = 0; i < 42; i++) {

    const dayDate = new Date(startDate)

    dayDate.setDate(startDate.getDate() + i)

    

    const dayElement = document.createElement('div')

    dayElement.className = 'calendar-day'

    dayElement.dataset.date = toLocalDateKey(dayDate)

    

    // Numéro du jour

    const dayNumber = document.createElement('div')

    dayNumber.className = 'calendar-day-number'

    dayNumber.textContent = dayDate.getDate()

    dayElement.appendChild(dayNumber)

    

    // Vérifier si c'est aujourd'hui

    const todayCheck = new Date()

    if (dayDate.toDateString() === todayCheck.toDateString()) {

      dayElement.classList.add('today')

    }

    

    // Vérifier si c'est un autre mois

    if (dayDate.getMonth() !== currentDate.getMonth()) {

      dayElement.classList.add('other-month')

    }

    

    // Marquer sélection selon les créneaux actuels

    const dateString = toLocalDateKey(dayDate)

    // L'état 'selected' sera recalculé par updateCalendarDayStates

    

    // Vérifier le niveau d'occupation du jour IMMÉDIATEMENT lors du rendu

    if (busyDays.has(dateString)) {

      // Jour complètement occupé (rouge)

      dayElement.classList.add('busy')

      

      // Ajouter un indicateur visuel pour les jours complètement occupés

      if (!dayElement.querySelector('.blocked-indicator')) {

        const blockedIndicator = document.createElement('div')

        blockedIndicator.className = 'blocked-indicator'

        blockedIndicator.innerHTML = '<i class="fas fa-ban"></i>'

        blockedIndicator.title = 'Tous les créneaux de cette date sont occupés'

        dayElement.appendChild(blockedIndicator)

      }

    } else if (partiallyOccupiedDays.has(dateString)) {

      // Jour partiellement occupé (jaune)

      dayElement.classList.add('partially-occupied')

      

      // Ajouter un indicateur visuel pour les jours partiellement occupés

      if (!dayElement.querySelector('.partial-indicator')) {

        const partialIndicator = document.createElement('div')

        partialIndicator.className = 'partial-indicator'

        partialIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i>'

        partialIndicator.title = 'Certains créneaux de cette date sont occupés'

        dayElement.appendChild(partialIndicator)

      }

    }

    

    // SUPPRIMÉ: La logique reserved-by-me qui causait la confusion des couleurs

    // Les jours avec des créneaux confirmés utiliseront maintenant les couleurs d'occupation

    

    // Ajouter les événements si connecté à Google

    if (googleCalendarEmbedded && selectedCalendarId) {

      // Ici on pourrait ajouter des événements Google Calendar

    }

    

    // Vérifier si c'est une date passée

    const todayForPast = new Date()

    todayForPast.setHours(0, 0, 0, 0) // Reset to start of day

    if (dayDate < todayForPast) {

      dayElement.classList.add('past-date')

    }

    

    // Gestionnaire de clic: ouvrir le sélecteur

    dayElement.addEventListener('click', async function() {

      // Seuls les jours passés et désactivés sont bloqués

      if (this.classList.contains('disabled') || this.classList.contains('past-date')) {

        // Afficher un message explicatif selon le type de blocage

        if (this.classList.contains('past-date')) {

          showNotification('Vous ne pouvez pas programmer d\'entretien dans le passé.', 'warning')

        }

        return

      }

      

      const dateString = this.dataset.date

      // Pré-remplir le modal avec les créneaux existants sur cette date (si présents)

      await showTimeSelector(dateString, this)

    })

    

    calendarDays.appendChild(dayElement)

  }

  

  // Afficher les heures déjà sélectionnées

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

}



function previousMonth() {

  currentDate.setMonth(currentDate.getMonth() - 1)

  renderCalendar()

  // Mettre à jour les états des jours après le re-rendu

  updateCalendarDayStates()

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

}



function nextMonth() {

  currentDate.setMonth(currentDate.getMonth() + 1)

  renderCalendar()

  // Mettre à jour les états des jours après le re-rendu

  updateCalendarDayStates()

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

}



function goToToday() {

  currentDate = new Date()

  renderCalendar()

  // Mettre à jour les états des jours après le re-rendu

  updateCalendarDayStates()

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

}



function updateSlotsFromSelectedDays() {

  if (selectedDays.size === 0) return

  

  // Convertir les jours sélectionnés en créneaux

  const selectedDates = Array.from(selectedDays).sort()

  

  // Effacer les créneaux existants

  for (let i = 1; i <= 4; i++) {

    const startInput = document.getElementById(`slot${i}_start`)

    const endInput = document.getElementById(`slot${i}_end`)

    if (startInput) startInput.value = ''

    if (endInput) endInput.value = ''

  }

  

  // Remplir les créneaux avec les jours sélectionnés

  // Permettre plusieurs créneaux le même jour avec des horaires différents

  selectedDates.forEach((dateString, index) => {

    if (index >= 4) return // Max 4 créneaux

    

    // Fix date offset: parse date components to avoid timezone issues

    const [year, month, day] = dateString.split('-').map(Number)

    const startTime = new Date(year, month - 1, day)

    const endTime = new Date(year, month - 1, day)

    

    // Horaires par défaut différents pour éviter les conflits

    const defaultHours = [

      { start: 9, end: 10 },   // 9h-10h

      { start: 11, end: 12 },  // 11h-12h

      { start: 14, end: 15 },  // 14h-15h

      { start: 16, end: 17 }   // 16h-17h

    ]

    

    const hourIndex = index % defaultHours.length

    startTime.setHours(defaultHours[hourIndex].start, 0, 0, 0)

    endTime.setHours(defaultHours[hourIndex].end, 0, 0, 0)

    

    const startInput = document.getElementById(`slot${index + 1}_start`)

    const endInput = document.getElementById(`slot${index + 1}_end`)

    

    if (startInput && endInput) {

      // Use local datetime string for datetime-local inputs (avoid TZ shift)

      startInput.value = toLocalDatetimeValue(startTime)

      endInput.value = toLocalDatetimeValue(endTime)

    }

  })

  

  // Vérifier les conflits Google et les conflits d'horaires

  checkGoogleConflicts()

  validateSlotTimes()

}



// Fonction pour forcer l'application des styles

function forceApplyCalendarStyles() {

  const allDays = document.querySelectorAll('.calendar-day')

  

  allDays.forEach(day => {

    const dateString = day.dataset.date

    

    // Forcer l'application des styles selon les données

    if (busyDays.has(dateString)) {

      day.classList.add('busy')

      day.classList.remove('partially-occupied')

      

      // Forcer l'application des styles CSS avec !important

      day.style.setProperty('background', '#fef2f2', 'important')

      day.style.setProperty('color', '#dc2626', 'important')

      day.style.setProperty('border-color', '#dc2626', 'important')

      day.style.setProperty('border-width', '2px', 'important')

      day.style.setProperty('font-weight', '600', 'important')

      

      // Ajouter l'indicateur si manquant

      if (!day.querySelector('.blocked-indicator')) {

        const indicator = document.createElement('div')

        indicator.className = 'blocked-indicator'

        indicator.innerHTML = '<i class="fas fa-ban"></i>'

        indicator.title = 'Tous les créneaux de cette date sont occupés'

        day.appendChild(indicator)

      }

    } else if (partiallyOccupiedDays.has(dateString)) {

      day.classList.add('partially-occupied')

      day.classList.remove('busy')

      

      // Forcer l'application des styles CSS avec !important

      day.style.setProperty('background', '#fef3c7', 'important')

      day.style.setProperty('color', '#d97706', 'important')

      day.style.setProperty('border-color', '#f59e0b', 'important')

      day.style.setProperty('border-width', '2px', 'important')

      day.style.setProperty('font-weight', '600', 'important')

      

      // Ajouter l'indicateur si manquant

      if (!day.querySelector('.partial-indicator')) {

        const indicator = document.createElement('div')

        indicator.className = 'partial-indicator'

        indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i>'

        indicator.title = 'Certains créneaux de cette date sont occupés'

        day.appendChild(indicator)

      }

    }

  })

}



// Fonction pour afficher les heures déjà sélectionnées en jaune

function showSelectedHours() {

  // Attendre que le DOM soit prêt

  setTimeout(() => {

    const allDays = document.querySelectorAll('.calendar-day')

    

    allDays.forEach(day => {

      const dateString = day.dataset.date

      

      // Vérifier si ce jour a des créneaux confirmés

      const hasConfirmedSlots = confirmedSlots && confirmedSlots.some(slot => {

        const slotDate = new Date(slot.start_time)

        const slotDateKey = toLocalDateKey(slotDate)

        return slotDateKey === dateString

      })

      

      if (hasConfirmedSlots) {

        // Afficher les heures confirmées en jaune

        day.style.background = '#fef3c7'

        day.style.color = '#d97706'

        day.style.borderColor = '#f59e0b'

        day.style.borderWidth = '2px'

        day.style.fontWeight = '600'

        

        // Ajouter un indicateur pour montrer qu'il y a des heures sélectionnées

        if (!day.querySelector('.selected-hours-indicator')) {

          const indicator = document.createElement('div')

          indicator.className = 'selected-hours-indicator'

          indicator.innerHTML = '<i class="fas fa-clock"></i>'

          indicator.title = 'Heures déjà sélectionnées sur cette date'

          day.appendChild(indicator)

        }

      } else {

        // Réinitialiser les styles si pas de créneaux confirmés

        day.style.background = ''

        day.style.color = ''

        day.style.borderColor = ''

        day.style.borderWidth = ''

        day.style.fontWeight = ''

        

        // Supprimer l'indicateur

        const existingIndicator = day.querySelector('.selected-hours-indicator')

        if (existingIndicator) {

          existingIndicator.remove()

        }

      }

    })

  }, 100)

}



// Fonction pour forcer l'application des styles avec retry

function forceApplyCalendarStylesWithRetry() {

  forceApplyCalendarStyles()

  

  // Retry après 200ms si les données ne sont pas encore chargées

  setTimeout(() => {

    if (busyDays.size > 0 || partiallyOccupiedDays.size > 0) {

      forceApplyCalendarStyles()

    }

  }, 200)

  

  // Retry après 500ms pour s'assurer que tout est appliqué

  setTimeout(() => {

    forceApplyCalendarStyles()

  }, 500)

  

  // Retry après 1000ms pour les cas les plus lents

  setTimeout(() => {

    forceApplyCalendarStyles()

  }, 1000)

  

  // Retry après 2000ms pour les cas très lents

  setTimeout(() => {

    forceApplyCalendarStyles()

  }, 2000)

}



// Système de surveillance pour détecter les changements de données

let lastBusyDaysSize = 0

let lastPartiallyOccupiedDaysSize = 0



function watchForDataChanges() {

  const currentBusySize = busyDays.size

  const currentPartiallySize = partiallyOccupiedDays.size

  

  if (currentBusySize !== lastBusyDaysSize || currentPartiallySize !== lastPartiallyOccupiedDaysSize) {

    // Les données ont changé, forcer l'application des styles

    forceApplyCalendarStyles()

    lastBusyDaysSize = currentBusySize

    lastPartiallyOccupiedDaysSize = currentPartiallySize

  }

}



// Démarrer la surveillance

setInterval(watchForDataChanges, 100)



function updateCalendarDayStates() {

  const allDays = document.querySelectorAll('.calendar-day')

  // Recalcule les jours marqués comme sélectionnés à partir des 4 inputs de créneaux

  const selectedBySlots = new Set()

  const confirmedBySlots = new Set()

  

  // Collecter les créneaux actuels (non confirmés)

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    if (s && s.value) {

      const d = new Date(s.value)

      const k = toLocalDateKey(d)

      selectedBySlots.add(k)

    }

  }

  

  // Collecter les créneaux confirmés depuis la base de données

  if (confirmedSlots && confirmedSlots.length > 0) {

    confirmedSlots.forEach(slot => {

      if (slot.start_time) {

        const d = new Date(slot.start_time)

        const k = toLocalDateKey(d)

        confirmedBySlots.add(k)

      }

    })

  }

  

  allDays.forEach(day => {

    const dateString = day.dataset.date

    

    // Supprimer seulement les classes de statut de sélection, pas les classes busy/reserved-by-me

    day.classList.remove('selected', 'confirmed', 'disabled')

    

    // Vérifier le niveau d'occupation du jour

    const shouldBeBusy = busyDays.has(dateString)

    const shouldBePartiallyOccupied = partiallyOccupiedDays.has(dateString)

    

    if (confirmedBySlots.has(dateString)) {

      // Jour avec créneaux confirmés - utiliser les couleurs d'occupation au lieu de 'confirmed'

      day.classList.remove('confirmed', 'reserved-by-me')

      day.style.cursor = 'pointer'

      day.style.opacity = '1'

      

      // Appliquer les couleurs d'occupation selon le niveau

      if (shouldBeBusy) {

        day.classList.add('busy')

        day.classList.remove('partially-occupied')

      } else if (shouldBePartiallyOccupied) {

        day.classList.add('partially-occupied')

        day.classList.remove('busy')

      }

      

      // GARDER le gestionnaire de clic

    } else if (selectedBySlots.has(dateString)) {

      // Jour avec créneaux non confirmés

      day.classList.add('selected')

      day.style.cursor = 'pointer'

      day.style.opacity = '1'

    } else {

      // Jour normal - restaurer l'état d'occupation si nécessaire

      day.style.cursor = 'pointer'

      day.style.opacity = '1'

      

      if (shouldBeBusy) {

        // Jour complètement occupé (rouge)

        day.classList.add('busy')

        day.classList.remove('partially-occupied')

        // S'assurer que l'indicateur bloqué est présent

        if (!day.querySelector('.blocked-indicator')) {

          const blockedIndicator = document.createElement('div')

          blockedIndicator.className = 'blocked-indicator'

          blockedIndicator.innerHTML = '<i class="fas fa-ban"></i>'

          blockedIndicator.title = 'Tous les créneaux de cette date sont occupés'

          day.appendChild(blockedIndicator)

        }

        // Supprimer l'indicateur partiel s'il existe

        const existingPartialIndicator = day.querySelector('.partial-indicator')

        if (existingPartialIndicator) {

          existingPartialIndicator.remove()

        }

      } else if (shouldBePartiallyOccupied) {

        // Jour partiellement occupé (jaune)

        day.classList.add('partially-occupied')

        day.classList.remove('busy')

        // S'assurer que l'indicateur partiel est présent

        if (!day.querySelector('.partial-indicator')) {

          const partialIndicator = document.createElement('div')

          partialIndicator.className = 'partial-indicator'

          partialIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i>'

          partialIndicator.title = 'Certains créneaux de cette date sont occupés'

          day.appendChild(partialIndicator)

        }

        // Supprimer l'indicateur bloqué s'il existe

        const existingBlockedIndicator = day.querySelector('.blocked-indicator')

        if (existingBlockedIndicator) {

          existingBlockedIndicator.remove()

        }

      } else {

        // Jour libre - supprimer tous les indicateurs

        day.classList.remove('busy', 'partially-occupied')

        const existingBlockedIndicator = day.querySelector('.blocked-indicator')

        const existingPartialIndicator = day.querySelector('.partial-indicator')

        if (existingBlockedIndicator) existingBlockedIndicator.remove()

        if (existingPartialIndicator) existingPartialIndicator.remove()

      }

    }

  })

  

  // Afficher les heures déjà sélectionnées

  showSelectedHours()

  setTimeout(() => showSelectedHours(), 200)

  setTimeout(() => showSelectedHours(), 500)

}



function validateSlotTimes() {

  const inputs = []

  

  // Collecter tous les créneaux saisis

  for (let i = 1; i <= 4; i++) {

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s && e && s.value && e.value) {

      const start = new Date(s.value)

      const end = new Date(e.value)

      if (end > start) {

        inputs.push({ start, end, slotNumber: i })

      }

    }

  }

  

  // SUPPRIMÉ: Vérification des conflits d'horaires pour permettre 4 créneaux le même jour

  // Permettre plusieurs créneaux le même jour sans conflit

  

  // Réinitialiser tous les statuts

  for (let i = 1; i <= 4; i++) {

    updateSlotStatus(i, 'free')

  }

  

  // Marquer tous les créneaux comme valides (pas de conflits)

  for (let i = 0; i < inputs.length; i++) {

    updateSlotStatus(inputs[i].slotNumber, 'free')

  }

}



async function showTimeSelector(dateString, dayElement) {

  const [y, m, d] = dateString.split('-').map(Number)

  const date = new Date(y, m - 1, d)

  const formattedDate = date.toLocaleDateString('fr-FR', { 

    weekday: 'long', 

    year: 'numeric', 

    month: 'long', 

    day: 'numeric' 

  })

  

  // Créer le modal de sélection d'heure

  const modal = document.createElement('div')

  modal.className = 'time-selector-modal'

  modal.innerHTML = `

    <div class="time-selector-overlay">

      <div class="time-selector-content">

        <div class="time-selector-header">

          <h3>Choisir jusqu'à 4 créneaux pour le ${formattedDate}</h3>

          <button class="time-selector-close" aria-label="Fermer">&times;</button>

        </div>

        <div class="time-selector-body">

          <div class="time-info">Sélectionnez des heures (max 4). Les choix seront mis en évidence et remplis dans les créneaux.</div>

          ${dayElement && dayElement.classList.contains('busy') ? '<div class="busy-day-warning">⚠️ Cette date a atteint sa limite de 4 créneaux. Vous ne pouvez pas ajouter de nouveaux créneaux.</div>' : ''}

          <div class="time-inputs">

            <div class="time-input-group">

              <label>Heure de début :</label>

              <input type="time" id="timeStart" value="09:00" class="time-input">

            </div>

            <div class="time-input-group">

              <label>Heure de fin :</label>

              <input type="time" id="timeEnd" value="10:00" class="time-input">

            </div>

            <button class="btn-add-time" type="button">Ajouter</button>

          </div>

          <div class="time-presets">

            <h4>Créneaux prédéfinis :</h4>

            <div class="preset-buttons">

              <button class="preset-btn" data-start="09:00" data-end="10:00">9h - 10h</button>

              <button class="preset-btn" data-start="10:00" data-end="11:00">10h - 11h</button>

              <button class="preset-btn" data-start="11:00" data-end="12:00">11h - 12h</button>

              <button class="preset-btn" data-start="14:00" data-end="15:00">14h - 15h</button>

              <button class="preset-btn" data-start="15:00" data-end="16:00">15h - 16h</button>

              <button class="preset-btn" data-start="16:00" data-end="17:00">16h - 17h</button>

            </div>

          </div>

          <div class="selected-times">

            <h4>Créneaux sélectionnés (<span class="selected-count">0</span>/4) :</h4>

            <div class="selected-times-list"></div>

          </div>

        </div>

        <div class="time-selector-actions">

          <button class="btn-cancel-time">Annuler</button>

          <button class="btn-confirm-time">Confirmer</button>

        </div>

      </div>

    </div>

  `

  

  document.body.appendChild(modal)

  

  // Marquer les créneaux occupés dans le modal

  // S'assurer que les données sont chargées

  if (!blockedSlots || blockedSlots.length === 0) {

    await loadBlockedSlots()

  }

  if (!confirmedSlots || confirmedSlots.length === 0) {

    await loadConfirmedSlots()

  }

  

  markOccupiedTimeSlots(modal, dateString)

  

  // Gestionnaires d'événements

  const closeBtn = modal.querySelector('.time-selector-close')

  const cancelBtn = modal.querySelector('.btn-cancel-time')

  const confirmBtn = modal.querySelector('.btn-confirm-time')

  const presetBtns = modal.querySelectorAll('.preset-btn')

  const startInput = modal.querySelector('#timeStart')

  const endInput = modal.querySelector('#timeEnd')

  const addBtn = modal.querySelector('.btn-add-time')

  const selectedList = modal.querySelector('.selected-times-list')

  const selectedCountEl = modal.querySelector('.selected-count')

  

  // Détecter si l'utilisateur a réellement ajouté/modifié un créneau

  let userMadeSelection = false

  

  // Compter les créneaux déjà remplis globalement (utilise helper global si dispo)

  const getExistingFilledCount = () => getFilledSlotsCount ? getFilledSlotsCount() : (() => {

    let c = 0

    for (let i = 1; i <= 4; i++) {

      const s = document.getElementById(`slot${i}_start`)

      const e = document.getElementById(`slot${i}_end`)

      if (s && e && s.value && e.value) c++

    }

    return c

  })()



  // État local des créneaux sélectionnés (nouveaux) dans ce modal

  const selectedRanges = []

  

  const getRemainingSlotCapacity = () => {

    let free = 0

    for (let i = 1; i <= 4; i++) {

      const s = document.getElementById(`slot${i}_start`)

      const e = document.getElementById(`slot${i}_end`)

      if (s && e && (!s.value || !e.value)) free++

    }

    return free

  }

  

  const updateSelectedUI = async () => {

    // Compter TOUS les créneaux existants pour ce candidat (toutes dates confondues)

    let existingSlotsForCandidate = 0

    if (currentCandidateId) {

      for (let i = 1; i <= 4; i++) {

        const s = document.getElementById(`slot${i}_start`)

        const e = document.getElementById(`slot${i}_end`)

        if (s && e && s.value && e.value) {

          existingSlotsForCandidate++

        }

      }

    }

    

    const total = Math.min(4, existingSlotsForCandidate + selectedRanges.length)

    selectedCountEl.textContent = String(total)

    selectedList.innerHTML = ''

    // Show existing slots for this date as chips

    for (let i = 1; i <= 4; i++) {

      const s = document.getElementById(`slot${i}_start`)

      const e = document.getElementById(`slot${i}_end`)

      if (s && e && s.value && e.value) {

        const sd = new Date(s.value)

        const ed = new Date(e.value)

        const k = sd.toISOString().split('T')[0]

        if (k === dateString) {

          const chip = document.createElement('div')

          chip.className = 'selected-time-chip existing'

          const timeStr = sd.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) + ' - ' + ed.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

          chip.innerHTML = `<span>${timeStr}</span><button class="remove-chip" data-existing="true" data-slot="${i}" aria-label="Supprimer">&times;</button>`

          selectedList.appendChild(chip)

        }

      }

    }

    selectedRanges.forEach((r, idx) => {

      const chip = document.createElement('div')

      chip.className = 'selected-time-chip'

      const timeStr = r.start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) + ' - ' + r.end.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

      chip.innerHTML = `<span>${timeStr}</span><button class="remove-chip" data-index="${idx}" aria-label="Supprimer">&times;</button>`

      selectedList.appendChild(chip)

    })

    

    // Vérifier la limite de 4 créneaux par candidat (utiliser le comptage déjà fait)

    let isCandidateLimitReached = false

    if (currentCandidateId) {

      // Vérifier si on peut encore ajouter des créneaux (limite stricte à 4)

      isCandidateLimitReached = existingSlotsForCandidate >= 4

    }

    

    // Vérifier si le compteur total atteint 4 (créneaux existants + sélectionnés)

    let isTotalLimitReached = false

    if (currentCandidateId) {

      const totalSlots = existingSlotsForCandidate + selectedRanges.length

      isTotalLimitReached = totalSlots >= 4

    }

    

    // Vérifier la limite de 4 créneaux par date

    let isDateLimitReached = false

    try {

      const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

      const slotsRes = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

      const slotsData = await slotsRes.json()

      

      const existingSlotsOnDate = slotsData.filter(slot => {

        const slotDate = new Date(slot.start_time)

        const slotDateString = toLocalDateKey(slotDate)

        return slotDateString === dateString

      }).length

      

      isDateLimitReached = existingSlotsOnDate >= 4

    } catch (error) {

      console.error('Erreur lors de la vérification des créneaux sur la date:', error)

    }

    

    // toggle preset highlight according to selection

    presetBtns.forEach(btn => {

      const s = btn.dataset.start

      const e = btn.dataset.end

      const exists = selectedRanges.some(r => r.meta === `${s}-${e}`)

      btn.classList.toggle('selected', !!exists)

      // Désactiver les boutons si la limite de candidat, de date ou totale est atteinte

      btn.disabled = isCandidateLimitReached || isDateLimitReached || isTotalLimitReached

    })

    

    // Mettre à jour l'état des boutons après chaque modification

    markOccupiedTimeSlots(modal, dateString)

  }

  

  const tryAddRange = async (startTimeStr, endTimeStr, metaKey = null) => {

    if (!startTimeStr || !endTimeStr || endTimeStr <= startTimeStr) return

    

    // Vérifier la limite de 4 créneaux par candidat (utiliser les créneaux globaux)

    if (currentCandidateId) {

      let existingSlotsForCandidate = 0

      for (let i = 1; i <= 4; i++) {

        const s = document.getElementById(`slot${i}_start`)

        const e = document.getElementById(`slot${i}_end`)

        if (s && e && s.value && e.value) {

          existingSlotsForCandidate++

        }

      }

      // Vérifier si on peut encore ajouter des créneaux (limite stricte à 4)

      if (existingSlotsForCandidate >= 4) {

        showNotification('Ce candidat a déjà 4 créneaux. Supprimez un créneau pour en ajouter un nouveau.', 'warning')

        return

      }

    }

    

    // Vérifier si le compteur total atteint 4 (créneaux existants + sélectionnés)

    let totalSlots = 0

    if (currentCandidateId) {

      let existingSlotsForCandidate = 0

      for (let i = 1; i <= 4; i++) {

        const s = document.getElementById(`slot${i}_start`)

        const e = document.getElementById(`slot${i}_end`)

        if (s && e && s.value && e.value) {

          existingSlotsForCandidate++

        }

      }

      totalSlots = existingSlotsForCandidate + selectedRanges.length

    }

    

    if (totalSlots >= 4) {

      showNotification('Limite de 4 créneaux atteinte. Supprimez un créneau pour en ajouter un nouveau.', 'warning')

      return

    }

    

    // Vérifier la limite de 4 créneaux par date (tous candidats confondus)

    try {

      const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

      const slotsRes = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

      const slotsData = await slotsRes.json()

      

      // Compter les créneaux existants sur cette date

      const existingSlotsOnDate = slotsData.filter(slot => {

        const slotDate = new Date(slot.start_time)

        const slotDateString = toLocalDateKey(slotDate)

        return slotDateString === dateString

      }).length

      

      // Vérifier si on peut encore ajouter des créneaux

      if (existingSlotsOnDate >= 4) {

        showNotification('Cette date a atteint sa limite de 4 créneaux. Choisissez une autre date.', 'warning')

        return

      }

      

      // Vérifier si l'ajout de ce créneau dépasserait la limite

      if (existingSlotsOnDate + selectedRanges.length >= 4) {

        showNotification('Cette date a atteint sa limite de 4 créneaux. Choisissez une autre date.', 'warning')

        return

      }

    } catch (error) {

      console.error('Erreur lors de la vérification des créneaux sur la date:', error)

      // Continuer même en cas d'erreur pour ne pas bloquer la sélection

    }

    

    // Fix date offset bug: create dates in local timezone to avoid UTC conversion

    const [year, month, day] = dateString.split('-').map(Number)

    const [startHour, startMinute] = startTimeStr.split(':').map(Number)

    const [endHour, endMinute] = endTimeStr.split(':').map(Number)

    

    const startDateTime = new Date(year, month - 1, day, startHour, startMinute, 0)

    const endDateTime = new Date(year, month - 1, day, endHour, endMinute, 0)

    

    // Vérifier les conflits avec les créneaux bloqués

    const hasConflictWithBlocked = blockedSlots.some(blockedSlot => {

      const blockedStart = new Date(blockedSlot.start_time)

      const blockedEnd = new Date(blockedSlot.end_time)

      

      // Vérifier si les créneaux se chevauchent

      return startDateTime < blockedEnd && endDateTime > blockedStart

    })

    

    if (hasConflictWithBlocked) {

      showNotification('Ce créneau est déjà réservé par un autre candidat', 'error')

      return

    }

    

    // SUPPRIMÉ: Vérification des conflits avec les créneaux déjà réservés par le même agent HR

    // Permettre d'ajouter plusieurs créneaux le même jour

    // éviter doublons exacts

    if (selectedRanges.some(r => r.start.getTime() === startDateTime.getTime() && r.end.getTime() === endDateTime.getTime())) return

    // SUPPRIMÉ: empêcher chevauchement le même jour pour permettre 4 créneaux le même jour

    selectedRanges.push({ start: startDateTime, end: endDateTime, meta: metaKey || `${startTimeStr}-${endTimeStr}` })

    await updateSelectedUI()

  }

  

  const removeByIndex = async (idx) => {

    if (idx < 0 || idx >= selectedRanges.length) return

    selectedRanges.splice(idx, 1)

    await updateSelectedUI()

  }

  

  // Fermer le modal

  const closeModal = () => {

    document.body.removeChild(modal)

  }

  

  closeBtn.addEventListener('click', closeModal)

  cancelBtn.addEventListener('click', closeModal)

  modal.querySelector('.time-selector-overlay').addEventListener('click', (e) => {

    if (e.target === modal.querySelector('.time-selector-overlay')) {

      closeModal()

    }

  })

  

  // Gestion des créneaux prédéfinis (toggle + highlight)

  presetBtns.forEach(btn => {

    btn.addEventListener('click', async () => {

      // Empêcher la sélection si le bouton est occupé ou réservé

      if (btn.classList.contains('occupied') || btn.classList.contains('reserved-by-me')) {

        const message = btn.classList.contains('occupied') 

          ? 'Ce créneau est réservé par un autre candidat' 

          : 'Ce créneau est réservé par vous'

        showNotification(message, 'warning')

        return

      }

      

      const s = btn.dataset.start

      const e = btn.dataset.end

      const key = `${s}-${e}`

      const idx = selectedRanges.findIndex(r => r.meta === key)

      if (idx >= 0) {

        selectedRanges.splice(idx, 1)

        await updateSelectedUI()

      } else {

        await tryAddRange(s, e, key)

      }

      userMadeSelection = true

    })

  })

  

  // Ajouter à partir des inputs manuels

  addBtn.addEventListener('click', async () => {

    await tryAddRange(startInput.value, endInput.value)

    userMadeSelection = true

  })

  ;['change','input'].forEach(evt => {

    startInput.addEventListener(evt, () => { userMadeSelection = true })

    endInput.addEventListener(evt, () => { userMadeSelection = true })

  })

  

  // Suppression d'un créneau dans la liste sélectionnée

  selectedList.addEventListener('click', async (e) => {

    const target = e.target

    if (target && target.classList.contains('remove-chip')) {

      const isExisting = target.getAttribute('data-existing') === 'true'

      if (isExisting) {

        const slotIdx = Number(target.getAttribute('data-slot'))

        if (!Number.isNaN(slotIdx)) {

          const s = document.getElementById(`slot${slotIdx}_start`)

          const e = document.getElementById(`slot${slotIdx}_end`)

          if (s) s.value = ''

          if (e) e.value = ''

          updateSlotStatus(slotIdx, '')

          updateSlotStatuses()

          await updateSelectedUI()

        }

      } else {

        const idx = Number(target.getAttribute('data-index'))

        await removeByIndex(idx)

      }

    }

  })

  

  // Confirmer la sélection

  confirmBtn.addEventListener('click', async () => {

    // Vérifier la limite de 4 créneaux par candidat (utiliser les créneaux globaux)

    if (currentCandidateId) {

      let existingSlotsForCandidate = 0

      for (let i = 1; i <= 4; i++) {

        const s = document.getElementById(`slot${i}_start`)

        const e = document.getElementById(`slot${i}_end`)

        if (s && e && s.value && e.value) {

          existingSlotsForCandidate++

        }

      }

      // Vérifier si on peut encore ajouter des créneaux (limite stricte à 4)

      if (existingSlotsForCandidate >= 4) {

        showNotification('Ce candidat a déjà 4 créneaux. Supprimez un créneau pour en ajouter un nouveau.', 'warning')

        return

      }

    }

    

    if (getFilledSlotsCount() >= 4) {

      showNotification('Tous les 4 créneaux sont déjà remplis. Supprimez un créneau pour ajouter un nouveau.', 'warning')

      return

    }

    // N'ajoute rien automatiquement si l'utilisateur n'a rien sélectionné/modifié

    if (!userMadeSelection && selectedRanges.length === 0) return

    // Si l'utilisateur a saisi manuellement mais n'a pas cliqué "Ajouter", tenter une seule fois

    if (userMadeSelection && selectedRanges.length === 0 && startInput.value && endInput.value) {

      await tryAddRange(startInput.value, endInput.value)

    }

    if (selectedRanges.length === 0) return

    

    // Remplir uniquement les slots vides sans effacer les existants

    const toApply = selectedRanges.slice(0, 4)

    toApply.forEach(r => addTimeSlotToCalendar(dateString, r.start, r.end))

    // Rafraîchir l'état visuel du calendrier d'après les nouveaux slots

    await loadBlockedSlots()

    updateCalendarDayStates()

    closeModal()

  })



  // Ne pas dupliquer les créneaux existants dans le panier des "nouveaux".

  // On affiche seulement ce qui est ajouté pendant cette session; les existants restent visibles via le compteur global et le calendrier.

  await updateSelectedUI()

}



function addTimeSlotToCalendar(dateString, startDateTime, endDateTime) {

  // Trouver le premier slot vide

  let emptySlotIndex = -1

  for (let i = 1; i <= 4; i++) {

    const startInput = document.getElementById(`slot${i}_start`)

    const endInput = document.getElementById(`slot${i}_end`)

    if (startInput && endInput && (!startInput.value || !endInput.value)) {

      emptySlotIndex = i

      break

    }

  }

  

  if (emptySlotIndex === -1) {

    // Tous les slots sont remplis: ne pas remplacer; informer l'utilisateur

    showNotification('Maximum 4 créneaux atteints. Supprimez un créneau pour en ajouter un nouveau.', 'warning')

    return

  }

  

  // Remplir le slot

  const startInput = document.getElementById(`slot${emptySlotIndex}_start`)

  const endInput = document.getElementById(`slot${emptySlotIndex}_end`)

  

  if (startInput && endInput) {

    startInput.value = toLocalDatetimeValue(startDateTime)

    endInput.value = toLocalDatetimeValue(endDateTime)

    

    // Vérifier les conflits

    validateSlotTimes()

    checkGoogleConflicts()

    

    // Afficher un message de confirmation

    const timeStr = startDateTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) + 

                   ' - ' + endDateTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

    showNotification(`Créneau ajouté : ${timeStr}`, 'success')

    // Mettre à jour l'état du calendrier et le compteur global

    updateCalendarDayStates()

  }

}



// Ajouter des boutons pour effacer les créneaux (si non présents)

document.addEventListener('DOMContentLoaded', () => {

  for (let i = 1; i <= 4; i++) {

    const card = document.querySelector(`.slot-card[data-slot="${i}"]`)

    if (!card) continue

    let clearBtn = card.querySelector('.slot-clear-btn')

    if (!clearBtn) {

      clearBtn = document.createElement('button')

      clearBtn.type = 'button'

      clearBtn.className = 'slot-clear-btn'

      clearBtn.innerHTML = '<i class="fas fa-times"></i>'

      clearBtn.style.marginTop = '10px'

      clearBtn.addEventListener('click', () => {

        const s = document.getElementById(`slot${i}_start`)

        const e = document.getElementById(`slot${i}_end`)

        const st = document.getElementById(`slot${i}_status`)

        if (s) s.value = ''

        if (e) e.value = ''

        // Laisser updateSlotStatuses remettre le statut par défaut

        updateSlotStatuses()

        updateCalendarDayStates()

        checkGoogleConflicts()

        

        // Si le modal de sélection est ouvert, rafraîchir le compteur et l'état des presets

        const modal = document.querySelector('.time-selector-modal')

        if (modal) {

          const countEl = modal.querySelector('.selected-count')

          const chips = modal.querySelectorAll('.selected-times-list .selected-time-chip').length

          const filled = getFilledSlotsCount()

          if (countEl) {

            countEl.textContent = String(Math.min(4, filled + chips))

          }

          const presetBtns = modal.querySelectorAll('.preset-btn')

          const remaining = Math.max(0, 4 - filled)

          presetBtns.forEach(btn => {

            const isSelected = btn.classList.contains('selected')

            btn.disabled = chips >= remaining && !isSelected

          })

        }

      })

      card.appendChild(clearBtn)

    }

  }

})



function connectGoogle() {

  // Vérifier que l'utilisateur est connecté

  const accessToken = localStorage.getItem('hr_access_token')

  if (!accessToken) {

    console.error('No HR access token found for Google connection')

    alert('Vous devez être connecté pour utiliser Google Calendar. Veuillez vous reconnecter.')

    window.location.href = '/enterprise-login'

    return

  }

  

  // Redirection simple vers l'endpoint OAuth

  window.location.href = '/api/hr/google/oauth/start'

}



function bindSlotInputsForGoogle() {

  const ids = ['slot1_start','slot1_end','slot2_start','slot2_end','slot3_start','slot3_end','slot4_start','slot4_end','googleCalendarSelect']

  ids.forEach(id => {

    const el = document.getElementById(id)

    if (el) {

      el.addEventListener('change', debounce(checkGoogleConflicts, 400))

      // Ajouter la validation des conflits d'horaires

      if (id.includes('slot') && (id.includes('_start') || id.includes('_end'))) {

        el.addEventListener('change', debounce(() => { validateSlotTimes(); updateCalendarDayStates() }, 300))

      }

    }

  })

}



async function checkGoogleConflicts() {

  const sel = document.getElementById('googleCalendarSelect')

  const info = document.getElementById('googleConflictInfo')

  if (!sel || sel.style.display === 'none') { 

    if (info) info.textContent = ''; 

    updateSlotStatuses()

    return 

  }

  

  const calId = sel.value

  if (!calId) { 

    if (info) info.textContent = ''; 

    updateSlotStatuses()

    return 

  }

  

  const ranges = []

  for (let i=1;i<=4;i++){

    const s = document.getElementById(`slot${i}_start`)

    const e = document.getElementById(`slot${i}_end`)

    if (s && e && s.value && e.value) {

      ranges.push({start:s.value, end:e.value, slot:i})

    }

  }

  

  if (!ranges.length) { 

    if (info) info.textContent=''; 

    updateSlotStatuses()

    return 

  }

  

  const min = new Date(Math.min(...ranges.map(r=>new Date(r.start).getTime()))).toISOString()

  const max = new Date(Math.max(...ranges.map(r=>new Date(r.end).getTime()))).toISOString()

  

  try {

    // Récupérer le token JWT depuis localStorage

    const accessToken = localStorage.getItem('hr_access_token')

    if (!accessToken) {

      if (info) {

        info.textContent = 'Token d\'authentification manquant'

        info.style.color = '#c0392b'

      }

      updateSlotStatuses()

      return

    }

    

    const busyResp = await fetch(`/api/hr/google/busy?calendarId=${encodeURIComponent(calId)}&timeMin=${encodeURIComponent(min)}&timeMax=${encodeURIComponent(max)}`, {

      headers: {

        'Authorization': `Bearer ${accessToken}`

      }

    })

    

    if (!busyResp.ok) {

      if (info) {

        info.textContent = 'Erreur lors de la vérification des conflits'

        info.style.color = '#c0392b'

      }

      updateSlotStatuses()

      return

    }

    

    const busyData = await busyResp.json()

    const busy = busyData.busy || []

    

    // Vérifier les conflits pour chaque créneau

    let hasConflict = false

    ranges.forEach(range => {

      const slotConflict = busy.some(b => new Date(range.start) < new Date(b.end) && new Date(range.end) > new Date(b.start))

      if (slotConflict) {

        hasConflict = true

        updateSlotStatus(range.slot, 'conflict')

      } else {

        updateSlotStatus(range.slot, 'free')

      }

    })

    

    if (info) {

      if (hasConflict) {

        info.textContent = 'Conflit détecté avec Google Calendar pour au moins un créneau.'

        info.style.color = '#c0392b'

      } else {

        info.textContent = 'Aucun conflit détecté sur Google Calendar.'

        info.style.color = '#2e7d32'

      }

    }

  } catch (e) {

    console.error('Error checking Google conflicts:', e)

    if (info) {

      info.textContent = 'Erreur lors de la vérification des conflits'

      info.style.color = '#c0392b'

    }

    updateSlotStatuses()

  }

}



function updateSlotStatus(slotNumber, status) {

  const statusElement = document.getElementById(`slot${slotNumber}_status`)

  if (!statusElement) return

  

  // Supprimer toutes les classes de statut

  statusElement.classList.remove('free', 'busy', 'conflict')

  

  // Ajouter la nouvelle classe de statut seulement si elle n'est pas vide

  if (status && status.trim() !== '') {

    statusElement.classList.add(status)

  }

  

  // Mettre à jour l'icône et le texte

  if (status && status.trim() !== '') {

    switch (status) {

      case 'free':

        statusElement.innerHTML = `<i class="fas fa-check-circle"></i> Créneau ${slotNumber} - Libre`

        break

      case 'busy':

        statusElement.innerHTML = `<i class="fas fa-times-circle"></i> Créneau ${slotNumber} - Occupé`

        break

      case 'conflict':

        statusElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Créneau ${slotNumber} - Conflit`

        break

      default:

        statusElement.innerHTML = `<i class="fas fa-circle"></i> Créneau ${slotNumber}`

    }

  } else {

    // Statut vide ou null - remettre l'état par défaut

    statusElement.innerHTML = `<i class="fas fa-circle"></i> Créneau ${slotNumber}`

  }

}



function updateSlotStatuses() {

  // D'abord recalculer les conflits/validités en fonction des valeurs actuelles

  validateSlotTimes()

  for (let i = 1; i <= 4; i++) {

    const startInput = document.getElementById(`slot${i}_start`)

    const endInput = document.getElementById(`slot${i}_end`)

    

    if (startInput && endInput && startInput.value && endInput.value) {

      // Vérifier si le créneau est valide

      const start = new Date(startInput.value)

      const end = new Date(endInput.value)

      

      if (end <= start) {

        updateSlotStatus(i, 'busy') // Créneau invalide

      } else {

        updateSlotStatus(i, 'free') // Créneau valide

      }

    } else {

      // Pas de créneau défini

      updateSlotStatus(i, '')

    }

  }

  // Après toute mise à jour, rafraîchir le calendrier

  updateCalendarDayStates()



  // Si un modal temps est ouvert, rafraîchir compteur et état pour refléter slots actuels

  const modal = document.querySelector('.time-selector-modal')

  if (modal) {

    const countEl = modal.querySelector('.selected-count')

    const chipsCount = modal.querySelectorAll('.selected-times-list .selected-time-chip').length

    const filled = getFilledSlotsCount()

    if (countEl) countEl.textContent = String(Math.min(4, filled + chipsCount))

    const presetBtns = modal.querySelectorAll('.preset-btn')

    const remaining = Math.max(0, 4 - filled)

    presetBtns.forEach(btn => {

      const isSelected = btn.classList.contains('selected')

      btn.disabled = chipsCount >= remaining && !isSelected

    })

  }

}



function debounce(fn, ms){ let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn(...args), ms) } }



async function loadInterviewDataForApplications() {

  console.log("[v0] Using interview data directly from applications table:", applications.length)



  for (let i = 0; i < applications.length; i++) {

    const app = applications[i]

    console.log("[v0] Application", app.id, "interview data:", {

      interview_date: app.interview_date,

      interview_time: app.interview_time,

      interview_type: app.interview_type,

      start_session: app.start_session,

      end_session: app.end_session

    })

    

    // Log détaillé pour l'application 46

    if (app.id === 46) {

      console.log("[DEBUG] Application 46 - Toutes les propriétés:", app)

      console.log("[DEBUG] Application 46 - interview_date:", app.interview_date)

      console.log("[DEBUG] Application 46 - interview_time:", app.interview_time)

      console.log("[DEBUG] Application 46 - interview_type:", app.interview_type)

    }

  }



  console.log("[v0] Interview data loaded from applications table.")

}



async function loadJobFromAPI(jobId) {

  try {

    showLoading("Chargement des détails du poste...")



    const response = await fetch(`/api/job-basic/${jobId}`)

    if (response.ok) {

      const result = await response.json()

      console.log("[DEBUG] Réponse complète de l'API:", result) // <-- AJOUTEZ CE LOG

      

      if (result.success) {

        currentJob = result.job

        applications = result.job.applications || []

        console.log("[DEBUG] Applications chargées:", applications) // <-- ET CELUI-CI



        if (!applications || applications.length === 0) {

          try {

            const appsResponse = await fetch(`/api/applications?job_id=${jobId}`)

            const appsResult = await appsResponse.json()

            console.log("[DEBUG] API /api/applications response:", appsResult)

            if (appsResult.success && appsResult.applications) {

              applications = appsResult.applications

              console.log("[DEBUG] Applications loaded from API:", applications.length)

              // Log the first application to see its structure

              if (applications.length > 0) {

                console.log("[DEBUG] First application data:", applications[0])

                // Chercher l'application 46 spécifiquement

                const app46 = applications.find(app => app.id === 46)

                if (app46) {

                  console.log("[DEBUG] Application 46 from API:", app46)

                  console.log("[DEBUG] Application 46 interview fields:", {

                    interview_date: app46.interview_date,

                    interview_time: app46.interview_time,

                    interview_type: app46.interview_type

                  })

                }

              }

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

        

        // La logique de verrouillage est maintenant gérée par candidat individuellement



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

  

  // Mettre à jour les boutons de chaque candidat après le rendu

  setTimeout(async () => {

    for (const app of filteredApplications) {

      await updateCandidateButton(app.id)

    }

  }, 100)

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



// Fonction pour charger les créneaux d'un candidat spécifique

async function loadCandidateSlots(candidateId) {

  try {

    const jobId = (currentJob && (currentJob.id || currentJob.job_id)) || new URLSearchParams(window.location.search).get("id")

    console.log(`[DEBUG] Chargement des créneaux pour le candidat ${candidateId} dans le job ${jobId}`)

    

    const slotsRes = await fetch(`/api/hr/interview-slots?job_id=${jobId}`)

    const slotsData = await slotsRes.json()

    

    // Filtrer les créneaux pour ce candidat spécifique

    const candidateSlots = slotsData.filter(slot => 

      slot.application_id == candidateId

    )

    

    // Stocker les créneaux pour ce candidat

    selectedSlotsByCandidate[candidateId] = candidateSlots.map(slot => ({

      start: new Date(slot.start_time),

      end: new Date(slot.end_time),

      id: slot.id,

      status: slot.status

    }))

    

    console.log(`[DEBUG] Créneaux chargés pour le candidat ${candidateId}:`, selectedSlotsByCandidate[candidateId])

    

    return selectedSlotsByCandidate[candidateId]

  } catch (error) {

    console.error('Erreur lors du chargement des créneaux du candidat:', error)

    selectedSlotsByCandidate[candidateId] = []

    return []

  }

}



async function openScheduleInterviewModal(applicationId, candidateName) {

  try {

    currentAppId = applicationId

    currentCandidateId = applicationId

    

    // Charger les créneaux existants pour ce candidat

    await loadCandidateSlots(applicationId)

    

    // Vérifier si ce candidat a déjà 4 créneaux (utiliser les créneaux globaux)

    let existingSlotsForCandidate = 0

    for (let i = 1; i <= 4; i++) {

      const s = document.getElementById(`slot${i}_start`)

      const e = document.getElementById(`slot${i}_end`)

      if (s && e && s.value && e.value) {

        existingSlotsForCandidate++

      }

    }

    

    // Vérifier si on peut encore ajouter des créneaux (limite stricte à 4)

    if (existingSlotsForCandidate >= 4) {

      showNotification('Ce candidat a déjà 4 créneaux. Supprimez un créneau pour en ajouter un nouveau.', 'warning')

      return

    }

    

    // Ouvrir le modal de création de créneaux

    clearModalSlots()

    

    const modal = document.getElementById('scheduleInterviewModal')

    if (modal) {

      modal.style.display = 'block'

      modal.classList.add('show')

    }

  } catch (_) {

    // no-op

  }

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

  console.log(`[DEBUG] Interview data for app ${app.id}:`, {

    interview_date: app.interview_date,

    interview_time: app.interview_time, 

    interview_type: app.interview_type,

    has_interview_data: !!(app.interview_date || app.interview_time || app.interview_type)

  })



  // Toujours afficher les champs d'entretien avec les valeurs par défaut ou les vraies données



  const now = new Date()

  const candidateName = app.candidate_profile?.name || app.candidate_name || "N/A"

  const isDeptHead = currentUser?.role === "department_head"



  // Afficher les données d'interview disponibles

  return `

    <div class="interview-overview">

      <div class="interview-info-grid">

        <div class="interview-info-item">

          <div class="info-icon">

            <i class="fas fa-calendar-check"></i>

          </div>

          <div class="info-content">

            <div class="info-label">Date prévue</div>

            <div class="info-value">${app.interview_date ? formatDateSafe(app.interview_date) : 'Non programmé'}</div>

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

            <div class="info-label">Status</div>

            <div class="info-value">${app.interview_type || 'À définir'}</div>

          </div>

        </div>

      </div>

    </div>

    

    ${isDeptHead ? '' : `

    <div class="interview-actions">

      <div class="interview-actions-row">

        <button class="btn-schedule-interview" onclick="openScheduleInterviewModal(${app.id}, '${candidateName}')" id="schedule-btn-${app.id}">

          <i class="fas fa-calendar-plus"></i> <span id="schedule-text-${app.id}">Programmer un entretien</span>

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

