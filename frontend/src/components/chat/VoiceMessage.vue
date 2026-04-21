<template>
  <div class="voice-msg" :class="{ outgoing: isOutgoing }">
    <button class="voice-btn" @click="toggle" :aria-label="isPlaying ? 'إيقاف' : 'تشغيل'">
      <svg v-if="!isPlaying" viewBox="0 0 24 24" width="20" height="20">
        <path fill="currentColor" d="M8 5v14l11-7z" />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="20" height="20">
        <path fill="currentColor" d="M6 5h4v14H6zM14 5h4v14h-4z" />
      </svg>
    </button>

    <div class="voice-body">
      <div class="voice-track" ref="trackRef" @click="seek">
        <!-- Waveform bars -->
        <div v-if="waveform.length" class="voice-waveform">
          <span
            v-for="(h, i) in waveform"
            :key="i"
            class="wave-bar"
            :class="{ played: (i / waveform.length) * 100 <= percent }"
            :style="{ height: (h * 100) + '%' }"
          ></span>
        </div>
        <!-- Fallback progress bar -->
        <template v-else>
          <div class="voice-progress" :style="{ width: percent + '%' }"></div>
          <div class="voice-thumb" :style="thumbStyle"></div>
        </template>
      </div>
      <div class="voice-meta">
        <span class="voice-time">{{ displayTime }}</span>
        <div class="voice-actions">
          <button v-if="duration" class="voice-speed" @click.stop="cycleSpeed">{{ speed }}x</button>
          <button v-if="showTranscribe" class="voice-transcribe" @click.stop="transcribe" :disabled="transcribing" title="تفريغ نصي">
            {{ transcribing ? '...' : 'نص' }}
          </button>
        </div>
      </div>
      <div v-if="transcript" class="voice-transcript">{{ transcript }}</div>
    </div>

    <span v-if="heard && !isOutgoing" class="voice-heard" title="تم الاستماع">🎤</span>

    <audio
      ref="audioRef"
      :src="src"
      preload="auto"
      crossorigin="anonymous"
      @loadedmetadata="onMeta"
      @durationchange="onMeta"
      @canplay="onMeta"
      @loadeddata="onMeta"
      @timeupdate="onTime"
      @ended="onEnded"
      @play="onPlay"
      @pause="isPlaying = false"
      @error="onError"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  src: { type: String, required: true },
  isOutgoing: { type: Boolean, default: false },
  messageId: { type: String, default: '' },
});

const audioRef = ref(null);
const trackRef = ref(null);
const isPlaying = ref(false);
const duration = ref(0);
const current = ref(0);
const errored = ref(false);
const speed = ref(1);
const waveform = ref([]);
const heard = ref(false);
const transcript = ref('');
const transcribing = ref(false);

const isRtl = typeof document !== 'undefined'
  && (document.dir === 'rtl' || document.documentElement?.dir === 'rtl');

const storageKey = computed(() => 'wa_heard_' + (props.messageId || props.src));
const transcriptKey = computed(() => 'wa_transcript_' + (props.messageId || props.src));
const showTranscribe = computed(() => !transcript.value && duration.value > 0);

onMounted(() => {
  try {
    if (!props.isOutgoing && localStorage.getItem(storageKey.value)) heard.value = true;
    const cached = localStorage.getItem(transcriptKey.value);
    if (cached) transcript.value = cached;
  } catch {}
  extractWaveform();
});

const percent = computed(() => {
  if (!duration.value || !isFinite(duration.value)) return 0;
  return Math.min(100, (current.value / duration.value) * 100);
});

const thumbStyle = computed(() => ({
  [isRtl ? 'right' : 'left']: percent.value + '%',
}));

const displayTime = computed(() => {
  if (errored.value) return '--:--';
  const t = isPlaying.value || current.value > 0 ? current.value : duration.value;
  if (!t || !isFinite(t)) return '0:00';
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return m + ':' + (s < 10 ? '0' : '') + s;
});

function toggle() {
  const a = audioRef.value;
  if (!a) return;
  if (a.paused) {
    a.play().catch(() => { errored.value = true; });
  } else {
    a.pause();
  }
}

function onPlay() {
  isPlaying.value = true;
  if (audioRef.value) audioRef.value.playbackRate = speed.value;
  if (!props.isOutgoing && !heard.value) {
    heard.value = true;
    try { localStorage.setItem(storageKey.value, '1'); } catch {}
  }
}

function onMeta() {
  const a = audioRef.value;
  if (!a) return;
  const d = a.duration;
  if (d && isFinite(d)) {
    duration.value = d;
    return;
  }
  // WhatsApp OGG/OPUS often reports Infinity until fully loaded.
  // Force browser to compute real duration by seeking to a huge value,
  // it will clamp to the real end and fire durationchange.
  if (d === Infinity && !a._wa_seek_tried) {
    a._wa_seek_tried = true;
    try {
      a.currentTime = 1e9;
      setTimeout(() => {
        try { a.currentTime = 0; } catch {}
      }, 80);
    } catch {}
  }
}

function onTime() {
  current.value = audioRef.value?.currentTime || 0;
}

function onEnded() {
  isPlaying.value = false;
  current.value = 0;
}

function onError() {
  errored.value = true;
}

function cycleSpeed() {
  const rates = [1, 1.5, 2];
  speed.value = rates[(rates.indexOf(speed.value) + 1) % rates.length];
  if (audioRef.value) audioRef.value.playbackRate = speed.value;
}

function seek(e) {
  const a = audioRef.value;
  const track = trackRef.value;
  if (!a || !track || !duration.value) return;
  const rect = track.getBoundingClientRect();
  let ratio = (e.clientX - rect.left) / rect.width;
  if (isRtl) ratio = 1 - ratio;
  ratio = Math.max(0, Math.min(1, ratio));
  a.currentTime = ratio * duration.value;
}

async function extractWaveform() {
  try {
    if (!window.AudioContext && !window.webkitAudioContext) return;
    const res = await fetch(props.src);
    if (!res.ok) return;
    const buf = await res.arrayBuffer();
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const decoded = await ctx.decodeAudioData(buf);
    const ch = decoded.getChannelData(0);
    const bars = 40;
    const block = Math.floor(ch.length / bars);
    const peaks = [];
    let max = 0;
    for (let i = 0; i < bars; i++) {
      let sum = 0;
      for (let j = 0; j < block; j++) sum += Math.abs(ch[i * block + j] || 0);
      const v = sum / block;
      peaks.push(v);
      if (v > max) max = v;
    }
    waveform.value = max > 0 ? peaks.map(p => Math.max(0.15, p / max)) : [];
    ctx.close?.();
  } catch {
    // silent fallback to progress bar
  }
}

async function transcribe() {
  if (transcribing.value || !props.messageId) return;
  transcribing.value = true;
  try {
    const r = await fetch('/api/method/whatsapp_inbox.api.transcribe_voice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.frappe?.csrf_token || '',
      },
      body: 'message_id=' + encodeURIComponent(props.messageId),
    });
    const data = await r.json();
    const text = data.message?.text || data.message?.transcript || '';
    if (text) {
      transcript.value = text;
      try { localStorage.setItem(transcriptKey.value, text); } catch {}
    } else if (data.message?.error) {
      alert('فشل التفريغ: ' + data.message.error);
    }
  } catch (e) {
    alert('تعذر الاتصال بخدمة التفريغ');
  } finally {
    transcribing.value = false;
  }
}
</script>

<style scoped>
.voice-msg {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 240px;
  max-width: 320px;
  padding: 4px 2px;
}
.voice-btn {
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #00a884;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  transition: background 0.15s;
}
.voice-btn:hover { background: #008f72; }
.voice-msg.outgoing .voice-btn { background: #128c7e; }
.voice-msg.outgoing .voice-btn:hover { background: #0e6f63; }

.voice-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.voice-track {
  position: relative;
  height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.voice-waveform {
  display: flex;
  align-items: center;
  gap: 2px;
  width: 100%;
  height: 100%;
  direction: ltr;
}
.wave-bar {
  flex: 1;
  min-width: 2px;
  background: rgba(0,0,0,0.25);
  border-radius: 1px;
  transition: background 0.1s;
}
.wave-bar.played { background: #00a884; }
.voice-msg.outgoing .wave-bar.played { background: #128c7e; }

.voice-progress {
  position: absolute;
  top: 50%;
  height: 4px;
  margin-top: -2px;
  left: 0;
  background: #00a884;
  border-radius: 2px;
  transition: width 0.1s linear;
}
[dir="rtl"] .voice-progress { left: auto; right: 0; }
.voice-thumb {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  background: #00a884;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.voice-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #667781;
}
.voice-time { font-variant-numeric: tabular-nums; }
.voice-actions { display: flex; gap: 4px; }
.voice-speed, .voice-transcribe {
  border: none;
  background: rgba(0,0,0,0.06);
  color: #3b4a54;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}
.voice-speed:hover, .voice-transcribe:hover { background: rgba(0,0,0,0.12); }
.voice-transcribe:disabled { opacity: 0.5; cursor: wait; }

.voice-transcript {
  font-size: 12px;
  color: #3b4a54;
  padding: 4px 6px;
  background: rgba(0,0,0,0.04);
  border-radius: 4px;
  line-height: 1.4;
  margin-top: 2px;
}

.voice-heard {
  font-size: 14px;
  color: #53bdeb;
  margin-inline-start: 4px;
}
</style>
