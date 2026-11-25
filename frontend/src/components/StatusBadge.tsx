import { STATUS_LABELS } from '../types'
import type { TaskStatus } from '../types'

export default function StatusBadge({ status }: { status: TaskStatus }) {
  return <span className={`status status-${status}`}>{STATUS_LABELS[status]}</span>
}
