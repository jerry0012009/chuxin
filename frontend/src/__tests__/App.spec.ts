import { describe, it, expect } from 'vitest'

import { shallowMount } from '@vue/test-utils'
import App from '../App.vue'

describe('App', () => {
  it('mounts the routed application shell', () => {
    const wrapper = shallowMount(App, {
      global: {
        stubs: {
          RouterView: { template: '<main data-testid="router-view" />' },
        },
      },
    })

    expect(wrapper.get('[data-testid="router-view"]').attributes('data-testid')).toBe('router-view')
  })
})
