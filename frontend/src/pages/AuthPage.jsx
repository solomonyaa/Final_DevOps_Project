import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import './AuthPage.css'

export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await api.post('/users/register', { username, password })
      } else {
        await api.get('/tasks', {
          auth: { username, password },
          validateStatus: s => s !== 401
        })
        const test = await api.get('/health')
        if (test.status !== 200) throw new Error('Server error')
        // verify credentials
        const res = await api.get('/tasks', { auth: { username, password } })
        if (res.status === 401) throw new Error('Invalid credentials')
      }
      localStorage.setItem('username', username)
      localStorage.setItem('password', password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <span className="auth-logo-icon">✓</span>
          <h1>TaskFlow</h1>
        </div>
        <p className="auth-subtitle">
          {mode === 'login' ? 'Welcome back!' : 'Create your account'}
        </p>

        <div className="auth-tabs">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => { setMode('login'); setError('') }}
          >Login</button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => { setMode('register'); setError('') }}
          >Register</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="auth-error">{error}</div>}
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username"
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'At least 6 characters' : 'Enter password'}
              required
            />
          </div>
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
