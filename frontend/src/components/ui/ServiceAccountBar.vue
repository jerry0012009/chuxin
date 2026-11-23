<script setup lang="ts">
import { ArrowLeftRight, LogOut, UserRound } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { useAccountActions } from '@/composables/useAccountActions'

const { state, roleLabel, accountName, leaving, leaveAccount } = useAccountActions()
</script>

<template>
  <div class="service-account-bar">
    <div class="service-width service-account-row">
      <p class="service-identity"><UserRound aria-hidden="true" /><strong>当前角色：{{ roleLabel }}</strong><span v-if="accountName" class="service-identity-name">{{ accountName }}</span></p>
      <div v-if="state.user" class="service-account-actions">
        <button type="button" :disabled="leaving" @click="leaveAccount(true)"><ArrowLeftRight aria-hidden="true" />切换角色</button>
        <button type="button" :disabled="leaving" @click="leaveAccount()"><LogOut aria-hidden="true" />退出登录</button>
      </div>
      <RouterLink v-else class="service-link" to="/login">账号登录</RouterLink>
    </div>
  </div>
</template>
