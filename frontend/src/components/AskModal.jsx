import { useState } from 'react'
import api from '../api'
import './Modal.css'
import './AskModal.css'

export default function AskModal({ task, onClose }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setAnswer('')
    setError('')
    try {
      const res = await api.post(`/task/${task.id}/ask`, { question })
      setAnswer(res.data.answer)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get answer')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🤖 Ask AI about this task</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="ask-task-info">
          <strong>{task.title}</strong>
          <p>{task.details}</p>
        </div>

        <form onSubmit={handleAsk} className="modal-form">
          {error && <div className="modal-error">{error}</div>}

          <div className="form-group">
            <label>Your question</label>
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="e.g. How should I approach this task? What's the best way to start?"
              required
            />
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose}>Close</button>
            <button type="submit" className="btn-primary" disabled={loading || !question.trim()}>
              {loading ? '⏳ Thinking...' : 'Ask AI'}
            </button>
          </div>
        </form>

        {answer && (
          <div className="ask-answer">
            <div className="ask-answer-label">💡 AI Response</div>
            <div className="ask-answer-text">{answer}</div>
          </div>
        )}
      </div>
    </div>
  )
}
