export type Role = 'manager' | 'employee'

export type TaskStatus = 'pending' | 'in_progress' | 'completed'

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string | null
  role: Role
  is_active: boolean
}

export interface TaskPhoto {
  id: number
  url: string
  uploaded_by: string | null
  created_at: string | null
}

export interface Task {
  id: number
  unit_name: string
  address: string
  description: string | null
  scheduled_date: string
  status: TaskStatus
  assigned_to: User | null
  /** True when the employee who did this task was permanently deleted */
  assignee_deleted: boolean
  photos: TaskPhoto[]
}

export interface TaskInput {
  unit_name: string
  address: string
  description: string
  scheduled_date: string
  assigned_to_id: number | null
  status?: TaskStatus
}

export interface CleanupSummary {
  days: number
  cutoff: string
  tasks: number
  photos: number
}

export interface ManagerDashboard {
  employees: User[]
  tasks: Task[]
  stats: Record<TaskStatus, number>
}

export const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
}
