<script setup>
const props = defineProps({
  tasks: Array,
  members: { type: Array, default: () => [] }
})
const emit = defineEmits(['toggle', 'remove'])

function memberName(id) {
  const m = props.members.find(m => m.id === id)
  return m ? m.name : ''
}
</script>

<template>
  <ul class="task-list">
    <li v-for="t in tasks" :key="t.id" :class="['task-item', { done: t.done }]">
      <label class="checkbox">
        <input type="checkbox" :checked="t.done" @change="emit('toggle', t)" />
        <span class="checkmark"></span>
      </label>

      <div class="task-main">
        <span class="task-title">{{ t.title }}</span>
        <div class="meta">
          <span class="who" v-if="memberName(t.member_id)">👤 {{ memberName(t.member_id) }}</span>
          <span class="done-badge" v-if="t.done">✔ Accompli</span>
        </div>
      </div>

      <button class="trash" @click="emit('remove', t)" aria-label="Supprimer la tâche">🗑</button>
    </li>
    <li v-if="tasks.length === 0" class="hint">Aucune tâche pour l'instant.</li>
  </ul>
</template>

<style scoped>
.task-main { flex: 1; display: flex; flex-direction: column; }
.meta { font-size: 0.8em; color: #666; margin-top: 4px; display:flex; gap:8px; align-items:center }
.done-badge { background:#e8f6ea; color:#2d7a3a; padding:2px 6px; border-radius:10px; font-weight:600; transform:scale(0.9); opacity:0; transition:transform .18s ease, opacity .18s ease }
.task-item.done .done-badge { transform:scale(1); opacity:1 }
.task-item { transition: background .18s ease, transform .12s ease }
.task-item:active { transform: translateY(1px) }
.checkbox { display:inline-flex; align-items:center; margin-right:8px }
.checkbox input { display:none }
.checkbox .checkmark { width:18px; height:18px; border-radius:4px; border:1px solid #ccc; display:inline-block }
.task-item.done .checkbox .checkmark { background:linear-gradient(90deg,#4ade80,#16a34a); border-color:transparent }
</style>
