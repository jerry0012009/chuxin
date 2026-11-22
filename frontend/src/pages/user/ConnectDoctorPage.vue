<script setup lang="ts">
import {
  Award,
  Bell,
  Check,
  ChevronLeft,
  Clock,
  MapPin,
  MessageCircle,
  Search,
  ShieldCheck,
  Star,
  UserCheck,
  Video,
  X,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'

interface DoctorCard {
  id: string
  name: string
  title: string
  specialty: string
  hospital: string
  rating: number
  reviews: number
  experience: string
  tags: string[]
  avatar: string
  status: 'online' | 'busy' | 'offline'
  desc: string
  price: string
}

const router = useRouter()

const searchQuery = ref('')
const activeTab = ref('全部管理员')
const selectedDoctor = ref<DoctorCard | null>(null)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error' | 'info'>('info')
let toastTimer: number | null = null

const tabs = ['全部管理员', '专家门诊', '在线咨询', '视频问诊', '心理咨询']
const doctors: DoctorCard[] = [
  {
    id: '1',
    name: '陈管理员',
    title: '主任管理员',
    specialty: '重度抑郁 / 焦虑障碍',
    hospital: '上海精神卫生中心',
    rating: 4.9,
    reviews: 128,
    experience: '15年经验',
    tags: ['专业亲和', '回复及时'],
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=doctor1',
    status: 'online',
    desc: '擅长各类心理障碍的个性化治疗方案，拥有多年临床经验，特别是在焦虑症与抑郁症的联合疗法上有深厚造诣。',
    price: '¥299/次',
  },
  {
    id: '2',
    name: '李教授',
    title: '资深心理咨询师',
    specialty: '青少年心理 / 家庭关系',
    hospital: '初心在线中心',
    rating: 4.8,
    reviews: 256,
    experience: '12年经验',
    tags: ['资深导师', '逻辑清晰'],
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=doctor2',
    status: 'busy',
    desc: '深耕青少年心理辅导多年，在处理家庭冲突、学业压力及青春期叛逆等方面有着丰富的咨询案例。',
    price: '¥199/次',
  },
  {
    id: '3',
    name: '王管理员',
    title: '副主任管理员',
    specialty: '睡眠障碍 / 职场压力',
    hospital: '华山医院心理科',
    rating: 4.7,
    reviews: 89,
    experience: '8年经验',
    tags: ['耐心周到', '方案落地'],
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=doctor3',
    status: 'offline',
    desc: '专注于失眠症及现代职场压力引发的各种身心问题，主张药物与心理引导相结合的综合治疗。',
    price: '¥249/次',
  },
]

const filteredDoctors = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return doctors.filter((doctor) =>
    !keyword ||
    [doctor.name, doctor.specialty, doctor.hospital].some((value) => value.toLowerCase().includes(keyword)),
  )
})

const showToast = (message: string, tone: 'success' | 'error' | 'info' = 'info', duration = 1800) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const handleTabClick = (tab: string) => {
  activeTab.value = tab
  if (tab !== '全部管理员') {
    showToast(`已切换至: ${tab}`, 'info')
  }
}

const showAllDoctors = () => {
  showToast('已为您显示全部可用专家列表', 'success')
}

const handleGuaranteeClick = (label: string) => {
  showToast(`初心保障：${label}。我们严格筛选每一位合作专家，确保提供最专业、最安全的心理咨询服务。`, 'info', 2600)
}

const handleTextConsult = (doctor: DoctorCard) => {
  showToast(`正在为您连接 ${doctor.name} 的图文咨询窗口...`, 'success', 1500)
  window.setTimeout(() => {
    void router.push('/assessment')
  }, 1500)
}

const handleVideoBooking = (doctor: DoctorCard) => {
  if (doctor.status === 'offline') {
    showToast(`${doctor.name} 目前不在线，请稍后再试或通过预约系统预约。`, 'error')
    return
  }
  showToast(`视频问诊申请已发送给 ${doctor.name}，请在挂号处确认时间。`, 'success')
}

onBeforeUnmount(() => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 dark:bg-slate-950">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : toastTone === 'success' ? 'bg-emerald-600 shadow-emerald-900/20' : 'bg-slate-950 shadow-slate-900/20'"
      data-testid="connect-doctor-toast"
    >
      {{ toastMessage }}
    </div>
    <div class="sticky top-0 z-30 border-b border-slate-100 bg-white/85 px-4 pb-6 pt-4 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/85">
      <div class="mx-auto flex max-w-3xl items-center justify-between">
        <div class="flex items-center gap-3">
          <button class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200" @click="router.back()">
            <ChevronLeft class="h-5 w-5" />
          </button>
          <h1 class="text-lg font-black text-slate-900 dark:text-white">对接管理员</h1>
        </div>
        <button class="relative flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400 dark:bg-slate-800" @click="showToast('目前暂无新的管理员动态', 'info')">
          <Bell class="h-5 w-5" />
        </button>
      </div>

      <div class="relative mx-auto mt-4 max-w-3xl">
        <Search class="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          v-model="searchQuery"
          class="h-12 w-full rounded-2xl border-0 bg-slate-100 pl-11 pr-11 text-sm outline-none ring-0 focus:ring-2 focus:ring-primary/20 dark:bg-slate-800 dark:text-white"
          data-testid="connect-doctor-search"
          placeholder="搜索管理员、科室、疾病..."
        />
        <button v-if="searchQuery" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400" @click="searchQuery = ''">
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>

    <main class="mx-auto max-w-3xl px-4 pt-6">
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="tab in tabs"
          :key="tab"
          class="whitespace-nowrap rounded-2xl px-5 py-2 text-xs font-black transition"
          :class="activeTab === tab ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-200/70' : 'bg-white text-slate-500 shadow-sm dark:bg-slate-900 dark:text-slate-400'"
          @click="handleTabClick(tab)"
        >
          {{ tab }}
        </button>
      </div>

      <div class="mt-6 flex items-center justify-between px-1">
        <h2 class="flex items-center gap-2 text-sm font-black uppercase tracking-[0.1em] text-slate-800 dark:text-slate-200">
          <Star class="h-4 w-4 fill-amber-500 text-amber-500" />
          推荐专家
        </h2>
        <button class="text-xs font-black text-indigo-600" @click="showAllDoctors">查看全部</button>
      </div>

      <div v-if="filteredDoctors.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-400">
        <Search class="h-12 w-12 text-slate-200" />
        <p class="mt-4 text-sm font-bold">未找到匹配的专家，换个搜索词试试？</p>
      </div>

      <div v-else class="mt-5 space-y-5">
        <BaseCard
          v-for="doctor in filteredDoctors"
          :key="doctor.id"
          class="cursor-pointer overflow-hidden border-0 bg-white shadow-xl shadow-slate-200/50 dark:bg-slate-900 dark:shadow-none"
          data-testid="connect-doctor-card"
          @click="selectedDoctor = doctor"
        >
          <div class="flex gap-5">
            <div class="relative">
              <img :src="doctor.avatar" :alt="doctor.name" class="h-16 w-16 rounded-[20px] border-2 border-white bg-indigo-50 object-cover shadow-md" />
              <span
                class="absolute -bottom-1 -right-1 h-5 w-5 rounded-full border-[3px] border-white"
                :class="doctor.status === 'online' ? 'bg-emerald-500' : doctor.status === 'busy' ? 'bg-amber-500' : 'bg-slate-300'"
              />
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-3">
                <div class="flex min-w-0 items-center gap-2">
                  <h3 class="truncate text-base font-black text-slate-800 dark:text-slate-100">{{ doctor.name }}</h3>
                  <span class="rounded bg-slate-50 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:bg-slate-800">{{ doctor.title }}</span>
                </div>
                <div class="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 dark:bg-amber-900/20">
                  <Star class="h-3 w-3 fill-amber-500 text-amber-500" />
                  <span class="text-[10px] font-black text-amber-600 dark:text-amber-400">{{ doctor.rating.toFixed(1) }}</span>
                </div>
              </div>
              <p class="mt-1.5 text-[11px] font-black text-indigo-500">{{ doctor.specialty }}</p>
              <div class="mt-1.5 flex items-center gap-2 text-[10px] font-bold text-slate-400">
                <MapPin class="h-3.5 w-3.5 text-slate-300" />
                <span class="truncate">{{ doctor.hospital }}</span>
                <span class="h-1 w-1 rounded-full bg-slate-200" />
                <span class="whitespace-nowrap">{{ doctor.experience }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4 flex items-center gap-2">
            <span v-for="tag in doctor.tags" :key="tag" class="rounded-lg bg-slate-100 px-2.5 py-1 text-[9px] font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
              {{ tag }}
            </span>
            <div class="flex-1" />
            <span class="text-[11px] font-black text-slate-700 dark:text-slate-200">{{ doctor.price }}</span>
          </div>

          <div class="mt-5 grid grid-cols-2 gap-3">
            <button
              class="inline-flex h-11 items-center justify-center rounded-2xl border border-slate-100 text-xs font-black text-slate-600 transition hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
              data-testid="connect-doctor-text"
              @click.stop="handleTextConsult(doctor)"
            >
              <MessageCircle class="mr-2 h-4 w-4 text-indigo-500" />
              图文咨询
            </button>
            <button
              class="inline-flex h-11 items-center justify-center rounded-2xl bg-indigo-500 text-xs font-black text-white shadow-lg shadow-indigo-100 transition hover:bg-indigo-600 disabled:opacity-60 dark:shadow-none"
              data-testid="connect-doctor-video"
              @click.stop="handleVideoBooking(doctor)"
            >
              <Video class="mr-2 h-4 w-4" />
              预约视频
            </button>
          </div>
        </BaseCard>
      </div>

      <div class="mt-8 grid grid-cols-2 gap-y-6 rounded-[32px] border border-emerald-100/60 bg-emerald-50/60 p-8 dark:border-emerald-900/40 dark:bg-emerald-950/10">
        <button v-for="item in [
          { icon: ShieldCheck, label: '隐私严格加密' },
          { icon: UserCheck, label: '执业资格认证' },
          { icon: Award, label: '三甲名医资源' },
          { icon: Clock, label: '7x24h 在线响应' },
        ]" :key="item.label" class="flex items-center gap-3 text-left" @click="handleGuaranteeClick(item.label)">
          <span class="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-100 shadow-inner dark:bg-emerald-900/30">
            <component :is="item.icon" class="h-4 w-4 text-emerald-600" />
          </span>
          <span class="text-[11px] font-black text-slate-600 dark:text-slate-400">{{ item.label }}</span>
        </button>
      </div>
    </main>

    <div v-if="selectedDoctor" class="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-4 backdrop-blur-sm sm:items-center" data-testid="connect-doctor-dialog" @click.self="selectedDoctor = null">
      <div class="w-full max-w-md overflow-hidden rounded-[32px] bg-white p-8 shadow-2xl dark:bg-slate-900">
        <div class="flex gap-6">
          <img :src="selectedDoctor.avatar" :alt="selectedDoctor.name" class="h-24 w-24 rounded-[24px] border-4 border-white bg-indigo-50 object-cover shadow-xl" />
          <div class="flex-1 pt-2">
            <div class="flex items-center gap-3">
              <h2 class="text-2xl font-black text-slate-800 dark:text-white">{{ selectedDoctor.name }}</h2>
              <span class="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-500">{{ selectedDoctor.title }}</span>
            </div>
            <div class="mt-3 flex items-center gap-4">
              <span class="inline-flex items-center gap-1 text-sm font-black">
                <Star class="h-4 w-4 fill-amber-500 text-amber-500" />
                {{ selectedDoctor.rating.toFixed(1) }}
              </span>
              <span class="h-3 w-px bg-slate-200" />
              <span class="text-sm font-bold text-slate-400">{{ selectedDoctor.reviews }} 条评价</span>
            </div>
          </div>
        </div>

        <div class="mt-8 space-y-6">
          <div>
            <h4 class="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400">
              <Check class="h-4 w-4 text-emerald-500" />
              医疗背景
            </h4>
            <div class="mt-3 rounded-2xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/80">
              <p class="text-sm font-black text-slate-700 dark:text-slate-200">{{ selectedDoctor.hospital }}</p>
              <p class="mt-2 text-xs font-bold text-slate-500">{{ selectedDoctor.specialty }}</p>
            </div>
          </div>
          <p class="text-xs font-bold leading-7 text-slate-500 dark:text-slate-400">{{ selectedDoctor.desc }}</p>
        </div>

        <div class="mt-8 grid grid-cols-2 gap-4">
          <button class="h-14 rounded-2xl border border-slate-100 text-sm font-black text-slate-500 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800" @click="handleTextConsult(selectedDoctor)">
            图文咨询
          </button>
          <button class="h-14 rounded-2xl bg-indigo-500 text-sm font-black text-white shadow-xl shadow-indigo-100 hover:bg-indigo-600 dark:shadow-none" data-testid="connect-doctor-apply" @click="handleVideoBooking(selectedDoctor)">
            立即预约
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
