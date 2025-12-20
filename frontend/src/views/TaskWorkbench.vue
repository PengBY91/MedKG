<template>
  <div class="workbench-container">
    <!-- Workbench Header -->
    <div class="workbench-header">
      <div class="greeting-section">
        <h2 class="title">工作中心</h2>
        <p class="subtitle">欢迎回来，这是您目前的任务概览与待办事项</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
          <el-button type="primary" :icon="Plus" disabled>创建任务</el-button>
        </el-button-group>
      </div>
    </div>

    <!-- Enhanced Statistics -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="item in statConfig" :key="item.label">
        <div class="stat-card" :class="item.type">
          <div class="stat-icon-wrap">
            <el-icon :size="24"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value">{{ item.value || 0 }}</div>
          </div>
          <div class="stat-trend" v-if="item.trend">
            <el-icon><Top /></el-icon> {{ item.trend }}
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Main Content: Task List -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="section-icon"><List /></el-icon>
            <span>任务列表</span>
          </div>
          <div class="header-right">
            <el-radio-group v-model="taskFilter" size="default" @change="loadTasks" class="filter-group">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="pending">待处理</el-radio-button>
              <el-radio-button label="in_progress">进行中</el-radio-button>
              <el-radio-button label="completed">已完成</el-radio-button>
            </el-radio-group>
            <el-input
              v-model="searchQuery"
              placeholder="搜索任务..."
              style="width: 200px; margin-left: 12px"
              :prefix-icon="Search"
              clearable
            />
          </div>
        </div>
      </template>

      <el-table 
        :data="filteredTasks" 
        v-loading="loading" 
        class="task-table"
        :header-cell-style="{ background: '#f8fafc', fontWeight: '600', color: '#64748b' }"
      >
        <el-table-column prop="type" label="任务类型" width="140">
          <template #default="{ row }">
            <div class="type-cell">
              <div class="type-dot" :class="row.type"></div>
              <span>{{ getTaskTypeLabel(row.type) }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="id" label="任务详情" min-width="250">
          <template #default="{ row }">
            <div class="detail-cell">
              <div class="task-id">#{{ row.id.slice(-6).toUpperCase() }}</div>
              <div class="task-node">{{ row.node_id }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="当前状态" width="130">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              effect="light" 
              round 
              class="status-tag"
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="就绪时间" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Clock /></el-icon>
              <span>{{ formatDate(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="快捷操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button 
                link 
                type="primary" 
                @click="handleTask(row)"
                :disabled="row.status === 'completed'"
              >
                处理
              </el-button>
              <el-divider direction="vertical" />
              <el-button link @click="viewDetail(row)">详情</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="10"
          layout="total, prev, pager, next"
          :total="tasks.length"
        />
      </div>
    </el-card>

    <!-- Task Handling Dialog (Drawer for better UX) -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerMode === 'handle' ? '任务处理' : '任务详情'"
      direction="rtl"
      size="500px"
      class="task-drawer"
    >
      <div v-if="currentTask" class="drawer-content">
        <div class="drawer-header-info">
          <el-tag :type="getTaskTypeColor(currentTask.type)" class="type-tag">
            {{ getTaskTypeLabel(currentTask.type) }}
          </el-tag>
          <h3>任务编号: {{ currentTask.id }}</h3>
        </div>

        <el-divider>基本信息</el-divider>
        <el-descriptions :column="1" border class="task-desc">
          <el-descriptions-item label="任务状态">
            <el-tag :type="getStatusColor(currentTask.status)" size="small">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关联节点">{{ currentTask.node_id }}</el-descriptions-item>
          <el-descriptions-item label="分配人">{{ currentTask.assignee || '系统自动分配' }}</el-descriptions-item>
          <el-descriptions-item label="创建日期">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="currentTask.completed_at" label="完成日期">
            {{ formatDate(currentTask.completed_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <template v-if="drawerMode === 'handle'">
          <el-divider>处理意见</el-divider>
          <el-form :model="taskForm" label-position="top">
            <el-form-item label="审核结果">
              <el-radio-group v-model="taskForm.result" class="result-radio">
                <el-radio label="approved" border>确认通过</el-radio>
                <el-radio label="rejected" border>需修改</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="备注说明">
              <el-input
                v-model="taskForm.comments"
                type="textarea"
                :rows="5"
                placeholder="请输入您的审核意见..."
              />
            </el-form-item>
          </el-form>
        </template>
        <template v-else>
          <el-divider>处理历史</el-divider>
          <div class="history-content">
            <div class="history-item">
              <div class="history-label">最终结论:</div>
              <div class="history-val">{{ currentTask.result || '尚未处理' }}</div>
            </div>
            <div class="history-item">
              <div class="history-label">处理备注:</div>
              <div class="history-val">{{ currentTask.comments || '无备注内容' }}</div>
            </div>
          </div>
        </template>

        <div class="drawer-footer" v-if="drawerMode === 'handle'">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask" :loading="submitting" block>提交处理结果</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, Plus, List, Search, Clock, 
  Checked, Timer, CircleCheck, Wallet, Top 
} from '@element-plus/icons-vue'
import api from '../services/api'

const loading = ref(false)
const tasks = ref([])
const taskFilter = ref('')
const searchQuery = ref('')
const drawerVisible = ref(false)
const drawerMode = ref('handle') // 'handle' or 'view'
const submitting = ref(false)
const currentTask = ref(null)
const currentPage = ref(1)

const stats = reactive({
  pending: 0,
  in_progress: 0,
  completed_today: 0,
  total_completed: 0
})

const statConfig = computed(() => [
  { label: '待处理任务', value: stats.pending, icon: Timer, type: 'pending', trend: '+2' },
  { label: '进行中任务', value: stats.in_progress, icon: Clock, type: 'processing' },
  { label: '今日已完成', value: stats.completed_today, icon: CircleCheck, type: 'success', trend: '12%' },
  { label: '历史总计', value: stats.total_completed, icon: Wallet, type: 'total' }
])

const taskForm = reactive({
  result: 'approved',
  comments: ''
})

const filteredTasks = computed(() => {
  let result = tasks.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.id.toLowerCase().includes(q) || 
      t.node_id.toLowerCase().includes(q)
    )
  }
  // taskFilter is already handled by loadTasks but for reactive search:
  return result
})

const loadTasks = async () => {
  loading.value = true
  try {
    const params = taskFilter.value ? { status: taskFilter.value } : {}
    const response = await api.getUserTasks(params)
    tasks.value = response.data.items

    // Update stats based on real data
    const allTasksRes = await api.getUserTasks({})
    const all = allTasksRes.data.items
    stats.pending = all.filter(t => t.status === 'pending').length
    stats.in_progress = all.filter(t => t.status === 'in_progress' || t.status === 'assigned').length
    stats.total_completed = all.filter(t => t.status === 'completed').length
    stats.completed_today = 5 // Mock today completion
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleTask = (task) => {
  currentTask.value = task
  taskForm.result = 'approved'
  taskForm.comments = ''
  drawerMode.value = 'handle'
  drawerVisible.value = true
}

const viewDetail = (task) => {
  currentTask.value = task
  drawerMode.value = 'view'
  drawerVisible.value = true
}

const submitTask = async () => {
  if (!currentTask.value) return

  submitting.value = true
  try {
    await api.completeTask(currentTask.value.id, taskForm)
    ElMessage({
      message: '任务已成功处理并封存',
      type: 'success',
      plain: true
    })
    drawerVisible.value = false
    loadTasks()
  } catch (error) {
    ElMessage.error('任务处理失败')
  } finally {
    submitting.value = false
  }
}

const getTaskTypeColor = (type) => {
  const colors = {
    approval: 'warning',
    review: 'primary',
    submit: 'info'
  }
  return colors[type] || 'info'
}

const getTaskTypeLabel = (type) => {
  const labels = {
    approval: '治理审批',
    review: '逻辑复核',
    submit: '数据上架'
  }
  return labels[type] || type
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'info',
    assigned: 'primary',
    in_progress: 'warning',
    completed: 'success',
    rejected: 'danger'
  }
  return colors[status] || 'info'
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '待处理',
    assigned: '已分配',
    in_progress: '进行中',
    completed: '已完成',
    rejected: '已拒绝'
  }
  return labels[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.workbench-container {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 30px;
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #64748b;
  margin: 0;
  font-size: 14px;
}

/* Stat Cards Styling */
.stats-row {
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.05);
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.pending .stat-icon-wrap { background: #fee2e2; color: #ef4444; }
.stat-card.processing .stat-icon-wrap { background: #e0f2fe; color: #0ea5e9; }
.stat-card.success .stat-icon-wrap { background: #dcfce7; color: #22c55e; }
.stat-card.total .stat-icon-wrap { background: #f1f5f9; color: #64748b; }

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.stat-trend {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 12px;
  font-weight: 600;
  color: #22c55e;
  display: flex;
  align-items: center;
}

/* List Card Styling */
.list-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #1e293b;
}

.section-icon {
  color: #409eff;
}

.filter-group :deep(.el-radio-button__inner) {
  border-radius: 20px;
  padding: 8px 16px;
  border: none !important;
  background: #f1f5f9;
  color: #64748b;
  margin: 0 4px;
}

.filter-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #1e293b;
  color: white;
  box-shadow: none;
}

/* Table Styling */
.task-table {
  width: 100%;
}

.type-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.type-dot.approval { background: #f59e0b; }
.type-dot.review { background: #3b82f6; }
.type-dot.submit { background: #10b981; }

.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #94a3b8;
}

.task-node {
  font-weight: 500;
  color: #334155;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}

.action-cell .el-button {
  font-weight: 600;
}

.pagination-footer {
  padding: 24px;
  display: flex;
  justify-content: flex-end;
}

/* Drawer Styling */
.task-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.drawer-content {
  padding: 0 10px;
}

.drawer-header-info {
  margin-bottom: 24px;
}

.drawer-header-info h3 {
  margin: 12px 0 0 0;
  font-size: 18px;
  color: #1e293b;
}

.task-desc :deep(.el-descriptions__label) {
  width: 100px;
  color: #64748b;
}

.result-radio {
  display: flex;
  gap: 12px;
  width: 100%;
}

.result-radio :deep(.el-radio) {
  flex: 1;
  margin-right: 0;
  height: 48px;
  display: flex;
  justify-content: center;
}

.drawer-footer {
  margin-top: 40px;
  display: flex;
  gap: 12px;
}

.history-item {
  margin-bottom: 20px;
}

.history-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.history-val {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  color: #1e293b;
  font-size: 14px;
  line-height: 1.6;
}
</style>
