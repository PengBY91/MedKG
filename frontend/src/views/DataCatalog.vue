<template>
  <div class="catalog-container">
    <el-row :gutter="20">
      <!-- Quality Dashboard -->
      <el-col :span="24">
        <el-card class="dashboard-card">
          <template #header>
            <span class="card-title">数据质量概览</span>
          </template>
          <el-row :gutter="20" v-if="qualityReport">
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ qualityReport.total_assets }}</div>
                <div class="stat-label">数据资产总数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box">
                <div class="stat-value">{{ (qualityReport.average_quality * 100).toFixed(0) }}%</div>
                <div class="stat-label">平均质量分数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box quality-excellent">
                <div class="stat-value">{{ qualityReport.quality_distribution?.excellent || 0 }}</div>
                <div class="stat-label">优秀 (≥90%)</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-box quality-good">
                <div class="stat-value">{{ qualityReport.quality_distribution?.good || 0 }}</div>
                <div class="stat-label">良好 (70-90%)</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- Data Assets -->
      <el-col :span="24" style="margin-top: 20px">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">数据资产目录</span>
              <div class="header-actions">
                <el-select v-model="assetTypeFilter" placeholder="资产类型" clearable @change="loadAssets" style="width: 150px; margin-right: 10px">
                  <el-option label="数据集" value="dataset" />
                  <el-option label="文档" value="document" />
                  <el-option label="表" value="table" />
                </el-select>
                <el-button type="primary" @click="showCreateDialog">
                  <el-icon><Plus /></el-icon>
                  新增资产
                </el-button>
              </div>
            </div>
          </template>

          <el-table :data="assets" v-loading="loading" border>
            <el-table-column prop="name" label="资产名称" min-width="200" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="scope">
                <el-tag :type="getTypeColor(scope.row.type)">
                  {{ getTypeLabel(scope.row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quality_score" label="质量分数" width="150">
              <template #default="scope">
                <el-progress 
                  :percentage="Math.round(scope.row.quality_score * 100)" 
                  :color="getQualityColor(scope.row.quality_score)"
                  :stroke-width="12"
                />
              </template>
            </el-table-column>
            <el-table-column prop="tags" label="标签" width="200">
              <template #default="scope">
                <el-tag 
                  v-for="tag in scope.row.tags.slice(0, 2)" 
                  :key="tag" 
                  size="small" 
                  style="margin-right: 5px"
                >
                  {{ tag }}
                </el-tag>
                <el-tag v-if="scope.row.tags.length > 2" size="small">+{{ scope.row.tags.length - 2 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewLineage(scope.row)">血缘</el-button>
                <el-button size="small" @click="viewDetail(scope.row)">详情</el-button>
                <el-button size="small" type="primary" @click="showEditDialog(scope.row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增数据资产' : '编辑数据资产'"
      width="600px"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="资产名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="资产类型" prop="type">
          <el-select v-model="formData.type" style="width: 100%">
            <el-option label="数据集" value="dataset" />
            <el-option label="文档" value="document" />
            <el-option label="表" value="table" />
            <el-option label="字段" value="field" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="tagsInput" placeholder="用逗号分隔多个标签" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Lineage Dialog -->
    <el-dialog v-model="lineageVisible" title="数据血缘" width="800px">
      <div v-if="currentLineage" class="lineage-container">
        <div class="lineage-section">
          <h4>上游资产</h4>
          <el-empty v-if="!currentLineage.upstream || currentLineage.upstream.length === 0" description="无上游资产" />
          <div v-else class="asset-list">
            <el-card v-for="asset in currentLineage.upstream" :key="asset.id" class="asset-card">
              <div class="asset-info">
                <span class="asset-name">{{ asset.name }}</span>
                <el-tag size="small">{{ getTypeLabel(asset.type) }}</el-tag>
              </div>
            </el-card>
          </div>
        </div>

        <div class="lineage-section current">
          <h4>当前资产</h4>
          <el-card class="asset-card current-asset">
            <div class="asset-info">
              <span class="asset-name">{{ currentLineage.asset.name }}</span>
              <el-tag size="small" type="success">{{ getTypeLabel(currentLineage.asset.type) }}</el-tag>
            </div>
          </el-card>
        </div>

        <div class="lineage-section">
          <h4>下游资产</h4>
          <el-empty v-if="!currentLineage.downstream || currentLineage.downstream.length === 0" description="无下游资产" />
          <div v-else class="asset-list">
            <el-card v-for="asset in currentLineage.downstream" :key="asset.id" class="asset-card">
              <div class="asset-info">
                <span class="asset-name">{{ asset.name }}</span>
                <el-tag size="small">{{ getTypeLabel(asset.type) }}</el-tag>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- Asset Detail Drawer -->
    <el-drawer
      v-model="detailVisible"
      title="资产详情"
      size="500px"
      direction="rtl"
    >
      <div v-if="selectedAsset" class="asset-detail-content">
        <div class="detail-header">
          <el-avatar :size="64" :icon="DataAnalysis" class="detail-avatar" />
          <div class="detail-main-info">
            <h3>{{ selectedAsset.name }}</h3>
            <el-tag :type="getTypeColor(selectedAsset.type)">{{ getTypeLabel(selectedAsset.type) }}</el-tag>
          </div>
        </div>

        <el-divider>核心属性</el-divider>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="资产编码">{{ selectedAsset.id }}</el-descriptions-item>
          <el-descriptions-item label="所有者">{{ selectedAsset.owner_id }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedAsset.description || '暂无描述' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedAsset.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(selectedAsset.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>质量看板</el-divider>
        <div class="quality-section">
          <div class="quality-main">
            <el-progress 
              type="dashboard" 
              :percentage="Math.round(selectedAsset.quality_score * 100)" 
              :color="getQualityColor(selectedAsset.quality_score)"
            />
            <div class="quality-label">综合质量评分</div>
          </div>
          <div class="quality-metrics">
            <div class="metric-item">
              <span>完整性</span>
              <el-progress :percentage="85" status="success" :stroke-width="10" />
            </div>
            <div class="metric-item">
              <span>一致性</span>
              <el-progress :percentage="92" status="success" :stroke-width="10" />
            </div>
            <div class="metric-item">
              <span>及时性</span>
              <el-progress :percentage="selectedAsset.quality_score > 0.8 ? 90 : 60" :stroke-width="10" />
            </div>
          </div>
        </div>

        <el-divider>业务元数据</el-divider>
        <div class="metadata-grid">
          <template v-if="Object.keys(selectedAsset.metadata).length > 0">
            <div v-for="(val, key) in selectedAsset.metadata" :key="key" class="meta-item">
              <div class="meta-key">{{ key }}</div>
              <div class="meta-val">{{ val }}</div>
            </div>
          </template>
          <el-empty v-else :image-size="40" description="暂无业务元数据" />
        </div>

        <div class="drawer-footer">
          <el-button type="primary" plain @click="viewLineage(selectedAsset)">查看血缘</el-button>
          <el-button type="warning" plain @click="showEditDialog(selectedAsset)">编辑资产</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, DataAnalysis } from '@element-plus/icons-vue'
import api from '../services/api'

const loading = ref(false)
const assets = ref([])
const qualityReport = ref(null)
const assetTypeFilter = ref('')
const dialogVisible = ref(false)
const lineageVisible = ref(false)
const detailVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)
const formRef = ref(null)
const currentLineage = ref(null)
const selectedAsset = ref(null)
const tagsInput = ref('')

const formData = reactive({
  name: '',
  type: 'dataset',
  description: '',
  owner_id: 'admin',
  tags: []
})

const formRules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择资产类型', trigger: 'change' }]
}

const loadAssets = async () => {
  loading.value = true
  try {
    const params = assetTypeFilter.value ? { asset_type: assetTypeFilter.value } : {}
    const response = await api.getDataAssets(params)
    assets.value = response.data.items
  } catch (error) {
    ElMessage.error('加载数据资产失败')
  } finally {
    loading.value = false
  }
}

const loadQualityReport = async () => {
  try {
    const response = await api.getQualityReport()
    qualityReport.value = response.data
  } catch (error) {
    console.error('加载质量报告失败', error)
  }
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  Object.assign(formData, {
    name: '',
    type: 'dataset',
    description: '',
    owner_id: 'admin',
    tags: []
  })
  tagsInput.value = ''
  dialogVisible.value = true
}

const showEditDialog = (asset) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: asset.id,
    name: asset.name,
    type: asset.type,
    description: asset.description,
    tags: asset.tags
  })
  tagsInput.value = asset.tags.join(', ')
  dialogVisible.value = true
  detailVisible.value = false // Close detail if editing
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  // Parse tags
  formData.tags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t)

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await api.createDataAsset(formData)
      ElMessage.success('数据资产创建成功')
    } else {
      await api.updateDataAsset(formData.id, formData)
      ElMessage.success('数据资产更新成功')
    }
    dialogVisible.value = false
    loadAssets()
    loadQualityReport()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const viewLineage = async (asset) => {
  try {
    const response = await api.getAssetLineage(asset.id)
    currentLineage.value = response.data
    lineageVisible.value = true
  } catch (error) {
    ElMessage.error('加载血缘关系失败')
  }
}

const viewDetail = (asset) => {
  selectedAsset.value = asset
  detailVisible.value = true
}

const getTypeColor = (type) => {
  const colors = {
    dataset: 'primary',
    document: 'success',
    table: 'warning',
    field: 'info'
  }
  return colors[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    dataset: '数据集',
    document: '文档',
    table: '表',
    field: '字段'
  }
  return labels[type] || type
}

const getQualityColor = (score) => {
  if (score >= 0.9) return '#67c23a'
  if (score >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAssets()
  loadQualityReport()
})
</script>

<style scoped>
.catalog-container {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.dashboard-card :deep(.el-card__header) {
  border-bottom-color: rgba(255, 255, 255, 0.2);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
}

.stat-box {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.quality-excellent {
  background: rgba(103, 194, 58, 0.2);
}

.quality-good {
  background: rgba(230, 162, 60, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.lineage-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lineage-section h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
}

.lineage-section.current h4 {
  color: #409eff;
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.asset-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.asset-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.current-asset {
  border: 2px solid #409eff;
  background: #ecf5ff;
}

.asset-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-name {
  font-weight: 500;
}

/* Detail Drawer Styles */
.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.detail-main-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #2c3e50;
}

.detail-avatar {
  background: #eef5ff;
  color: #409eff;
}

.quality-section {
  display: flex;
  gap: 30px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 15px;
}

.quality-main {
  text-align: center;
}

.quality-label {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.quality-metrics {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
  justify-content: center;
}

.metric-item span {
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
  display: block;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 10px;
}

.meta-item {
  padding: 12px;
  background: #f4f7f9;
  border-radius: 8px;
}

.meta-key {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-val {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.drawer-footer {
  margin-top: 40px;
  display: flex;
  gap: 12px;
}
</style>
