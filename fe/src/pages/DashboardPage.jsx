import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ChangePasswordForm from '../components/ChangePasswordForm.jsx'
import UserList from '../components/UserList.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showChangePassword, setShowChangePassword] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <h1>Xin chào, {user?.full_name}</h1>
          <p className="dashboard-email">{user?.email}</p>
        </div>
        <div className="dashboard-header-actions">
          <button className="btn-secondary" onClick={() => setShowChangePassword((v) => !v)}>
            Đổi mật khẩu
          </button>
          <button className="btn-secondary" onClick={handleLogout}>
            Đăng xuất
          </button>
        </div>
      </header>

      {showChangePassword && <ChangePasswordForm onClose={() => setShowChangePassword(false)} />}

      <section className="dashboard-section">
        <h2>Người dùng đã đăng ký</h2>
        <UserList />
      </section>
    </div>
  )
}
