/**
 * Authentication-related TypeScript types
 */

export interface User {
  id: string
  email: string
  full_name: string
  role: "processor" | "admin"
  is_active: boolean
  organization_id: string
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface LoginResponse {
  user: User
  access_token: string
  token_type: "bearer"
}

export interface AuthError {
  detail: string
}
