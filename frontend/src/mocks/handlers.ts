/**
 * MSW Request Handlers
 *
 * Define mock API responses for testing
 */

import { http, HttpResponse } from 'msw'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Auth endpoint: POST /api/auth/login
  http.post(`${API_BASE_URL}/api/auth/login`, async () => {
    return HttpResponse.json({
      access_token: 'mock_access_token_12345',
      token_type: 'bearer',
      expires_in: 900,  // 15 minutes
      user: {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        is_active: true,
        is_superuser: false
      }
    })
  }),

  // Declarations endpoint: GET /api/declarations
  http.get(`${API_BASE_URL}/api/declarations`, async () => {
    return HttpResponse.json([
      {
        id: 1,
        declaration_number: 'DECL-2024-001',
        status: 'draft',
        importer_name: 'ABC Import Corp',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z'
      },
      {
        id: 2,
        declaration_number: 'DECL-2024-002',
        status: 'submitted',
        importer_name: 'XYZ Trading Ltd',
        created_at: '2024-01-16T14:20:00Z',
        updated_at: '2024-01-16T15:00:00Z'
      }
    ])
  }),

  // Declaration detail: GET /api/declarations/:id
  http.get(`${API_BASE_URL}/api/declarations/:id`, async ({ params }) => {
    const { id } = params
    return HttpResponse.json({
      id: Number(id),
      declaration_number: `DECL-2024-${String(id).padStart(3, '0')}`,
      status: 'draft',
      importer_name: 'Test Importer',
      importer_address: '123 Business St',
      total_value: 10500.00,
      currency: 'USD',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      documents: []
    })
  }),

  // Create declaration: POST /api/declarations
  http.post(`${API_BASE_URL}/api/declarations`, async () => {
    return HttpResponse.json({
      id: 3,
      declaration_number: 'DECL-2024-003',
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }, { status: 201 })
  }),

  // Upload document: POST /api/declarations/:id/documents
  http.post(`${API_BASE_URL}/api/declarations/:id/documents`, async ({ params }) => {
    const { id } = params
    return HttpResponse.json({
      id: 1,
      declaration_id: Number(id),
      document_type: 'invoice',
      filename: 'invoice.pdf',
      upload_status: 'completed',
      created_at: new Date().toISOString()
    }, { status: 201 })
  }),

  // Error scenario: 401 Unauthorized
  http.get(`${API_BASE_URL}/api/declarations/unauthorized`, async () => {
    return HttpResponse.json({
      detail: 'Not authenticated'
    }, { status: 401 })
  }),

  // Error scenario: 500 Internal Server Error
  http.get(`${API_BASE_URL}/api/declarations/error`, async () => {
    return HttpResponse.json({
      detail: 'Internal server error'
    }, { status: 500 })
  })
]
