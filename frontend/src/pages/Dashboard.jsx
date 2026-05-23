import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import api from '../api'
import TaskCard from '../components/TaskCard'
import TaskForm from '../components/TaskForm'
import AskModal from '../components/AskModal'
import './Dashboard.css'

const NAV_ITEMS = [
  { key: 'all', label: 'All Tasks', icon: '📋' },
  { key: 'active', label: 'Active', icon: '⏳' },
  { key: 'completed', label: 'Completed', icon: '✅' },
]

const CATEGORIES = ['all', 'personal', 'work', 'shopping']
const PRIORITIES = ['all', 'high', 'medium', 'low']
const CAT_ICONS = { personal: '👤', work: '💼', shopping: '🛒' }
const PRI_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' }

export default function Dashboard() {
  const [allTasks, setAllTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('all')
  const [filterCategory, setFilterCategory] = useState('all')
  const [filterPriority, setFilterPriority] = useState('all')
  const [search, setSearch] = useState('')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true')
  const [showForm, setShowForm] = useState(false)
  const [editTask, setEditTask] = useState(null)
  const [askTask, setAskTask] = useState(null)
  const navigate = useNavigate()

  const username = localStorage.getItem('username')

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode)
    localStorage.setItem('darkMode', darkMode)
  }, [darkMode])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('username')
    localStorage.removeItem('password')
    navigate('/login')
  }, [navigate])

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/tasks')
      setAllTasks(res.data)
    } catch (err) {
      if (err.response?.status === 404) setAllTasks([])
      else if (err.response?.status === 401) handleLogout()
      else setError('Failed to load tasks')
    } finally {
      setLoading(false)
    }
  }, [handleLogout])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  const tasks = useMemo(() => {
    let result = allTasks
    if (view === 'active') result = result.filter(t => !t.is_complete)
    if (view === 'completed') result = result.filter(t => t.is_complete)
    if (filterCategory !== 'all') result = result.filter(t => t.category === filterCategory)
    if (filterPriority !== 'all') result = result.filter(t => t.priority === filterPriority)
    if (search) result = result.filter(t => t.title.toLowerCase().includes(search.toLowerCase()))
    return result
  }, [allTasks, view, filterCategory, filterPriority, search])

  const counts = useMemo(() => ({
    all: allTasks.length,
    active: allTasks.filter(t => !t.is_complete).length,
    completed: allTasks.filter(t => t.is_complete).length,
    personal: allTasks.filter(t => t.category === 'personal').length,
    work: allTasks.filter(t => t.category === 'work').length,
    shopping: allTasks.filter(t => t.category === 'shopping').length,
    high: allTasks.filter(t => t.priority === 'high').length,
    medium: allTasks.filter(t => t.priority === 'medium').length,
    low: allTasks.filter(t => t.priority === 'low').length,
  }), [allTasks])

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this task?')) return
    await api.delete(`/task/${id}`)
    setAllTasks(prev => prev.filter(t => t.id !== id))
  }

  const handleToggleComplete = async (task) => {
    const res = await api.patch(`/task/${task.id}/complete`, { is_complete: !task.is_complete })
    setAllTasks(prev => prev.map(t => t.id === task.id ? res.data.task : t))
  }

  const handleSaved = () => {
    setShowForm(false)
    setEditTask(null)
    fetchTasks()
  }

  const onDragEnd = (result) => {
    if (!result.destination || result.source.index === result.destination.index) return
    const displayed = [...tasks]
    const [moved] = displayed.splice(result.source.index, 1)
    displayed.splice(result.destination.index, 0, moved)
    setAllTasks(prev => {
      const displayedSet = new Set(displayed.map(t => t.id))
      let i = 0
      return prev.map(t => displayedSet.has(t.id) ? displayed[i++] : t)
    })
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">✓</span>
          <span>CloudTasks</span>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">{username?.[0]?.toUpperCase()}</div>
          <span className="user-name">{username}</span>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <button
              key={item.key}
              className={`nav-item ${view === item.key ? 'active' : ''}`}
              onClick={() => setView(item.key)}
            >
              <span>{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {counts[item.key] > 0 && <span className="badge">{counts[item.key]}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Category</div>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              className={`nav-item ${filterCategory === cat ? 'active' : ''}`}
              onClick={() => setFilterCategory(cat)}
            >
              <span>{cat === 'all' ? '🗂️' : CAT_ICONS[cat]}</span>
              <span className="nav-label">{cat.charAt(0).toUpperCase() + cat.slice(1)}</span>
              {cat !== 'all' && counts[cat] > 0 && <span className="badge">{counts[cat]}</span>}
            </button>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Priority</div>
          {PRIORITIES.map(pri => (
            <button
              key={pri}
              className={`nav-item ${filterPriority === pri ? 'active' : ''}`}
              onClick={() => setFilterPriority(pri)}
            >
              <span className="priority-dot"
                style={{ background: pri === 'all' ? '#94a3b8' : PRI_COLORS[pri] }} />
              <span className="nav-label">{pri.charAt(0).toUpperCase() + pri.slice(1)}</span>
              {pri !== 'all' && counts[pri] > 0 && <span className="badge">{counts[pri]}</span>}
            </button>
          ))}
        </div>

        <div className="sidebar-bottom">
          <button className="dark-mode-btn" onClick={() => setDarkMode(d => !d)}>
            <span>{darkMode ? '☀️' : '🌙'}</span>
            <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
          <button className="logout-btn" onClick={handleLogout}>
            <span>🚪</span> Logout
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="main-header">
          <div>
            <h2 className="main-title">
              {view === 'all' ? 'All Tasks' : view === 'active' ? 'Active Tasks' : 'Completed Tasks'}
            </h2>
            <p className="main-subtitle">{tasks.length} task{tasks.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="header-actions">
            <input
              className="search-input"
              type="text"
              placeholder="🔍  Search tasks..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <button className="add-btn" onClick={() => { setEditTask(null); setShowForm(true) }}>
              + Add Task
            </button>
          </div>
        </div>

        {error && <div className="main-error">{error}</div>}

        {loading ? (
          <div className="empty-state">Loading...</div>
        ) : tasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📝</div>
            <p>{search ? 'No tasks match your search.' : 'No tasks yet.'}</p>
            {!search && <button className="add-btn" onClick={() => setShowForm(true)}>Add your first task</button>}
          </div>
        ) : (
          <DragDropContext onDragEnd={onDragEnd}>
            <Droppable droppableId="tasks">
              {(provided) => (
                <div className="task-list" {...provided.droppableProps} ref={provided.innerRef}>
                  {tasks.map((task, index) => (
                    <Draggable key={task.id} draggableId={String(task.id)} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          style={{ ...provided.draggableProps.style, opacity: snapshot.isDragging ? 0.85 : 1 }}
                        >
                          <TaskCard
                            task={task}
                            dragHandleProps={provided.dragHandleProps}
                            onToggleComplete={handleToggleComplete}
                            onEdit={() => { setEditTask(task); setShowForm(true) }}
                            onDelete={() => handleDelete(task.id)}
                            onAsk={() => setAskTask(task)}
                          />
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        )}
      </main>

      {showForm && (
        <TaskForm task={editTask} onSaved={handleSaved} onClose={() => { setShowForm(false); setEditTask(null) }} />
      )}
      {askTask && <AskModal task={askTask} onClose={() => setAskTask(null)} />}
    </div>
  )
}
