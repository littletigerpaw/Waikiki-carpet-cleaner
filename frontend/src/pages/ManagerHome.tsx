import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import EditTaskModal from '../components/EditTaskModal'
import Navbar from '../components/Navbar'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import { STATUS_LABELS } from '../types'
import type { ManagerDashboard, Task, TaskStatus, User } from '../types'

const emptyTask = { unit_name: '', address: '', description: '', scheduled_date: '', assigned_to_id: '' }
const emptyEmployee = { first_name: '', last_name: '', email: '', phone: '', password: '' }
const emptyFilters = { search: '', status: '', employee: '', from: '', to: '' }

export default function ManagerHome() {
  const { user } = useAuth()
  const [data, setData] = useState<ManagerDashboard | null>(null)
  const [error, setError] = useState('')

  const [taskForm, setTaskForm] = useState(emptyTask)
  const [empForm, setEmpForm] = useState(emptyEmployee)
  const [formMsg, setFormMsg] = useState('')
  const [editing, setEditing] = useState<Task | null>(null)
  const [filters, setFilters] = useState(emptyFilters)

  const load = useCallback(() => {
    api.managerDashboard().then(setData).catch((e: Error) => setError(e.message))
  }, [])

  useEffect(load, [load])

  const activeEmployees = useMemo(() => data?.employees.filter((e) => e.is_active) ?? [], [data])

  // Filtering happens in the browser: we already have every task loaded
  const filteredTasks = useMemo(() => {
    if (!data) return []
    const q = filters.search.trim().toLowerCase()
    return data.tasks.filter((t) => {
      if (q && !`${t.unit_name} ${t.address} ${t.description ?? ''}`.toLowerCase().includes(q)) return false
      if (filters.status && t.status !== filters.status) return false
      if (filters.employee === 'unassigned' && t.assigned_to) return false
      if (filters.employee && filters.employee !== 'unassigned' && String(t.assigned_to?.id) !== filters.employee)
        return false
      // ISO dates (YYYY-MM-DD) compare correctly as strings
      if (filters.from && t.scheduled_date < filters.from) return false
      if (filters.to && t.scheduled_date > filters.to) return false
      return true
    })
  }, [data, filters])

  const filtersActive = Object.values(filters).some(Boolean)

  const setToday = () => {
    const today = new Date().toLocaleDateString('en-CA')
    setFilters({ ...filters, from: today, to: today })
  }

  const submitTask = async (e: FormEvent) => {
    e.preventDefault()
    setFormMsg('')
    try {
      await api.createTask({
        ...taskForm,
        assigned_to_id: taskForm.assigned_to_id ? Number(taskForm.assigned_to_id) : null,
      })
      setTaskForm(emptyTask)
      setFormMsg('Task created.')
      load()
    } catch (err) {
      setFormMsg(err instanceof Error ? err.message : 'Could not create task')
    }
  }

  const submitEmployee = async (e: FormEvent) => {
    e.preventDefault()
    setFormMsg('')
    try {
      await api.createEmployee(empForm)
      setEmpForm(emptyEmployee)
      setFormMsg('Employee added.')
      load()
    } catch (err) {
      setFormMsg(err instanceof Error ? err.message : 'Could not add employee')
    }
  }

  const toggleEmployee = async (emp: User) => {
    const name = `${emp.first_name} ${emp.last_name}`
    if (
      emp.is_active &&
      !window.confirm(
        `Deactivate ${name}? They will no longer be able to log in, and their unfinished tasks will become unassigned.`,
      )
    )
      return
    setFormMsg('')
    try {
      const res = await api.setEmployeeActive(emp.id, !emp.is_active)
      setFormMsg(
        res.employee.is_active
          ? `${name} reactivated.`
          : `${name} deactivated. ${res.unassigned_tasks} unfinished task(s) are now unassigned.`,
      )
      load()
    } catch (err) {
      setFormMsg(err instanceof Error ? err.message : 'Could not update employee')
    }
  }

  return (
    <>
      <Navbar />
      <main className="container">
        <h2>Aloha, {user?.first_name} 👋</h2>
        <p className="muted">Manager dashboard — schedule cleanings and manage your team.</p>

        {error && <p className="error">{error}</p>}
        {formMsg && <p className="notice">{formMsg}</p>}

        {data && (
          <>
            <section className="stats">
              {(Object.keys(STATUS_LABELS) as TaskStatus[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`stat-card stat-${s} ${filters.status === s ? 'selected' : ''}`}
                  onClick={() => setFilters({ ...filters, status: filters.status === s ? '' : s })}
                  title={`Show only ${STATUS_LABELS[s]} tasks`}
                >
                  <span className="stat-num">{data.stats[s]}</span>
                  <span className="stat-label">{STATUS_LABELS[s]}</span>
                </button>
              ))}
              <div className="stat-card">
                <span className="stat-num">{activeEmployees.length}</span>
                <span className="stat-label">Active Employees</span>
              </div>
            </section>

            <section className="card">
              <div className="card-header">
                <h3>All Cleaning Tasks</h3>
                <span className="muted small">
                  Showing {filteredTasks.length} of {data.tasks.length}
                </span>
              </div>

              <div className="filters">
                <input
                  type="search"
                  placeholder="Search unit, address, notes…"
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                />
                <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                  <option value="">All statuses</option>
                  {(Object.keys(STATUS_LABELS) as TaskStatus[]).map((s) => (
                    <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                  ))}
                </select>
                <select
                  value={filters.employee}
                  onChange={(e) => setFilters({ ...filters, employee: e.target.value })}
                >
                  <option value="">All employees</option>
                  <option value="unassigned">Unassigned</option>
                  {data.employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name}{emp.is_active ? '' : ' (deactivated)'}
                    </option>
                  ))}
                </select>
                <label className="date-filter">
                  From
                  <input type="date" value={filters.from}
                    onChange={(e) => setFilters({ ...filters, from: e.target.value })} />
                </label>
                <label className="date-filter">
                  To
                  <input type="date" value={filters.to}
                    onChange={(e) => setFilters({ ...filters, to: e.target.value })} />
                </label>
                <button type="button" className="btn btn-outline btn-sm" onClick={setToday}>Today</button>
                {filtersActive && (
                  <button type="button" className="btn btn-outline btn-sm" onClick={() => setFilters(emptyFilters)}>
                    Clear filters
                  </button>
                )}
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Unit</th>
                      <th>Address</th>
                      <th>Assigned To</th>
                      <th>Status</th>
                      <th>Photos</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTasks.map((t) => (
                      <tr key={t.id}>
                        <td>{t.scheduled_date}</td>
                        <td>
                          <strong>{t.unit_name}</strong>
                          {t.description && <div className="muted small">{t.description}</div>}
                        </td>
                        <td>{t.address}</td>
                        <td>
                          {t.assigned_to ? (
                            <>
                              {t.assigned_to.first_name} {t.assigned_to.last_name}
                              {!t.assigned_to.is_active && <div className="muted small">deactivated</div>}
                            </>
                          ) : (
                            <span className="muted">Unassigned</span>
                          )}
                        </td>
                        <td>
                          <StatusBadge status={t.status} />
                        </td>
                        <td>
                          {t.photos.length > 0 ? (
                            <button className="link-btn" onClick={() => setEditing(t)}>
                              📷 {t.photos.length}
                            </button>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td>
                          <button className="btn btn-outline btn-sm" onClick={() => setEditing(t)}>
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                    {filteredTasks.length === 0 && (
                      <tr>
                        <td colSpan={7} className="muted">
                          {data.tasks.length === 0 ? 'No tasks yet.' : 'No tasks match these filters.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <div className="grid-2">
              <section className="card">
                <h3>Schedule a Cleaning</h3>
                <form className="form" onSubmit={submitTask}>
                  <input placeholder="Unit name" required value={taskForm.unit_name}
                    onChange={(e) => setTaskForm({ ...taskForm, unit_name: e.target.value })} />
                  <input placeholder="Address" required value={taskForm.address}
                    onChange={(e) => setTaskForm({ ...taskForm, address: e.target.value })} />
                  <textarea placeholder="Notes (optional)" rows={2} value={taskForm.description}
                    onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} />
                  <input type="date" required value={taskForm.scheduled_date}
                    onChange={(e) => setTaskForm({ ...taskForm, scheduled_date: e.target.value })} />
                  <select value={taskForm.assigned_to_id}
                    onChange={(e) => setTaskForm({ ...taskForm, assigned_to_id: e.target.value })}>
                    <option value="">Unassigned</option>
                    {activeEmployees.map((emp) => (
                      <option key={emp.id} value={emp.id}>
                        {emp.first_name} {emp.last_name}
                      </option>
                    ))}
                  </select>
                  <button className="btn btn-primary" type="submit">Create Task</button>
                </form>
              </section>

              <section className="card">
                <h3>Add Employee</h3>
                <form className="form" onSubmit={submitEmployee}>
                  <div className="row">
                    <input placeholder="First name" required value={empForm.first_name}
                      onChange={(e) => setEmpForm({ ...empForm, first_name: e.target.value })} />
                    <input placeholder="Last name" required value={empForm.last_name}
                      onChange={(e) => setEmpForm({ ...empForm, last_name: e.target.value })} />
                  </div>
                  <input type="email" placeholder="Email" required value={empForm.email}
                    onChange={(e) => setEmpForm({ ...empForm, email: e.target.value })} />
                  <input placeholder="Phone (optional)" value={empForm.phone}
                    onChange={(e) => setEmpForm({ ...empForm, phone: e.target.value })} />
                  <input type="password" placeholder="Temporary password" required value={empForm.password}
                    onChange={(e) => setEmpForm({ ...empForm, password: e.target.value })} />
                  <button className="btn btn-primary" type="submit">Add Employee</button>
                </form>

                <h4>Team</h4>
                <ul className="team-list">
                  {data.employees.map((emp) => (
                    <li key={emp.id} className={emp.is_active ? '' : 'inactive'}>
                      <div className="team-info">
                        <strong>
                          {emp.first_name} {emp.last_name}
                          {!emp.is_active && <span className="pill-muted">Deactivated</span>}
                        </strong>
                        <span className="muted small">{emp.email}</span>
                      </div>
                      <button
                        type="button"
                        className={`btn btn-sm ${emp.is_active ? 'btn-danger' : 'btn-outline'}`}
                        onClick={() => toggleEmployee(emp)}
                      >
                        {emp.is_active ? 'Deactivate' : 'Reactivate'}
                      </button>
                    </li>
                  ))}
                  {data.employees.length === 0 && <li className="muted">No employees yet.</li>}
                </ul>
              </section>
            </div>
          </>
        )}

        {editing && data && (
          <EditTaskModal
            task={editing}
            employees={data.employees}
            onClose={() => setEditing(null)}
            onSaved={() => {
              setEditing(null)
              setFormMsg('Task updated.')
              load()
            }}
          />
        )}
      </main>
    </>
  )
}
