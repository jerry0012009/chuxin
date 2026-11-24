<script setup lang="ts">
import { AlertTriangle, CheckCircle, MessageSquareText } from 'lucide-vue-next'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import { getAllProfiles, getRiskAlerts, handleRiskAlert } from '@/db/api'
import type { Profile, RiskAlert } from '@/types'

type AlertTab = 'pending' | 'handled'

interface AlertViewModel extends RiskAlert {
  patient_name: string
}

const { state: authState } = useAuthSession()

const loading = ref(true)
const loadFailed = ref(false)
const saving = ref(false)
const activeTab = ref<AlertTab>('pending')
const pendingAlerts = ref<AlertViewModel[]>([])
const handledAlerts = ref<AlertViewModel[]>([])
const selectedAlert = ref<AlertViewModel | null>(null)
const notesInput = ref<HTMLTextAreaElement | null>(null)
const pendingTab = ref<HTMLButtonElement | null>(null)
let handleTrigger: HTMLElement | null = null
const notes = ref('')
const statusMessage = ref('')
const errorMessage = ref('')
const toastMessage = computed(() => errorMessage.value || statusMessage.value)
const toastTone = computed(() => (errorMessage.value ? 'error' : 'success'))
let toastTimer: number | null = null

watch(toastMessage, (message) => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  if (!message) {
    toastTimer = null
    return
  }
  toastTimer = window.setTimeout(() => {
    statusMessage.value = ''
    errorMessage.value = ''
    toastTimer = null
  }, 2200)
})

const latestAlertDate = computed(() =>
  [...pendingAlerts.value, ...handledAlerts.value].reduce((latest, item) => item.created_at > latest ? item.created_at : latest, ''),
)

const currentAlerts = computed(() => (activeTab.value === 'pending' ? pendingAlerts.value : handledAlerts.value))

const loadAlerts = async () => {
  loading.value = true
  loadFailed.value = false
  errorMessage.value = ''
  try {
    const [unhandled, handled, profiles] = await Promise.all([
      getRiskAlerts(false),
      getRiskAlerts(true),
      getAllProfiles().catch(() => [] as Profile[]),
    ])
    const profileMap = new Map(profiles.map((item) => [item.id, item]))
    const enrich = (alert: RiskAlert): AlertViewModel => {
      const profile = profileMap.get(alert.patient_id)
      return {
        ...alert,
        patient_name: profile?.full_name || profile?.username || alert.patient_id,
      }
    }
    pendingAlerts.value = unhandled.map(enrich).sort((a, b) => b.risk_level - a.risk_level || b.created_at.localeCompare(a.created_at))
    handledAlerts.value = handled.map(enrich).sort((a, b) => (b.handled_at || b.created_at).localeCompare(a.handled_at || a.created_at))
  } catch (error) {
    pendingAlerts.value = []
    handledAlerts.value = []
    loadFailed.value = true
    errorMessage.value = error instanceof Error ? error.message : '加载预警失败'
  } finally {
    loading.value = false
  }
}

const riskText = (riskLevel: number) => {
  if (riskLevel >= 8) return '高风险'
  if (riskLevel >= 5) return '中风险'
  return '低风险'
}

const openHandleDialog = async (alert: AlertViewModel, event: MouseEvent) => {
  handleTrigger = event.currentTarget as HTMLElement
  selectedAlert.value = alert
  notes.value = ''
  statusMessage.value = ''
  errorMessage.value = ''
  await nextTick()
  notesInput.value?.focus()
}

const closeDialog = (handled = false) => {
  selectedAlert.value = null
  notes.value = ''
  void nextTick(() => (handled ? pendingTab.value : handleTrigger)?.focus())
}

const markHandled = async () => {
  if (!authState.user || !selectedAlert.value) return
  saving.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    await handleRiskAlert(selectedAlert.value.id, authState.user.id, notes.value.trim() || undefined)
    statusMessage.value = '预警已处理'
    closeDialog(true)
    await loadAlerts()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '处理失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadAlerts()
})

onUnmounted(() => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="space-y-6">
    <Transition name="toast-slide">
      <div
        v-if="toastMessage"
        data-testid="doctor-alerts-toast"
        :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
        class="fixed left-1/2 top-6 z-[80] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full px-5 py-3 text-sm font-medium text-white shadow-xl"
      >
        {{ toastMessage }}
      </div>
    </Transition>

    <header class="alert-queue-title">
      <h1>风险预警</h1>
      <p v-if="latestAlertDate">最新预警 · {{ new Date(latestAlertDate).toLocaleString('zh-CN') }}</p>
    </header>

    <div class="service-tabs" role="group" aria-label="预警状态">
      <button
        ref="pendingTab"
        data-testid="alerts-tab-pending"
        class="service-tab"
        :aria-pressed="activeTab === 'pending'"
        type="button"
        @click="activeTab = 'pending'"
      >
        待处理
        <span v-if="!loading && !loadFailed" class="alert-tab-count">{{ pendingAlerts.length }}</span>
      </button>
      <button
        data-testid="alerts-tab-handled"
        class="service-tab"
        :aria-pressed="activeTab === 'handled'"
        type="button"
        @click="activeTab = 'handled'"
      >
        已处理
        <span v-if="!loading && !loadFailed" class="alert-tab-count">{{ handledAlerts.length }}</span>
      </button>
    </div>

    <p v-if="loading" role="status" class="alert-queue-state">正在加载预警列表…</p>
    <div v-else-if="loadFailed" role="alert" class="alert-queue-state">预警列表暂时无法加载。<button class="service-button service-outline" type="button" @click="loadAlerts">重试</button></div>
    <p v-else-if="!currentAlerts.length" class="alert-queue-state"><CheckCircle v-if="activeTab === 'pending'" aria-hidden="true" /><AlertTriangle v-else aria-hidden="true" />{{ activeTab === 'pending' ? '暂无待处理预警' : '暂无已处理预警' }}</p>
    <ul v-else class="alert-queue-list" :aria-label="activeTab === 'pending' ? '待处理预警' : '已处理预警'">
      <li v-for="item in currentAlerts" :key="item.id" class="alert-queue-row">
        <h2>{{ item.patient_name }}</h2>
        <div class="alert-queue-status">
          <ServiceStatus :tone="item.risk_level >= 8 ? 'danger' : item.risk_level >= 5 ? 'attention' : 'idle'">{{ riskText(item.risk_level) }} {{ item.risk_level }}/10</ServiceStatus>
          <ServiceStatus v-if="item.is_handled" tone="done">已处理</ServiceStatus>
        </div>
        <p class="alert-queue-time">{{ item.alert_type }} · <time :datetime="item.created_at">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</time></p>
        <div class="alert-queue-detail">
          <p>{{ item.description }}</p>
          <p v-if="item.data_source">数据来源：{{ item.data_source }}</p>
          <p v-if="item.is_handled && item.notes">处理备注：{{ item.notes }}</p>
          <p v-if="item.is_handled && item.handled_at">处理时间：{{ new Date(item.handled_at).toLocaleString('zh-CN') }}</p>
        </div>
        <button v-if="!item.is_handled" data-testid="alert-handle-trigger" class="service-button service-outline alert-queue-action" type="button" @click="openHandleDialog(item, $event)">标记已处理</button>
      </li>
    </ul>

    <div
      v-if="selectedAlert"
      class="service-dialog fixed inset-0 z-50 flex justify-center bg-slate-950/50"
      @click.self="closeDialog()"
      @keydown.esc.stop="closeDialog()"
    >
      <div role="dialog" aria-labelledby="alert-handle-title" class="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-amber-100 text-amber-600">
            <MessageSquareText class="h-5 w-5" />
          </div>
          <div class="min-w-0 flex-1">
            <h2 id="alert-handle-title" class="text-xl font-bold">处理预警</h2>
            <p class="mt-2 text-sm service-muted [overflow-wrap:anywhere]">{{ selectedAlert.patient_name }} · {{ selectedAlert.alert_type }}</p>
          </div>
        </div>

        <div class="mt-5 bg-muted p-4 text-sm leading-7 service-muted [overflow-wrap:anywhere]">
          {{ selectedAlert.description }}
        </div>

        <div class="mt-5">
          <label for="alert-notes" class="mb-2 block text-sm font-semibold">
            处理备注
            <span class="font-normal text-slate-400">（可选）</span>
          </label>
          <textarea
            id="alert-notes"
            ref="notesInput"
            v-model="notes"
            data-testid="alert-notes-input"
            class="min-h-32 w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
            placeholder="请输入处理措施、随访建议等记录..."
          />
        </div>

        <div class="mt-5 flex gap-3">
          <button
            data-testid="alert-confirm-handle"
            class="service-button flex-1"
            :disabled="saving"
            type="button"
            @click="markHandled"
          >
            {{ saving ? '提交中...' : '确认已处理' }}
          </button>
          <button
            class="service-button service-outline"
            type="button"
            @click="closeDialog()"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alert-queue-title { border-bottom: 1px solid var(--service-gold); padding-bottom: 14px; }
.alert-queue-title h1 { font-size: 29px; line-height: 1.25; font-weight: 750; }
.alert-queue-title p { margin-top: 7px; color: var(--service-muted); font-size: 13px; font-variant-numeric: tabular-nums; }
.alert-tab-count { font-variant-numeric: tabular-nums; }
.alert-queue-state { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 15px; background: var(--workspace-warm); color: var(--service-muted); font-size: 14px; }
.alert-queue-state svg { width: 18px; height: 18px; }
.alert-queue-list { border-top: 1px solid var(--service-border); }
.alert-queue-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: start; gap: 6px 14px; padding: 12px; border-bottom: 1px solid var(--service-border); overflow-wrap: anywhere; }
.alert-queue-row h2 { font-size: 16px; font-weight: 720; }
.alert-queue-status { display: flex; flex-wrap: wrap; justify-content: end; gap: 4px; }
.alert-queue-time, .alert-queue-detail { color: var(--service-muted); font-size: 13px; }
.alert-queue-time { grid-column: 1 / -1; font-variant-numeric: tabular-nums; }
.alert-queue-detail { display: grid; gap: 4px; white-space: pre-line; }
.alert-queue-action { justify-self: end; }
@media (max-width: 600px) {
  .alert-queue-title h1 { font-size: 25px; }
  .alert-queue-detail, .alert-queue-action { grid-column: 1 / -1; }
}
</style>
