<template>
  <div class="terminology-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">术语标准化工作台</h2>
        <p class="subtitle">利用知识图谱与语义模型，将临床术语映射至标准编码体系 (ICD-10 / CVPS)</p>
      </div>
      <div class="header-actions">
        <el-button v-if="taskId" type="success" :icon="Check" @click="completeWorkflowTask">完成当前治理任务</el-button>
        <el-button :icon="Refresh" @click="fetchLibrary">刷新水库</el-button>
        <el-button type="primary" :icon="Plus" @click="showAddDialog = true">新增标准项</el-button>
      </div>
    </div>

    <!-- Main Workflow Section -->
    <div class="workflow-grid">
      <!-- Input Section -->
      <el-card class="input-card" shadow="never">
        <template #header>
          <div class="card-header-icon">
            <el-icon><MagicStick /></el-icon>
            <span>智能匹配引擎</span>
          </div>
        </template>
        
        <el-form :model="form" label-position="top">
          <el-form-item label="待标准化术语 (支持批量)">
            <el-select
              v-model="form.terms"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="请输入临床诊断、手术或药物名称..."
              class="premium-select"
            >
              <el-option label="二型糖伴酮症" value="二型糖伴酮症" />
              <el-option label="原发性高血压" value="原发性高血压" />
              <el-option label="冠状动脉粥样硬化" value="冠状动脉粥样硬化" />
            </el-select>
          </el-form-item>

          <div class="form-footer">
            <el-button type="primary" :loading="normalizing" @click="normalizeTerms" class="run-btn">
              <el-icon><VideoPlay /></el-icon> 执行标准化流程
            </el-button>
            <el-button @click="clearResults" plain>清空输入</el-button>
          </div>
        </el-form>
      </el-card>

      <!-- Match Results -->
      <div v-if="results.length > 0" class="results-wrapper">
        <div class="section-title">匹配分析报告</div>
        <div v-for="(item, index) in results" :key="index" class="result-item-card">
          <div class="result-main">
            <div class="term-info">
              <div class="label">原始术语</div>
              <div class="value">{{ item.term }}</div>
            </div>
            <el-icon class="arrow-icon"><Right /></el-icon>
            <div class="match-info">
              <div class="label">标准编码 / 名称</div>
              <div class="value-wrap">
                <el-tag size="small" effect="dark" class="code-tag">{{ item.code }}</el-tag>
                <span class="match-name">{{ item.display || '匹配项' }}</span>
              </div>
            </div>
            <div class="confidence-info">
              <div class="label">语义置信度</div>
              <el-progress 
                :percentage="Math.round((item.confidence || 0.9) * 100)" 
                :color="getConfidenceColor(item.confidence || 0.9)"
                :stroke-width="12"
                stroke-linecap="round"
              />
            </div>
            <div class="action-info">
              <el-button-group v-if="item.status === 'AUTO_MATCHED'">
                <el-button type="success" :icon="Check" circle @click="approveTerm(item)" />
                <el-button type="danger" :icon="Close" circle @click="rejectTerm(item)" />
              </el-button-group>
              <el-tag v-else :type="getStatusType(item.status)" round>{{ getStatusLabel(item.status) }}</el-tag>
            </div>
          </div>
          
          <!-- Evidence Chain (Expandable) -->
          <div class="evidence-chain">
            <div class="chain-header">
              <el-icon><Share /></el-icon>
              <span>知识图谱推理路径 (KAG Reasoning Path)</span>
            </div>
            <div class="chain-content">
              {{ item.evidence_path || '通过语义嵌入 (Semantic Embedding) 与图谱本体节点实现高置信度映射。' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Library Table -->
    <el-card class="library-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="section-icon"><Reading /></el-icon>
            <span>本地标准术语映射库</span>
          </div>
        </div>
      </template>

      <el-table :data="libraryTerms" v-loading="loadingLibrary" class="custom-table">
        <el-table-column prop="term" label="原始术语" min-width="200" />
        <el-table-column prop="code" label="标准编码" width="140">
          <template #default="{ row }">
            <span class="code-text">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="display" label="标准对应名称" min-width="200" />
        <el-table-column prop="system" label="所属体系" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info" plain>{{ row.system || 'ICD-10' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="管理" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="danger" link @click="deleteTerm(row.term)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add Dialog -->
    <el-dialog v-model="showAddDialog" title="人工录入标准化映射" width="480px" class="premium-dialog">
      <el-form :model="addForm" label-position="top">
        <el-form-item label="原始术语名称">
          <el-input v-model="addForm.term" placeholder="临床侧使用的术语" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="标准编码">
              <el-input v-model="addForm.code" placeholder="如 E11.900" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="术语体系">
              <el-select v-model="addForm.system" style="width: 100%">
                <el-option label="ICD-10" value="ICD-10" />
                <el-option label="CVPS-4" value="CVPS-4" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标准显示名称">
          <el-input v-model="addForm.display" placeholder="国家标准库中的正式名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddTerm">确认入库</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  MagicStick, Check, Close, Share, Refresh, Plus, 
  VideoPlay, Reading, Right, Search
} from '@element-plus/icons-vue'
import api from '../services/api'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.query.taskId)
const instanceId = computed(() => route.query.instanceId)

const form = reactive({ terms: [] })
const showAddDialog = ref(false)
const addForm = reactive({ term: '', code: '', display: '', system: 'ICD-10' })
const normalizing = ref(false)
const loadingLibrary = ref(false)
const results = ref([])
const libraryTerms = ref([])

const fetchLibrary = async () => {
    loadingLibrary.value = true
    try {
        const response = await api.getTerminology()
        libraryTerms.value = response.data
    } catch (error) {
        ElMessage.error('获取术语库失败')
    } finally {
        loadingLibrary.value = false
    }
}

const handleAddTerm = async () => {
    if(!addForm.term || !addForm.code) {
        ElMessage.warning('请填写必填项')
        return
    }
    try {
        await api.submitFeedback({
            term: addForm.term,
            suggested_code: addForm.code,
            reviewer_id: 'ADMIN',
            status: 'APPROVED'
        })
        ElMessage.success('术语映射已手动同步至正式库')
        showAddDialog.value = false
        fetchLibrary()
    } catch (e) {
        ElMessage.error('同步失败')
    }
}

const normalizeTerms = async () => {
  if (form.terms.length === 0) {
    ElMessage.warning('请提供至少一个临床术语')
    return
  }
  normalizing.value = true
  results.value = []
  try {
    const response = await api.normalizeTerms(form.terms)
    results.value = response.data
    ElMessage.success({ message: `完成 ${results.value.length} 项术语的智能标准化分析`, duration: 3000 })
  } catch (error) {
    ElMessage.error('标准化流程异常断开')
  } finally {
    normalizing.value = false
  }
}

const clearResults = () => {
  form.terms = []
  results.value = []
}

const getStatusType = (status) => {
  const map = { 'AUTO_MATCHED': 'warning', 'APPROVED': 'success', 'REJECTED': 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = { 'AUTO_MATCHED': '待核对', 'APPROVED': '已入库', 'REJECTED': '已驳回' }
  return labels[status] || status
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.85) return '#10b981'
  if (confidence >= 0.7) return '#f59e0b'
  return '#ef4444'
}

const approveTerm = async (row) => {
  try {
    await api.submitFeedback({ term: row.term, suggested_code: row.code, status: 'APPROVED' })
    row.status = 'APPROVED'
    ElMessage.success('已确认匹配并自动归档')
    fetchLibrary()
  } catch (error) {}
}

const rejectTerm = async (row) => {
  try {
    row.status = 'REJECTED'
    ElMessage.info('已标记为匹配错误，将进入人工校准池')
  } catch (error) {}
}

const deleteTerm = async (term) => {
    try {
        await ElMessageBox.confirm('确定要从正式映射库中移除此项吗？', '重要提醒', { 
          confirmButtonText: '确定移除',
          cancelButtonText: '保留',
          type: 'warning' 
        })
        await api.deleteTerminology(term)
        ElMessage.success('映射记录已抹除')
        fetchLibrary()
    } catch (e) {}
}

const completeWorkflowTask = async () => {
    try {
        await api.completeTask(taskId.value, {
            result: 'approved',
            comments: '术语标准化核对完成'
        })
        ElMessage.success('治理任务已提交，流水线将自动进入下一阶段')
        router.push('/pipeline')
    } catch (e) {
        ElMessage.error('提交失败')
    }
}

onMounted(async () => {
    fetchLibrary()
    
    // If part of a workflow, pre-populate from context
    if (instanceId.value) {
        try {
            const response = await api.getWorkflowInstance(instanceId.value)
            const instance = response.data
            if (instance.context && instance.context.entities) {
                // Remove duplicates and empty values
                const uniqueEntities = [...new Set(instance.context.entities)].filter(Boolean)
                form.terms = uniqueEntities
                if (uniqueEntities.length > 0) {
                    ElMessage.info(`已根据文档解析结果预填 ${uniqueEntities.length} 个待核对术语`)
                }
            }
        } catch (e) {
            console.error('Failed to fetch instance details', e)
        }
    }
})
</script>

<style scoped>
.terminology-container {
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

/* Workflow Grid */
.workflow-grid {
  display: grid;
  gap: 24px;
  margin-bottom: 40px;
}

.input-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.card-header-icon {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #3b82f6;
}

.premium-select {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  padding: 8px 12px;
  border-radius: 12px;
}

.form-footer {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.run-btn {
  height: 44px;
  padding: 0 24px;
  border-radius: 12px;
  font-weight: 600;
}

/* Results Wrapper */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-item-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.result-item-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
}

.result-main {
  display: flex;
  align-items: center;
  padding: 24px;
  gap: 30px;
}

.label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.term-info, .match-info {
  flex: 1;
}

.term-info .value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.arrow-icon {
  font-size: 20px;
  color: #cbd5e1;
}

.value-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.code-tag {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.match-name {
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
}

.confidence-info {
  width: 180px;
}

.action-info {
  width: 120px;
  display: flex;
  justify-content: flex-end;
}

/* Evidence Chain */
.evidence-chain {
  background: #f8fafc;
  padding: 16px 24px;
  border-top: 1px solid #f1f5f9;
}

.chain-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}

.chain-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
}

/* Library Table */
.library-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.section-icon { color: #10b981; }

.code-text {
  font-family: 'JetBrains Mono', monospace;
  color: #3b82f6;
  font-weight: 600;
}

.custom-table :deep(.el-table__header-wrapper th) {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
}

/* Dialog */
.premium-dialog :deep(.el-dialog) {
  border-radius: 20px;
}

.premium-dialog :deep(.el-dialog__header) {
  padding-bottom: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
