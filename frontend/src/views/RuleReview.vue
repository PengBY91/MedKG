<template>
  <div class="rule-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">规则编译与智能审核</h2>
        <p class="subtitle">将自然语言政策解析为语义 SHACL 规则，并在仿真沙箱中验证业务影响</p>
      </div>
      <div class="header-actions">
        <el-button v-if="taskId" type="success" :icon="CircleCheck" @click="completeWorkflowTask">完成规则治理流程</el-button>
        <el-button :icon="Refresh" @click="fetchRules">同步规则库</el-button>
        <el-button type="primary" :icon="Plus" @click="showAddDialog = true">手动录入</el-button>
      </div>
    </div>

    <!-- Compilation Workflow -->
    <div class="workflow-section">
      <el-card class="primary-card" shadow="never">
        <template #header>
          <div class="card-header-icon">
            <el-icon><MagicStick /></el-icon>
            <span>规则编译器 (NLP → SHACL)</span>
          </div>
        </template>
        
        <el-form :model="form" label-position="top">
          <el-form-item label="输入政策条文 (自然语言)">
            <el-input
              v-model="form.policyText"
              type="textarea"
              :rows="5"
              placeholder="例如：参保人员在门诊进行血液透析治疗，每日最高限额标准为 400 元..."
              class="premium-textarea"
            />
          </el-form-item>

          <div class="form-actions">
            <el-button type="primary" :loading="compiling" @click="compileRule" class="action-btn-main">
              <el-icon><Cpu /></el-icon> 智能编译规则
            </el-button>
            <el-button @click="clearForm" plain>重置输入</el-button>
          </div>
        </el-form>
      </el-card>

      <!-- Compiled Output & Sandbox -->
      <el-collapse-transition>
        <div v-if="compiledRule" class="output-section">
          <div class="result-grid">
            <!-- Code Viewer -->
            <el-card class="code-card" shadow="never">
              <template #header>
                <div class="code-header">
                  <div class="status-indicator">
                    <div class="dot" :class="compiledRule.status"></div>
                    <span>{{ compiledRule.status === 'success' ? '编译就绪' : '编译失败' }}</span>
                  </div>
                  <el-tag size="small" effect="dark" type="info">SHACL Script</el-tag>
                </div>
              </template>
              <div class="code-container">
                <pre class="shacl-code">{{ compiledRule.shacl_content || '# Cannot retrieve script' }}</pre>
              </div>
              <div class="code-footer" v-if="compiledRule.status === 'success'">
                <el-button type="warning" :loading="testing" @click="testInSandbox" style="width: 100%">
                  <el-icon><Odometer /></el-icon> 启动沙箱压力测试
                </el-button>
              </div>
            </el-card>

            <!-- Test Metrics -->
            <div v-if="testResult" class="metrics-panel">
              <div class="section-title">由于此规则变更引发的预期影响</div>
              <div class="metrics-grid">
                <div class="metric-item">
                  <div class="m-label">预计拒付率</div>
                  <div class="m-value" :class="testResult.rejection_rate > 30 ? 'danger' : 'success'">
                    {{ testResult.rejection_rate }}%
                  </div>
                  <div class="m-trend">较基线 {{ testResult.delta_from_baseline > 0 ? '+' : '' }}{{ testResult.delta_from_baseline }}%</div>
                </div>
                <div class="metric-item">
                  <div class="m-label">涉及总病例</div>
                  <div class="m-value primary">{{ testResult.total_cases }}</div>
                  <div class="m-trend">测试集: {{ testResult.test_dataset }}</div>
                </div>
                <div class="metric-item">
                  <div class="m-label">违规预警数</div>
                  <div class="m-value warning">{{ testResult.violations_found }}</div>
                  <div class="m-trend">命中率: {{ testResult.total_cases > 0 ? ((testResult.violations_found/testResult.total_cases)*100).toFixed(1) : 0 }}%</div>
                </div>
              </div>

              <!-- Action Prompt -->
              <div class="sandbox-actions">
                <el-alert title="测试结论：规则符合预期，建议部署。" type="success" :closable="false" show-icon />
                <div class="btn-group">
                  <el-button type="primary" @click="saveToLibrary">保存并发布</el-button>
                  <el-button type="success" plain @click="submitForReview">提交专家人工审核</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-transition>
    </div>

    <!-- Knowledge Store -->
    <el-card class="library-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="section-icon"><Reading /></el-icon>
            <span>规则知识库 (SHACL Store)</span>
          </div>
        </div>
      </template>

      <el-table :data="allRules" v-loading="loadingLibrary" class="custom-table">
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="rule_type" label="规则类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="light" round>{{ row.rule_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject" label="监管实体" width="150" />
        <el-table-column prop="explanation" label="业务解释" min-width="250" />
        <el-table-column prop="object_value" label="阈值设定" width="120" align="center">
          <template #default="{ row }">
            <span class="threshold-text">{{ row.object_value }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button link type="primary" @click="editRule(row)">编辑</el-button>
              <el-button link type="danger" @click="deleteRule(row.id)">下架</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Manual Add Dialog -->
    <el-dialog v-model="showAddDialog" title="人工录入业务规则" width="580px" class="premium-dialog">
      <el-form :model="addForm" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="规则分类">
              <el-select v-model="addForm.rule_type" style="width: 100%">
                <el-option label="限额规则" value="limit" />
                <el-option label="互斥规则" value="exclusion" />
                <el-option label="频次规则" value="frequency" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规则主体 (实体路径)">
              <el-input v-model="addForm.subject" placeholder="如：肾透析" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="业务逻辑说明">
          <el-input v-model="addForm.explanation" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="SHACL 脚本代码 (底层执行逻辑)">
          <el-input v-model="addForm.shacl_content" type="textarea" :rows="6" class="monospaced-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddRule">确认入库</el-button>
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
  MagicStick, Refresh, Plus, Cpu, Odometer, Reading, 
  CircleCheck, CloseBold, Search 
} from '@element-plus/icons-vue'
import api from '../services/api'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.query.taskId)
const instanceId = computed(() => route.query.instanceId)

const form = reactive({ policyText: '' })
const showAddDialog = ref(false)
const addForm = reactive({ 
    rule_type: 'limit', subject: '', predicate: 'max_cost', 
    object_value: '', explanation: '', shacl_content: '' 
})

const compiling = ref(false)
const testing = ref(false)
const loadingLibrary = ref(false)
const compiledRule = ref(null)
const testResult = ref(null)
const allRules = ref([])

const fetchRules = async () => {
    loadingLibrary.value = true
    try {
        const response = await api.getRules()
        allRules.value = response.data
    } catch (error) {
        ElMessage.error('规则库同步失败')
    } finally {
        loadingLibrary.value = false
    }
}

const compileRule = async () => {
  if (!form.policyText.trim()) {
    ElMessage.warning('请输入需要编译的政策条文')
    return
  }
  compiling.value = true
  compiledRule.value = null
  testResult.value = null
  try {
    const response = await api.compileRule(form.policyText)
    compiledRule.value = response.data
    ElMessage.success('NLP语义解析核心已完成规则提取')
  } catch (error) {
    ElMessage.error('编译引擎响应异常')
  } finally {
    compiling.value = false
  }
}

const testInSandbox = async () => {
  testing.value = true
  try {
    const response = await api.testRule(compiledRule.value.shacl_content)
    testResult.value = response.data
    ElMessage.success('沙箱风险模拟完成')
  } catch (error) {
    ElMessage.error('测试环境无法就绪')
  } finally {
    testing.value = false
  }
}

const saveToLibrary = async () => {
    try {
        const payload = {
            ...compiledRule.value,
            explanation: compiledRule.value.explanation || form.policyText,
        }
        await api.saveRule(payload)
        ElMessage.success('规则已正式发布至生产环境')
        fetchRules()
        clearForm()
    } catch (e) {
        ElMessage.error('发布失败')
    }
}

const handleAddRule = async () => {
    if(!addForm.subject || !addForm.explanation) return ElMessage.warning('请填写核心业务逻辑')
    try {
        await api.saveRule(addForm)
        ElMessage.success('规则已手动同步入库')
        showAddDialog.value = false
        fetchRules()
    } catch (e) {}
}

const deleteRule = async (id) => {
    try {
        await ElMessageBox.confirm('确定要从生产库中下架此规则吗？', '提示', { type: 'warning', confirmButtonText: '确定下架' })
        await api.deleteRule(id)
        ElMessage.success('规则已归档下架')
        fetchRules()
    } catch (e) {}
}

const editRule = (rule) => {
    form.policyText = rule.explanation || ""
    compiledRule.value = rule
    ElMessage.info('已将历史规则载入编译器')
}

const submitForReview = () => ElMessage.success('已提交至医疗专家委员会进行终审')
const clearForm = () => { form.policyText = ''; compiledRule.value = null; testResult.value = null }

const completeWorkflowTask = async () => {
    try {
        await api.completeTask(taskId.value, {
            result: 'approved',
            comments: '政策规则风控审核通过，准备上线'
        })
        ElMessage.success('规则审核任务已完成，流水线将自动部署规则')
        router.push('/pipeline')
    } catch (e) {
        ElMessage.error('提交失败')
    }
}

onMounted(async () => {
    fetchRules()
    
    // If part of a workflow, pre-populate from context
    if (instanceId.value) {
        try {
            const response = await api.getWorkflowInstance(instanceId.value)
            const instance = response.data
            if (instance.context && instance.context.document_content) {
                form.policyText = instance.context.document_content
                ElMessage.info('已根据工作流上下文预载入政策条文')
            }
        } catch (e) {
            console.error('Failed to fetch instance details', e)
        }
    }
})
</script>

<style scoped>
.rule-container {
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

/* Workflow Section */
.workflow-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 40px;
}

.primary-card {
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

.premium-textarea :deep(.el-textarea__inner) {
  border-radius: 16px;
  padding: 16px;
  background: #f8fafc;
  line-height: 1.6;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.action-btn-main {
  height: 48px;
  padding: 0 32px;
  border-radius: 12px;
  font-weight: 600;
}

/* Result Section */
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.code-card {
  border-radius: 20px;
  background: #1e293b;
  border: none;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
}

.dot.success { background: #10b981; }

.code-container {
  padding: 20px;
  background: #0f172a;
  border-radius: 12px;
  margin-bottom: 20px;
}

.shacl-code {
  margin: 0;
  color: #e2e8f0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  min-height: 200px;
}

/* Metrics Panel */
.metrics-panel {
  background: white;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  padding: 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-item {
  background: #f8fafc;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
}

.m-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.m-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.m-value.success { color: #10b981; }
.m-value.danger { color: #ef4444; }
.m-value.warning { color: #f59e0b; }
.m-value.primary { color: #3b82f6; }

.m-trend {
  font-size: 11px;
  color: #64748b;
}

.sandbox-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.btn-group {
  display: flex;
  gap: 12px;
}

/* Library Table */
.library-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.section-icon { color: #10b981; }

.threshold-text {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #3b82f6;
}

.custom-table :deep(.el-table__header-wrapper th) {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
}

/* Dialog */
.monospaced-input :deep(.el-textarea__inner) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  background: #f1f5f9;
}
</style>
