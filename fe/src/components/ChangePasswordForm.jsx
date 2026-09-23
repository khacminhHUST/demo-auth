import { useState } from 'react'
import * as authApi from '../api/authApi'
import FormError from './FormError.jsx'

export default function ChangePasswordForm({ onClose }) {
  const [form, setForm] = useState({ current_password: '', new_password: '' })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      const { data } = await authApi.changePassword(form)
      setMessage(data.message)
      setForm({ current_password: '', new_password: '' })
    } catch (err) {
      setError(err.response?.data?.detail || 'Đổi mật khẩu thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="inline-card" onSubmit={handleSubmit}>
      <h3>Đổi mật khẩu</h3>
      <FormError message={error} />
      {message && <p className="auth-message">{message}</p>}

      <label>Mật khẩu hiện tại</label>
      <input
        type="password"
        name="current_password"
        value={form.current_password}
        onChange={handleChange}
        required
      />

      <label>Mật khẩu mới</label>
      <input
        type="password"
        name="new_password"
        value={form.new_password}
        onChange={handleChange}
        required
        minLength={8}
      />

      <div className="inline-card-actions">
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang lưu...' : 'Lưu'}
        </button>
        <button type="button" className="btn-secondary" onClick={onClose}>
          Đóng
        </button>
      </div>
    </form>
  )
}
