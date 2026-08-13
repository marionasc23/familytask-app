<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isLogged, getMe, logout as apiLogout } from './api.js'

const route = useRoute()
const router = useRouter()
const theme = ref('beige')

function logout() { apiLogout(); router.push('/login') }
function toggleTheme() {
  theme.value = theme.value === 'beige' ? 'apple' : 'beige'
}
</script>

<template>
  <div class="phone" :class="theme === 'beige' ? 'theme-beige' : 'theme-apple'">
    <header class="appbar" v-if="isLogged() && route.meta.nav">
      <div class="brand">🏠 FamilyTask</div>
      <div class="toolbar">
        <button class="theme-switch" @click="toggleTheme">
          {{ theme === 'beige' ? 'Apple' : 'Beige' }}
        </button>
        <button class="link" @click="logout">Quitter</button>
      </div>
    </header>

    <main class="screen"><router-view /></main>

    <nav class="tabbar" v-if="isLogged() && route.meta.nav">
      <router-link to="/taches" class="tab"><span class="ico">✅</span>Tâches</router-link>
      <router-link to="/assistant" class="tab"><span class="ico">🤖</span>Assistant</router-link>
      <router-link v-if="getMe() && getMe().is_admin" to="/famille" class="tab"><span class="ico">👨‍👩‍👧</span>Famille</router-link>
    </nav>
  </div>
</template>
