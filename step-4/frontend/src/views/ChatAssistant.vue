<script setup>
import { ref, onBeforeUnmount, computed } from 'vue'
import { API, authHeaders, getMe } from '../api.js'

const emit = defineEmits(['refresh-tasks'])

const me = computed(() => getMe())
const input = ref('')
const isLoading = ref(false)
const listening = ref(false)
const messages = ref([
  { role: 'bot', text: 'Bonjour ! Je peux t’aider à organiser la maison et créer des tâches pour la famille.' }
])
let recognition = null

const familyIcons = {
  parent: '👩‍🦳',
  parents: '👩‍🦳',
  mere: '👩‍🦳',
  "mère": '👩‍🦳',
  maman: '👩‍🦳',
  pere: '👨‍🦳',
  "père": '👨‍🦳',
  papa: '👨‍🦳',
  grandmere: '👵',
  "grand-mere": '👵',
  grandpere: '👴',
  "grand-pere": '👴',
  grandparent: '👵',
  fille: '👧',
  fils: '👦',
  frere: '👦',
  "frère": '👦',
  soeur: '👧',
  "soeur": '👧',
  enfant: '🧒',
  cousin: '🧑',
  cousine: '👧',
  tante: '👩',
  oncle: '👨',
  ami: '🧑‍🤝‍🧑',
  amie: '🧑‍🤝‍🧑',
  conjoint: '💑',
  conjointe: '💑',
  mari: '👨',
  femme: '👩',
  default: '👤'
}

function memberAvatar(memberName, relation = '') {
  if (!memberName) return '👤'
  const key = (relation || memberName || '').toLowerCase()
  const match = Object.keys(familyIcons).find(iconKey => key.includes(iconKey))
  return match ? familyIcons[match] : familyIcons.default
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', text, icon: memberAvatar(me.value?.name, me.value?.lien) })
  input.value = ''
  isLoading.value = true

  try {
    const response = await fetch(`${API}/api/assistant`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ message: text })
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'L’assistant est momentanément indisponible.')
    }

    const reply = data.reply || 'Je n’ai pas de réponse pour le moment.'
    messages.value.push({ role: 'bot', text: reply, icon: '🤖' })

    if (data.tasks && data.tasks.length) {
      emit('refresh-tasks')
    }
  } catch (error) {
    messages.value.push({ role: 'bot', text: error.message || 'Un problème est survenu avec l’assistant.', icon: '⚠️' })
  } finally {
    isLoading.value = false
  }
}

function startVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

  if (!SpeechRecognition) {
    messages.value.push({ role: 'bot', text: 'La reconnaissance vocale n’est pas disponible sur ce navigateur.', icon: '⚠️' })
    return
  }

  if (recognition) {
    recognition.stop()
    recognition = null
    listening.value = false
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = 'fr-FR'
  recognition.continuous = false
  recognition.interimResults = false

  recognition.onstart = () => {
    listening.value = true
    messages.value.push({ role: 'bot', text: 'Je t’écoute…', icon: '🎧' })
  }

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0]?.transcript || '')
      .join(' ')
      .trim()

    if (transcript) {
      input.value = transcript
    }
  }

  recognition.onerror = () => {
    messages.value.push({ role: 'bot', text: 'Je n’ai pas bien compris. Réessaie.', icon: '⚠️' })
    listening.value = false
  }

  recognition.onend = () => {
    recognition = null
    listening.value = false
  }

  recognition.start()
}

onBeforeUnmount(() => {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
})
</script>

<template>
  <div class="view assistant-view">
    <div class="hello">Assistant <strong>familial</strong> ✨</div>

    <div class="card assistant-card">
      <div class="messages">
        <div v-for="(message, index) in messages" :key="index" :class="['message-row', message.role]">
          <div v-if="message.role === 'bot'" class="avatar-bubble bot">{{ message.icon || '🤖' }}</div>
          <div :class="['message', message.role]">
            {{ message.text }}
          </div>
          <div v-if="message.role === 'user'" class="avatar-bubble user">{{ message.icon || '👤' }}</div>
        </div>
      </div>

      <div class="composer">
        <input
          v-model="input"
          type="text"
          placeholder="Demande à l’assistant…"
          @keyup.enter="sendMessage"
        />

        <button class="primary square" @click="sendMessage" :disabled="isLoading">
          {{ isLoading ? '…' : '➤' }}
        </button>

        <button class="mic" :class="{ live: listening }" @click="startVoiceRecognition" aria-label="Dictée vocale">
          🎤
        </button>
      </div>
    </div>
  </div>
</template>
