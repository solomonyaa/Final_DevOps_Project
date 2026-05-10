import './TaskCard.css'

const PRI_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' }
const CAT_ICONS = { personal: '👤', work: '💼', shopping: '🛒' }

const isOverdue = (dueDateStr, isComplete) => {
  if (isComplete) return false
  const [d, m, y] = dueDateStr.split('/')
  const due = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return due < today
}

export default function TaskCard({ task, dragHandleProps, onToggleComplete, onEdit, onDelete, onAsk }) {
  const overdue = isOverdue(task.due_date, task.is_complete)
  const borderColor = overdue ? '#ef4444' : PRI_COLORS[task.priority]

  return (
    <div className={`task-card ${task.is_complete ? 'completed' : ''} ${overdue ? 'overdue' : ''}`}
         style={{ borderLeft: `4px solid ${borderColor}` }}>

      <div className="task-drag-handle" {...dragHandleProps} title="Drag to reorder">⠿</div>

      <div className="task-check-area">
        <button
          className={`check-btn ${task.is_complete ? 'checked' : ''}`}
          onClick={() => onToggleComplete(task)}
          title={task.is_complete ? 'Mark incomplete' : 'Mark complete'}
        >
          {task.is_complete ? '✓' : ''}
        </button>
      </div>

      <div className="task-body">
        <div className="task-title">
          {task.title}
          {overdue && <span className="overdue-badge">Overdue</span>}
        </div>
        {task.details && <div className="task-details">{task.details}</div>}
        <div className="task-meta">
          <span className={`meta-chip ${overdue ? 'date-overdue' : ''}`}>📅 {task.due_date}</span>
          <span className="meta-chip cat-chip">{CAT_ICONS[task.category]} {task.category}</span>
          <span className="meta-chip pri-chip"
            style={{ background: PRI_COLORS[task.priority] + '20', color: PRI_COLORS[task.priority] }}>
            {task.priority}
          </span>
        </div>
      </div>

      <div className="task-actions">
        <button className="action-btn" onClick={onAsk} title="Ask AI">🤖</button>
        <button className="action-btn" onClick={onEdit} title="Edit">✏️</button>
        <button className="action-btn delete-btn" onClick={onDelete} title="Delete">🗑️</button>
      </div>
    </div>
  )
}
