import { useState } from 'react'
import api from '../api'
import './Modal.css'

const toInputDate = (ddmmyyyy) => {
  if (!ddmmyyyy) return ''
  const [d, m, y] = ddmmyyyy.split('/')
  return `${y}-${m}-${d}`
}

const toApiDate = (yyyymmdd) => {
  if (!yyyymmdd) return ''
  const [y, m, d] = yyyymmdd.split('-')
  return `${d}/${m}/${y}`
}

export default function TaskForm({ task, onSaved, onClose }) {
  const isEdit = !!task
  const [form, setForm] = useState({
    title: task?.title || '',
    details: task?.details || '',
    due_date: toInputDate(task?.due_date) || '',
    category: task?.category || 'personal',
    priority: task?.priority || 'medium',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (field) => (e) => setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { ...form, due_date: toApiDate(form.due_date) }
      if (isEdit) {
        await api.patch(`/task/${task.id}`, payload)
      } else {
        await api.post('/tasks', payload)
      }
      onSaved()
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{isEdit ? 'Edit Task' : 'New Task'}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && <div className="modal-error">{error}</div>}

          <div className="form-group">
            <label>Title <span className="char-count">{form.title.length}/30</span></label>
            <input
              value={form.title}
              onChange={set('title')}
              maxLength={30}
              placeholder="Task title"
              required
            />
          </div>

          <div className="form-group">
            <label>Details <span className="char-count">{form.details.length}/500</span></label>
            <textarea
              value={form.details}
              onChange={set('details')}
              maxLength={500}
              placeholder="Describe the task..."
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Due Date</label>
              <input
                type="date"
                value={form.due_date}
                onChange={set('due_date')}
                required
              />
            </div>

            <div className="form-group">
              <label>Category</label>
              <select value={form.category} onChange={set('category')}>
                <option value="personal">👤 Personal</option>
                <option value="work">💼 Work</option>
                <option value="shopping">🛒 Shopping</option>
              </select>
            </div>

            <div className="form-group">
              <label>Priority</label>
              <select value={form.priority} onChange={set('priority')}>
                <option value="high">🔴 High</option>
                <option value="medium">🟡 Medium</option>
                <option value="low">🟢 Low</option>
              </select>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
