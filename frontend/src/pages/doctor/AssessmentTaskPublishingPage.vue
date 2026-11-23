<script setup lang="ts">
import { ClipboardList, Loader2, RefreshCw, Rocket, Settings2, SquareStack, StopCircle } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import {
  createAssessmentPublishTask,
  getAllProfiles,
  getAssessmentPublishMaterials,
  getAssessmentPublishTasks,
  getDefaultAssessmentTaskTemplate,
  getDepartments,
  publishAssessmentPublishTask,
  stopAssessmentPublishTask,
  updateDefaultAssessmentTaskTemplate,
} from '@/db/api'
import type { AssessmentPublishItem, AssessmentPublishItemType, AssessmentPublishTask, Department, NeuropsychTest, Profile, ScaleSurvey } from '@/types'

const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const tasks = ref<AssessmentPublishTask[]>([])
const defaultTemplate = ref<AssessmentPublishTask | null>(null)
const profiles = ref<Profile[]>([])
const departments = ref<Department[]>([])
const scales = ref<ScaleSurvey[]>([])
const neuropsychTests = ref<NeuropsychTest[]>([])
const reserved = ref<Array<{ type: string; title: string; enabled: boolean }>>([])
const activeMode = ref<'publish' | 'template'>('publish')
const form = ref({
  title: '',
  description: '',
  user_ids: [] as string[],
  department_ids: [] as string[],
  selected_scale_ids: [] as string[],
  selected_neuropsych_ids: [] as string[],
  selected_module_types: [] as AssessmentPublishItemType[],
})

const patients = computed(() => profiles.value.filter((item) => item.role === 'user'))

const loadAll = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextTasks, materials, nextProfiles, nextDepartments] = await Promise.all([
      getAssessmentPublishTasks(),
      getAssessmentPublishMaterials(),
      getAllProfiles(),
      getDepartments(true),
    ])
    tasks.value = nextTasks
    scales.value = materials.scale || []
    neuropsychTests.value = materials.neuropsych || []
    reserved.value = materials.reserved || []
    profiles.value = nextProfiles
    departments.value = nextDepartments
    defaultTemplate.value = await getDefaultAssessmentTaskTemplate().catch(() => null)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载发布测评任务失败'
  } finally {
    loading.value = false
  }
}

const buildItems = (): AssessmentPublishItem[] => {
  const items: AssessmentPublishItem[] = []
  for (const surveyId of form.value.selected_scale_ids) {
    const survey = scales.value.find((item) => item.id === surveyId)
    if (survey) items.push({ item_type: 'scale', target_id: survey.id, title: survey.title, required: true })
  }
  for (const testId of form.value.selected_neuropsych_ids) {
    const test = neuropsychTests.value.find((item) => item.id === testId)
    if (test) items.push({ item_type: 'neuropsych', target_id: test.id, title: test.title, required: true })
  }
  for (const moduleType of form.value.selected_module_types) {
    const module = reserved.value.find((item) => item.type === moduleType)
    if (module?.enabled) items.push({ item_type: moduleType, target_id: null, title: module.title, required: true })
  }
  return items.map((item, index) => ({ ...item, order_no: index + 1 }))
}

const createAndPublish = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    const items = buildItems()
    if (!form.value.title.trim()) throw new Error('请填写任务标题')
    if (!form.value.user_ids.length && !form.value.department_ids.length) throw new Error('请选择参与者或部门')
    if (!items.length) throw new Error('请选择至少一个测评项目')
    const task = await createAssessmentPublishTask({
      title: form.value.title,
      description: form.value.description,
      user_ids: form.value.user_ids,
      department_ids: form.value.department_ids,
      items,
    })
    await publishAssessmentPublishTask(task.id)
    statusMessage.value = '发布测评任务已创建并发布'
    form.value = { title: '', description: '', user_ids: [], department_ids: [], selected_scale_ids: [], selected_neuropsych_ids: [], selected_module_types: [] }
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布失败'
  } finally {
    saving.value = false
  }
}

const saveDefaultTemplate = async (enabled: boolean) => {
  if (!defaultTemplate.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    defaultTemplate.value = await updateDefaultAssessmentTaskTemplate({
      title: defaultTemplate.value.title,
      description: defaultTemplate.value.description,
      auto_assign_enabled: enabled,
      items: defaultTemplate.value.items || [],
    })
    statusMessage.value = enabled ? '默认测评模板已启用' : '默认测评模板已停用'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存默认模板失败'
  } finally {
    saving.value = false
  }
}

const stopTask = async (task: AssessmentPublishTask) => {
  saving.value = true
  try {
    await stopAssessmentPublishTask(task.id)
    statusMessage.value = '测评任务已停止'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '停止失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <SectionTitle title="发布测评任务" description="一次发布可组合量表、神经心理、对话、语音和表情测评；默认模板用于新用户注册后自动分配。" />
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
          { key: 'template', label: '默认模板' },
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

    <BaseCard v-if="activeMode === 'template'">
      <SectionTitle title="新用户默认测评模板" description="用户注册后自动获得这套五段式测评包。量表与神经心理项目可后续在模板 items 中继续扩展。" />
      <div v-if="defaultTemplate" class="mt-5 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div class="rounded-[24px] bg-slate-50 p-5 dark:bg-slate-900">
          <div class="flex items-center gap-3">
            <div class="grid h-11 w-11 place-items-center rounded-2xl bg-primary/10 text-primary">
              <Settings2 class="h-5 w-5" />
            </div>
            <div>
              <h3 class="text-lg font-black text-slate-900 dark:text-white">{{ defaultTemplate.title }}</h3>
              <p class="mt-1 text-sm text-slate-500">{{ defaultTemplate.description }}</p>
            </div>
          </div>
          <div class="mt-5 flex flex-wrap gap-3">
            <span class="rounded-full px-3 py-1 text-xs font-bold" :class="defaultTemplate.auto_assign_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'">
              {{ defaultTemplate.auto_assign_enabled ? '注册后自动分配' : '已停用自动分配' }}
            </span>
            <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-600">{{ defaultTemplate.items?.length || 0 }} 个项目</span>
          </div>
          <div class="mt-5 flex gap-3">
            <button class="rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white disabled:opacity-60" :disabled="saving" type="button" @click="saveDefaultTemplate(true)">启用自动分配</button>
            <button class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-700 disabled:opacity-60 dark:border-slate-800 dark:text-slate-200" :disabled="saving" type="button" @click="saveDefaultTemplate(false)">停用</button>
          </div>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div v-for="item in defaultTemplate.items || []" :key="item.id" class="rounded-[20px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
            <p class="text-xs font-bold text-primary">{{ item.item_type }}</p>
            <h4 class="mt-2 font-black text-slate-900 dark:text-white">{{ item.title }}</h4>
            <p class="mt-2 text-xs text-slate-400">排序 {{ item.order_no }} · {{ item.required ? '必做' : '选做' }}</p>
          </div>
        </div>
      </div>
    </BaseCard>

    <div v-if="activeMode === 'publish'" class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <BaseCard>
        <SectionTitle title="新建测评任务" description="选择参与者与测评项目后立即发布。未来干预任务会作为独立模块，不混入这里。" />
        <div class="mt-5 space-y-5">
          <input v-model="form.title" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="任务标题，例如：入组初筛测评包" />
          <textarea v-model="form.description" class="min-h-24 w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="任务说明" />

          <div class="grid gap-4 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">按部门发布</p>
              <div class="max-h-52 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
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
              <div class="max-h-52 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
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

          <div class="grid gap-4 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">量表</p>
              <label v-for="survey in scales" :key="survey.id" class="mb-2 flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-900">
                <input v-model="form.selected_scale_ids" :value="survey.id" type="checkbox" />
                <span>{{ survey.title }}</span>
              </label>
            </div>
            <div>
              <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">神经心理测评</p>
              <label v-for="test in neuropsychTests" :key="test.id" class="mb-2 flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-900">
                <input v-model="form.selected_neuropsych_ids" :value="test.id" type="checkbox" />
                <span>{{ test.title }}</span>
              </label>
            </div>
          </div>

          <div>
            <p class="mb-2 text-sm font-bold text-slate-800 dark:text-slate-100">对话 / 语音 / 表情</p>
            <div class="grid gap-2 sm:grid-cols-2">
              <label
                v-for="item in reserved"
                :key="item.type"
                class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm"
                :class="item.enabled ? 'bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-200' : 'bg-slate-100 text-slate-400 dark:bg-slate-900'"
              >
                <input v-model="form.selected_module_types" :value="item.type" :disabled="!item.enabled" type="checkbox" />
                <span>{{ item.title }}</span>
                <span v-if="!item.enabled" class="text-xs">预留</span>
              </label>
            </div>
          </div>

          <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-500/20 disabled:opacity-60" :disabled="saving" type="button" @click="createAndPublish">
            <Rocket class="h-4 w-4" />
            创建并发布测评任务
          </button>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle title="任务列表" description="查看已发布测评任务的项目数、对象数和完成率。" />
        <div v-if="loading" class="flex items-center justify-center gap-2 py-16 text-slate-500"><Loader2 class="h-5 w-5 animate-spin" /> 正在加载...</div>
        <div v-else class="mt-5 space-y-4">
          <div v-for="task in tasks" :key="task.id" class="rounded-[24px] border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">{{ task.status }}</span>
                  <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-600 dark:bg-blue-950/30 dark:text-blue-200">{{ task.item_count || 0 }} 项</span>
                </div>
                <h3 class="mt-3 text-lg font-black text-slate-900 dark:text-white">{{ task.title }}</h3>
                <p class="mt-1 text-sm text-slate-500">{{ task.description || '无说明' }}</p>
                <p class="mt-3 text-xs text-slate-400">对象 {{ task.assignee_count || 0 }} 人 / 完成 {{ task.completed_count || 0 }} 人</p>
              </div>
              <button v-if="task.status === 'active'" class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-700 dark:border-slate-800 dark:text-slate-200" type="button" @click="stopTask(task)">
                <StopCircle class="h-4 w-4" />
                停止
              </button>
            </div>
          </div>
          <div v-if="tasks.length === 0" class="rounded-3xl bg-slate-50 py-12 text-center text-sm text-slate-500 dark:bg-slate-900">
            <SquareStack class="mx-auto mb-2 h-8 w-8 text-slate-300" />
            暂无发布测评任务
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
