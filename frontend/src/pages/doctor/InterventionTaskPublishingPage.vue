<script setup lang="ts">
import {
  Brain,
  CalendarDays,
  CheckCircle2,
  Clock,
  FileText,
  Gamepad2,
  HeartPulse,
  Loader2,
  Music,
  NotebookPen,
  RefreshCw,
  Rocket,
  Settings2,
  StopCircle,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import { assessmentStatusLabel } from '@/lib/assessment-display'
import {
  createInterventionTask,
  getAllProfiles,
  getDepartments,
  getInterventionMaterials,
  getInterventionTasks,
  getInterventionTemplates,
  publishInterventionTask,
  stopInterventionTask,
  updateInterventionTemplate,
} from '@/db/api'
import type { Department, InterventionFrequencyType, InterventionMaterial, InterventionPlanTemplate, InterventionPlanTemplateItem, InterventionPublishBatch, Profile } from '@/types'

const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const activeMode = ref<'publish' | 'templates' | 'tracking'>('publish')
const materials = ref<Record<string, InterventionMaterial[]>>({})
const templates = ref<InterventionPlanTemplate[]>([])
const tasks = ref<InterventionPublishBatch[]>([])
const profiles = ref<Profile[]>([])
const departments = ref<Department[]>([])
const templateDrafts = ref<Record<string, InterventionPlanTemplate>>({})
const form = ref({
  title: '',
  description: '',
  start_date: new Date().toISOString().slice(0, 10),
  duration_days: 7,
  daily_required_count: 1,
  risk_level: '',
  user_ids: [] as string[],
  department_ids: [] as string[],
  material_ids: [] as string[],
})

const patients = computed(() => profiles.value.filter((item) => item.role === 'user'))
const materialList = computed(() => materials.value.all || Object.values(materials.value).flat())

const categoryMeta: Record<string, { label: string; icon: any; tone: string }> = {
  mood: { label: '心情', icon: NotebookPen, tone: 'bg-amber-50 text-amber-700' },
  meditation: { label: '冥想', icon: Music, tone: 'bg-cyan-50 text-cyan-700' },
  knowledge: { label: '知识', icon: FileText, tone: 'bg-emerald-50 text-emerald-700' },
  game: { label: '游戏', icon: Gamepad2, tone: 'bg-orange-50 text-orange-700' },
  brain_intervention: { label: '脑机干预', icon: Brain, tone: 'bg-slate-900 text-white' },
}

const riskLabel = (risk?: string | null) => {
  if (risk === 'high') return '高风险'
  if (risk === 'middle') return '中风险'
  if (risk === 'low') return '低风险'
  return '未指定'
}

const frequencyText = (value?: string) => {
  if (value === 'weekly') return '每周'
  if (value === 'once') return '一次'
  if (value === 'plan_total') return '计划内'
  return '每日'
}

const loadAll = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextMaterials, nextTemplates, nextTasks, nextProfiles, nextDepartments] = await Promise.all([
      getInterventionMaterials(),
      getInterventionTemplates(),
      getInterventionTasks(),
      getAllProfiles(),
      getDepartments(true),
    ])
    materials.value = nextMaterials || {}
    templates.value = nextTemplates || []
    tasks.value = nextTasks || []
    profiles.value = nextProfiles || []
    departments.value = nextDepartments || []
    templateDrafts.value = Object.fromEntries(
      templates.value.map((template) => [template.id, JSON.parse(JSON.stringify(template))]),
    )
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载干预任务失败'
  } finally {
    loading.value = false
  }
}

const buildItems = () =>
  form.value.material_ids
    .map((materialId, index) => {
      const material = materialList.value.find((item) => item.id === materialId)
      if (!material) return null
      return {
        material_id: material.id,
        title: material.title,
        required: true,
        frequency_type: 'daily',
        required_count: 1,
        duration_sec: material.duration_sec || 10,
        order_no: index + 1,
        config_json: {},
      }
    })
    .filter(Boolean)

const materialToDraftItem = (material: InterventionMaterial, index: number): InterventionPlanTemplateItem => ({
  material_id: material.id,
  title: material.title,
  frequency_type: 'daily' as InterventionFrequencyType,
  required_count: 1,
  duration_sec: material.duration_sec || 10,
  order_no: index + 1,
  required: true,
  config_json: {},
  category: material.category,
  subtype: material.subtype,
  route_path: material.route_path,
  completion_mode: material.completion_mode,
})

const isTemplateMaterialSelected = (templateId: string, materialId: string) =>
  Boolean((templateDrafts.value[templateId]?.items || []).some((item) => item.material_id === materialId))

const toggleTemplateMaterial = (templateId: string, material: InterventionMaterial) => {
  const draft = templateDrafts.value[templateId]
  if (!draft) return
  const current = draft.items || []
  const exists = current.some((item) => item.material_id === material.id)
  const nextItems = exists
    ? current.filter((item) => item.material_id !== material.id)
    : [...current, materialToDraftItem(material, current.length)]
  draft.items = nextItems.map((item, index) => ({ ...item, order_no: index + 1 }))
}

const createAndPublish = async () => {
  saving.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    const items = buildItems()
    if (!form.value.title.trim()) throw new Error('请填写干预任务标题')
    if (!form.value.user_ids.length && !form.value.department_ids.length) throw new Error('请选择参与者或部门')
    if (!items.length) throw new Error('请选择至少一个干预小项目')
    const task = await createInterventionTask({
      title: form.value.title,
      description: form.value.description,
      start_date: form.value.start_date,
      duration_days: form.value.duration_days,
      daily_required_count: form.value.daily_required_count,
      risk_level: form.value.risk_level || null,
      user_ids: form.value.user_ids,
      department_ids: form.value.department_ids,
      items,
    })
    await publishInterventionTask(task.id)
    statusMessage.value = '发布干预任务已创建并发布'
    form.value = {
      title: '',
      description: '',
      start_date: new Date().toISOString().slice(0, 10),
      duration_days: 7,
      daily_required_count: 1,
      risk_level: '',
      user_ids: [],
      department_ids: [],
      material_ids: [],
    }
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布干预任务失败'
  } finally {
    saving.value = false
  }
}

const saveTemplate = async (templateId: string) => {
  const draft = templateDrafts.value[templateId]
  if (!draft) return
  saving.value = true
  errorMessage.value = ''
  try {
    await updateInterventionTemplate(templateId, {
      title: draft.title,
      description: draft.description,
      duration_days: draft.duration_days,
      daily_required_count: draft.daily_required_count,
      auto_assign_enabled: draft.auto_assign_enabled,
      status: draft.status,
      items: draft.items || [],
    })
    statusMessage.value = '默认干预方案已保存'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存默认方案失败'
  } finally {
    saving.value = false
  }
}

const stopTask = async (task: InterventionPublishBatch) => {
  saving.value = true
  errorMessage.value = ''
  try {
    await stopInterventionTask(task.id)
    statusMessage.value = '干预任务已停止'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '停止干预任务失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <SectionTitle title="发布干预任务" description="跨菜单安排冥想、心情、游戏、知识和脑机干预；参与者需要回到真实功能入口完成。" />
      <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="loadAll">
        <RefreshCw class="h-4 w-4" />
        刷新
      </button>
    </div>

    <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-medium text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>
    <div v-if="statusMessage" class="rounded-2xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">{{ statusMessage }}</div>

    <div class="flex gap-2 rounded-2xl bg-slate-100 p-1 dark:bg-slate-900">
      <button
        v-for="mode in [
          { key: 'publish', label: '手动发布' },
          { key: 'templates', label: '默认方案' },
          { key: 'tracking', label: '进度追踪' },
        ]"
        :key="mode.key"
        class="flex-1 rounded-xl px-4 py-2 text-sm font-bold transition"
        :class="activeMode === mode.key ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-800 dark:text-white' : 'text-slate-500'"
        type="button"
        @click="activeMode = mode.key as any"
      >
        {{ mode.label }}
      </button>
    </div>

    <div v-if="loading" class="rounded-[28px] bg-white p-10 text-center text-slate-500 dark:bg-slate-900">
      <Loader2 class="mx-auto h-6 w-6 animate-spin" />
      <p class="mt-3 text-sm">正在加载干预任务配置...</p>
    </div>

    <div v-else-if="activeMode === 'publish'" class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <BaseCard>
        <SectionTitle title="新建干预任务" description="同一任务可包含多个小项目，参与者端会按今日子项目合并展示。" />
        <div class="mt-5 space-y-5">
          <input v-model="form.title" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="任务标题，例如：中风险情绪调节计划" />
          <textarea v-model="form.description" class="min-h-24 w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="任务说明" />
          <div class="grid gap-3 md:grid-cols-3">
            <label class="space-y-1 text-sm font-bold text-slate-700 dark:text-slate-200">
              <span>开始日期</span>
              <input v-model="form.start_date" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-950" type="date" />
            </label>
            <label class="space-y-1 text-sm font-bold text-slate-700 dark:text-slate-200">
              <span>持续天数</span>
              <input v-model.number="form.duration_days" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-950" min="1" max="60" type="number" />
            </label>
            <label class="space-y-1 text-sm font-bold text-slate-700 dark:text-slate-200">
              <span>每日发布数量</span>
              <input v-model.number="form.daily_required_count" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-950" min="1" max="8" type="number" />
              <span class="block text-[11px] font-medium leading-5 text-slate-400">从任务池中每天抽取几个发布；任务池小于该数时全量发布。</span>
            </label>
          </div>
          <select v-model="form.risk_level" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950">
            <option value="">不指定风险层级</option>
            <option value="low">低风险</option>
            <option value="middle">中风险</option>
            <option value="high">高风险</option>
          </select>

          <div class="grid gap-4 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">按部门发布</p>
              <div class="max-h-48 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
                <label v-for="department in departments.filter((item) => item.status === 'active')" :key="department.id" class="mb-1 flex items-center justify-between gap-2 rounded-lg p-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-900">
                  <span class="flex min-w-0 items-center gap-2">
                    <input v-model="form.department_ids" :value="department.id" type="checkbox" />
                    <span class="truncate">{{ department.name }}</span>
                  </span>
                  <span class="shrink-0 text-xs font-bold text-slate-400">{{ department.user_count || 0 }}人</span>
                </label>
                <p v-if="departments.filter((item) => item.status === 'active').length === 0" class="p-3 text-sm text-slate-400">暂无启用部门</p>
              </div>
            </div>
            <div>
              <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">选择参与者</p>
              <div class="max-h-48 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
                <label v-for="patient in patients" :key="patient.id" class="mb-1 flex items-center justify-between gap-2 rounded-lg p-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-900">
                  <span class="flex min-w-0 items-center gap-2">
                    <input v-model="form.user_ids" :value="patient.id" type="checkbox" />
                    <span class="truncate">{{ patient.full_name || patient.username }}</span>
                  </span>
                  <span class="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500 dark:bg-slate-800">{{ patient.department_name || '未分部门' }}</span>
                </label>
              </div>
            </div>
          </div>

          <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-500/20 disabled:opacity-60" :disabled="saving" type="button" @click="createAndPublish">
            <Rocket class="h-4 w-4" />
            创建并发布干预任务
          </button>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle title="选择干预小项目" description="心情每天只完成一次；冥想需指定音频；知识、游戏和脑机项目会进入对应入口倒计时完成。" />
        <div class="mt-5 grid gap-3 md:grid-cols-2">
          <label
            v-for="material in materialList"
            :key="material.id"
            class="flex cursor-pointer gap-3 rounded-[20px] border p-4 transition"
            :class="form.material_ids.includes(material.id) ? 'border-primary bg-primary/5 ring-2 ring-primary/10' : 'border-slate-100 bg-slate-50 hover:bg-white dark:border-slate-800 dark:bg-slate-900'"
          >
            <input v-model="form.material_ids" :value="material.id" class="mt-1" type="checkbox" />
            <div :class="['grid h-10 w-10 shrink-0 place-items-center rounded-2xl', categoryMeta[material.category]?.tone || 'bg-slate-100 text-slate-600']">
              <component :is="categoryMeta[material.category]?.icon || HeartPulse" class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <p class="font-black text-slate-900 dark:text-white">{{ material.title }}</p>
                <span class="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-slate-950">{{ categoryMeta[material.category]?.label }}</span>
              </div>
              <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{{ material.description }}</p>
              <p class="mt-2 text-[11px] font-bold text-slate-400">{{ material.completion_mode === 'diary_once' ? '保存日记后完成' : `${material.duration_sec || 10} 秒后可完成` }}</p>
            </div>
          </label>
        </div>
      </BaseCard>
    </div>

    <div v-else-if="activeMode === 'templates'" class="grid gap-5">
      <BaseCard v-for="template in templates" :key="template.id">
        <div class="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div class="grid h-11 w-11 place-items-center rounded-2xl bg-emerald-50 text-emerald-700">
                <Settings2 class="h-5 w-5" />
              </div>
              <div>
                <p class="text-xs font-bold text-slate-400">{{ riskLabel(template.risk_level) }}默认方案</p>
                <h3 class="text-lg font-black text-slate-900 dark:text-white">{{ template.title }}</h3>
              </div>
            </div>
            <input v-model="templateDrafts[template.id]!.title" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950" />
            <textarea v-model="templateDrafts[template.id]!.description" class="min-h-20 w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950" />
            <div class="grid grid-cols-2 gap-3">
              <label class="space-y-1 text-xs font-bold text-slate-500">
                <span>周期天数</span>
                <input v-model.number="templateDrafts[template.id]!.duration_days" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-950" type="number" min="1" />
              </label>
              <label class="space-y-1 text-xs font-bold text-slate-500">
                <span>每日发布数量</span>
                <input v-model.number="templateDrafts[template.id]!.daily_required_count" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-950" type="number" min="1" />
              </label>
            </div>
            <label class="flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
              <input v-model="templateDrafts[template.id]!.auto_assign_enabled" type="checkbox" />
              初筛后自动分配
            </label>
            <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white disabled:opacity-60 dark:bg-white dark:text-slate-900" :disabled="saving" type="button" @click="saveTemplate(template.id)">
              <CheckCircle2 class="h-4 w-4" />
              保存方案
            </button>
          </div>
          <div>
            <div class="mb-3 flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-black text-slate-900 dark:text-white">方案项目</p>
                <p class="text-xs text-slate-500">勾选后会用于初筛完成后的自动干预计划。</p>
              </div>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-800">
                {{ templateDrafts[template.id]?.items?.length || 0 }} 项
              </span>
            </div>
            <div class="grid max-h-[520px] gap-3 overflow-y-auto pr-1 md:grid-cols-2">
              <label
                v-for="material in materialList"
                :key="`${template.id}-${material.id}`"
                class="flex cursor-pointer gap-3 rounded-[20px] border p-4 transition"
                :class="isTemplateMaterialSelected(template.id, material.id) ? 'border-emerald-300 bg-emerald-50 ring-2 ring-emerald-100 dark:bg-emerald-950/20' : 'border-slate-100 bg-slate-50 hover:bg-white dark:border-slate-800 dark:bg-slate-900'"
              >
                <input :checked="isTemplateMaterialSelected(template.id, material.id)" class="mt-1" type="checkbox" @change="toggleTemplateMaterial(template.id, material)" />
                <div :class="['grid h-10 w-10 shrink-0 place-items-center rounded-2xl', categoryMeta[material.category]?.tone || 'bg-slate-100 text-slate-600']">
                  <component :is="categoryMeta[material.category]?.icon || HeartPulse" class="h-5 w-5" />
                </div>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <p class="font-black text-slate-900 dark:text-white">{{ material.title }}</p>
                    <span class="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-slate-950">{{ categoryMeta[material.category]?.label }}</span>
                  </div>
                  <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{{ material.description }}</p>
                  <p class="mt-2 text-[11px] font-bold text-slate-400">
                    每日任务池 ·
                    {{ material.completion_mode === 'diary_once' ? '保存日记后完成' : `${material.duration_sec || 10} 秒后可完成` }}
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <BaseCard v-else>
      <SectionTitle title="干预任务进度" />
      <div class="mt-5 grid gap-3">
        <article v-for="task in tasks" :key="task.id" class="rounded-[22px] border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="font-black text-slate-900 dark:text-white">{{ task.title }}</h3>
                <ServiceStatus :tone="task.status === 'active' ? 'active' : task.status === 'completed' ? 'done' : 'idle'">{{ assessmentStatusLabel(task.status) }}</ServiceStatus>
                <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">{{ riskLabel(task.risk_level) }}</span>
              </div>
              <p class="mt-2 text-sm text-slate-500">{{ task.description || '暂无说明' }}</p>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center text-xs">
              <span class="rounded-2xl bg-white px-3 py-2 dark:bg-slate-950"><CalendarDays class="mx-auto mb-1 h-4 w-4" />{{ task.duration_days }}天</span>
              <span class="rounded-2xl bg-white px-3 py-2 dark:bg-slate-950"><Clock class="mx-auto mb-1 h-4 w-4" />{{ task.assignee_count || 0 }}人</span>
              <span class="rounded-2xl bg-white px-3 py-2 dark:bg-slate-950"><CheckCircle2 class="mx-auto mb-1 h-4 w-4" />{{ task.finished_count || 0 }}结束</span>
            </div>
            <button v-if="task.status === 'active'" class="inline-flex items-center justify-center gap-2 rounded-xl border border-rose-200 px-4 py-2 text-sm font-bold text-rose-600 disabled:opacity-60" :disabled="saving" type="button" @click="stopTask(task)">
              <StopCircle class="h-4 w-4" />
              停止
            </button>
          </div>
        </article>
      </div>
    </BaseCard>
  </div>
</template>
