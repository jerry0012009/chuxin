import type {
  MeditationTrack,
  MoodLevel,
} from '@/types'
import { nswMandarinMindfulnessTracks } from '@/data/nsw-mindfulness'

export const moodMeta: Record<MoodLevel, { label: string; emoji: string; tone: string }> = {
  very_good: { label: '极好', emoji: '😄', tone: 'bg-emerald-100 text-emerald-700' },
  good: { label: '不错', emoji: '😊', tone: 'bg-sky-100 text-sky-700' },
  neutral: { label: '一般', emoji: '😐', tone: 'bg-slate-100 text-slate-600' },
  bad: { label: '难过', emoji: '😔', tone: 'bg-amber-100 text-amber-700' },
  very_bad: { label: '糟糕', emoji: '😢', tone: 'bg-rose-100 text-rose-700' },
}

export const meditationTracks: MeditationTrack[] = [
  {
    id: 'm1',
    title: '焦虑缓解呼吸法',
    category: 'relax',
    duration: '3分钟',
    cover: 'from-pink-100 to-rose-100',
    emoji: '🌸',
    audio: '/srcs/music/焦虑缓解呼吸法.mp3',
    description: '用缓慢呼吸把紧绷节奏降下来，适合突发焦虑时快速使用。',
  },
  {
    id: 'm2',
    title: '睡前放松引导',
    category: 'sleep',
    duration: '15分钟',
    cover: 'from-indigo-100 to-purple-100',
    emoji: '🌙',
    audio: '/srcs/music/睡前放松引导.mp3',
    description: '降低入睡前的杂念与身体紧张，帮助建立更稳定的睡前节律。',
  },
  {
    id: 'm3',
    title: '身体扫描冥想',
    category: 'relax',
    duration: '10分钟',
    cover: 'from-amber-100 to-orange-100',
    emoji: '☀️',
    audio: '/srcs/music/身体扫描冥想.mp3',
    description: '从头到脚感知身体状态，识别被忽视的疲劳与压力。',
  },
  {
    id: 'm4',
    title: '专注力训练',
    category: 'focus',
    duration: '8分钟',
    cover: 'from-emerald-100 to-teal-100',
    emoji: '🎯',
    audio: '/srcs/music/专注力训练.mp3',
    description: '在学习和工作前使用，帮助你把注意力聚回当下。',
  },
  {
    id: 'm5',
    title: '抑郁症康复之路',
    category: 'focus',
    duration: '12分钟',
    cover: 'from-violet-100 to-purple-100',
    emoji: '🌈',
    audio: '/srcs/music/抑郁症康复之路.mp3',
    description: '以温和节奏梳理康复过程，建立对恢复的耐心和信心。',
  },
  ...nswMandarinMindfulnessTracks,
]
