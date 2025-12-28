<template>
  <el-container class="app-container">
    <el-header v-if="!isLoginPage" class="app-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <el-icon :size="32"><DataAnalysis /></el-icon>
          </div>
          <div class="title-section">
            <h1>医疗数据治理平台</h1>
            <p class="subtitle">Medical Data Governance Platform</p>
          </div>
        </div>
        
        <el-menu 
          mode="horizontal" 
          :default-active="activeIndex" 
          router
          class="nav-menu"
          :ellipsis="false"
        >
          <el-menu-item index="/tasks">
            <el-icon><Checked /></el-icon>
            <span>工作中心</span>
          </el-menu-item>

          <el-sub-menu index="governance">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>治理工具</span>
            </template>
            <el-menu-item index="/pipeline">
              <el-icon><Connection /></el-icon>
              <span>治理流水线</span>
            </el-menu-item>
            <el-menu-item index="/upload">
              <el-icon><Upload /></el-icon>
              <span>政策管理</span>
            </el-menu-item>
            <el-menu-item index="/rules">
              <el-icon><Document /></el-icon>
              <span>规则审核</span>
            </el-menu-item>
            <el-menu-item index="/terminology">
              <el-icon><Edit /></el-icon>
              <span>术语清洗</span>
            </el-menu-item>
            <el-menu-item index="/examination">
              <el-icon><Checked /></el-icon>
              <span>标准化任务</span>
            </el-menu-item>
            <el-menu-item index="/quality">
              <el-icon><DataAnalysis /></el-icon>
              <span>质量监控</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/examination/ontology">
             <el-icon><Connection /></el-icon>
             <span>知识图谱</span>
          </el-menu-item>

          <el-menu-item index="/catalog">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据资产</span>
          </el-menu-item>
          
          <el-menu-item index="/explanation">
            <el-icon><ChatDotRound /></el-icon>
            <span>辅助决策</span>
          </el-menu-item>

          <el-sub-menu index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统中心</span>
            </template>
            <el-menu-item index="/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/tenants">
              <el-icon><OfficeBuilding /></el-icon>
              <span>租户管理</span>
            </el-menu-item>
            <el-menu-item index="/system-config">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>

        <div class="user-section">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
              <span class="username">{{ currentUser }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="system-config">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <el-main :class="['app-main', { 'is-login': isLoginPage }]">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>

    <el-footer v-if="!isLoginPage" class="app-footer">
      <div class="footer-content">
        <span>© 2024 医疗数据治理平台 | Medical Data Governance Platform</span>
        <span class="footer-links">
          <a href="#">帮助文档</a>
          <a href="#">API文档</a>
          <a href="#">关于我们</a>
        </span>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  DataAnalysis, Checked, Upload, Document, Edit, 
  ChatDotRound, User, OfficeBuilding, Tools, Setting 
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const activeIndex = computed(() => route.path)
const isLoginPage = computed(() => route.path === '/login')
const currentUser = ref('Admin')

onMounted(() => {
  const user = localStorage.getItem('user')
  if (user) {
    try {
      const userData = JSON.parse(user)
      currentUser.value = userData.username || 'Admin'
    } catch (e) {
      console.error('Failed to parse user data')
    }
  }
})

const handleUserCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中')
  } else if (command === 'system-config') {
    router.push('/system-config')
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 80px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 100%;
  margin: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  backdrop-filter: blur(10px);
}

.title-section h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: white;
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
}

.nav-menu {
  flex: 1;
  margin: 0 40px;
  background: transparent;
  border: none;
}

.nav-menu :deep(.el-menu-item),
.nav-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.9) !important;
  border: none !important;
  font-weight: 500;
  transition: all 0.3s ease;
  background: transparent !important;
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
}

.nav-menu :deep(.el-menu-item.is-active),
.nav-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  border-bottom: 3px solid white !important;
}

.nav-menu :deep(.el-icon) {
  margin-right: 6px;
  color: inherit !important;
}

.user-section {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.25);
}

.username {
  color: white;
  font-weight: 500;
  font-size: 14px;
}

.app-main {
  width: 100%;
  margin: 0;
  padding: 24px;
  min-height: calc(100vh - 140px);
}

.app-main.is-login {
  max-width: none;
  width: 100vw;
  height: 100vh;
  padding: 0;
  margin: 0;
  overflow: hidden;
}

.app-footer {
  background: white;
  border-top: 1px solid #e4e7ed;
  height: 60px;
  padding: 0;
}

.footer-content {
  width: 100%;
  margin: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  color: #606266;
  font-size: 14px;
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-links a {
  color: #606266;
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #409eff;
}

/* Page transition animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
