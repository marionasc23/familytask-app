<script setup>
import { onMounted, ref } from 'vue'
import TaskList from './components/TaskList.vue'

const tasks = ref([])
const newTitle = ref('')
const errorMessage = ref('')

const fallbackTitles = [
  'Routine maison',
  'Coup de boost',
  'Petit rappel utile',
  'À faire quand j’ai 2 minutes',
  'Tâche improvisée',
]

async function loadTasks() {
  const response = await fetch('/api/tasks')
  if (!response.ok) {
    throw new Error('Impossible de charger les tâches.')
  }

  tasks.value = await response.json()
}

onMounted(async () => {
  try {
    await loadTasks()
  } catch (error) {
    errorMessage.value = error.message
  }
})

async function addTask() {
  const titleToSend = newTitle.value.trim() || fallbackTitles[Math.floor(Math.random() * fallbackTitles.length)]

  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: titleToSend })
  })

  if (!response.ok) {
    errorMessage.value = 'Impossible d’ajouter la tâche.'
    return
  }

  newTitle.value = ''
  errorMessage.value = ''
  await loadTasks()
}

async function toggle(task) {
  const response = await fetch(`/api/tasks/${task.id}`, {
    method: 'PATCH'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Tâche introuvable' }))
    errorMessage.value = error.detail || 'Erreur lors du changement de statut.'
    return
  }

  errorMessage.value = ''
  await loadTasks()
}

async function remove(task) {
  const response = await fetch(`/api/tasks/${task.id}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Tâche introuvable' }))
    errorMessage.value = error.detail || 'Erreur lors de la suppression.'
    return
  }

  errorMessage.value = ''
  await loadTasks()
}
</script>

<template>
  <header><h1>🏠 FamilyTask</h1></header>
  <main>
    <div class="card">
      <h2>Nouvelle tâche</h2>
      <div class="row">
        <input v-model="newTitle" placeholder="Ex: Sortir les poubelles" @keyup.enter="addTask" />
        <button @click="addTask">Ajouter</button>
      </div>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
    <div class="card">
      <h2>Les tâches</h2>
      <TaskList :tasks="tasks" @toggle="toggle" @remove="remove" />
    </div>
  </main>
</template>
