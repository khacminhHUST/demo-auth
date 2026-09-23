import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import * as authApi from '../api/authApi'
import FormError from '../components/FormError.jsx'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const navigate = useNavigate()
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await authApi.resetPassword({ token, new_password: newPassword })
      navigate('/login', { state: { justReset: true } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Đặt lại mật khẩu thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>Liên kết không hợp lệ</h1>
          <p className="auth-subtitle">Vui lòng dùng liên kết được gửi trong email</p>
          <Link to="/forgot-password">Gửi lại yêu cầu</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Đặt lại mật khẩu</h1>
        <p className="auth-subtitle">Nhập mật khẩu mới cho tài khoản của bạn</p>

        <FormError message={error} />

        <label>Mật khẩu mới</label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={8}
        />

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang lưu...' : 'Đặt lại mật khẩu'}
        </button>
      </form>
    </div>
  )
}
