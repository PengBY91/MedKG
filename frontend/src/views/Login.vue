<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-section">
          <el-icon :size="48" class="logo-icon"><DataAnalysis /></el-icon>
        </div>
        <h1>医疗数据治理平台</h1>
        <p class="subtitle">Medical Data Governance Platform</p>
      </div>

      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="logging"
            @click="handleLogin"
            class="login-button"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <el-alert
          title="测试账号"
          type="info"
          :closable="false"
          show-icon
        >
          <p>管理员: admin / admin123</p>
          <p>审核员: reviewer / reviewer123</p>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
import api from '../services/api'

const router = useRouter()
const loginFormRef = ref(null)
const logging = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate()
  if (!valid) return

  logging.value = true

  try {
    const response = await api.login(loginForm.username, loginForm.password)
    
    // Store token
    localStorage.setItem('token', response.data.access_token)
    localStorage.setItem('user', JSON.stringify(response.data.user || { username: loginForm.username }))
    
    ElMessage.success('登录成功')
    
    // Redirect to home
    router.push('/home')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    logging.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-section {
  margin-bottom: 20px;
}

.logo-icon {
  color: #667eea;
}

.login-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 30px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

.login-footer {
  margin-top: 30px;
}

.login-footer :deep(.el-alert) {
  background: #f5f7fa;
}

.login-footer p {
  margin: 4px 0;
  font-size: 13px;
}
</style>
