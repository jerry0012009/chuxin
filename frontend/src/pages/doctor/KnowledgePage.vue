<script setup lang="ts">
import {
  ArrowDown,
  ArrowUp,
  BookOpen,
  Copy,
  Edit3,
  Eye,
  FileText,
  Plus,
  Search,
  SlidersHorizontal,
  Trash2,
  Upload,
} from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useAppState } from '@/composables/useAppState'
import { useAuthSession } from '@/composables/useAuthSession'
import {
  createKnowledge,
  deleteKnowledge,
  deleteKnowledgeDocument,
  getKnowledgeBase,
  getKnowledgeDocumentUrl,
  updateKnowledge,
  uploadKnowledgeDocument,
} from '@/db/api'
import type { KnowledgeBase } from '@/types'

interface ScaleQuestion {
  id: string
  text: string
  order: number
}

const { refreshCurrentAccountProfile } = useAppState()
const { state: authState } = useAuthSession()

const knowledge = ref<KnowledgeBase[]>([])
const loading = ref(true)
const saving = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('all')
const editingId = ref<string | null>(null)
const statusMessage = ref('')
const errorMessage = ref('')

const title = ref('')
const category = ref<'assessment' | 'therapy' | 'research'>('assessment')
const content = ref('')
const tags = ref('')
const scaleQuestions = ref<ScaleQuestion[]>([])
const newQuestionText = ref('')
const uploadFile = ref<File | null>(null)
const uploadProgress = ref(0)
const uploading = ref(false)
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

const categories = [
  { value: 'all', label: '全部' },
  { value: 'assessment', label: '评估量表' },
  { value: 'therapy', label: '治疗方法' },
  { value: 'research', label: '研究资料' },
] as const

const documentCategory = computed(() => category.value === 'therapy' || category.value === 'research')

const filteredKnowledge = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return knowledge.value.filter((item) => {
    const matchCategory = selectedCategory.value === 'all' || item.category === selectedCategory.value
    if (!matchCategory) return false
    if (!keyword) return true
    return [item.title, item.content, item.category, ...(item.tags || [])]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
})

const summaryCards = computed(() => [
  { label: '内容总数', value: knowledge.value.length, icon: BookOpen },
  { label: '量表类', value: knowledge.value.filter((item) => item.category === 'assessment').length, icon: SlidersHorizontal },
  { label: '文档类', value: knowledge.value.filter((item) => item.content_type === 'document').length, icon: FileText },
])

const parseScaleContent = (item: KnowledgeBase) => {
  try {
    const parsed = JSON.parse(item.content || '{}')
    if (parsed?.type !== 'scale' || !Array.isArray(parsed.questions)) return []
    return parsed.questions
      .slice()
      .sort((a: ScaleQuestion, b: ScaleQuestion) => (a.order || 0) - (b.order || 0))
  } catch {
    return []
  }
}

const articleSummary = (item: KnowledgeBase) => {
  if (item.content_type === 'document') {
    return item.content || `文档：${item.file_name || '未命名文件'}`
  }
  if (item.category === 'assessment') {
    const questions = parseScaleContent(item)
    return questions.length > 0 ? `共 ${questions.length} 题` : '未配置题目'
  }
  return item.content.slice(0, 120) || '暂无摘要'
}

const formatFileSize = (size?: number | null) => {
  if (!size) return '未知大小'
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${size} B`
}

const resetForm = () => {
  editingId.value = null
  title.value = ''
  category.value = 'assessment'
  content.value = ''
  tags.value = ''
  scaleQuestions.value = []
  newQuestionText.value = ''
  uploadFile.value = null
  uploadProgress.value = 0
  uploading.value = false
  errorMessage.value = ''
}

const syncWorkspace = async () => {
  await refreshCurrentAccountProfile()
}

const loadKnowledge = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    knowledge.value = await getKnowledgeBase()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载知识库失败'
  } finally {
    loading.value = false
  }
}

const startCreate = () => {
  resetForm()
  statusMessage.value = ''
}

const startEdit = (item: KnowledgeBase) => {
  resetForm()
  editingId.value = item.id
  title.value = item.title
  category.value = (item.category as 'assessment' | 'therapy' | 'research') || 'assessment'
  content.value = item.content
  tags.value = (item.tags || []).join(', ')
  if (item.category === 'assessment') {
    scaleQuestions.value = parseScaleContent(item)
  }
}

const addQuestion = () => {
  const next = newQuestionText.value.trim()
  if (!next) return
  scaleQuestions.value.push({
    id: crypto.randomUUID(),
    text: next,
    order: scaleQuestions.value.length,
  })
  newQuestionText.value = ''
}

const moveQuestion = (index: number, direction: -1 | 1) => {
  const target = index + direction
  if (target < 0 || target >= scaleQuestions.value.length) return
  const clone = scaleQuestions.value.slice()
  const [item] = clone.splice(index, 1)
  if (!item) return
  clone.splice(target, 0, item)
  scaleQuestions.value = clone.map((question, order) => ({ ...question, order }))
}

const removeQuestion = (index: number) => {
  scaleQuestions.value = scaleQuestions.value
    .filter((_, position) => position !== index)
    .map((question, order) => ({ ...question, order }))
}

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] || null
  if (!file) return
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = '文件大小不能超过 50MB'
    input.value = ''
    return
  }
  uploadFile.value = file
  errorMessage.value = ''
}

const simulateUpload = () =>
  window.setInterval(() => {
    uploadProgress.value = Math.min(uploadProgress.value + 10, 90)
  }, 180)

const save = async () => {
  if (!authState.user || !title.value.trim()) {
    errorMessage.value = '请先填写标题'
    return
  }

  const payload: Partial<KnowledgeBase> = {
    title: title.value.trim(),
    category: category.value,
    created_by: authState.user.id,
    tags: tags.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean),
    is_active: true,
  }

  if (category.value === 'assessment') {
    if (scaleQuestions.value.length === 0) {
      errorMessage.value = '请至少添加一道量表题目'
      return
    }
    payload.content = JSON.stringify({
      type: 'scale',
      description: title.value.trim(),
      version: 1,
      questions: scaleQuestions.value.map((item, order) => ({
        id: item.id,
        text: item.text,
        order,
      })),
    })
    if (!payload.tags?.includes('量表')) {
      payload.tags = [...(payload.tags || []), '量表', '评估量表']
    }
  } else {
    payload.content = content.value.trim()
  }

  saving.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const editingItem = editingId.value ? knowledge.value.find((item) => item.id === editingId.value) : null

    if (documentCategory.value && uploadFile.value) {
      uploading.value = true
      uploadProgress.value = 0
      const timer = simulateUpload()
      try {
        const uploaded = await uploadKnowledgeDocument(uploadFile.value, category.value)
        window.clearInterval(timer)
        uploadProgress.value = 100
        payload.content_type = 'document'
        payload.file_url = uploaded.path
        payload.file_name = uploaded.name
        payload.file_size = uploaded.size
        payload.file_mime_type = uploaded.type
        payload.content = content.value.trim() || `文档：${uploaded.name}`
      } catch (error) {
        window.clearInterval(timer)
        throw error
      } finally {
        uploading.value = false
      }
    } else if (documentCategory.value && editingItem?.content_type === 'document' && editingItem.file_url) {
      payload.content_type = 'document'
      payload.file_url = editingItem.file_url
      payload.file_name = editingItem.file_name
      payload.file_size = editingItem.file_size
      payload.file_mime_type = editingItem.file_mime_type
      payload.content = content.value.trim() || editingItem.content
    } else if (!payload.content?.trim()) {
      errorMessage.value = '请填写内容说明'
      return
    }

    if (editingId.value) {
      await updateKnowledge(editingId.value, payload)
      statusMessage.value = '知识内容已更新'
    } else {
      await createKnowledge(payload)
      statusMessage.value = '知识内容已创建'
    }

    await loadKnowledge()
    await syncWorkspace()
    resetForm()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败'
  } finally {
    saving.value = false
    uploading.value = false
  }
}

const removeKnowledgeItem = async (item: KnowledgeBase) => {
  if (!window.confirm(`确定删除“${item.title}”吗？`)) return
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    if (item.content_type === 'document' && item.file_url) {
      await deleteKnowledgeDocument(item.file_url)
    }
    await deleteKnowledge(item.id)
    statusMessage.value = '知识内容已删除'
    if (editingId.value === item.id) resetForm()
    await loadKnowledge()
    await syncWorkspace()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除失败'
  }
}

const duplicateKnowledge = async (item: KnowledgeBase) => {
  if (!authState.user) return
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    await createKnowledge({
      title: `${item.title} 副本`,
      category: item.category,
      content: item.content,
      tags: item.tags || [],
      content_type: item.content_type,
      file_url: item.file_url,
      file_name: item.file_name,
      file_size: item.file_size,
      file_mime_type: item.file_mime_type,
      is_active: true,
      created_by: authState.user.id,
    })
    statusMessage.value = '已生成副本'
    await loadKnowledge()
    await syncWorkspace()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '复制失败'
  }
}

const openDocument = (item: KnowledgeBase) => {
  if (!item.file_url) return
  window.open(getKnowledgeDocumentUrl(item.file_url), '_blank', 'noopener,noreferrer')
}

onMounted(async () => {
  resetForm()
  await loadKnowledge()
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
        data-testid="doctor-knowledge-toast"
        :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
        class="fixed left-1/2 top-6 z-[80] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full px-5 py-3 text-sm font-medium text-white shadow-xl"
      >
        {{ toastMessage }}
      </div>
    </Transition>

    <SectionTitle title="知识库管理" description="维护评估量表、治疗资料和研究文档。" />

    <div class="grid gap-4 md:grid-cols-3">
      <BaseCard v-for="item in summaryCards" :key="item.label">
        <div class="flex items-center justify-between">
          <p class="text-sm text-slate-500">{{ item.label }}</p>
          <component :is="item.icon" class="h-5 w-5 text-primary" />
        </div>
        <p class="mt-4 text-3xl font-bold text-slate-900 dark:text-white">{{ item.value }}</p>
      </BaseCard>
    </div>

    <div class="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
      <BaseCard>
        <div class="flex items-center justify-between gap-3">
          <SectionTitle
            :title="editingId ? '编辑知识' : '添加知识'"
            description="支持评估量表题目、治疗方法资料和研究文档的统一维护。"
          />
          <button
            class="rounded-[8px] border border-slate-200 px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            type="button"
            @click="startCreate"
          >
            新建
          </button>
        </div>

        <div class="mt-5 space-y-4">
          <div>
            <label class="mb-2 block text-sm text-slate-500">标题</label>
            <input
              v-model="title"
              data-testid="knowledge-title-input"
              class="w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
              placeholder="请输入知识标题"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm text-slate-500">分类</label>
            <select
              v-model="category"
              data-testid="knowledge-category-select"
              class="w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
            >
              <option value="assessment">评估量表</option>
              <option value="therapy">治疗方法</option>
              <option value="research">研究资料</option>
            </select>
          </div>

          <div>
            <label class="mb-2 block text-sm text-slate-500">标签</label>
            <input
              v-model="tags"
              class="w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
              placeholder="标签，使用逗号分隔"
            />
          </div>

          <div v-if="category === 'assessment'" class="space-y-3">
            <label class="block text-sm text-slate-500">量表题目</label>
            <div class="flex gap-2">
              <input
                v-model="newQuestionText"
                class="min-w-0 flex-1 rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
                placeholder="请输入题目文本"
                @keyup.enter="addQuestion"
              />
              <button
                class="rounded-[8px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
                type="button"
                @click="addQuestion"
              >
                添加
              </button>
            </div>
            <div class="space-y-2">
              <div
                v-for="(question, index) in scaleQuestions"
                :key="question.id"
                class="rounded-[8px] border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900"
              >
                <div class="flex items-center gap-3">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {{ index + 1 }}
                  </div>
                  <input
                    v-model="question.text"
                    class="min-w-0 flex-1 rounded-[8px] border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
                  />
                  <button class="rounded-[8px] p-2 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800" type="button" @click="moveQuestion(index, -1)">
                    <ArrowUp class="h-4 w-4" />
                  </button>
                  <button class="rounded-[8px] p-2 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800" type="button" @click="moveQuestion(index, 1)">
                    <ArrowDown class="h-4 w-4" />
                  </button>
                  <button class="rounded-[8px] p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40" type="button" @click="removeQuestion(index)">
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="space-y-4">
            <div>
              <label class="mb-2 block text-sm text-slate-500">内容说明</label>
              <textarea
                v-model="content"
                class="min-h-32 w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900"
                placeholder="请输入内容摘要、适用场景或说明"
              />
            </div>

            <div class="rounded-[8px] border border-dashed border-slate-300 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-900/80">
              <div class="flex items-start gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-[8px] bg-primary/10 text-primary">
                  <Upload class="h-5 w-5" />
                </div>
                <div class="min-w-0 flex-1">
                  <p class="font-semibold text-slate-900 dark:text-white">上传文档</p>
                  <p class="mt-1 text-sm text-slate-500">支持 PDF、Word、Excel、TXT，最大 50MB。</p>
                  <input
                    data-testid="knowledge-file-input"
                    class="mt-3 block w-full text-sm text-slate-500 file:mr-4 file:rounded-[8px] file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:font-semibold file:text-white dark:file:bg-white dark:file:text-slate-900"
                    type="file"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.txt"
                    @change="onFileChange"
                  />
                  <div v-if="uploadFile" class="mt-3 rounded-[8px] bg-white p-3 dark:bg-slate-950">
                    <div class="flex items-center justify-between gap-3">
                      <div class="min-w-0">
                        <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ uploadFile.name }}</p>
                        <p class="text-xs text-slate-500">{{ formatFileSize(uploadFile.size) }}</p>
                      </div>
                      <button class="rounded-[8px] p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40" type="button" @click="uploadFile = null">
                        <Trash2 class="h-4 w-4" />
                      </button>
                    </div>
                    <div v-if="uploading" class="mt-3">
                      <div class="mb-2 flex items-center justify-between text-xs text-slate-500">
                        <span>上传中</span>
                        <span>{{ uploadProgress }}%</span>
                      </div>
                      <div class="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                        <div class="h-full rounded-full bg-primary transition-all" :style="{ width: `${uploadProgress}%` }" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button
            data-testid="knowledge-save"
            class="w-full rounded-[8px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900"
            :disabled="saving"
            type="button"
            @click="save"
          >
            <span class="inline-flex items-center gap-2">
              <Plus class="h-4 w-4" />
              {{ saving ? '保存中...' : editingId ? '保存修改' : '添加知识' }}
            </span>
          </button>
        </div>
      </BaseCard>

      <div class="space-y-4">
        <BaseCard>
          <div class="grid gap-3 md:grid-cols-[1fr_auto]">
            <div class="relative">
              <Search class="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                v-model="searchQuery"
                class="w-full rounded-[8px] border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 dark:border-slate-800 dark:bg-slate-900"
                placeholder="搜索标题、分类、标签、内容"
              />
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="item in categories"
                :key="item.value"
                class="rounded-full px-4 py-2 text-sm transition"
                :class="selectedCategory === item.value ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'"
                type="button"
                @click="selectedCategory = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
        </BaseCard>

        <BaseCard v-if="loading">
          <p class="text-sm text-slate-500">正在加载知识库...</p>
        </BaseCard>

        <BaseCard v-else-if="filteredKnowledge.length === 0">
          <p class="text-sm text-slate-500">当前没有匹配的知识内容。</p>
        </BaseCard>

        <BaseCard v-for="item in filteredKnowledge" :key="item.id">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="rounded-full bg-info/10 px-3 py-1 text-xs font-semibold text-info">
                  {{ categories.find((entry) => entry.value === item.category)?.label || item.category }}
                </span>
                <span v-if="item.content_type === 'document'" class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                  文档
                </span>
                <span
                  v-for="tag in item.tags || []"
                  :key="tag"
                  class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-300"
                >
                  {{ tag }}
                </span>
              </div>

              <h3 class="mt-4 text-lg font-bold text-slate-900 dark:text-white">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-7 text-slate-500">{{ articleSummary(item) }}</p>

              <div v-if="item.content_type === 'document'" class="mt-3 rounded-[8px] bg-slate-50 p-3 text-sm text-slate-500 dark:bg-slate-900">
                <p class="font-semibold text-slate-700 dark:text-slate-200">{{ item.file_name || '未命名文件' }}</p>
                <p class="mt-1">{{ formatFileSize(item.file_size) }}{{ item.file_mime_type ? ` · ${item.file_mime_type}` : '' }}</p>
              </div>

              <div v-if="item.category === 'assessment'" class="mt-4 space-y-2">
                <div
                  v-for="question in parseScaleContent(item).slice(0, 3)"
                  :key="question.id"
                  class="rounded-[8px] bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300"
                >
                  {{ question.order + 1 }}. {{ question.text }}
                </div>
                <p v-if="parseScaleContent(item).length > 3" class="text-xs text-slate-400">
                  另有 {{ parseScaleContent(item).length - 3 }} 题未展开
                </p>
              </div>
            </div>

            <div class="flex shrink-0 flex-col gap-2">
              <button class="rounded-[8px] p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" type="button" title="编辑" @click="startEdit(item)">
                <Edit3 class="h-4 w-4" />
              </button>
              <button class="rounded-[8px] p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" type="button" title="复制" @click="duplicateKnowledge(item)">
                <Copy class="h-4 w-4" />
              </button>
              <button
                v-if="item.content_type === 'document' && item.file_url"
                class="rounded-[8px] p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                type="button"
                title="查看文档"
                @click="openDocument(item)"
              >
                <Eye class="h-4 w-4" />
              </button>
              <button class="rounded-[8px] p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40" type="button" title="删除" @click="removeKnowledgeItem(item)">
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
</template>
