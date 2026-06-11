<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Задачи</h2>
      <router-link to="/tasks/new" class="btn btn-primary">+ Новая задача</router-link>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-5">
            <input type="text" class="form-control" v-model="filters.search" placeholder="Поиск по названию" @input="searchDebounced">
          </div>
          <div class="col-md-3">
            <select class="form-select" v-model="filters.status" @change="loadTasks">
              <option value="">Все статусы</option>
              <option value="pending">Ожидает</option>
              <option value="preprocessing">Предобработка</option>
              <option value="processing">Анализ</option>
              <option value="completed">Завершено</option>
              <option value="failed">Ошибка</option>
            </select>
          </div>
          <div class="col-md-2">
            <button class="btn btn-secondary w-100" @click="resetFilters">Сбросить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Список задач -->
    <div v-if="loading" class="text-center my-5">Загрузка...</div>
    <div v-else>
      <div class="row g-4">
        <div class="col-md-6 col-lg-4" v-for="task in tasks" :key="task.id">
          <div class="card h-100 task-card" :class="{ 'disabled-card': task.status !== 'completed' }" @click="goToTask(task)">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <span class="badge" :class="statusBadge(task.status)">{{ statusText(task.status) }}</span>
                <small class="text-muted">{{ formatDate(task.created_at) }}</small>
              </div>
              <h5 class="card-title mt-2">{{ task.title }}</h5>
              <p class="card-text text-muted">{{ truncate(task.description, 80) }}</p>
              <div class="mt-2 small text-muted">
                <i class="bi bi-person"></i> {{ task.user_username || task.user }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="tasks.length === 0" class="alert alert-info mt-3">Задач не найдено</div>
    </div>

    <!-- Пагинация -->
    <nav v-if="totalPages > 1" class="mt-4">
      <ul class="pagination justify-content-center">
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <button class="page-link" @click="changePage(currentPage - 1)">Назад</button>
        </li>
        <li class="page-item disabled"><span class="page-link">{{ currentPage }} / {{ totalPages }}</span></li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <button class="page-link" @click="changePage(currentPage + 1)">Вперёд</button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { taskApi } from '../api'

const router = useRouter()
const tasks = ref([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const filters = ref({ search: '', status: '' })
let debounceTimer = null

const statusMap = {
  pending: 'Ожидает',
  preprocessing: 'Предобработка',
  processing: 'Анализ',
  completed: 'Завершено',
  failed: 'Ошибка'
}
const statusBadgeClass = {
  pending: 'bg-secondary',
  preprocessing: 'bg-info',
  processing: 'bg-primary',
  completed: 'bg-success',
  failed: 'bg-danger'
}

function statusText(status) { return statusMap[status] || status }
function statusBadge(status) { return statusBadgeClass[status] || 'bg-secondary' }
function formatDate(iso) { return new Date(iso).toLocaleString() }
function truncate(str, len) { return str?.length > len ? str.slice(0, len) + '…' : str || '' }

async function loadTasks() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      search: filters.value.search,
      status: filters.value.status
    }
    const res = await taskApi.list(params)
    tasks.value = res.data.results
    totalPages.value = Math.ceil(res.data.count / 10)
  } catch (err) { console.error(err) }
  finally { loading.value = false }
}

function searchDebounced() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadTasks()
  }, 500)
}

function resetFilters() {
  filters.value = { search: '', status: '' }
  currentPage.value = 1
  loadTasks()
}

function changePage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadTasks()
  }
}

function goToTask(task) {
  if (task.status === 'completed') {
    router.push(`/tasks/${task.id}`)
  } else {
    alert(`Задача в статусе «${statusText(task.status)}». Результаты появятся после завершения.`)
  }
}

onMounted(loadTasks)
</script>

<style scoped>
.task-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.task-card:hover:not(.disabled-card) {
  transform: translateY(-4px);
  box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
}
.disabled-card {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>