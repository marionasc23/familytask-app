<script setup>
// Le composant reçoit la liste des tâches depuis son parent via props.
// Il ne modifie pas directement les données : il demande au parent de les modifier
// en émettant des événements.
const props = defineProps({
  tasks: {
    type: Array,
    required: true
  }
})

// Les événements que le composant remonte au parent.
const emit = defineEmits(['toggle', 'remove'])

function toggleTask(taskId) {
  emit('toggle', taskId)
}

function removeTask(taskId) {
  emit('remove', taskId)
}
</script>

<template>
  <ul class="task-list">
    <li v-for="task in props.tasks" :key="task.id" :class="{ done: task.done }">
      <label class="checkbox-wrap" :title="task.done ? 'Tâche terminée' : 'Tâche en cours'">
        <input :checked="task.done" type="checkbox" @change="toggleTask(task.id)" />
        <span class="checkmark"></span>
      </label>

      <span class="task-title">{{ task.title }}</span>

      <button class="delete-btn" @click="removeTask(task.id)" aria-label="Supprimer la tâche">🗑️</button>
    </li>
  </ul>
</template>
