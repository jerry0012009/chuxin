import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'
import UserLayout from '@/layouts/UserLayout.vue'
import LoginPage from '@/pages/auth/LoginPage.vue'
import AssessmentPage from '@/pages/user/AssessmentPage.vue'
import ConnectDoctorPage from '@/pages/user/ConnectDoctorPage.vue'
import HealingPage from '@/pages/user/HealingPage.vue'
import HealingPlanPage from '@/pages/user/HealingPlanPage.vue'
import HomePage from '@/pages/user/HomePage.vue'
import ProfilePage from '@/pages/user/ProfilePage.vue'
import ScaleAssessmentPage from '@/pages/user/ScaleAssessmentPage.vue'
import AssessmentTaskCenterPage from '@/pages/user/AssessmentTaskCenterPage.vue'
import NeuropsychAssessmentPage from '@/pages/user/NeuropsychAssessmentPage.vue'
import BrainInterventionPage from '@/pages/user/BrainInterventionPage.vue'
import BrainInterventionReportsPage from '@/pages/user/BrainInterventionReportsPage.vue'
import PersonalInfoPage from '@/pages/user/PersonalInfoPage.vue'
import PrivacySettingsPage from '@/pages/user/PrivacySettingsPage.vue'
import RecordPage from '@/pages/user/RecordPage.vue'
import SmartBandPage from '@/pages/user/SmartBandPage.vue'
import SubscriptionPage from '@/pages/user/SubscriptionPage.vue'
import VoiceTestPage from '@/pages/user/VoiceTestPage.vue'
import AlertsPage from '@/pages/doctor/AlertsPage.vue'
import AboutUsPage from '@/pages/user/AboutUsPage.vue'
import DashboardPage from '@/pages/doctor/DashboardPage.vue'
import KnowledgePage from '@/pages/doctor/KnowledgePage.vue'
import PatientsPage from '@/pages/doctor/PatientsPage.vue'
import ScaleAssessmentsPage from '@/pages/doctor/ScaleAssessmentsPage.vue'
import AssessmentTaskPublishingPage from '@/pages/doctor/AssessmentTaskPublishingPage.vue'
import InterventionTaskPublishingPage from '@/pages/doctor/InterventionTaskPublishingPage.vue'
import NeuropsychAssessmentsPage from '@/pages/doctor/NeuropsychAssessmentsPage.vue'
import DoctorBrainInterventionReportsPage from '@/pages/doctor/BrainInterventionReportsPage.vue'
import DepartmentsPage from '@/pages/admin/DepartmentsPage.vue'
import HtpEvaluationPage from '@/pages/user/HtpEvaluationPage.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import type { UserRole } from '@/types'

const staffRoles: UserRole[] = ['doctor', 'admin', 'super_admin']

const redirectLegacyAdminPath = (prefix: '/doctor' | '/super-admin') => (to: { fullPath: string }) => {
  const legacyPath = to.fullPath.replace(new RegExp(`^${prefix}`), '')
  const nextPath = legacyPath && legacyPath !== '/' ? legacyPath : prefix === '/super-admin' ? '/departments' : '/dashboard'
  return `/admin${nextPath}`
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: UserLayout,
      children: [
        { path: '', component: HomePage },
        { path: 'home', redirect: '/' },
        { path: 'record', component: RecordPage },
        { path: 'assessment', component: AssessmentPage },
        { path: 'assessment/htp', component: HtpEvaluationPage },
        { path: 'scale-assessment', component: ScaleAssessmentPage },
        { path: 'assessment-tasks', component: AssessmentTaskCenterPage },
        { path: 'assessment-tasks/:assigneeId', component: AssessmentTaskCenterPage },
        { path: 'neuropsych-assessment', component: NeuropsychAssessmentPage },
        { path: 'neuropsych-assessment/records/:recordId', component: NeuropsychAssessmentPage },
        { path: 'neuropsych-assessment/free/:testCode', component: NeuropsychAssessmentPage },
        { path: 'neuropsych-assessment/report/:recordId', component: NeuropsychAssessmentPage },
        { path: 'brain-intervention', component: BrainInterventionPage },
        { path: 'brain-intervention/reports', component: BrainInterventionReportsPage },
        { path: 'brain-intervention/reports/:reportId', component: BrainInterventionReportsPage },
        { path: 'brain-intervention/:mode', component: BrainInterventionPage },
        { path: 'healing', component: HealingPage },
        { path: 'profile', component: ProfilePage },
        { path: 'profile/personal', component: PersonalInfoPage },
        { path: 'profile/smart-band', component: SmartBandPage },
        { path: 'profile/privacy', component: PrivacySettingsPage },
        { path: 'profile/subscription', component: SubscriptionPage },
        { path: 'profile/healing-plan', component: HealingPlanPage },
        { path: 'profile/connect-doctor', component: ConnectDoctorPage },
        { path: 'profile/about', component: AboutUsPage },
        { path: 'test/voice', component: VoiceTestPage },
      ],
    },
    {
      path: '/admin',
      component: AdminLayout,
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', component: DashboardPage, meta: { roles: staffRoles } },
        { path: 'patients', component: PatientsPage, meta: { roles: staffRoles } },
        { path: 'assessment-task-publishing', component: AssessmentTaskPublishingPage, meta: { roles: staffRoles } },
        { path: 'intervention-task-publishing', component: InterventionTaskPublishingPage, meta: { roles: staffRoles } },
        { path: 'brain-intervention-reports', component: DoctorBrainInterventionReportsPage, meta: { roles: staffRoles } },
        { path: 'scale-assessments', component: ScaleAssessmentsPage, meta: { roles: staffRoles } },
        { path: 'neuropsych-assessments', component: NeuropsychAssessmentsPage, meta: { roles: staffRoles } },
        { path: 'knowledge', component: KnowledgePage, meta: { roles: staffRoles } },
        { path: 'alerts', component: AlertsPage, meta: { roles: staffRoles } },
        { path: 'departments', component: DepartmentsPage, meta: { roles: ['super_admin'] } },
      ],
    },
    { path: '/doctor', redirect: '/admin/dashboard' },
    { path: '/doctor/:pathMatch(.*)*', redirect: redirectLegacyAdminPath('/doctor') },
    { path: '/super-admin', redirect: '/admin/departments' },
    { path: '/super-admin/:pathMatch(.*)*', redirect: redirectLegacyAdminPath('/super-admin') },
    { path: '/login', component: LoginPage },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const { state, ensureInitialized, isAdminUser } = useAuthSession()

  if (!state.initialized) {
    await ensureInitialized()
  }

  const publicPaths = new Set(['/', '/login', '/403', '/404'])
  if (!state.user && !publicPaths.has(to.path)) {
    return {
      path: '/login',
      state: to.fullPath !== '/' ? { from: to.fullPath } : undefined,
    }
  }

  if (to.path.startsWith('/admin') && state.user && !isAdminUser.value) {
    return '/profile'
  }

  const requiredRoles = to.matched.flatMap((record) => {
    const roles = record.meta.roles
    return Array.isArray(roles) ? roles as UserRole[] : []
  })
  const currentRole = state.profile?.role
  if (requiredRoles.length > 0 && (!currentRole || !requiredRoles.includes(currentRole))) {
    return isAdminUser.value ? '/admin/dashboard' : '/profile'
  }

  return true
})

export default router
