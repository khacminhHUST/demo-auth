import { apiClient } from './client'

export const listUsers = () => apiClient.get('/users')
