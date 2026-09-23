import { useEffect, useState } from 'react'
import { API_BASE_URL, getAccessToken } from '../api/client'
import { listUsers } from '../api/userApi'

export default function UserList() {
  const [users, setUsers] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    listUsers()
      .then(({ data }) => {
        if (mounted) setUsers(data)
      })
      .finally(() => {
        if (mounted) setIsLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const token = getAccessToken()
    if (!token) return undefined

    const source = new EventSource(`${API_BASE_URL}/users/stream?token=${encodeURIComponent(token)}`)

    source.onmessage = (event) => {
      try {
        const newUser = JSON.parse(event.data)
        setUsers((prev) => (prev.some((u) => u.id === newUser.id) ? prev : [newUser, ...prev]))
      } catch {
        // bỏ qua payload không hợp lệ
      }
    }

    return () => source.close()
  }, [])

  if (isLoading) return <p>Đang tải danh sách...</p>

  if (users.length === 0) return <p>Chưa có người dùng nào.</p>

  return (
    <table className="user-table">
      <thead>
        <tr>
          <th>Họ tên</th>
          <th>Email</th>
        </tr>
      </thead>
      <tbody>
        {users.map((u) => (
          <tr key={u.id}>
            <td>{u.full_name}</td>
            <td>{u.email}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
