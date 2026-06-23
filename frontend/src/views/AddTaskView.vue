<template>
  <div class="container my-4">
    <div class="mb-4">
      <button class="btn btn-outline-secondary" @click="goBack">
        <i class="bi bi-arrow-left"></i> Назад к задачам
      </button>
    </div>

    <div class="card">
      <div class="card-header bg-primary text-white">
        <h3 class="mb-0">Добавление новой задачи</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="submitTask">
          <!-- Основные поля -->
          <div class="mb-3">
            <label for="title" class="form-label">Название задачи *</label>
            <input type="text" id="title" class="form-control" v-model="form.title" required />
          </div>

          <div class="mb-3">
            <label for="description" class="form-label">Краткое описание</label>
            <textarea id="description" class="form-control" rows="2" v-model="form.description"></textarea>
          </div>

          <!-- Качество -->
          <div class="mb-3">
            <label class="form-label">Целевое качество улучшения</label>
            <div class="d-flex flex-wrap gap-3">
              <div class="form-check" v-for="opt in qualityOptions" :key="opt.value">
                <input class="form-check-input" type="radio" :value="opt.value" :id="opt.value" v-model="form.quality" />
                <label class="form-check-label" :for="opt.value">
                  {{ opt.label }}
                  <span class="text-muted small">({{ timeEstimate[opt.value] }})</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Тип материала -->
          <div class="mb-3">
            <label class="form-label">Тип исходного материала</label>
            <div class="d-flex gap-3">
              <div class="form-check" v-for="type in fileTypes" :key="type.value">
                <input class="form-check-input" type="radio" :value="type.value" :id="type.value" v-model="form.fileType" />
                <label class="form-check-label" :for="type.value">{{ type.label }}</label>
              </div>
            </div>
          </div>

          <!-- Загрузка медиафайла (для наземного режима) -->
          <div v-if="!isSatelliteMode">
            <div class="mb-3">
              <label class="form-label">Загрузите изображение или видео *</label>
              <div
                class="dropzone border rounded p-4 text-center"
                :class="{ 'border-primary bg-light': dragActive }"
                @dragover.prevent="dragActive = true"
                @dragleave.prevent="dragActive = false"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <i class="bi bi-cloud-upload fs-1"></i>
                <p class="mt-2">Перетащите файл сюда или кликните для выбора</p>
                <p class="text-muted small">Поддерживаются: JPG, PNG, MP4, AVI (до 200 МБ)</p>
                <input type="file" ref="fileInput" class="d-none" @change="handleFileSelect" accept="image/jpeg,image/png,video/mp4,video/avi" />
              </div>
              <!-- Превью и калибровка -->
              <div v-if="form.mediaPreview" class="mt-2">
                <p><strong>Выбран файл:</strong> {{ form.mediaFileName }}</p>
                <div v-if="isImage" class="calibration-area">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="fw-bold">Калибровка размера (укажите опорный отрезок)</span>
                    <button type="button" class="btn btn-sm btn-outline-danger" @click="clearCalibrationPoints">Очистить точки</button>
                  </div>
                  <div class="image-container">
                    <img
                      ref="staticImage"
                      :src="form.mediaPreview"
                      class="img-fluid"
                      alt="Preview"
                      style="max-height: 400px; cursor: crosshair;"
                      @click="handleImageClick"
                    />
                    <canvas ref="staticCanvas" class="static-canvas" @click="handleCanvasClick"></canvas>
                  </div>
                  <div class="mt-2 small text-muted">
                    <span v-if="calibrationPoints.length === 0">Кликните на изображении, чтобы задать первую точку →</span>
                    <span v-else-if="calibrationPoints.length === 1">Теперь кликните, чтобы задать вторую точку</span>
                    <span v-else>
                      <strong>Размер в пикселях:</strong> {{ pixelDistance.toFixed(1) }} px.
                      <template v-if="form.realSize">Масштаб: {{ (form.realSize / pixelDistance).toFixed(4) }} м/px.</template>
                    </span>
                  </div>
                </div>
                <video v-else-if="isVideo" controls class="img-thumbnail" style="max-height: 200px">
                  <source :src="form.mediaPreview" />
                </video>
              </div>
            </div>

            <div v-if="calibrationPoints.length === 2" class="mb-3">
              <label class="form-label">Реальный размер объекта (метры)</label>
              <input type="number" step="0.01" class="form-control" v-model.number="form.realSize" placeholder="3.5" />
            </div>
          </div>

          <!-- Спутниковый режим -->
          <div v-else>
            <div class="mb-3">
              <label class="form-label">Спутниковый снимок выбранной области</label>
              <div v-if="!form.mediaPreview" class="alert alert-secondary">
                <i class="bi bi-info-circle"></i> Снимок появится после выбора 4 точек на карте ниже.
              </div>
              <div v-else class="mt-2">
                <img :src="form.mediaPreview" class="img-fluid" alt="Satellite preview" style="max-height: 400px;" />
                <div class="small text-muted mt-1" v-if="form.calibrationAuto">
                  Масштаб: ~{{ (form.calibrationAuto.realSize / form.calibrationAuto.pixelDistance).toFixed(4) }} м/пиксель
                </div>
              </div>
            </div>
          </div>

          <!-- Загрузка файла весов (опционально) -->
          <div class="mb-3">
            <label class="form-label">Файл весов модели (опционально)</label>
            <input type="file" class="form-control" @change="handleWeightsFile" accept=".pt,.pth,.h5,.onnx" />
            <div v-if="form.weightsFile" class="mt-1 small text-success">
              <i class="bi bi-check-circle"></i> Выбран: {{ form.weightsFileName }}
            </div>
          </div>

          <!-- Карта -->
          <div class="mb-3">
            <label class="form-label">
              <span v-if="isSatelliteMode">Выберите область для спутникового снимка (4 угловые точки)</span>
              <span v-else>Опорный отрезок на карте (укажите две точки)</span>
            </label>
            <div class="border rounded p-2">
              <div id="map" class="map-container" style="height: 350px;"></div>
              <div class="mt-2 small text-muted">
                <template v-if="isSatelliteMode">
                  <span v-if="satellitePoints.length === 0">Кликните на карте, чтобы задать первую точку →</span>
                  <span v-else-if="satellitePoints.length < 4">Выбрано {{ satellitePoints.length }} точки. Нужно 4 угла.</span>
                  <span v-else><strong>Область задана.</strong> Спутниковый снимок загружен.</span>
                  <button v-if="satellitePoints.length > 0" type="button" class="btn btn-sm btn-link" @click="clearSatellitePoints">Очистить точки</button>
                </template>
                <template v-else>
                  <span v-if="form.mapPoints.length === 0">Кликните на карте, чтобы задать первую точку</span>
                  <span v-else-if="form.mapPoints.length === 1">Теперь кликните, чтобы задать вторую точку</span>
                  <span v-else>
                    <strong>Расстояние на карте:</strong> {{ mapDistance.toFixed(2) }} м.
                  </span>
                  <button v-if="form.mapPoints.length > 0" type="button" class="btn btn-sm btn-link" @click="clearMapPoints">Очистить точки</button>
                </template>
              </div>
            </div>
          </div>

          <div class="d-flex justify-content-end gap-2 mt-4">
            <button type="button" class="btn btn-secondary" @click="goBack">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? 'Отправка...' : 'Добавить задачу' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useTaskStore } from '@/stores/taskStore';
import { createTask } from '@/api/tasks'; // предполагаемый API-метод

const router = useRouter();
const taskStore = useTaskStore();

const qualityOptions = [
  { value: 'fast', label: 'Быстрое' },
  { value: 'quality', label: 'Качественное' },
  { value: 'high', label: 'Высокое' }
];
const fileTypes = [
  { value: 'ground', label: 'Наземный снимок / видео' },
  { value: 'satellite', label: 'Спутниковый снимок' }
];

// ---- Состояние формы ----
const form = reactive({
  title: '',
  description: '',
  quality: 'quality',
  fileType: 'ground',
  mediaFile: null,
  mediaFileName: '',
  mediaPreview: null,
  weightsFile: null,
  weightsFileName: '',
  startX: null,
  startY: null,
  endX: null,
  endY: null,
  realSize: null,
  mapPoints: [],
  calibrationAuto: null,
  satelliteArea: null
});

const isSatelliteMode = computed(() => form.fileType === 'satellite');
const satellitePoints = ref([]);
const isSubmitting = ref(false);

// ---- Флаги и ссылки для наземного режима ----
const dragActive = ref(false);
const fileInput = ref(null);
const staticImage = ref(null);
const staticCanvas = ref(null);
const calibrationPoints = ref([]);

let map = null;
let mapMarkers = [];
let mapLine = null;
let satMarkers = [];
let satPolygon = null;

// ---- Вспомогательные функции ----
const haversineDistance = (p1, p2) => {
  const R = 6371000;
  const φ1 = p1.lat * Math.PI / 180;
  const φ2 = p2.lat * Math.PI / 180;
  const Δφ = (p2.lat - p1.lat) * Math.PI / 180;
  const Δλ = (p2.lng - p1.lng) * Math.PI / 180;
  const a = Math.sin(Δφ/2)**2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
};

// ---- Работа с медиафайлом ----
const triggerFileInput = () => fileInput.value.click();
const handleFileSelect = (e) => {
  if (e.target.files[0]) processFile(e.target.files[0]);
};
const handleDrop = (e) => {
  dragActive.value = false;
  if (e.dataTransfer.files[0]) processFile(e.dataTransfer.files[0]);
};

const processFile = (file) => {
  const allowed = ['image/jpeg', 'image/png', 'video/mp4', 'video/avi'];
  if (!allowed.includes(file.type)) return alert('Неподдерживаемый формат');
  if (file.size > 200 * 1024 * 1024) return alert('Файл не должен превышать 200 МБ');
  form.mediaFile = file;
  form.mediaFileName = file.name;
  if (form.mediaPreview) URL.revokeObjectURL(form.mediaPreview);
  form.mediaPreview = URL.createObjectURL(file);
  calibrationPoints.value = [];
  form.startX = form.startY = form.endX = form.endY = null;
  form.realSize = null;
  form.calibrationAuto = null;
  nextTick(() => updateCanvas());
};

// ---- Файл весов ----
const handleWeightsFile = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  // Проверка расширения
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pt', 'pth', 'h5', 'onnx'].includes(ext)) {
    alert('Поддерживаются только .pt, .pth, .h5, .onnx');
    e.target.value = '';
    return;
  }
  form.weightsFile = file;
  form.weightsFileName = file.name;
};

// ---- Калибровка на изображении ----
const updateCanvas = () => {
  if (!staticCanvas.value || !staticImage.value) return;
  const img = staticImage.value;
  const canvas = staticCanvas.value;
  const rect = img.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (calibrationPoints.value.length === 0) return;
  calibrationPoints.value.forEach((p, idx) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, 2 * Math.PI);
    ctx.fillStyle = idx === 0 ? 'red' : 'lime';
    ctx.fill();
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = 'white';
    ctx.font = 'bold 14px sans-serif';
    ctx.fillText(idx === 0 ? 'A' : 'B', p.x - 5, p.y - 5);
  });
  if (calibrationPoints.value.length === 2) {
    const p1 = calibrationPoints.value[0];
    const p2 = calibrationPoints.value[1];
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = 'yellow';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
  }
};

const getImageClickCoords = (event) => {
  const img = staticImage.value;
  if (!img) return null;
  const rect = img.getBoundingClientRect();
  let clickX = event.clientX - rect.left;
  let clickY = event.clientY - rect.top;
  clickX = Math.min(Math.max(0, clickX), rect.width);
  clickY = Math.min(Math.max(0, clickY), rect.height);
  return { x: clickX, y: clickY };
};

const handleImageClick = (event) => {
  if (!isImage.value) return;
  const coords = getImageClickCoords(event);
  if (!coords) return;
  if (calibrationPoints.value.length === 0) {
    calibrationPoints.value = [coords];
    form.startX = coords.x; form.startY = coords.y;
    form.endX = form.endY = null;
  } else if (calibrationPoints.value.length === 1) {
    calibrationPoints.value.push(coords);
    form.endX = coords.x; form.endY = coords.y;
  } else {
    calibrationPoints.value = [coords];
    form.startX = coords.x; form.startY = coords.y;
    form.endX = form.endY = null;
  }
  updateCanvas();
};

const handleCanvasClick = (event) => {
  if (staticImage.value) {
    const rect = staticCanvas.value.getBoundingClientRect();
    const fakeEvent = {
      clientX: rect.left + event.offsetX,
      clientY: rect.top + event.offsetY
    };
    handleImageClick(fakeEvent);
  }
};

const clearCalibrationPoints = () => {
  calibrationPoints.value = [];
  form.startX = form.startY = form.endX = form.endY = null;
  form.realSize = null;
  updateCanvas();
};

// ---- Спутниковый режим ----
const fetchSatelliteImageForArea = async (points) => {
  if (points.length !== 4) return;
  const lats = points.map(p => p.lat);
  const lngs = points.map(p => p.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const bbox = `${minLng},${minLat},${maxLng},${maxLat}`;
  const width = 800;
  const height = 600;

  const url = `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=${bbox}&bboxSR=4326&size=${width},${height}&format=png&f=image`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Ошибка загрузки снимка');
    const imgBlob = await response.blob();
    const file = new File([imgBlob], 'satellite_image.png', { type: 'image/png' });
    form.mediaFile = file;
    form.mediaFileName = 'satellite_image.png';
    if (form.mediaPreview) URL.revokeObjectURL(form.mediaPreview);
    form.mediaPreview = URL.createObjectURL(file);
    const distanceMeters = haversineDistance({ lat: minLat, lng: minLng }, { lat: minLat, lng: maxLng });
    const pixelDistance = width;
    form.calibrationAuto = {
      realSize: distanceMeters,
      pixelDistance: pixelDistance,
      startX: 0, startY: 0, endX: width, endY: 0
    };
    form.startX = 0; form.startY = 0; form.endX = width; form.endY = 0;
    form.realSize = distanceMeters;
    satellitePoints.value = [...points];
    form.satelliteArea = points;
  } catch (err) {
    console.error(err);
    alert('Не удалось загрузить спутниковый снимок. Проверьте интернет или выберите другую область.');
    form.mediaPreview = null;
    form.mediaFile = null;
    form.calibrationAuto = null;
  }
};

const clearSatellitePoints = () => {
  satellitePoints.value = [];
  form.satelliteArea = null;
  if (satMarkers.length) satMarkers.forEach(m => m.remove());
  satMarkers = [];
  if (satPolygon) { satPolygon.remove(); satPolygon = null; }
  if (form.mediaPreview) URL.revokeObjectURL(form.mediaPreview);
  form.mediaPreview = null;
  form.mediaFile = null;
  form.calibrationAuto = null;
  form.startX = form.startY = form.endX = form.endY = null;
  form.realSize = null;
};

const updateSatelliteOverlay = () => {
  if (!map) return;
  if (satMarkers.length) satMarkers.forEach(m => m.remove());
  satMarkers = [];
  if (satPolygon) satPolygon.remove();

  satellitePoints.value.forEach((p, idx) => {
    const marker = L.marker([p.lat, p.lng], {
      icon: L.divIcon({
        html: `<div style="background: ${idx === 0 ? 'red' : idx === 1 ? 'orange' : idx === 2 ? 'blue' : 'purple'}; width:12px; height:12px; border-radius:50%; border:2px solid white;"></div>`,
        iconSize: [12, 12]
      })
    }).addTo(map);
    satMarkers.push(marker);
  });

  if (satellitePoints.value.length === 4) {
    const latLngs = satellitePoints.value.map(p => [p.lat, p.lng]);
    satPolygon = L.polygon(latLngs, { color: 'red', weight: 2, fillOpacity: 0.2 }).addTo(map);
    fetchSatelliteImageForArea(satellitePoints.value);
  }
};

// ---- Карта (наземный режим) ----
const updateGroundOverlay = () => {
  if (!map) return;
  if (mapMarkers.length) mapMarkers.forEach(m => m.remove());
  mapMarkers = [];
  if (mapLine) mapLine.remove();

  form.mapPoints.forEach((p, idx) => {
    const marker = L.marker([p.lat, p.lng], {
      icon: L.divIcon({
        html: `<div style="background:${idx === 0 ? 'red' : 'lime'}; width:12px; height:12px; border-radius:50%; border:2px solid white;"></div>`,
        iconSize: [12, 12]
      })
    }).addTo(map);
    mapMarkers.push(marker);
  });

  if (form.mapPoints.length === 2) {
    const [a, b] = form.mapPoints;
    mapLine = L.polyline([[a.lat, a.lng], [b.lat, b.lng]], { color: 'blue', weight: 3, dashArray: '5,5' }).addTo(map);
  }
};

const clearMapPoints = () => {
  form.mapPoints = [];
  if (mapMarkers.length) mapMarkers.forEach(m => m.remove());
  mapMarkers = [];
  if (mapLine) { mapLine.remove(); mapLine = null; }
};

// ---- Инициализация карты ----
async function initMap() {
  if (!window.L) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
    await new Promise(resolve => {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
  }
  if (map) return;
  const container = document.getElementById('map');
  if (!container) return;
  map = L.map('map', { attributionControl: false }).setView([52.2864, 104.2807], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {}).addTo(map);

  map.on('click', (e) => {
    const { lat, lng } = e.latlng;
    if (isSatelliteMode.value) {
      if (satellitePoints.value.length < 4) {
        satellitePoints.value.push({ lat, lng });
        updateSatelliteOverlay();
      } else {
        alert('Вы уже выбрали 4 точки. Очистите их, чтобы задать новую область.');
      }
    } else {
      if (form.mapPoints.length === 0) {
        form.mapPoints.push({ lat, lng });
        updateGroundOverlay();
      } else if (form.mapPoints.length === 1) {
        form.mapPoints.push({ lat, lng });
        updateGroundOverlay();
      } else {
        clearMapPoints();
        form.mapPoints.push({ lat, lng });
        updateGroundOverlay();
      }
    }
  });
}

// ---- Вычисляемые свойства ----
const isImage = computed(() => form.mediaFile && form.mediaFile.type.startsWith('image/'));
const isVideo = computed(() => form.mediaFile && form.mediaFile.type.startsWith('video/'));
const pixelDistance = computed(() => {
  if (calibrationPoints.value.length !== 2) return 0;
  const [a, b] = calibrationPoints.value;
  return Math.hypot(a.x - b.x, a.y - b.y);
});
const mapDistance = computed(() => {
  if (form.mapPoints.length !== 2) return 0;
  const [a, b] = form.mapPoints;
  return haversineDistance(a, b);
});
const timeEstimate = computed(() => {
  if (form.fileType === 'satellite') {
    return { fast: '~15 мин/фото', quality: '~30 мин/фото', high: '~60 мин/фото' };
  } else {
    return { fast: '~30 сек/кадр', quality: '~1 мин/кадр', high: '~5 мин/кадр' };
  }
});

// ---- Отправка задачи ----
const submitTask = async () => {
  if (!form.title.trim()) return alert('Введите название задачи');
  if (isSatelliteMode.value) {
    if (satellitePoints.value.length !== 4) return alert('Для спутникового снимка необходимо выбрать 4 угловые точки на карте');
    if (!form.mediaFile) return alert('Спутниковый снимок не загружен. Попробуйте очистить точки и выбрать заново.');
  } else {
    if (!form.mediaFile) return alert('Выберите файл');
    if (calibrationPoints.value.length === 2 && !form.realSize) {
      if (!confirm('Вы указали опорный отрезок на изображении, но не ввели реальный размер. Измерения размеров объектов будут недоступны. Продолжить?')) return;
    }
  }

  isSubmitting.value = true;

  try {
    // Собираем данные в FormData
    const payload = new FormData();
    payload.append('title', form.title);
    payload.append('description', form.description || '');
    payload.append('quality', form.quality);
    payload.append('file_type', form.fileType);
    payload.append('media_file', form.mediaFile);
    if (form.weightsFile) {
      payload.append('weights_file', form.weightsFile);
    }
    // Калибровка
    if (!isSatelliteMode.value && calibrationPoints.value.length === 2 && form.realSize) {
      payload.append('calibration_start_x', form.startX);
      payload.append('calibration_start_y', form.startY);
      payload.append('calibration_end_x', form.endX);
      payload.append('calibration_end_y', form.endY);
      payload.append('calibration_real_size', form.realSize);
    } else if (isSatelliteMode.value && form.calibrationAuto) {
      payload.append('calibration_start_x', form.calibrationAuto.startX);
      payload.append('calibration_start_y', form.calibrationAuto.startY);
      payload.append('calibration_end_x', form.calibrationAuto.endX);
      payload.append('calibration_end_y', form.calibrationAuto.endY);
      payload.append('calibration_real_size', form.calibrationAuto.realSize);
    }
    // Точки на карте
    if (form.mapPoints.length === 2) {
      payload.append('map_points', JSON.stringify(form.mapPoints));
    }
    if (isSatelliteMode.value && satellitePoints.value.length === 4) {
      payload.append('satellite_area', JSON.stringify(satellitePoints.value));
    }

    // Отправка на сервер
    const response = await createTask(payload);
    // Сохраняем задачу в store (опционально)
    taskStore.addTask(response.data);
    alert('Задача успешно добавлена!');
    router.push('/');
  } catch (error) {
    console.error('Ошибка при создании задачи:', error);
    alert('Не удалось создать задачу. Попробуйте ещё раз.');
  } finally {
    isSubmitting.value = false;
  }
};

const goBack = () => router.push('/');

// ---- Слежение за переключением режима ----
watch(() => form.fileType, (newVal) => {
  if (map) {
    if (mapMarkers.length) mapMarkers.forEach(m => m.remove());
    if (mapLine) mapLine.remove();
    if (satMarkers.length) satMarkers.forEach(m => m.remove());
    if (satPolygon) satPolygon.remove();
    mapMarkers = [];
    satMarkers = [];
    mapLine = null;
    satPolygon = null;
  }
  if (newVal === 'satellite') {
    if (form.mediaPreview && !form.calibrationAuto) URL.revokeObjectURL(form.mediaPreview);
    form.mediaFile = null;
    form.mediaFileName = '';
    if (!form.calibrationAuto) form.mediaPreview = null;
    calibrationPoints.value = [];
    form.startX = form.startY = form.endX = form.endY = null;
    form.realSize = null;
    clearMapPoints();
    clearSatellitePoints();
  } else {
    clearSatellitePoints();
    form.calibrationAuto = null;
    if (form.mediaPreview && !form.mediaFile) URL.revokeObjectURL(form.mediaPreview);
    form.mediaPreview = null;
    form.mediaFile = null;
    calibrationPoints.value = [];
    form.startX = form.startY = form.endX = form.endY = null;
    form.realSize = null;
    clearMapPoints();
  }
});

watch([() => form.mediaPreview, isImage], async () => {
  if (!isSatelliteMode.value && isImage.value && form.mediaPreview) {
    await nextTick();
    updateCanvas();
  }
});

// ---- Жизненный цикл ----
onMounted(async () => {
  await nextTick();
  await initMap();
  window.addEventListener('resize', () => updateCanvas());
});
onUnmounted(() => {
  if (map) map.remove();
  if (form.mediaPreview) URL.revokeObjectURL(form.mediaPreview);
  window.removeEventListener('resize', () => updateCanvas());
});
</script>

<style scoped>
.dropzone { cursor: pointer; transition: 0.2s; }
.dropzone:hover { background-color: #f8f9fa; border-color: #86b7fe; }
.image-container { position: relative; display: inline-block; max-width: 100%; }
.static-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: auto; cursor: crosshair; }
.map-container { border-radius: 0.375rem; overflow: hidden; }
</style>