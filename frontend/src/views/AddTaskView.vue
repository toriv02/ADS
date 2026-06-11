<template>
  <div class="container mt-4">
    <h2>Новая задача</h2>
    <form @submit.prevent="submitTask">
      <div class="mb-3">
        <label class="form-label">Название *</label>
        <input type="text" class="form-control" v-model="form.title" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Описание</label>
        <textarea class="form-control" rows="2" v-model="form.description"></textarea>
      </div>
      <div class="mb-3">
        <label class="form-label">Тип материала</label>
        <select class="form-select" v-model="form.material_type">
          <option value="ground">Наземное фото</option>
          <option value="satellite">Спутниковый снимок</option>
          <option value="video">Видео</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Качество улучшения</label>
        <select class="form-select" v-model="form.quality_profile">
          <option value="fast">Быстрое</option>
          <option value="balanced">Качественное</option>
          <option value="high">Высокое</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Файл *</label>
        <input type="file" class="form-control" @change="handleFile" accept="image/*,video/*" required>
        <div v-if="previewUrl && form.material_type !== 'video'" class="mt-2">
          <img :src="previewUrl" class="img-thumbnail" style="max-height: 200px">
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Калибровка (опорный размер в метрах)</label>
        <div class="row">
          <div class="col-md-4">
            <label class="form-label small">Расстояние в пикселях</label>
            <input type="number" step="0.1" class="form-control" v-model.number="form.reference_pixels" placeholder="px">
          </div>
          <div class="col-md-4">
            <label class="form-label small">Реальный размер (м)</label>
            <input type="number" step="0.01" class="form-control" v-model.number="form.reference_meters" placeholder="м">
          </div>
        </div>
        <div class="mt-2 small text-muted">Для автоматического измерения размеров укажите длину известного объекта на изображении.</div>
      </div>
      <div class="mb-3">
        <label class="form-label">Геопозиция (центр участка)</label>
        <div class="row">
          <div class="col-md-6">
            <input type="number" step="any" class="form-control" v-model.number="form.latitude" placeholder="Широта">
          </div>
          <div class="col-md-6">
            <input type="number" step="any" class="form-control" v-model.number="form.longitude" placeholder="Долгота">
          </div>
        </div>
      </div>
      <div class="d-flex gap-2">
        <button type="submit" class="btn btn-primary" :disabled="submitting">Создать</button>
        <router-link to="/" class="btn btn-secondary">Отмена</router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { taskApi } from '../api'

const router = useRouter()
const form = ref({
  title: '',
  description: '',
  material_type: 'ground',
  quality_profile: 'balanced',
  reference_pixels: null,
  reference_meters: null,
  latitude: null,
  longitude: null
})
const file = ref(null)
const previewUrl = ref(null)
const submitting = ref(false)

function handleFile(e) {
  file.value = e.target.files[0]
  if (file.value && file.value.type.startsWith('image/')) {
    previewUrl.value = URL.createObjectURL(file.value)
  } else {
    previewUrl.value = null
  }
}

async function submitTask() {
  if (!file.value) {
    alert('Выберите файл')
    return
  }
  submitting.value = true
  const fd = new FormData()
  for (let [k, v] of Object.entries(form.value)) {
    if (v !== null && v !== '') fd.append(k, v)
  }
  fd.append('media_file', file.value)

  try {
    await taskApi.create(fd)
    router.push('/')
  } catch (err) {
    console.error(err)
    alert('Ошибка при создании задачи')
  } finally {
    submitting.value = false
  }
}
</script>