<template>
  <form @submit.prevent="submit">
    <input v-model="title" placeholder="Название задачи" required />
    <textarea v-model="description" placeholder="Описание"></textarea>
    <select v-model="materialType">
      <option value="ground">Наземный снимок</option>
      <option value="satellite">Спутниковый снимок</option>
    </select>
    <select v-model="targetQuality">
      <option value="fast">Быстрое</option>
      <option value="quality">Качественное</option>
      <option value="high">Высокое</option>
    </select>
    <input type="file" @change="onFileChange" />
    <button type="submit">Создать задачу</button>
  </form>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return { title: '', description: '', materialType: 'ground', targetQuality: 'fast', file: null }
  },
  methods: {
    onFileChange(e) { this.file = e.target.files[0] },
    async submit() {
      const formData = new FormData()
      formData.append('title', this.title)
      formData.append('description', this.description)
      formData.append('material_type', this.materialType)
      formData.append('target_quality', this.targetQuality)
      formData.append('source_file', this.file)
      await axios.post('/api/tasks/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      this.$router.push('/')
    }
  }
}
</script>