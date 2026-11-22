import type { HealingContent, MeditationTrack } from '@/types'

export const nswMindfulnessSourceUrl =
  'https://www.mhcs.health.nsw.gov.au/campaigns-and-projects/current-campaigns/mindfulness-program-audio-resources/mandarin'

export const nswMandarinMindfulnessTrackContentIds: Record<string, string> = {
  'mhcs-mandarin-intro': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a001',
  'mhcs-mandarin-sensory-awareness': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a002',
  'mhcs-mandarin-mindful-breathing': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a003',
  'mhcs-mandarin-body-scan': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a004',
  'mhcs-mandarin-stream': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a005',
  'mhcs-mandarin-self-compassion': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a006',
  'mhcs-mandarin-emotions': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a007',
}

const nswMandarinMindfulnessKnowledgeIds: Record<string, string> = {
  'mhcs-mandarin-intro': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a201',
  'mhcs-mandarin-sensory-awareness': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a202',
  'mhcs-mandarin-mindful-breathing': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a203',
  'mhcs-mandarin-body-scan': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a204',
  'mhcs-mandarin-stream': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a205',
  'mhcs-mandarin-self-compassion': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a206',
  'mhcs-mandarin-emotions': 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a207',
}

export const nswMandarinMindfulnessTracks: MeditationTrack[] = [
  {
    id: 'mhcs-mandarin-intro',
    title: '普通话正念练习导言',
    category: 'relax',
    duration: '4分钟',
    cover: 'from-cyan-100 to-blue-100',
    emoji: '🪷',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_Intro.mp3',
    description: '来自 NSW Multicultural Health Communication Service 的普通话正念音频，适合开始练习前了解正念方法。',
  },
  {
    id: 'mhcs-mandarin-sensory-awareness',
    title: '感官觉察练习',
    category: 'relax',
    duration: '7分钟',
    cover: 'from-emerald-100 to-teal-100',
    emoji: '🌿',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_SensoryAwareness.mp3',
    description: '通过声音、触觉和身体感受把注意力带回当下，适合压力升高时使用。',
  },
  {
    id: 'mhcs-mandarin-mindful-breathing',
    title: '正念呼吸练习',
    category: 'relax',
    duration: '9分钟',
    cover: 'from-sky-100 to-cyan-100',
    emoji: '🌬️',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_MindfulBreathing.mp3',
    description: '以呼吸作为稳定锚点，帮助觉察杂念并温和回到当前体验。',
  },
  {
    id: 'mhcs-mandarin-body-scan',
    title: '身体扫描练习',
    category: 'sleep',
    duration: '12分钟',
    cover: 'from-indigo-100 to-sky-100',
    emoji: '🧘',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_BodyScan.mp3',
    description: '逐步觉察身体各部位的紧张和放松，适合睡前或身心疲惫时练习。',
  },
  {
    id: 'mhcs-mandarin-stream',
    title: '溪流意象练习',
    category: 'focus',
    duration: '11分钟',
    cover: 'from-teal-100 to-cyan-100',
    emoji: '💧',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_Stream.mp3',
    description: '借助溪流意象观察念头流动，练习不被想法牵走的心理距离。',
  },
  {
    id: 'mhcs-mandarin-self-compassion',
    title: '自我慈悲练习',
    category: 'relax',
    duration: '11分钟',
    cover: 'from-rose-100 to-pink-100',
    emoji: '💗',
    audio: '/srcs/music/mhcs-mandarin/Mandarin-Self-Compassion.mp3',
    description: '用更温和的态度回应压力、挫败和自责，适合作为情绪低落时的支持练习。',
  },
  {
    id: 'mhcs-mandarin-emotions',
    title: '情绪觉察练习',
    category: 'focus',
    duration: '15分钟',
    cover: 'from-violet-100 to-fuchsia-100',
    emoji: '🌈',
    audio: '/srcs/music/mhcs-mandarin/Mandarin_Emotions.mp3',
    description: '练习识别、命名并容纳情绪体验，帮助减少对情绪的回避和压抑。',
  },
]

const practiceGuides: Record<string, string> = {
  'mhcs-mandarin-intro': `这张卡片对应“普通话正念练习导言”。它适合第一次接触这组音频时先阅读和收听，帮助用户理解正念练习的基本态度。

适用场景：
1. 第一次使用普通话正念素材。
2. 想了解正念和普通放松训练有什么区别。
3. 练习前需要先建立安全、稳定、不过度追求效果的心态。

练习提示：
可以把导言当作进入练习前的准备。收听时不需要强迫自己立刻平静，只要留意身体姿势、呼吸节奏和当前感受即可。`,
  'mhcs-mandarin-sensory-awareness': `这张卡片对应“感官觉察练习”。练习重点是通过听觉、触觉、身体接触点等感官线索，把注意力从反复思考带回当下。

适用场景：
1. 焦虑、紧张或注意力涣散时。
2. 需要在短时间内稳定身心时。
3. 不适合做闭眼深度练习，但可以做轻量觉察时。

练习提示：
练习时可以睁眼或闭眼。若出现不适，优先感受脚底触地、椅子支撑和周围声音，帮助自己回到稳定状态。`,
  'mhcs-mandarin-mindful-breathing': `这张卡片对应“正念呼吸练习”。练习重点是把呼吸作为注意力锚点，发现走神后温和地回到呼吸。

适用场景：
1. 情绪波动、压力升高或睡前难以安静时。
2. 想建立每日短时正念习惯时。
3. 需要训练觉察力和专注稳定度时。

练习提示：
不要刻意控制呼吸长短。注意力跑开是正常现象，关键是发现之后重新回到一次吸气或呼气。`,
  'mhcs-mandarin-body-scan': `这张卡片对应“身体扫描练习”。练习会逐步把注意力放到身体不同部位，帮助识别紧张、疲劳和放松感。

适用场景：
1. 睡前放松。
2. 身体紧绷、久坐疲劳或压力后恢复。
3. 想增强身体觉察，而不是继续停留在头脑思考中。

练习提示：
如果某个部位没有明显感觉，也不需要制造感觉。只要知道“此刻没有明显感觉”，然后继续跟随引导移动注意力。`,
  'mhcs-mandarin-stream': `这张卡片对应“溪流意象练习”。练习借助溪流意象观察念头出现、停留和离开，训练与想法保持距离。

适用场景：
1. 反复担忧、复盘或陷入内耗时。
2. 被某个念头牵着走，难以抽离时。
3. 想学习不压制想法，但也不被想法控制时。

练习提示：
可以把念头想象成溪流上的叶子或水面漂过的事物。练习目标不是消灭念头，而是看见它们正在变化。`,
  'mhcs-mandarin-self-compassion': `这张卡片对应“自我慈悲练习”。练习重点是用更温和、更有人情味的方式回应压力、挫败和自责。

适用场景：
1. 自责、羞愧或低落时。
2. 对自己要求过高、难以休息时。
3. 经历失败、冲突或挫折后需要恢复时。

练习提示：
自我慈悲不是纵容自己，而是在困难时减少二次伤害。可以把对朋友说的话，尝试用同样语气说给自己。`,
  'mhcs-mandarin-emotions': `这张卡片对应“情绪觉察练习”。练习帮助用户识别、命名并容纳情绪，减少对情绪的回避和压抑。

适用场景：
1. 情绪复杂、说不清自己怎么了时。
2. 容易压抑情绪或被情绪淹没时。
3. 想建立情绪记录和调节能力时。

练习提示：
可以先给情绪一个简单名字，例如“紧张”“委屈”“烦躁”。命名不是评判，而是让自己更清楚地看见正在发生什么。`,
}

const timestamp = '2026-07-02T00:00:00.000Z'

export const nswMandarinMindfulnessArticleTitle = '普通话正念音频资源'

export const nswMandarinMindfulnessArticleBody = `这组普通话正念音频整理自 NSW Multicultural Health Communication Service 的 Mindfulness Program Audio Resources。素材包括导言、感官觉察、正念呼吸、身体扫描、溪流意象、自我慈悲和情绪觉察等练习。

使用建议：
1. 初次使用可以先听“普通话正念练习导言”，了解练习方式。
2. 情绪紧张或焦虑时，可以选择“感官觉察练习”或“正念呼吸练习”。
3. 睡前或身体疲惫时，可以选择“身体扫描练习”。
4. 反复陷入想法或情绪时，可以选择“溪流意象练习”“自我慈悲练习”或“情绪觉察练习”。

正念练习不是为了立刻清空想法，而是训练自己觉察当下经验，并以更稳定、更友善的方式回应压力。若练习过程中出现明显不适，可以暂停音频，回到睁眼、慢呼吸和感受脚底触地等稳定动作。`

export const nswMandarinMindfulnessArticleBodies: Record<string, string> = {
  [nswMandarinMindfulnessArticleTitle]: nswMandarinMindfulnessArticleBody,
  ...Object.fromEntries(
    nswMandarinMindfulnessTracks.map((track) => [
      `${track.title}说明`,
      `${practiceGuides[track.id]}

音频入口：
请在“冥想”页签中选择“${track.title}”播放完整普通话练习音频。

素材来源：
NSW Multicultural Health Communication Service - Mindfulness Program Audio Resources (Mandarin)
${nswMindfulnessSourceUrl}`,
    ]),
  ),
}

export const nswMandarinMindfulnessContents: HealingContent[] = [
  ...nswMandarinMindfulnessTracks.map((track, index) => ({
    id: nswMandarinMindfulnessTrackContentIds[track.id]!,
    title: track.title,
    description: track.description,
    category: track.category,
    content_type: 'audio',
    content_url: track.audio,
    duration: Number(track.duration.match(/\d+/)?.[0] || 1) * 60,
    thumbnail_url: '',
    author: 'NSW Multicultural Health Communication Service',
    tags: ['正念', '普通话', '音频', 'NSW'],
    is_active: true,
    view_count: 0,
    like_count: 0,
    created_at: timestamp,
    updated_at: timestamp,
  })),
  ...nswMandarinMindfulnessTracks.map((track) => ({
    id: nswMandarinMindfulnessKnowledgeIds[track.id]!,
    title: `${track.title}说明`,
    description: `${track.description} 点击查看适用场景、练习提示和对应冥想入口。`,
    category: 'knowledge',
    content_type: 'article',
    content_url: '',
    duration: 0,
    thumbnail_url: '',
    author: 'NSW Multicultural Health Communication Service',
    tags: ['正念', '普通话', '练习说明', '知识卡片'],
    is_active: true,
    view_count: 0,
    like_count: 0,
    created_at: timestamp,
    updated_at: timestamp,
  })),
  {
    id: 'b4a3c4a0-31d3-4c42-8c0d-fd2b1d24a101',
    title: nswMandarinMindfulnessArticleTitle,
    description: '整理自 NSW Multicultural Health Communication Service 的普通话正念音频资源，包含使用建议和练习入口。',
    category: 'knowledge',
    content_type: 'article',
    content_url: nswMindfulnessSourceUrl,
    duration: 0,
    thumbnail_url: '',
    author: 'NSW Multicultural Health Communication Service',
    tags: ['正念', '普通话', '疗愈素材', '音频资源'],
    is_active: true,
    view_count: 0,
    like_count: 0,
    created_at: timestamp,
    updated_at: timestamp,
  },
]
