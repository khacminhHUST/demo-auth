import { apiClient } from './client'

export const register = (data) => apiClient.post('/auth/register', data)
export const verifyEmail = (data) => apiClient.post('/auth/verify-email', data)
export const resendCode = (data) => apiClient.post('/auth/resend-code', data)
export const login = (data) => apiClient.post('/auth/login', data)
export const refresh = () => apiClient.post('/auth/refresh')
export const logout = () => apiClient.post('/auth/logout')
export const me = () => apiClient.get('/auth/me')
export const forgotPassword = (data) => apiClient.post('/password/forgot', data)
export const resetPassword = (data) => apiClient.post('/password/reset', data)
export const changePassword = (data) => apiClient.post('/password/change', data)
