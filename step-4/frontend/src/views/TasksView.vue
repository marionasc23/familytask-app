<script setup>
import { ref, onMounted, computed } from 'vue'
import TaskList from '../components/TaskList.vue'
import { API, authHeaders, getMe } from '../api.js'

const me = getMe()
const tasks = ref([])
const members = ref([])
const newTitle = ref('')
const assignTo = ref(null)
const isAdmin = computed(() => me && me.is_admin)
// default filter: admins see the whole family, non-admins see their own tasks
const filterMember = ref(isAdmin.value ? 'family' : 'me')

async function refresh() {
  // load members for select
  members.value = await (await fetch(`${API}/api/members`, { headers: authHeaders() })).json()

  // load tasks depending on filter and role
  if (isAdmin.value && filterMember.value === 'family') {
    tasks.value = await (await fetch(`${API}/api/tasks/famille`, { headers: authHeaders() })).json()
    return
  }

  const q = new URLSearchParams()
  // only append member_id when a specific member (not 'me' or 'family') is selected
  if (
    filterMember.value &&
    filterMember.value !== 'me' &&
    filterMember.value !== 'family'
  ) {
    q.append('member_id', String(filterMember.value))
  }
  // if filterMember is 'me' or undefined, call /api/tasks (server uses token to return current member tasks)
  const url = `${API}/api/tasks${q.toString() ? ('?' + q.toString()) : ''}`
  tasks.value = await (await fetch(url, { headers: authHeaders() })).json()
}

async function addTask() {
  if (!newTitle.value.trim()) return

  const params = new URLSearchParams({ title: newTitle.value.trim() })
  // always include member_id explicitly to avoid ambiguity
  const target = (isAdmin.value ? (assignTo.value || me.id) : me.id)
  params.append('member_id', target)

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
  if (isAdmin.value && filterMember.value === 'family') return "Toutes les tâches de la famille"
  if (filterMember.value === 'me') return 'Mes tâches'
  const m = members.value.find(x => String(x.id) === String(filterMember.value))
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
        <option :value="me.id">Pour moi</option>
        <option v-for="m in members.filter(x => x.id !== me.id)" :key="m.id" :value="m.id">Pour {{ m.name }}</option>
      </select>
    </div>

    <div class="card">
      <div class="row" style="margin-bottom:10px;">
        <label style="margin-right:8px">Filtrer les tâches :</label>
        <select v-model="filterMember">
          <option v-if="isAdmin" value="family">Toutes la famille</option>
          <option value="me">Mes tâches</option>
          <option v-for="m in members" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
        <button class="link" @click="refresh">Appliquer</button>
      </div>
      <h3>{{ currentTitle }}</h3>
      <TaskList :tasks="tasks" :members="members" @toggle="toggle" @remove="remove" />
    </div>
  </div>
</template>
