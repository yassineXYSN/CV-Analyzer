;(function () {
  const STORAGE_KEY = 'preferred_lang'
  const PAGE_LANG = 'fr'

  function setCookie(name, value, days) {
    let expires = ''
    if (days) {
      const date = new Date()
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000)
      expires = '; expires=' + date.toUTCString()
    }
    const path = '; path=/'
    document.cookie = name + '=' + (value || '') + expires + path
  }

  function setGoogTransCookie(lang) {
    if (!lang || lang === PAGE_LANG) {
      // Clear cookie to revert to original
      setCookie('googtrans', '/'+PAGE_LANG+'/'+PAGE_LANG, 365)
      return
    }
    setCookie('googtrans', '/' + PAGE_LANG + '/' + lang, 365)
  }

  function applyPreferredLanguage() {
    const pref = localStorage.getItem(STORAGE_KEY)
    if (!pref) return
    setGoogTransCookie(pref)

    // If translator dropdown exists, set it and trigger change
    const attempt = () => {
      const combo = document.querySelector('.goog-te-combo')
      if (combo) {
        if (combo.value !== pref) {
          combo.value = pref
          combo.dispatchEvent(new Event('change'))
        }
        return true
      }
      return false
    }

    // Try a few times as the widget loads asynchronously
    let tries = 0
    const interval = setInterval(() => {
      if (attempt() || tries++ > 20) clearInterval(interval)
    }, 300)
  }

  function bindTranslatorChange() {
    const observer = new MutationObserver(() => {
      const combo = document.querySelector('.goog-te-combo')
      if (combo && !combo.dataset.bound) {
        combo.dataset.bound = '1'
        combo.addEventListener('change', () => {
          const lang = combo.value
          localStorage.setItem(STORAGE_KEY, lang)
          setGoogTransCookie(lang)
        })
      }
    })
    observer.observe(document.documentElement, { childList: true, subtree: true })
  }

  document.addEventListener('DOMContentLoaded', () => {
    applyPreferredLanguage()
    bindTranslatorChange()
  })
})()


