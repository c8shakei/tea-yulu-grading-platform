import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getToken, removeToken, setToken } from '../utils/auth'
import { getMe, logout } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(getToken())
  const user = ref(null)
  const loading = ref(false)

  const isLoggedIn = () => !!token.value && !!user.value

  async function restoreToken() {
    const t = getToken()
    if (!t) {
      user.value = null
      return
    }
    token.value = t
    try {
      loading.value = true
      const data = await getMe()
      user.value = data
    } catch (e) {
      removeToken()
      token.value = null
      user.value = null
    } finally {
      loading.value = false
    }
  }

  function setUser(data) {
    user.value = data
    if (data.token) {
      token.value = data.token
      setToken(data.token)
    }
  }

  async function logoutUser() {
    try {
      await logout()
    } catch (e) {
      // ignore
    }
    removeToken()
    token.value = null
    user.value = null
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    restoreToken,
    setUser,
    logoutUser,
  }
})
