<template>
  <div class="reply-box" :class="{ 'reply-locked': disabled }">
    <!-- Lock overlay -->
    <div v-if="disabled" class="reply-lock-overlay">
      <span>{{ disabledMessage || '🔒 لا يمكنك الرد حالياً' }}</span>
    </div>

    <!-- File preview -->
    <div v-if="selectedFile" class="reply-file-preview">
      <img v-if="isImage" :src="filePreview" class="reply-file-thumb" />
      <span v-else class="reply-file-name">📎 {{ selectedFile.name }}</span>
      <button class="reply-file-remove" @click="removeFile">✕</button>
    </div>

    <!-- Recording indicator -->
    <div v-if="isRecording || isPaused" class="reply-recording" :class="{ danger: nearLimit }">
      <span class="recording-dot" :class="{ paused: isPaused }"></span>
      <span class="recording-text">
        {{ isPaused ? 'متوقف مؤقت' : 'جاري التسجيل' }}... {{ recordingTime }}
        <span v-if="nearLimit" class="recording-limit">/ {{ formatTime(MAX_SECONDS) }}</span>
      </span>
      <button class="recording-action" @click="togglePause" :title="isPaused ? 'استئناف' : 'إيقاف مؤقت'">
        {{ isPaused ? '▶' : '⏸' }}
      </button>
      <button class="recording-cancel" @click="cancelRecording" title="إلغاء">✕</button>
    </div>

    <div class="reply-row">
      <!-- Attach button -->
      <button class="reply-attach-btn" @click="openFilePicker" title="إرفاق ملف">📎</button>
      <input
        ref="fileInput"
        type="file"
        accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar"
        style="display:none"
        @change="onFileSelected"
      />

      <!-- Voice record button (supports push-to-talk) -->
      <button
        class="reply-voice-btn"
        :class="{ recording: isRecording, paused: isPaused }"
        @click="onVoiceClick"
        @mousedown="onVoicePressStart"
        @mouseup="onVoicePressEnd"
        @mouseleave="onVoicePressEnd"
        @touchstart.prevent="onVoicePressStart"
        @touchend.prevent="onVoicePressEnd"
        @touchcancel.prevent="onVoicePressEnd"
        title="اضغط للتسجيل / اضغط مستمر للتسجيل السريع"
      >🎤</button>

      <!-- Text input -->
      <textarea
        ref="inputRef"
        v-model="text"
        @keydown="onKeydown"
        placeholder="اكتب رسالة..."
        class="reply-input"
        rows="2"
        dir="auto"
      ></textarea>

      <!-- Send button -->
      <button class="reply-send-btn" @click="send" :disabled="(!text.trim() && !selectedFile && !audioBlob && !isRecording) || sending">
        {{ sending ? '...' : isRecording ? '⏹' : '📤' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';

const emit = defineEmits(['send', 'send-file']);
const text = ref('');
const inputRef = ref(null);
const fileInput = ref(null);
const selectedFile = ref(null);
const filePreview = ref('');
const props = defineProps({
  sending: Boolean,
  disabled: { type: Boolean, default: false },
  disabledMessage: { type: String, default: '' },
});

const MAX_SECONDS = 300; // 5 minutes
const MAX_BYTES = 15 * 1024 * 1024; // 15 MB (Meta limit is 16)
const WARN_BEFORE = 30; // warn 30s before limit

const isRecording = ref(false);
const isPaused = ref(false);
const audioBlob = ref(null);
const recordingTime = ref('0:00');
let mediaRecorder = null;
let mediaStream = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;
let pressTimer = null;
let pressedLong = false;
let warnedLimit = false;

const isImage = computed(() => {
  return selectedFile.value && selectedFile.value.type.startsWith('image/');
});

const nearLimit = computed(() => recordingSeconds >= MAX_SECONDS - WARN_BEFORE);

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m + ':' + (s < 10 ? '0' : '') + s;
}

function openFilePicker() {
  fileInput.value?.click();
}

function onFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > MAX_BYTES) {
    alert('حجم الملف كبير جداً (الحد الأقصى 15MB)');
    e.target.value = '';
    return;
  }
  selectedFile.value = file;
  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (ev) => { filePreview.value = ev.target.result; };
    reader.readAsDataURL(file);
  }
}

function removeFile() {
  selectedFile.value = null;
  filePreview.value = '';
  if (fileInput.value) fileInput.value.value = '';
}

// --- Voice recording ---

let recordedMime = 'audio/webm;codecs=opus';
let recordedExt = 'webm';

function pickSupportedMime() {
  const candidates = [
    { mime: 'audio/ogg;codecs=opus', ext: 'ogg' },
    { mime: 'audio/webm;codecs=opus', ext: 'webm' },
    { mime: 'audio/mp4;codecs=mp4a.40.2', ext: 'm4a' },
    { mime: 'audio/mp4', ext: 'm4a' },
    { mime: 'audio/webm', ext: 'webm' },
  ];
  for (const c of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(c.mime)) return c;
  }
  return { mime: '', ext: 'webm' };
}

async function startRecording() {
  if (isRecording.value) return;
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    const picked = pickSupportedMime();
    recordedMime = picked.mime || 'audio/webm';
    recordedExt = picked.ext;
    mediaRecorder = picked.mime
      ? new MediaRecorder(mediaStream, { mimeType: picked.mime })
      : new MediaRecorder(mediaStream);
    audioChunks = [];
    recordingSeconds = 0;
    warnedLimit = false;
    isPaused.value = false;

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: recordedMime });
      stopStream();
      clearInterval(recordingTimer);
      if (blob.size > MAX_BYTES) {
        alert('حجم التسجيل تجاوز الحد الأقصى (15MB)');
        audioBlob.value = null;
      } else if (blob.size > 0) {
        audioBlob.value = blob;
        sendAudio();
      }
    };

    mediaRecorder.start();
    isRecording.value = true;

    recordingTimer = setInterval(() => {
      if (isPaused.value) return;
      recordingSeconds++;
      recordingTime.value = formatTime(recordingSeconds);
      if (!warnedLimit && recordingSeconds === MAX_SECONDS - WARN_BEFORE) {
        warnedLimit = true;
      }
      if (recordingSeconds >= MAX_SECONDS) stopRecording();
    }, 1000);
  } catch (err) {
    alert('لا يمكن الوصول للميكروفون');
  }
}

function stopStream() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
    mediaStream = null;
  }
}

function stopRecording() {
  if (mediaRecorder && (mediaRecorder.state === 'recording' || mediaRecorder.state === 'paused')) {
    try { mediaRecorder.stop(); } catch {}
  }
  isRecording.value = false;
  isPaused.value = false;
}

function togglePause() {
  if (!mediaRecorder) return;
  if (mediaRecorder.state === 'recording') {
    try { mediaRecorder.pause(); isPaused.value = true; } catch {}
  } else if (mediaRecorder.state === 'paused') {
    try { mediaRecorder.resume(); isPaused.value = false; } catch {}
  }
}

function cancelRecording() {
  if (mediaRecorder && (mediaRecorder.state === 'recording' || mediaRecorder.state === 'paused')) {
    mediaRecorder.ondataavailable = null;
    mediaRecorder.onstop = () => {};
    try { mediaRecorder.stop(); } catch {}
  }
  stopStream();
  isRecording.value = false;
  isPaused.value = false;
  audioBlob.value = null;
  audioChunks = [];
  clearInterval(recordingTimer);
  recordingTime.value = '0:00';
}

function sendAudio() {
  if (audioBlob.value) {
    const file = new File([audioBlob.value], 'voice_' + Date.now() + '.' + recordedExt, { type: recordedMime });
    emit('send-file', { file, message: '' });
    audioBlob.value = null;
    recordingTime.value = '0:00';
  }
}

// --- Mic button interactions ---
// Short click (< 400ms): toggle record/stop
// Long press: record while held (push-to-talk)

function onVoicePressStart(e) {
  if (isRecording.value) return;
  pressedLong = false;
  pressTimer = setTimeout(async () => {
    pressedLong = true;
    await startRecording();
  }, 400);
}

function onVoicePressEnd() {
  if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
  if (pressedLong && isRecording.value) {
    stopRecording();
  }
  pressedLong = false;
}

function onVoiceClick() {
  if (pressedLong) return; // handled by press end
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
}

function send() {
  if (isRecording.value) {
    stopRecording();
    return;
  }
  if (selectedFile.value) {
    emit('send-file', { file: selectedFile.value, message: text.value });
    text.value = '';
    removeFile();
  } else if (text.value.trim()) {
    emit('send', text.value);
    text.value = '';
  }
  inputRef.value?.focus();
}

function onKeydown(e) {
  if (e.ctrlKey && e.key === 'Enter') {
    send();
  }
}

onUnmounted(() => {
  cancelRecording();
});
</script>

<style scoped>
.reply-box {
  position: relative;
}
.reply-box.reply-locked {
  opacity: 0.5;
  pointer-events: none;
}
.reply-lock-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(254, 226, 226, 0.85);
  color: #991b1b;
  font-size: 13px;
  font-weight: 600;
  z-index: 5;
  pointer-events: auto;
  cursor: not-allowed;
}
</style>
