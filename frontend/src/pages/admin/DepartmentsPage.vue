<script setup lang="ts">
import { Building2, CheckCircle2, Loader2, Pencil, Plus, RefreshCw, Save, ShieldCheck, Trash2 } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { createDepartment, deleteDepartment, getDepartments, updateDepartment, updateSuperAdminAccount } from '@/db/api'
import { useAuthSession } from '@/composables/useAuthSession'
import type { Department } from '@/types'

const { state: authState, refreshProfile } = useAuthSession()

const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const departments = ref<Department[]>([])
const draft = ref({ name: '', description: '', status: 'active' as Department['status'] })
const editingId = ref<string | null>(null)
const accountDraft = ref({ username: '', password: '' })

const activeDepartments = computed(() => departments.value.filter((item) => item.status === 'active'))
const inactiveDepartments = computed(() => departments.value.filter((item) => item.status === 'inactive'))

const resetDraft = () => {
  editingId.value = null
  draft.value = { name: '', description: '', status: 'active' }
}

const showStatus = (message: string) => {
  statusMessage.value = message
  window.setTimeout(() => {
    if (statusMessage.value === message) statusMessage.value = ''
  }, 2200)
}

const loadDepartments = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    departments.value = await getDepartments(true)
    if (!accountDraft.value.username) {
      accountDraft.value.username = authState.profile?.username || ''
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载部门失败'
  } finally {
    loading.value = false
  }
}

const editDepartment = (department: Department) => {
  editingId.value = department.id
  draft.value = {
    name: department.name,
    description: department.description || '',
    status: department.status,
  }
}

const saveDepartment = async () => {
  if (!draft.value.name.trim()) {
    errorMessage.value = '请填写部门名称'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    if (editingId.value) {
      await updateDepartment(editingId.value, {
        name: draft.value.name.trim(),
        description: draft.value.description.trim() || null,
        status: draft.value.status,
      })
      showStatus('部门已更新')
    } else {
      await createDepartment({
        name: draft.value.name.trim(),
        description: draft.value.description.trim() || null,
        status: draft.value.status,
      })
      showStatus('部门已新增')
    }
    resetDraft()
    await loadDepartments()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存部门失败'
  } finally {
    saving.value = false
  }
}

const deactivateDepartment = async (department: Department) => {
  if (department.status === 'inactive') return
  saving.value = true
  errorMessage.value = ''
  try {
    await deleteDepartment(department.id)
    showStatus('部门已停用')
    await loadDepartments()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '停用部门失败'
  } finally {
    saving.value = false
  }
}

const saveAccount = async () => {
  if (!accountDraft.value.username.trim()) {
    errorMessage.value = '请填写账户名'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await updateSuperAdminAccount({
      username: accountDraft.value.username.trim(),
      password: accountDraft.value.password.trim() || undefined,
    })
    accountDraft.value.password = ''
    await refreshProfile()
    showStatus('超级管理员账户已更新')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新账户失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadDepartments)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <SectionTitle title="部门管理" description="维护用户注册所属部门；管理员可按部门发布测评任务和干预任务。" />
      <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="loadDepartments">
        <RefreshCw class="h-4 w-4" />
        刷新
      </button>
    </div>

    <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-medium text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>
    <div v-if="statusMessage" class="rounded-2xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">{{ statusMessage }}</div>

    <div class="grid gap-6 xl:grid-cols-[0.86fr_1.14fr]">
      <BaseCard>
        <SectionTitle :title="editingId ? '编辑部门' : '新增部门'" description="注册页只展示启用中的部门，停用部门会保留历史用户归属。" />
        <div class="mt-5 space-y-4">
          <label class="block space-y-2 text-sm font-bold text-slate-700 dark:text-slate-200">
            <span>部门名称</span>
            <input v-model="draft.name" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="例如：心理一部" />
          </label>
          <label class="block space-y-2 text-sm font-bold text-slate-700 dark:text-slate-200">
            <span>部门说明</span>
            <textarea v-model="draft.description" class="min-h-24 w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="填写部门职责或适用人群" />
          </label>
          <label class="block space-y-2 text-sm font-bold text-slate-700 dark:text-slate-200">
            <span>状态</span>
            <select v-model="draft.status" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950">
              <option value="active">启用</option>
              <option value="inactive">停用</option>
            </select>
          </label>
          <div class="flex gap-3">
            <button class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white disabled:opacity-60" :disabled="saving" type="button" @click="saveDepartment">
              <Save class="h-4 w-4" />
              {{ editingId ? '保存修改' : '新增部门' }}
            </button>
            <button v-if="editingId" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700 dark:border-slate-800 dark:text-slate-200" type="button" @click="resetDraft">
              取消
            </button>
          </div>
        </div>

        <div class="mt-8 border-t border-slate-100 pt-6 dark:border-slate-800">
          <SectionTitle title="账户设置" description="系统只允许一个超级管理员账户；初始账户为 admin，密码 123456。" />
          <div class="mt-5 space-y-4">
            <label class="block space-y-2 text-sm font-bold text-slate-700 dark:text-slate-200">
              <span>账户名</span>
              <input v-model="accountDraft.username" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" autocomplete="username" />
            </label>
            <label class="block space-y-2 text-sm font-bold text-slate-700 dark:text-slate-200">
              <span>新密码</span>
              <input v-model="accountDraft.password" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" autocomplete="new-password" placeholder="不填写则不修改密码" type="password" />
            </label>
            <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white disabled:opacity-60 dark:bg-white dark:text-slate-900" :disabled="saving" type="button" @click="saveAccount">
              <ShieldCheck class="h-4 w-4" />
              保存账户
            </button>
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <SectionTitle title="部门列表" description="部门变化会同步到注册页和管理员发布任务页。" />
          <div class="grid grid-cols-2 gap-2 text-center text-xs">
            <span class="rounded-2xl bg-emerald-50 px-3 py-2 font-bold text-emerald-700">{{ activeDepartments.length }} 个启用</span>
            <span class="rounded-2xl bg-slate-100 px-3 py-2 font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ inactiveDepartments.length }} 个停用</span>
          </div>
        </div>

        <div v-if="loading" class="flex items-center justify-center gap-2 py-16 text-slate-500">
          <Loader2 class="h-5 w-5 animate-spin" />
          正在加载...
        </div>
        <div v-else class="mt-5 space-y-3">
          <article v-for="department in departments" :key="department.id" class="rounded-[22px] border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <Building2 class="h-4 w-4 text-slate-400" />
                  <h3 class="font-black text-slate-900 dark:text-white">{{ department.name }}</h3>
                  <span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="department.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-300'">
                    {{ department.status === 'active' ? '启用' : '停用' }}
                  </span>
                </div>
                <p class="mt-2 text-sm text-slate-500">{{ department.description || '暂无说明' }}</p>
                <p class="mt-2 text-xs font-bold text-slate-400">{{ department.user_count || 0 }} 名用户</p>
              </div>
              <div class="flex shrink-0 gap-2">
                <button class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" type="button" @click="editDepartment(department)">
                  <Pencil class="h-4 w-4" />
                  修改
                </button>
                <button
                  class="inline-flex items-center justify-center gap-2 rounded-xl border border-rose-200 px-3 py-2 text-sm font-bold text-rose-600 disabled:opacity-50"
                  :disabled="saving || department.status === 'inactive'"
                  type="button"
                  @click="deactivateDepartment(department)"
                >
                  <Trash2 class="h-4 w-4" />
                  停用
                </button>
              </div>
            </div>
          </article>

          <div v-if="departments.length === 0" class="rounded-3xl bg-slate-50 py-12 text-center text-sm text-slate-500 dark:bg-slate-900">
            <Plus class="mx-auto mb-2 h-8 w-8 text-slate-300" />
            暂无部门
          </div>
          <div v-else class="flex items-center gap-2 rounded-2xl bg-blue-50 px-4 py-3 text-sm font-medium text-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
            <CheckCircle2 class="h-4 w-4" />
            启用中的部门会出现在用户注册页。
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>
