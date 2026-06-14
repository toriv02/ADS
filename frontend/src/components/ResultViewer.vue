<template>
  <div>
    <img :src="imageUrl" ref="image" @load="draw" />
    <canvas ref="canvas" @click="onCanvasClick"></canvas>
    <button @click="exportGeoJSON">Экспорт GeoJSON</button>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  props: ['taskId'],
  data() { return { task: null, objects: [] } },
  async mounted() {
    const res = await axios.get(`/api/tasks/${this.taskId}/`)
    this.task = res.data
    this.objects = this.task.objects || []
    this.draw()
  },
  methods: {
    draw() {
      const img = this.$refs.image, canvas = this.$refs.canvas
      canvas.width = img.width; canvas.height = img.height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0)
      for (let obj of this.objects) {
        ctx.strokeStyle = 'red'
        ctx.strokeRect(obj.position_x, obj.position_y, obj.width, obj.height)
        ctx.fillText(obj.object_type, obj.position_x, obj.position_y)
      }
    },
    onCanvasClick(e) { /* логика редактирования */ },
    async exportGeoJSON() {
      const res = await axios.get(`/api/tasks/${this.taskId}/export_geojson/`)
      const blob = new Blob([JSON.stringify(res.data)], {type: 'application/json'})
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = 'export.geojson'; a.click()
    }
  }
}
</script>