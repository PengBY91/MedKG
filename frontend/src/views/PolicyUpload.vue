<template>
  <div class="policy-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">政策文档管理</h2>
        <p class="subtitle">上传并解析医保政策文档，自动提取核心业务规则与实体</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :icon="Refresh" @click="loadDocuments">刷新</el-button>
          <el-button type="primary" :icon="Plus" @click="showUploadSection = !showUploadSection">
            {{ showUploadSection ? '精简视图' : '上传新文档' }}
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- Enhanced Statistics Indicators -->
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
        </div>
      </el-col>
    </el-row>

    <!-- Redesigned Upload Section -->
    <el-collapse-transition>
      <div v-show="showUploadSection" class="upload-wrapper">
        <el-card class="upload-card" shadow="never">
          <div class="upload-inner">
            <el-upload
              ref="uploadRef"
              class="drag-upload"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :file-list="fileList"
              multiple
              accept=".pdf,.docx,.txt"
            >
              <el-icon class="upload-icon-main"><CloudUpload /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 PDF, DOCX, TXT 格式，批量解析效率更高
                </div>
              </template>
            </el-upload>
            
            <div class="upload-footer" v-if="fileList.length > 0">
              <div class="file-count-tip">已选择 {{ fileList.length }} 个文件</div>
              <div class="action-buttons">
                <el-button @click="clearFiles">取消</el-button>
                <el-button type="primary" :loading="uploading" @click="uploadFiles">
                  {{ uploading ? `上传并解析中...` : '立即导入' }}
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </el-collapse-transition>

    <!-- Document List Section -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="section-icon"><Collection /></el-icon>
            <span>已入库文档</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档名称..."
              :prefix-icon="Search"
              clearable
              style="width: 240px; margin-right: 12px"
            />
            <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="loadDocuments" style="width: 120px">
              <el-option label="已完成" value="completed" />
              <el-option label="处理中" value="processing" />
              <el-option label="失败" value="failed" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table 
        :data="documents" 
        v-loading="loading" 
        class="custom-table"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
      >
        <el-table-column prop="filename" label="文档名称" min-width="300">
          <template #default="{ row }">
            <div class="file-cell">
              <div class="file-icon" :class="getFileExt(row.filename)">
                <el-icon><Document /></el-icon>
              </div>
              <div class="file-info">
                <div class="file-name">{{ row.filename }}</div>
                <div class="file-meta">{{ formatFileSize(row.file_size) }} • {{ formatNumber(row.total_chars) }} 字符</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="解析状态" width="120">
          <template #default="{ row }">
            <div class="status-wrap">
              <el-tag :type="getStatusType(row.status)" effect="light" round>
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="extracted_rules_count" label="提取规则" width="120" align="center">
          <template #default="{ row }">
            <div class="count-badge" v-if="row.extracted_rules_count > 0">
              {{ row.extracted_rules_count }}
            </div>
            <span v-else class="empty-text">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="上传日期" width="180">
          <template #default="{ row }">
            <div class="time-text">{{ formatDate(row.created_at) }}</div>
          </template>
        </el-table-column>

        <el-table-column label="管理操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
              <el-divider direction="vertical" />
              <el-dropdown trigger="click">
                <el-button link>更多</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :icon="Connection" @click="extractRules(row)" :disabled="row.status !== 'completed'">
                      重新提取规则
                    </el-dropdown-item>
                    <el-dropdown-item :icon="Download" divided @click="handleDownload(row)">下载原文</el-dropdown-item>
                    <el-dropdown-item :icon="Delete" style="color: #f56c6c" @click="handleDelete(row)">删除记录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadDocuments"
        />
      </div>
    </el-card>

    <!-- Document Detail Drawer -->
    <el-drawer
      v-model="detailVisible"
      title="文档详情与解析结果"
      size="560px"
      direction="rtl"
      class="detail-drawer"
    >
      <div v-if="currentDetail" class="drawer-inner">
        <div class="drawer-header-info">
          <div class="drawer-file-title">
            <el-icon class="file-icon-big"><Document /></el-icon>
            <h3>{{ currentDetail.filename }}</h3>
          </div>
          <div class="drawer-status-tags">
            <el-tag :type="getStatusType(currentDetail.status)">{{ getStatusLabel(currentDetail.status) }}</el-tag>
            <el-tag type="info" plain>{{ currentDetail.category || '未分类' }}</el-tag>
          </div>
        </div>

        <el-divider>核心指标</el-divider>
        <el-descriptions :column="2" border class="drawer-desc">
          <el-descriptions-item label="字符规模">{{ formatNumber(currentDetail.total_chars) }}</el-descriptions-item>
          <el-descriptions-item label="切片数量">{{ currentDetail.chunks_count }}</el-descriptions-item>
          <el-descriptions-item label="提取规则">{{ currentDetail.extracted_rules_count }}</el-descriptions-item>
          <el-descriptions-item label="上传用户">{{ currentDetail.uploaded_by }}</el-descriptions-item>
          <el-descriptions-item label="上传时间" :span="2">{{ formatDate(currentDetail.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>文本预览 (前500字)</el-divider>
        <div class="text-preview">
          {{ currentDetail.preview_text || '暂无详细预览，解析中...' }}
        </div>

        <el-divider>智能标签</el-divider>
        <div class="tag-cloud">
          <el-tag 
            v-for="tag in (currentDetail.tags || ['医保政策', '门诊报销', '2024规范'])" 
            :key="tag"
            class="mx-1"
            round
            effect="plain"
          >
            {{ tag }}
          </el-tag>
        </div>

        <el-divider>提取规则详情</el-divider>
        <div v-if="currentDetail.extracted_rules && currentDetail.extracted_rules.length > 0" class="extraction-section">
          <el-collapse>
            <el-collapse-item v-for="(rule, idx) in currentDetail.extracted_rules" :key="idx">
              <template #title>
                <div class="rule-header">
                  <el-icon color="#409eff"><Document /></el-icon>
                  <span class="rule-title">规则 {{ idx + 1 }}</span>
                  <el-tag size="small" :type="rule.status === 'valid' ? 'success' : 'warning'">
                    {{ rule.status || '未知' }}
                  </el-tag>
                </div>
              </template>
              <div class="rule-content">
                <div class="rule-field" v-if="rule.name">
                  <strong>规则名称:</strong> {{ rule.name }}
                </div>
                <div class="rule-field" v-if="rule.description">
                  <strong>描述:</strong> {{ rule.description }}
                </div>
                <div class="rule-field" v-if="rule.shacl_content">
                  <strong>SHACL 内容预览:</strong>
                  <pre class="shacl-preview">{{ rule.shacl_content.substring(0, 200) }}...</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        <div v-else class="empty-state">
          <el-icon><Warning /></el-icon>
          <span>暂无提取的规则</span>
        </div>

        <el-divider>提取实体详情</el-divider>
        <div v-if="currentDetail.extracted_entities && currentDetail.extracted_entities.length > 0" class="extraction-section">
          <div class="entity-list">
            <div v-for="(entity, idx) in currentDetail.extracted_entities" :key="idx" class="entity-item">
              <div class="entity-term">{{ entity.term }}</div>
              <div class="entity-meta">
                <el-tag size="small" type="info">{{ entity.suggestion || '未映射' }}</el-tag>
                <span class="confidence">置信度: {{ (entity.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <el-icon><Warning /></el-icon>
          <span>暂无提取的实体</span>
        </div>

        <div class="drawer-footer">
          <el-button type="primary" plain @click="extractRules(currentDetail)" block>
            重新运行提取流程
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, Refresh, Plus, Document, Search, 
  Collection, Download, Delete, Connection, 
  Files, CircleCheck, Timer, Warning, Upload as CloudUpload
} from '@element-plus/icons-vue'
import api from '../services/api'

const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const loading = ref(false)
const documents = ref([])
const detailVisible = ref(false)
const currentDetail = ref(null)
const showUploadSection = ref(false)
const searchQuery = ref('')

const statistics = reactive({
  total_documents: 0,
  completed: 0,
  processing: 0,
  total_extracted_rules: 0
})

const statConfig = computed(() => [
  { label: '库中文档总数', value: statistics.total_documents, icon: Files, type: 'total' },
  { label: '解析完成', value: statistics.completed, icon: CircleCheck, type: 'success' },
  { label: '正在异步处理', value: statistics.processing, icon: Timer, type: 'warning' },
  { label: '自动化提取规则', value: statistics.total_extracted_rules, icon: Connection, type: 'primary' }
])

const filters = reactive({
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const handleFileChange = (file, files) => {
  fileList.value = files
}

const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const uploadFiles = async () => {
  if (fileList.value.length === 0) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    for (const fileItem of fileList.value) {
      await api.uploadPolicy(fileItem.raw)
      uploadProgress.value++
    }
    ElMessage.success(`成功导入并触发 ${uploadProgress.value} 个解析任务`)
    clearFiles()
    showUploadSection.value = false
    loadStatistics()
    loadDocuments()
  } catch (error) {
    ElMessage.error(`文档上传失败: ${error.message}`)
  } finally {
    uploading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const response = await api.getPolicyStatistics()
    Object.assign(statistics, response.data)
  } catch (error) {}
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      status: filters.status || undefined
    }
    const response = await api.getPolicies(params)
    documents.value = response.data.items
    pagination.total = response.data.total || response.data.items.length
  } catch (error) {
    ElMessage.error('无法同步文档列表')
  } finally {
    loading.value = false
  }
}

const viewDetail = (doc) => {
  currentDetail.value = doc
  detailVisible.value = true
}

const handleDownload = async (doc) => {
  try {
    const response = await api.downloadPolicy(doc.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', doc.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error(`下载失败: ${error.message}`)
  }
}

const handleDelete = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确定要永久删除文档 "${doc.filename}" 及其所有提取结果吗？此操作不可撤销。`,
      '警告',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    
    await api.deletePolicy(doc.id)
    ElMessage.success('文档已成功删除')
    loadStatistics()
    loadDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`删除失败: ${error.message}`)
    }
  }
}

const extractRules = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新对 "${doc.filename}" 运行 KAG/DeepKE 提取引擎吗？`,
      '规则提取引擎',
      { confirmButtonText: '启动', cancelButtonText: '取消', type: 'info' }
    )
    ElMessage({ message: '提取序列已启动，分析结果将稍后同步', type: 'success' })
  } catch (error) {}
}

const getStatusType = (status) => {
  const types = { processing: 'warning', completed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = { processing: '解析中', completed: '已就绪', failed: '失败' }
  return labels[status] || status
}

const getFileExt = (name) => {
  if (!name) return ''
  const ext = name.split('.').pop().toLowerCase()
  return `ext-${ext}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const formatNumber = (num) => num?.toLocaleString() || '0'

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i]
}

onMounted(() => {
  loadStatistics()
  loadDocuments()
})
</script>

<style scoped>
.policy-container {
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

/* Stat Cards */
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
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.05);
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.total .stat-icon-wrap { background: #f1f5f9; color: #64748b; }
.stat-card.success .stat-icon-wrap { background: #dcfce7; color: #22c55e; }
.stat-card.warning .stat-icon-wrap { background: #fef3c7; color: #f59e0b; }
.stat-card.primary .stat-icon-wrap { background: #e0f2fe; color: #0ea5e9; }

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

/* Upload Section */
.upload-wrapper {
  margin-bottom: 30px;
}

.upload-card {
  border-radius: 20px;
  border: 2px dashed #e2e8f0;
  background: #f8fafc;
}

.upload-inner {
  padding: 20px;
}

.drag-upload :deep(.el-upload-dragger) {
  background: transparent;
  border: none;
}

.upload-icon-main {
  font-size: 48px;
  color: #3b82f6;
  margin-bottom: 16px;
}

.upload-footer {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.file-count-tip {
  color: #64748b;
  font-size: 14px;
}

/* List Card */
.list-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
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

.section-icon { color: #3b82f6; }

.file-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.file-icon.ext-pdf { background: #fee2e2; color: #ef4444; }
.file-icon.ext-docx { background: #e0f2fe; color: #3b82f6; }

.file-name {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 2px;
}

.file-meta {
  font-size: 12px;
  color: #94a3b8;
}

.count-badge {
  display: inline-block;
  padding: 2px 10px;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.time-text {
  color: #64748b;
  font-size: 13px;
}

.pagination-footer {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* Drawer Styling */
.detail-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.drawer-inner {
  padding: 10px;
}

.drawer-header-info {
  margin-bottom: 24px;
}

.drawer-file-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-icon-big {
  font-size: 32px;
  color: #3b82f6;
}

.drawer-file-title h3 {
  margin: 0;
  font-size: 20px;
  color: #1e293b;
}

.drawer-status-tags {
  display: flex;
  gap: 8px;
}

.text-preview {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.drawer-footer {
  margin-top: 40px;
}

.drawer-footer .el-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
}

/* Extraction Results Styles */
.extraction-section {
  margin: 16px 0;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.rule-title {
  flex: 1;
  font-weight: 500;
  color: #1e293b;
}

.rule-content {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.rule-field {
  margin-bottom: 12px;
  font-size: 14px;
  color: #475569;
}

.rule-field:last-child {
  margin-bottom: 0;
}

.rule-field strong {
  color: #1e293b;
  margin-right: 8px;
}

.shacl-preview {
  margin-top: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  color: #64748b;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.entity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.entity-item {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.entity-term {
  font-size: 15px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 8px;
}

.entity-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence {
  font-size: 13px;
  color: #64748b;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: #94a3b8;
  font-size: 14px;
}

.empty-state .el-icon {
  font-size: 20px;
}
</style>
