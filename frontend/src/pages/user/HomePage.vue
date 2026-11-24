<script setup lang="ts">
import { Activity, ArrowRight, Brain, BrainCircuit, CalendarDays, ClipboardList, Gamepad2, Heart, NotebookPen } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import { assessmentItemName, nextAssessmentItem } from '@/lib/assessment-display'
import { publicAssetUrl } from '@/utils/public-assets'
import { getMyAssessmentPublishTasks, getMyInterventionTodayTasks, getMyScaleRecords } from '@/db/api'
import type { AssessmentPublishAssignee, InterventionTodayResponse, ScaleDistributionRecord } from '@/types'

const { state: auth } = useAuthSession()
const tasks = ref<AssessmentPublishAssignee[]>([])
const today = ref<InterventionTodayResponse | null>(null)
const records = ref<ScaleDistributionRecord[]>([])
const loading = ref(Boolean(auth.user))
const failed = ref<string[]>([])
const current = computed(() => tasks.value.find((task) => ['pending', 'in_progress'].includes(task.status)))
const required = computed(() => (current.value?.items || []).filter((item) => item.required !== false))
const done = computed(() => required.value.filter((item) => ['completed', 'unsupported'].includes(item.status)).length)
const nextItem = computed(() => nextAssessmentItem(current.value?.items || []))
const continuing = computed(() => current.value?.status === 'in_progress' || current.value?.items?.some((item) => item.status === 'in_progress' || item.status === 'completed'))
const displayName = computed(() => auth.profile?.full_name || auth.profile?.username || '用户')
const todayLabel = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full' }).format(new Date())
const dateLabel = (date?: string | null) => date ? new Date(date).toLocaleDateString('zh-CN') : ''
const links = [
  { title: '量表测评', to: '/scale-assessment', icon: ClipboardList },
  { title: 'AI 多模态评估', to: '/assessment', icon: Activity, test: 'home-feature-assessment' },
  { title: '神经心理', to: '/neuropsych-assessment', icon: Brain },
  { title: '脑机调控', to: '/brain-intervention', icon: BrainCircuit },
  { title: '情绪记录', to: '/record', icon: NotebookPen, test: 'home-feature-record' },
  { title: '放松疗愈', to: '/healing', icon: Heart, test: 'home-feature-healing' },
  { title: '疗愈游戏', to: { path: '/healing', state: { activeTab: 'game' } }, icon: Gamepad2, test: 'home-game-card' },
]

async function load() {
  if (!auth.user) return
  loading.value = true
  failed.value = []
  await Promise.all([
    getMyAssessmentPublishTasks().then((result) => { tasks.value = result }).catch(() => { failed.value.push('测评任务') }),
    getMyInterventionTodayTasks().then((result) => { today.value = result }).catch(() => { failed.value.push('今日干预') }),
    getMyScaleRecords().then((result) => {
      records.value = result.filter((record) => record.status === 'completed' && record.calc_status === 'done')
        .sort((a, b) => (b.completed_at || b.sent_at).localeCompare(a.completed_at || a.sent_at)).slice(0, 3)
    }).catch(() => { failed.value.push('测评记录') }),
  ])
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div class="workbench">
    <header class="service-width workbench-intro">
      <div><h1>我的工作台</h1><p v-if="auth.user">您好，{{ displayName }}</p></div>
      <p class="workbench-date"><CalendarDays aria-hidden="true" />{{ todayLabel }}</p>
    </header>

    <section class="work-scene" aria-labelledby="work-current-heading" data-testid="work-current">
      <div class="service-width work-scene-inner">
        <img class="work-scene-art" :src="publicAssetUrl('images/potala-workbench.webp')" alt="" />
        <div class="work-scene-copy">
          <div class="work-scene-meta">
            <p class="work-eyebrow">当前测评</p>
            <ServiceStatus v-if="current" :tone="continuing ? 'active' : 'idle'" class="work-task-status">{{ continuing ? '进行中' : '待开始' }}</ServiceStatus>
          </div>
          <h2 id="work-current-heading">{{ current?.batch_title || (current ? '测评任务' : loading ? '正在加载测评…' : failed.includes('测评任务') ? '测评暂不可用' : auth.user ? '暂无待办测评' : '登录后查看测评') }}</h2>
        </div>
        <div class="work-scene-bar">
          <div v-if="required.length" class="work-progress">
            <div class="work-progress-label">
              <strong aria-hidden="true">{{ done }}<small> / {{ required.length }}</small></strong>
              <span class="sr-only">已完成 {{ done }} / {{ required.length }} 项</span><span aria-hidden="true">已完成</span>
            </div>
            <div class="work-progress-meter">
              <ProgressBar :value="done / required.length * 100" label="当前测评完成进度" />
            </div>
          </div>
          <p v-if="nextItem" class="work-next"><span>下一步</span><strong>{{ assessmentItemName(nextItem) }}</strong></p>
          <RouterLink v-if="auth.user" :to="current ? `/assessment-tasks/${current.id}` : '/assessment-tasks'" class="service-button work-continue" data-testid="work-current-link">{{ nextItem ? (continuing ? '继续测评' : '开始测评') : '查看测评任务' }} <ArrowRight aria-hidden="true" /></RouterLink>
          <RouterLink v-else to="/login" class="service-button work-continue">账号登录 <ArrowRight aria-hidden="true" /></RouterLink>
        </div>
      </div>
    </section>

    <div class="service-width workbench-body">
      <p v-if="loading" class="sr-only" role="status">正在加载个人事项…</p>
      <div v-if="failed.length" class="work-feedback" role="alert">
        <p>{{ failed.join('、') }}加载失败。</p><button class="service-button service-outline" type="button" @click="load">重试</button>
      </div>

      <section v-if="auth.user" class="work-grid" aria-label="个人事项">
        <article class="work-agenda" data-testid="work-intervention">
          <header class="work-section-heading">
            <h2>今日干预</h2>
            <p v-if="today?.tasks.length">已完成 <strong>{{ today.summary.completed }} / {{ today.summary.total }} 项</strong></p>
          </header>
          <template v-if="today?.tasks.length">
            <ul class="work-list">
              <li v-for="task in today.tasks.slice(0, 3)" :key="task.id" class="work-intervention-row">
                <RouterLink :to="task.navigation_path || task.route_path || '/healing'" class="service-link break-words">{{ task.title }}</RouterLink>
                <ServiceStatus :tone="task.status === 'completed' ? 'done' : task.status === 'in_progress' ? 'active' : 'idle'">{{ task.status === 'completed' ? '已完成' : task.status === 'in_progress' ? '进行中' : task.status === 'expired' ? '已过期' : '待完成' }}</ServiceStatus>
              </li>
            </ul>
          </template>
          <p v-else-if="loading" class="work-empty">正在加载干预任务…</p>
          <p v-else-if="!failed.includes('今日干预')" class="work-empty">今日暂无干预任务。</p>
          <RouterLink to="/profile/healing-plan" class="work-action service-link">查看干预计划 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>

        <article class="work-records" data-testid="work-records">
          <header class="work-section-heading"><h2>测评记录</h2></header>
          <ul v-if="records.length" class="work-list">
            <li v-for="record in records" :key="record.id" class="work-record-row">
              <RouterLink :to="{ path: '/scale-assessment', query: { recordId: record.id } }" class="service-link">{{ record.survey_title || record.survey?.title || '量表测评报告' }}</RouterLink>
              <p>{{ dateLabel(record.completed_at || record.sent_at) }}</p>
            </li>
          </ul>
          <p v-else-if="loading" class="work-empty">正在加载测评记录…</p>
          <p v-else-if="!failed.includes('测评记录')" class="work-empty">暂无已完成的量表测评。</p>
          <RouterLink :to="{ path: '/scale-assessment', query: { tab: 'completed' } }" class="work-action service-link">查看量表记录 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>
      </section>

    <section aria-labelledby="work-services">
      <h2 id="work-services" class="work-services-title">常用服务</h2>
      <div class="work-service-grid">
        <RouterLink v-for="link in links" :key="link.title" :to="link.to" :data-testid="link.test" class="work-service">
          <component :is="link.icon" class="work-service-icon" aria-hidden="true" /><span>{{ link.title }}</span><ArrowRight class="work-service-arrow" aria-hidden="true" />
        </RouterLink>
      </div>
    </section>
    </div>
  </div>
</template>

<style scoped>
.workbench-intro { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 6px 24px; padding-block: 24px 20px; }
.workbench-intro h1 { font-size: 24px; font-weight: 730; }
.workbench-intro p { margin-top: 3px; color: var(--service-muted); font-size: 14px; overflow-wrap: anywhere; }
.workbench-intro .workbench-date { display: flex; align-items: center; gap: 7px; font-size: 13px; }
.workbench-date svg, .work-action svg { width: 16px; height: 16px; }
.work-scene { background: #ede4d6; border-block: 1px solid #ccba9e; }
.work-scene-inner { position: relative; isolation: isolate; }
.work-scene-art { position: absolute; z-index: -1; right: 0; bottom: 0; width: min(64%, 750px); height: 100%; object-fit: contain; object-position: right bottom; opacity: .92; mask-image: linear-gradient(90deg, transparent, #000 18%, #000 93%, transparent); }
.work-scene-copy { display: grid; align-content: center; gap: 16px; min-height: 220px; max-width: 52%; padding-block: 30px; }
.work-scene-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; }
.work-eyebrow { display: flex; align-items: center; gap: 9px; color: var(--service-deep); font-size: 13px; font-weight: 700; }
.work-eyebrow::before { content: ''; width: 22px; height: 1px; background: #997043; }
.work-scene-copy h2 { max-width: 14em; color: #302525; font-size: 43px; font-weight: 760; line-height: 1.24; text-wrap: balance; }
.work-scene-bar { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, .8fr) auto; align-items: center; gap: 18px 24px; padding: 15px 22px; border-top: 2px solid var(--service-gold); background: #fffdfa; }
.work-progress { min-width: 0; display: grid; gap: 8px; }
.work-progress-label { display: flex; flex-wrap: wrap; align-items: baseline; gap: 3px 12px; font-variant-numeric: tabular-nums; }
.work-progress-label > strong { color: var(--service-deep); font-size: 29px; line-height: 1; }
.work-progress-label small { color: var(--service-muted); font-size: 17px; font-weight: 550; }
.work-progress-label > span, .work-next span { color: var(--service-muted); font-size: 12px; }
.work-next { grid-column: 2; display: grid; gap: 3px; padding-left: 24px; border-left: 1px solid var(--service-border); overflow-wrap: anywhere; }
.work-next strong { font-size: 16px; }
.work-continue { grid-column: 3; white-space: nowrap; }
.workbench-body { display: grid; gap: 24px; padding-block: 24px 40px; }
.work-feedback { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; font-size: 14px; }
.work-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 30px; }
.work-section-heading { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 4px 12px; padding-bottom: 9px; border-bottom: 1px solid #bdb1a1; }
.work-section-heading h2, .work-services-title { font-size: 19px; font-weight: 720; }
.work-section-heading p, .work-record-row p { color: var(--service-muted); font-size: 13px; font-variant-numeric: tabular-nums; }
.work-list { font-size: 14px; }
.work-list li { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; border-bottom: 1px solid var(--workspace-line); }
.work-list a { min-height: 44px; padding-block: 12px; overflow-wrap: anywhere; color: var(--service-ink); }
.work-list a:hover { color: var(--service-red); }
.work-empty { padding: 14px 0; color: var(--service-muted); font-size: 14px; }
.work-action { display: inline-flex; gap: 7px; align-items: center; min-height: 44px; font-size: 14px; }
.work-services-title { margin-bottom: 8px; }
.work-service-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0 18px; border-top: 1px solid #bdb1a1; }
.work-service { display: flex; align-items: center; gap: 8px; min-height: 46px; padding: 7px 3px; border-bottom: 1px solid var(--workspace-line); overflow-wrap: anywhere; font-size: 14px; }
.work-service:hover { color: var(--service-red); background: var(--workspace-warm); }
.work-service-icon { width: 18px; height: 18px; color: var(--service-red); }
.work-service-arrow { width: 14px; height: 14px; margin-left: auto; color: var(--service-muted); }
@media (max-width: 760px) {
  .workbench-intro { padding-block: 16px 13px; }
  .workbench-intro h1 { font-size: 21px; }
  .work-scene-art { right: -16px; width: min(100%, 480px); height: auto; bottom: auto; top: 4px; opacity: .49; mask-image: linear-gradient(90deg, transparent 5%, #000 57%), linear-gradient(0deg, transparent, #000 30%); mask-composite: intersect; }
  .work-scene-copy { min-height: 145px; max-width: none; gap: 10px; padding-block: 16px; }
  .work-scene-copy h2 { max-width: 12em; font-size: 30px; text-wrap: initial; }
  .work-scene-bar { grid-template-columns: minmax(0, 1fr); gap: 12px; padding: 12px; }
  .work-next, .work-continue { grid-column: 1; }
  .work-next { grid-template-columns: auto minmax(0, 1fr); align-items: baseline; gap: 10px; border-left: 0; padding: 0; }
  .work-progress-label > strong { font-size: 23px; }
  .workbench-body { gap: 20px; padding-block: 20px 28px; }
  .work-grid { grid-template-columns: minmax(0, 1fr); gap: 18px; }
  .work-service-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 12px; }
}
</style>
