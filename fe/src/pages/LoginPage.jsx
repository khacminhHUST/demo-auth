import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import FormError from '../components/FormError.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { loginWithCredentials } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await loginWithCredentials(form.email, form.password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Đăng nhập thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  const successMessage = location.state?.justVerified
    ? 'Xác thực email thành công, bạn có thể đăng nhập'
    : location.state?.justReset
      ? 'Đặt lại mật khẩu thành công, vui lòng đăng nhập'
      : ''

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Đăng nhập</h1>
        <p className="auth-subtitle">Nhập email và mật khẩu để tiếp tục</p>

        {successMessage && <p className="auth-message">{successMessage}</p>}
        <FormError message={error} />

        <label>Email</label>
        <input type="email" name="email" value={form.email} onChange={handleChange} required />

        <label>Mật khẩu</label>
        <input type="password" name="password" value={form.password} onChange={handleChange} required />

        <div className="auth-links-row">
          <Link to="/forgot-password">Quên mật khẩu?</Link>
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>

        <p className="auth-footer">
          Chưa có tài khoản? <Link to="/register">Đăng ký</Link>
        </p>
      </form>
    </div>
  )
}
