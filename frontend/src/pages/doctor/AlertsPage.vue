<script setup lang="ts">
import { AlertTriangle, CheckCircle, Clock3, MessageSquareText } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import { getAllProfiles, getRiskAlerts, handleRiskAlert } from '@/db/api'
import type { Profile, RiskAlert } from '@/types'

type AlertTab = 'pending' | 'handled'

interface AlertViewModel extends RiskAlert {
  patient_name: string
}

const { state: authState } = useAuthSession()

const loading = ref(true)
const saving = ref(false)
const activeTab = ref<AlertTab>('pending')
const pendingAlerts = ref<AlertViewModel[]>([])
const handledAlerts = ref<AlertViewModel[]>([])
const selectedAlert = ref<AlertViewModel | null>(null)
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

const summaryCards = computed(() => [
  { label: '待处理', value: pendingAlerts.value.length, icon: AlertTriangle, tone: 'text-rose-500' },
  { label: '已处理', value: handledAlerts.value.length, icon: CheckCircle, tone: 'text-emerald-500' },
  {
    label: '最近一条',
    value: [...pendingAlerts.value, ...handledAlerts.value][0]?.created_at
      ? new Date([...pendingAlerts.value, ...handledAlerts.value][0]!.created_at).toLocaleString('zh-CN')
      : '-',
    icon: Clock3,
    tone: 'text-primary',
  },
])

const currentAlerts = computed(() => (activeTab.value === 'pending' ? pendingAlerts.value : handledAlerts.value))

const loadAlerts = async () => {
  loading.value = true
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
    pendingAlerts.value = unhandled.map(enrich)
    handledAlerts.value = handled.map(enrich)
  } catch (error) {
    pendingAlerts.value = []
    handledAlerts.value = []
    errorMessage.value = error instanceof Error ? error.message : '加载预警失败'
  } finally {
    loading.value = false
  }
}

const riskBadgeClass = (riskLevel: number) => {
  if (riskLevel >= 8) return 'bg-rose-500 text-white'
  if (riskLevel >= 5) return 'bg-amber-500 text-white'
  return 'bg-emerald-500 text-white'
}

const riskText = (riskLevel: number) => {
  if (riskLevel >= 8) return '高风险'
  if (riskLevel >= 5) return '中风险'
  return '低风险'
}

const openHandleDialog = (alert: AlertViewModel) => {
  selectedAlert.value = alert
  notes.value = ''
  statusMessage.value = ''
  errorMessage.value = ''
}

const closeDialog = () => {
  selectedAlert.value = null
  notes.value = ''
}

const markHandled = async () => {
  if (!authState.user || !selectedAlert.value) return
  saving.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    await handleRiskAlert(selectedAlert.value.id, authState.user.id, notes.value.trim() || undefined)
    statusMessage.value = '预警已处理'
    closeDialog()
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

    <SectionTitle title="风险预警" description="查看待处理与已处理预警，及时记录干预备注。" />

    <div class="grid gap-4 md:grid-cols-3">
      <BaseCard v-for="item in summaryCards" :key="item.label">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm text-slate-500">{{ item.label }}</p>
          <component :is="item.icon" :class="['h-5 w-5', item.tone]" />
        </div>
        <p class="mt-4 text-3xl font-bold text-slate-900 dark:text-white">{{ item.value }}</p>
      </BaseCard>
    </div>

    <div class="flex gap-3">
      <button
        data-testid="alerts-tab-pending"
        class="rounded-full px-4 py-2 text-sm font-semibold transition"
        :class="activeTab === 'pending' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-white text-slate-500 dark:bg-slate-900 dark:text-slate-300'"
        type="button"
        @click="activeTab = 'pending'"
      >
        待处理
        <span
          v-if="pendingAlerts.length > 0"
          class="ml-2 inline-flex min-w-5 items-center justify-center rounded-full bg-rose-500 px-1.5 py-0.5 text-[10px] font-bold text-white"
        >
          {{ pendingAlerts.length }}
        </span>
      </button>
      <button
        data-testid="alerts-tab-handled"
        class="rounded-full px-4 py-2 text-sm font-semibold transition"
        :class="activeTab === 'handled' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-white text-slate-500 dark:bg-slate-900 dark:text-slate-300'"
        type="button"
        @click="activeTab = 'handled'"
      >
        已处理
      </button>
    </div>

    <BaseCard v-if="loading">
      <p class="text-sm text-slate-500">正在加载预警列表...</p>
    </BaseCard>

    <div v-else class="grid gap-4">
      <BaseCard v-if="currentAlerts.length === 0" class="border-dashed">
        <div class="py-12 text-center">
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-[8px] bg-slate-100 dark:bg-slate-800">
            <CheckCircle v-if="activeTab === 'pending'" class="h-8 w-8 text-slate-400" />
            <AlertTriangle v-else class="h-8 w-8 text-slate-400" />
          </div>
          <p class="mt-4 text-base font-semibold text-slate-700 dark:text-slate-200">
            {{ activeTab === 'pending' ? '暂无待处理预警' : '暂无已处理预警' }}
          </p>
        </div>
      </BaseCard>

      <BaseCard v-for="item in currentAlerts" :key="item.id">
        <div class="flex flex-col gap-4">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span :class="['rounded-full px-3 py-1 text-xs font-semibold', riskBadgeClass(item.risk_level)]">
                  风险等级 {{ item.risk_level }}/10
                </span>
                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                  {{ item.alert_type }}
                </span>
                <span v-if="item.is_handled" class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  已处理
                </span>
              </div>

              <h3 class="mt-4 text-lg font-bold text-slate-900 dark:text-white">{{ item.patient_name }}</h3>
              <p class="mt-2 text-sm text-slate-500">
                {{ riskText(item.risk_level) }} · {{ new Date(item.created_at).toLocaleString('zh-CN') }}
              </p>
              <p class="mt-4 whitespace-pre-line text-sm leading-7 text-slate-600 dark:text-slate-300">
                {{ item.description }}
              </p>

              <div v-if="item.data_source" class="mt-4 rounded-[8px] bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:bg-slate-900">
                数据来源：{{ item.data_source }}
              </div>
              <div v-if="item.is_handled && item.notes" class="mt-4 rounded-[8px] bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                处理备注：{{ item.notes }}
              </div>
              <div v-if="item.is_handled && item.handled_at" class="mt-3 text-xs text-slate-400">
                处理时间：{{ new Date(item.handled_at).toLocaleString('zh-CN') }}
              </div>
            </div>

            <button
              v-if="!item.is_handled"
              data-testid="alert-handle-trigger"
              class="rounded-[8px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
              type="button"
              @click="openHandleDialog(item)"
            >
              标记已处理
            </button>
          </div>
        </div>
      </BaseCard>
    </div>

    <div
      v-if="selectedAlert"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4"
      @click.self="closeDialog"
    >
      <div class="w-full max-w-md rounded-[8px] bg-white p-6 shadow-xl dark:bg-slate-900">
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-amber-100 text-amber-600">
            <MessageSquareText class="h-5 w-5" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-xl font-bold text-slate-900 dark:text-white">处理预警</h3>
            <p class="mt-2 text-sm text-slate-500">{{ selectedAlert.patient_name }} · {{ selectedAlert.alert_type }}</p>
          </div>
        </div>

        <div class="mt-5 rounded-[8px] bg-slate-50 p-4 text-sm leading-7 text-slate-600 dark:bg-slate-950 dark:text-slate-300">
          {{ selectedAlert.description }}
        </div>

        <div class="mt-5">
          <label class="mb-2 block text-sm font-semibold text-slate-900 dark:text-white">
            处理备注
            <span class="font-normal text-slate-400">（可选）</span>
          </label>
          <textarea
            v-model="notes"
            data-testid="alert-notes-input"
            class="min-h-32 w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
            placeholder="请输入处理措施、随访建议等记录..."
          />
        </div>

        <div class="mt-5 flex gap-3">
          <button
            data-testid="alert-confirm-handle"
            class="flex-1 rounded-[8px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900"
            :disabled="saving"
            type="button"
            @click="markHandled"
          >
            {{ saving ? '提交中...' : '确认已处理' }}
          </button>
          <button
            class="rounded-[8px] border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-500 dark:border-slate-700 dark:text-slate-300"
            type="button"
            @click="closeDialog"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
