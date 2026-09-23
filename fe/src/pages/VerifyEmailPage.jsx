import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import * as authApi from '../api/authApi'
import FormError from '../components/FormError.jsx'

export default function VerifyEmailPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState(location.state?.email || '')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await authApi.verifyEmail({ email, code })
      navigate('/login', { state: { justVerified: true } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Xác thực thất bại')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResend = async () => {
    setError('')
    setMessage('')
    try {
      await authApi.resendCode({ email })
      setMessage('Đã gửi lại mã xác nhận, kiểm tra email của bạn')
    } catch (err) {
      setError(err.response?.data?.detail || 'Không gửi lại được mã')
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Xác nhận email</h1>
        <p className="auth-subtitle">Nhập mã 6 số vừa được gửi tới email của bạn</p>

        <FormError message={error} />
        {message && <p className="auth-message">{message}</p>}

        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label>Mã xác nhận</label>
        <input value={code} onChange={(e) => setCode(e.target.value)} required maxLength={6} minLength={6} />

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang xác nhận...' : 'Xác nhận'}
        </button>

        <button type="button" className="btn-secondary" onClick={handleResend}>
          Gửi lại mã
        </button>

        <p className="auth-footer">
          <Link to="/login">Quay lại đăng nhập</Link>
        </p>
      </form>
    </div>
  )
}
