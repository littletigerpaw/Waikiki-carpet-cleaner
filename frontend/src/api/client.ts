import { compressImage } from '../image'
import type { CleanupSummary, ManagerDashboard, Role, Task, TaskInput, TaskStatus, User } from '../types'

const TOKEN_KEY = 'token'

/**
 * Where the Flask API lives. Normally empty: requests go to /api on the same site
 * (Vite proxies it to Flask in dev; Vercel routes it to the Python function in
 * production). Set VITE_API_URL only if the API is hosted on a different domain.
 */
export const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

/** Photo URLs are either absolute (Firebase Storage) or relative to the API (/api/uploads/...). */
export const assetUrl = (url: string) => (/^https?:\/\//.test(url) ? url : `${API_BASE}${url}`)

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenStore.get()
  // For file uploads (FormData) the browser must set Content-Type itself
  const isForm = options.body instanceof FormData
  const res = await fetch(`${API_BASE}/api${path}`, {
    ...options,
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    // Expired/invalid session or deactivated account: log out and go to login
    if (res.status === 401 && token && path !== '/auth/login') {
      tokenStore.clear()
      window.location.assign('/login')
    }
    if (res.status === 413) throw new ApiError('Photo too large to upload (4 MB max)', 413)
    throw new ApiError(data.error ?? 'Something went wrong', res.status)
  }
  return data as T
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) })

export const api = {
  // Auth
  login: (email: string, password: string, role: Role) =>
    request<{ token: string; user: User }>('/auth/login', json('POST', { email, password, role })),
  me: () => request<User>('/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    request<{ message: string }>('/auth/change-password', json('POST', { current_password, new_password })),

  // Manager
  managerDashboard: () => request<ManagerDashboard>('/manager/dashboard'),
  createTask: (task: TaskInput) => request<Task>('/manager/tasks', json('POST', task)),
  updateTask: (id: number, task: Partial<TaskInput>) =>
    request<Task>(`/manager/tasks/${id}`, json('PATCH', task)),
  deleteTask: (id: number) => request<{ message: string }>(`/manager/tasks/${id}`, { method: 'DELETE' }),
  createEmployee: (emp: {
    first_name: string
    last_name: string
    email: string
    phone: string
    password: string
  }) => request<User>('/manager/employees', json('POST', emp)),
  deleteEmployee: (id: number) =>
    request<{ message: string; tasks_updated: number }>(`/manager/employees/${id}`, { method: 'DELETE' }),
  managerDeletePhoto: (taskId: number, photoId: number) =>
    request<Task>(`/manager/tasks/${taskId}/photos/${photoId}`, { method: 'DELETE' }),
  cleanupPreview: (days: number) => request<CleanupSummary>(`/manager/cleanup?days=${days}`),
  cleanupOldTasks: (days: number) => request<CleanupSummary>('/manager/cleanup', json('POST', { days })),
  setEmployeeActive: (id: number, is_active: boolean) =>
    request<{ employee: User; unassigned_tasks: number }>(`/manager/employees/${id}`, json('PATCH', { is_active })),

  // Employee
  myTasks: () => request<Task[]>('/employee/tasks'),
  updateTaskStatus: (id: number, status: TaskStatus) =>
    request<Task>(`/employee/tasks/${id}`, json('PATCH', { status })),
  /** Shrinks each photo, then uploads them one per request (keeps each under Vercel's limit). */
  uploadPhotos: async (taskId: number, files: FileList | File[]) => {
    let task: Task | null = null
    for (const original of Array.from(files)) {
      const form = new FormData()
      form.append('photos', await compressImage(original))
      task = await request<Task>(`/employee/tasks/${taskId}/photos`, { method: 'POST', body: form })
    }
    if (!task) throw new ApiError('No photos selected', 400)
    return task
  },
  deletePhoto: (taskId: number, photoId: number) =>
    request<Task>(`/employee/tasks/${taskId}/photos/${photoId}`, { method: 'DELETE' }),
}
