<script setup>
import { ref, onMounted, computed } from 'vue'
import TaskList from '../components/TaskList.vue'
import { API, authHeaders, getMe } from '../api.js'

const me = getMe()
const tasks = ref([])
const members = ref([])
const newTitle = ref('')
const assignTo = ref(null)
const filterMember = ref(null)
const isAdmin = computed(() => me && me.is_admin)

async function refresh() {
  // load members for select
  members.value = await (await fetch(`${API}/api/members`, { headers: authHeaders() })).json()

  // build tasks URL with optional member filter
  const q = new URLSearchParams()
  if (filterMember.value) q.append('member_id', filterMember.value)
  // default: member_id not provided -> current member tasks
  const url = `${API}/api/tasks${q.toString() ? ('?' + q.toString()) : ''}`
  tasks.value = await (await fetch(url, { headers: authHeaders() })).json()
}

async function addTask() {
  if (!newTitle.value.trim()) return

  const params = new URLSearchParams({ title: newTitle.value.trim() })
  if (isAdmin.value && assignTo.value) params.append('member_id', assignTo.value)

  await fetch(`${API}/api/tasks?${params.toString()}`, { method: 'POST', headers: authHeaders() })
  newTitle.value = ''
  // after creating, refresh using current filter
  await refresh()
}

async function toggle(task) {
  // toggle done state
  const newDone = !task.done
  const q = new URLSearchParams({ done: newDone })
  await fetch(`${API}/api/tasks/${task.id}?${q.toString()}`, { method: 'PATCH', headers: authHeaders() })
  await refresh()
}

async function remove(task) {
  if (!confirm(`Supprimer la tâche "${task.title}" ?`)) return
  await fetch(`${API}/api/tasks/${task.id}`, { method: 'DELETE', headers: authHeaders() })
  await refresh()
}

const currentTitle = computed(() => {
  if (!filterMember.value) return 'Mes tâches'
  const m = members.value.find(x => x.id === filterMember.value)
  return m ? `Tâches de ${m.name}` : 'Tâches filtrées'
})

onMounted(refresh)
</script>

<template>
  <div class="view">
    <div class="hello">Bonjour <strong>{{ me?.name }}</strong> 👋</div>

    <div class="card add">
      <div class="row">
        <input v-model="newTitle" placeholder="Nouvelle tâche…" @keyup.enter="addTask" />
        <button class="primary square" @click="addTask">＋</button>
      </div>
      <select v-if="isAdmin" v-model="assignTo" class="assign">
        <option :value="null">Pour moi</option>
        <option v-for="m in members.filter(x => x.id !== me.id)" :key="m.id" :value="m.id">Pour {{ m.name }}</option>
      </select>
    </div>

    <div class="card">
      <h3>{{ currentTitle }}</h3>
      <TaskList :tasks="tasks" :members="members" @toggle="toggle" @remove="remove" />
    </div>
  </div>
</template>
