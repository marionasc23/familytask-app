<script setup>
import { computed, ref } from 'vue'
import TaskList from './components/TaskList.vue'

// Données maîtresses : elles vivent dans le parent App.vue.
const tasks = ref([
  { id: 1, title: 'Faire les courses', done: false },
  { id: 2, title: 'Préparer le dîner', done: true }
])

const newTask = ref('')

const remainingTasks = computed(() => {
  return tasks.value.filter(task => !task.done).length
})

const completedTasks = computed(() => {
  return tasks.value.filter(task => task.done).length
})

const totalTasks = computed(() => tasks.value.length)

const isEmpty = computed(() => tasks.value.length === 0)

function addTask() {
  if (!newTask.value.trim()) return

  tasks.value.push({
    id: Date.now(),
    title: newTask.value.trim(),
    done: false
  })

  newTask.value = ''
}

function toggleTask(taskId) {
  tasks.value = tasks.value.map(task => {
    if (task.id === taskId) {
      return { ...task, done: !task.done }
    }
    return task
  })
}

function removeTask(taskId) {
  tasks.value = tasks.value.filter(task => task.id !== taskId)
}

function clearAll() {
  tasks.value = []
}
</script>

<template>
  <header>
    <h1>🏠 FamilyTask</h1>
  </header>

  <main>
    <div class="card">
      <div class="title-row">
        <h2>Ma todo-list</h2>
        <span class="task-badge">{{ totalTasks }}</span>
      </div>

      <div class="stats-row">
        <p class="counter">{{ remainingTasks }} tâche(s) restante(s)</p>
        <p class="counter done-counter">{{ completedTasks }} terminée(s)</p>
      </div>

      <div class="add-task">
        <input
          v-model="newTask"
          type="text"
          placeholder="Ajouter une tâche..."
          @keyup.enter="addTask"
        />
        <button @click="addTask">➕ Ajouter</button>
      </div>

      <div v-if="!isEmpty" class="actions-row">
        <button class="clear-btn" @click="clearAll">Tout effacer</button>
      </div>

      <TaskList v-if="!isEmpty" :tasks="tasks" @toggle="toggleTask" @remove="removeTask" />

      <div v-else class="empty-state">
        <div class="trophy">🏆</div>
        <p>Bravo champion !</p>
        <small>On recommence bientôt</small>
      </div>
    </div>
  </main>
</template>
