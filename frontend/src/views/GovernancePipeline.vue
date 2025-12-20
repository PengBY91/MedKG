<template>
  <div class="pipeline-container">
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">数据治理流水线</h2>
        <p class="subtitle">全流程自动化监管：从政策入库到规则部署的闭环管理</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="fetchInstances">刷新流水线</el-button>
        <el-button type="primary" :icon="Plus" @click="$router.push('/upload')">启动新任务</el-button>
      </div>
    </div>

    <!-- Active Pipelines -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="instances.length > 0" class="pipeline-list">
      <div v-for="inst in instances" :key="inst.id" class="pipeline-card">
        <div class="pipeline-meta">
          <div class="meta-main">
            <span class="doc-name">{{ inst.context?.document_name || '未命名治理任务' }}</span>
            <el-tag :type="getStatusType(inst.status)" size="small" effect="dark" round>
              {{ getStatusLabel(inst.status) }}
            </el-tag>
          </div>
          <div class="meta-footer">
            <span>实例 ID: {{ inst.id.substring(0,8) }}</span>
            <el-divider direction="vertical" />
            <span>启动于: {{ formatDate(inst.created_at) }}</span>
          </div>
        </div>

        <div class="pipeline-progress">
          <el-steps :active="getStepIndex(inst.current_node)" align-center finish-status="success">
            <el-step title="政策入库" description="DeepKE 解析" />
            <el-step title="术语核对" description="ICD-10 映射" />
            <el-step title="规则提取" description="NLP 编译" />
            <el-step title="风控确认" description="沙箱验证" />
            <el-step title="归档部署" description="正式上线" />
          </el-steps>
        </div>

        <div class="pipeline-actions">
          <div class="current-status">
            <el-icon class="status-icon" :class="inst.status"><Timer /></el-icon>
            <span>当前环节：{{ getNodeName(inst.current_node) }}</span>
          </div>
          <el-button 
            v-if="inst.status === 'running'"
            type="primary" 
            plain 
            class="action-btn"
            @click="handleJump(inst)"
          >
            立即协同处理 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <el-empty v-else description="暂无正在运行的治理流水线" />

    <!-- History / Completed Pipelines -->
    <div class="history-section" v-if="completedInstances.length > 0">
      <div class="section-title">已完成的流水线记录</div>
      <el-table :data="completedInstances" class="history-table">
        <el-table-column prop="context.document_name" label="政策文档" min-width="200" />
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="120">
          <template #default="{ row }">
            {{ calculateDuration(row) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default>
            <el-tag type="success" size="small" plain>已部署</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Plus, Timer, ArrowRight } from '@element-plus/icons-vue'
import api from '../services/api'
import { dayjs } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const allInstances = ref([])

const instances = computed(() => allInstances.value.filter(i => i.status === 'running'))
const completedInstances = computed(() => allInstances.value.filter(i => i.status === 'completed'))

const fetchInstances = async () => {
    loading.value = true
    try {
        const response = await api.getWorkflowInstances()
        allInstances.value = response.data.items.filter(i => i.definition_id && (i.definition_id !== 'terminology_review' || i.context?.document_name))
        // Filter for governance_pipeline by name or definition_id if available, 
        // but here we just show those that look like our new pipeline.
    } catch (e) {
        console.error('Failed to fetch instances')
    } finally {
        loading.value = false
    }
}

const getStepIndex = (nodeId) => {
    const map = {
        'start': 0,
        'ingest': 0,
        'terminology': 1,
        'extraction': 2,
        'review': 3,
        'end': 5
    }
    return map[nodeId] ?? 0
}

const getNodeName = (nodeId) => {
    const map = {
        'start': '准备中',
        'ingest': '自动解析中',
        'terminology': '人工介入：术语核对',
        'extraction': '自动编译中',
        'review': '人工介入：规则确认',
        'end': '已上线'
    }
    return map[nodeId] ?? nodeId
}

const getStatusType = (status) => {
    return status === 'running' ? 'primary' : 'success'
}

const getStatusLabel = (status) => {
    return status === 'running' ? '进行中' : '已归档'
}

const formatDate = (dateStr) => {
    return dateStr ? dayjs(dateStr).format('YYYY-MM-DD HH:mm') : '-'
}

const calculateDuration = (inst) => {
    if(!inst.started_at || !inst.completed_at) return '-'
    const start = dayjs(inst.started_at)
    const end = dayjs(inst.completed_at)
    const diff = end.diff(start, 'minute')
    return diff < 60 ? `${diff} 分钟` : `${(diff/60).toFixed(1)} 小时`
}

const handleJump = (inst) => {
    // Find active task for this instance
    // In a real app, the API would return the current task object
    // For now, we find the task from the instance.tasks list if available
    const taskId = inst.tasks && inst.tasks.length > 0 ? inst.tasks[inst.tasks.length - 1] : null
    
    const query = taskId ? { taskId: taskId, instanceId: inst.id } : {}

    if (inst.current_node === 'terminology') {
        router.push({ path: '/terminology', query })
    } else if (inst.current_node === 'review') {
        router.push({ path: '/rules', query })
    } else {
        router.push('/upload')
    }
}

onMounted(fetchInstances)
</script>

<style scoped>
.pipeline-container {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 50px;
}

.page-header {
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
}

.pipeline-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 50px;
}

.pipeline-card {
  background: white;
  border-radius: 24px;
  border: 1px solid #e2e8f0;
  padding: 30px;
  transition: all 0.3s ease;
}

.pipeline-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.08);
}

.pipeline-meta {
  margin-bottom: 30px;
}

.meta-main {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.doc-name {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.meta-footer {
  font-size: 13px;
  color: #94a3b8;
}

.pipeline-progress {
  padding: 20px 0 40px 0;
}

.pipeline-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  border-top: 1px solid #f1f5f9;
}

.current-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.status-icon {
  font-size: 18px;
}

.status-icon.running {
  color: #3b82f6;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.action-btn {
  border-radius: 12px;
  padding: 0 24px;
  height: 40px;
  font-weight: 600;
}

.history-section {
  margin-top: 60px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 20px;
}

.history-table {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}
</style>
