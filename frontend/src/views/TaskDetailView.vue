<template>
  <div class="container mt-4">
    <div v-if="loading" class="text-center">Загрузка...</div>
    <div v-else-if="task">
      <div class="d-flex justify-content-between align-items-center">
        <h2>{{ task.title }}</h2>
        <button class="btn btn-success" @click="exportGeoJSON" :disabled="!isCompleted">Экспорт GeoJSON</button>
      </div>
      <p class="text-muted">{{ task.description }}</p>
      <p>Статус: <span class="badge" :class="statusBadge(task.status)">{{ statusText(task.status) }}</span></p>

      <div v-if="isCompleted && solution">
        <div class="row mt-4">
          <div class="col-md-6">
            <div class="card mb-3">
              <div class="card-header bg-primary text-white">Сводные параметры</div>
              <ul class="list-group list-group-flush">
                <li class="list-group-item">Всего парковочных мест: {{ solution.total_parking_spots }}</li>
                <li class="list-group-item">Занятых: {{ solution.occupied_parking_spots }}</li>
                <li class="list-group-item">Свободных: {{ solution.free_parking_spots }}</li>
                <li class="list-group-item">Остановок: {{ solution.public_transport_stops }}</li>
                <li class="list-group-item">Ширина дороги: {{ solution.road_width }} м</li>
                <li class="list-group-item">Ширина тротуара: {{ solution.sidewalk_width }} м</li>
              </ul>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-header bg-light">Карта с объектами</div>
              <div class="card-body p-0">
                <div id="detailMap" style="height: 400px;"></div>
              </div>
              <div class="card-footer small text-muted">
                <button class="btn btn-sm btn-outline-danger" @click="toggleAddMode">
                  {{ addMode ? 'Отключить добавление' : 'Добавить объект (точку)' }}
                </button>
                <span class="ms-2">Клик по объекту – редактировать, клик по карте в режиме добавления – создать точку.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Таблица объектов -->
        <div class="card mt-3">
          <div class="card-header">Список объектов ({{ objects.length }})</div>
          <div class="card-body p-0" style="max-height: 300px; overflow-y: auto;">
            <table class="table table-sm table-hover mb-0">
              <thead>
                <tr><th>Тип</th><th>Параметры</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="(obj, idx) in objects" :key="obj.id || idx">
                  <td>{{ obj.object_type }}</td>
                  <td>
                    <span v-if="obj.width">Ширина: {{ obj.width }} м</span>
                    <span v-if="obj.area"> Площадь: {{ obj.area }} м²</span>
                    <span v-if="obj.is_occupied !== null">{{ obj.is_occupied ? 'Занято' : 'Свободно' }}</span>
                  </td>
                  <td><button class="btn btn-sm btn-outline-danger" @click="deleteObject(obj)">🗑️</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-else-if="task.status === 'pending' || task.status === 'preprocessing' || task.status === 'processing'">
        <div class="alert alert-info">Задача обрабатывается. Обновите страницу позже.</div>
        <button class="btn btn-primary" @click="refresh">Обновить</button>
      </div>
    </div>
    <div v-else class="alert alert-danger">Задача не найдена</div>

    <!-- Модальное окно редактирования объекта -->
    <div class="modal fade" id="editModal" tabindex="-1" ref="editModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Редактировать объект</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <form @submit.prevent="saveObject">
              <div class="mb-2"><label>Тип</label><input type="text" class="form-control" v-model="editObject.object_type" required></div>
              <div class="mb-2"><label>Ширина (м)</label><input type="number" step="0.01" class="form-control" v-model.number="editObject.width"></div>
              <div class="mb-2"><label>Высота (м)</label><input type="number" step="0.01" class="form-control" v-model.number="editObject.height"></div>
              <div class="mb-2"><label>Площадь (м²)</label><input type="number" step="0.01" class="form-control" v-model.number="editObject.area"></div>
              <div class="mb-2"><label>Занято</label><select class="form-select" v-model="editObject.is_occupied"><option :value="true">Да</option><option :value="false">Нет</option><option :value="null">Не указано</option></select></div>
            </form>
          </div>
          <div class="modal-footer"><button class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button><button class="btn btn-primary" @click="saveObject">Сохранить</button></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { taskApi } from '../api'
import L from 'leaflet'
import { Modal } from 'bootstrap'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id
const task = ref(null)
const solution = ref(null)
const objects = ref([])
const loading = ref(false)
let map = null
let geoJsonLayer = null
let editModalInstance = null
const editModal = ref(null)
const editObject = ref({})
let addMode = ref(false)

const statusMap = {
  pending: 'Ожидает', preprocessing: 'Предобработка', processing: 'Анализ',
  completed: 'Завершено', failed: 'Ошибка'
}
const statusBadgeClass = {
  pending: 'bg-secondary', preprocessing: 'bg-info', processing: 'bg-primary',
  completed: 'bg-success', failed: 'bg-danger'
}
function statusText(s) { return statusMap[s] || s }
function statusBadge(s) { return statusBadgeClass[s] || 'bg-secondary' }
const isCompleted = () => task.value?.status === 'completed'

async function loadData() {
  loading.value = true
  try {
    const t = await taskApi.get(taskId)
    task.value = t.data
    if (isCompleted()) {
      const s = await taskApi.getSolution(taskId)
      solution.value = s.data
      objects.value = s.data.objects || []
      initMap()
    }
  } catch (err) { console.error(err) }
  finally { loading.value = false }
}

function initMap() {
  if (!map) {
    map = L.map('detailMap').setView([52.2864, 104.2807], 17)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '' }).addTo(map)
    map.on('click', onMapClick)
  }
  if (geoJsonLayer) geoJsonLayer.clearLayers()
  geoJsonLayer = L.geoJSON(objects.value, {
    style: (feature) => ({ color: '#3388ff', weight: 2, fillOpacity: 0.4 }),
    onEachFeature: (feature, layer) => {
      layer.bindTooltip(`${feature.properties.object_type}`, { sticky: true })
      layer.on('click', () => openEditModal(feature))
    }
  }).addTo(map)
  if (geoJsonLayer.getBounds().isValid()) map.fitBounds(geoJsonLayer.getBounds())
}

function onMapClick(e) {
  if (!addMode.value) return
  const newObj = {
    id: Date.now(),
    object_type: 'Точка',
    geometry: { type: 'Point', coordinates: [e.latlng.lng, e.latlng.lat] },
    width: null, height: null, area: null, is_occupied: null
  }
  objects.value.push(newObj)
  updateObjectsOnServer()
  initMap()
}

function openEditModal(feature) {
  editObject.value = { ...feature.properties, id: feature.id, geometry: feature.geometry }
  editModalInstance.show()
}

function saveObject() {
  const idx = objects.value.findIndex(o => o.id === editObject.value.id)
  if (idx !== -1) {
    objects.value[idx] = { ...objects.value[idx], ...editObject.value }
    updateObjectsOnServer()
  }
  editModalInstance.hide()
}

function deleteObject(obj) {
  if (confirm('Удалить объект?')) {
    objects.value = objects.value.filter(o => o.id !== obj.id)
    updateObjectsOnServer()
  }
}

async function updateObjectsOnServer() {
  try {
    await taskApi.updateObjects(taskId, objects.value)
    initMap()
  } catch (err) { console.error(err) }
}

async function exportGeoJSON() {
  try {
    const res = await taskApi.exportGeoJSON(taskId)
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `task_${taskId}.geojson`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) { alert('Ошибка экспорта') }
}

function toggleAddMode() { addMode.value = !addMode.value }
function refresh() { loadData() }

onMounted(async () => {
  await loadData()
  editModalInstance = new Modal(editModal.value)
})
onUnmounted(() => { if (map) map.remove() })
</script>