import type { ManagerDashboard, Role, Task, TaskInput, TaskStatus, User } from '../types'

const TOKEN_KEY = 'token'

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
  const res = await fetch(`/api${path}`, {
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
    if (res.status === 413) throw new ApiError('Upload too large (10 MB max)', 413)
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
  setEmployeeActive: (id: number, is_active: boolean) =>
    request<{ employee: User; unassigned_tasks: number }>(`/manager/employees/${id}`, json('PATCH', { is_active })),

  // Employee
  myTasks: () => request<Task[]>('/employee/tasks'),
  updateTaskStatus: (id: number, status: TaskStatus) =>
    request<Task>(`/employee/tasks/${id}`, json('PATCH', { status })),
  uploadPhotos: (taskId: number, files: FileList | File[]) => {
    const form = new FormData()
    Array.from(files).forEach((f) => form.append('photos', f))
    return request<Task>(`/employee/tasks/${taskId}/photos`, { method: 'POST', body: form })
  },
  deletePhoto: (taskId: number, photoId: number) =>
    request<Task>(`/employee/tasks/${taskId}/photos/${photoId}`, { method: 'DELETE' }),
}
