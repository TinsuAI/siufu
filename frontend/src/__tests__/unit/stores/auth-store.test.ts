import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/stores/auth-store'

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({ user: null, isAuthenticated: false })
  })

  it('should initialize with no user', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should set user on login', () => {
    const testUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
    }

    const { login } = useAuthStore.getState()
    login(testUser)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(testUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should clear user on logout', () => {
    const testUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
    }

    const { login, logout } = useAuthStore.getState()

    // First login
    login(testUser)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    // Then logout
    logout()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should set user with setUser action', () => {
    const testUser = {
      id: '2',
      email: 'another@example.com',
      name: 'Another User',
      role: 'admin',
    }

    const { setUser } = useAuthStore.getState()
    setUser(testUser)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(testUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should set isAuthenticated to false when setUser is called with null', () => {
    const testUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
    }

    const { setUser } = useAuthStore.getState()

    // Set user
    setUser(testUser)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    // Clear user
    setUser(null)

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
