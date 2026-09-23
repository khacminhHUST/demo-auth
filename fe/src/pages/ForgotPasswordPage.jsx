import { useState } from 'react'
import { Link } from 'react-router-dom'
import * as authApi from '../api/authApi'
import FormError from '../components/FormError.jsx'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await authApi.forgotPassword({ email })
      setMessage('Đã gửi email hướng dẫn đặt lại mật khẩu, kiểm tra hộp thư của bạn')
    } catch (err) {
      setError(err.response?.data?.detail || 'Không gửi được yêu cầu')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Quên mật khẩu</h1>
        <p className="auth-subtitle">Nhập email để nhận liên kết đặt lại mật khẩu</p>

        <FormError message={error} />
        {message && <p className="auth-message">{message}</p>}

        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang gửi...' : 'Gửi liên kết'}
        </button>

        <p className="auth-footer">
          <Link to="/login">Quay lại đăng nhập</Link>
        </p>
      </form>
    </div>
  )
}
