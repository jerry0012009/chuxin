import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthSession } from './useAuthSession'

export function useAccountActions() {
  const router = useRouter()
  const { state, signOut } = useAuthSession()
  const role = computed(() => state.profile?.role || state.user?.user_metadata?.role)
  const staff = computed(() => ['doctor', 'admin', 'super_admin'].includes(role.value || ''))
  const roleLabel = computed(() => !state.user ? '未登录' : role.value === 'super_admin' ? '超级管理员' : staff.value ? '管理员' : '参与者')
  const accountName = computed(() => state.profile?.full_name || state.profile?.username || state.user?.user_metadata?.username)
  const leaving = ref(false)

  async function leaveAccount(switchRole = false) {
    if (leaving.value) return
    const target = router.resolve({ path: '/login', query: switchRole ? { role: staff.value ? 'user' : 'doctor' } : {} })
    leaving.value = true
    await signOut()
    // Reload to discard any data cached in the previous account's workspace.
    window.location.replace(target.href)
  }

  return { state, staff, roleLabel, accountName, leaving, leaveAccount }
}
