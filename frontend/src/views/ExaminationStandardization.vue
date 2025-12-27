<template>
  <div class="examination-container">
    <el-row :gutter="20" class="full-height-row">
      <!-- Left Sidebar: Task History -->
      <el-col :span="6" class="history-col">
        <el-card class="history-card" :body-style="{ padding: '0', height: '100%', display: 'flex', flexDirection: 'column' }">
          <template #header>
            <div class="card-header">
              <span class="card-title">📜 任务历史</span>
              <el-button type="primary" size="small" icon="Plus" @click="createNewTask">
                新建任务
              </el-button>
            </div>
          </template>
          
          <div class="history-list" v-loading="loadingHistory">
            <div 
              v-for="task in historyTasks" 
              :key="task.id" 
              :class="['history-item', { active: currentTask && currentTask.id === task.id }]"
              @click="selectTask(task)"
            >
              <div class="item-header">
                <span class="filename" :title="task.filename">{{ task.filename }}</span>
                <el-tag :type="getStatusType(task.status)" size="small" effect="dark">
                  {{ getStatusText(task.status) }}
                </el-tag>
              </div>
              <div class="item-meta">
                <span>{{ formatDate(task.created_at) }}</span>
                <span>{{ task.processed_records }} / {{ task.total_records }}</span>
              </div>
              <div class="item-stats" v-if="task.status === 'completed'">
                <span class="success-dot">● {{ task.success_count }}</span>
                <span class="failed-dot">● {{ task.failed_count }}</span>
              </div>
            </div>
            <div v-if="historyTasks.length === 0 && !loadingHistory" class="empty-history">
              暂无历史记录
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Right Main: Work Area -->
      <el-col :span="18" class="main-col">
        <!-- Mode 1: Upload / New Task -->
        <el-card v-if="!currentTask" class="upload-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">📥 新建标准化任务</span>
            </div>
          </template>
          
          <div class="upload-container">
            <el-upload
              class="upload-area"
              drag
              action=""
              :auto-upload="false"
              :on-change="handleFileSelect"
              :show-file-list="false"
              accept=".csv,.xlsx,.xls"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 .csv, .xlsx 格式文件，需包含"检查项目名"和"检查标准模态"列
                </div>
              </template>
            </el-upload>

            <div v-if="selectedFile" class="file-actions">
              <el-alert
                :title="`已选择文件: ${selectedFile.name}`"
                type="info"
                show-icon
                style="margin-bottom: 20px"
              />
              <el-button type="primary" size="large" @click="uploadFile" :loading="uploading">
                {{ uploading ? '正在处理中...' : '开始标准化处理' }}
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- Mode 2: Task Detail / Progress -->
        <div v-else class="task-detail-container">
            <!-- Compact Task Header / Progress -->
            <el-card class="progress-card compact-card" shadow="hover">
                <div class="compact-header">
                   <div class="header-left">
                       <span class="card-title">当前任务: {{ currentTask.filename }}</span>
                       <el-divider direction="vertical" />
                       <el-tag :type="getStatusType(currentTask.status)" size="small" effect="dark">{{ getStatusText(currentTask.status) }}</el-tag>
                   </div>
                   <div class="header-right">
                       <el-button v-if="['processing'].includes(currentTask.status)" type="text" disabled>
                         <el-icon class="is-loading"><Loading /></el-icon> 处理中
                       </el-button>
                       <template v-else>
                           <el-button type="primary" link icon="Refresh" @click="refreshCurrentTask" size="small">刷新</el-button>
                           <el-divider direction="vertical" />
                           <el-dropdown split-button type="primary" size="small" @click="exportResults('csv')" @command="handleExportCommand">
                              导出 CSV
                              <template #dropdown>
                                <el-dropdown-menu>
                                  <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
                                </el-dropdown-menu>
                              </template>
                           </el-dropdown>
                       </template>
                   </div>
                </div>

                <div class="compact-stats">
                     <!-- Progress -->
                     <div class="stat-group">
                         <span class="label">进度:</span>
                         <span class="val">{{ currentTask.processed_records }} / {{ currentTask.total_records }}</span>
                         <el-progress 
                           :percentage="progressPercentage" 
                           :stroke-width="6" 
                           :width="150"
                           :show-text="false"
                           style="width: 100px; margin-left: 8px;"
                           v-if="currentTask.status === 'processing'"
                         />
                     </div>
                     
                     <el-divider direction="vertical" />
                     
                     <!-- Success/Fail -->
                     <div class="stat-group">
                         <span class="success-dot">● 成功: <b>{{ currentTask.success_count }}</b></span>
                         <span class="failed-dot" style="margin-left: 12px">● 异常: <b>{{ currentTask.failed_count }}</b></span>
                     </div>
                </div>
            </el-card>

          <!-- Results Table -->
          <el-card class="results-card">
             <template #header>
               <div class="card-header">
                 <span class="card-title">标准化结果列表</span>
                 <div class="table-filters">
                    <el-input
                      v-model="searchQuery"
                      placeholder="搜索检查名称..."
                      prefix-icon="Search"
                      style="width: 200px; margin-right: 10px"
                      clearable
                    />
                    <el-select v-model="statusFilter" placeholder="全部状态" style="width: 120px" clearable>
                      <el-option label="成功" value="success" />
                      <el-option label="需复核" value="review_required" />
                      <el-option label="失败" value="failed" />
                    </el-select>
                 </div>
               </div>
             </template>
             
             <el-table :data="paginatedResults" style="width: 100%" border v-loading="loadingResults" height="500">
                <el-table-column prop="original_name" label="原始检查名称" min-width="150" show-overflow-tooltip />
                <el-table-column prop="modality" label="模态" width="80">
                  <template #default="scope">
                    <el-tag size="small" effect="plain">{{ scope.row.modality }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="标准化结果" min-width="250">
                  <template #default="scope">
                    <div v-if="scope.row.standardized && scope.row.standardized.length > 0" class="standardized-list">
                      <div v-for="(triple, idx) in scope.row.standardized" :key="idx" class="triple-item">
                        <el-tag size="small" type="info">{{ triple[0] }}</el-tag>
                        <el-icon class="arrow-icon"><Right /></el-icon>
                        <el-tag size="small" type="warning">{{ triple[1] }}</el-tag>
                        <el-icon class="arrow-icon"><Right /></el-icon>
                        <el-tag size="small" type="success">{{ triple[2] }}</el-tag>
                      </div>
                    </div>
                    <el-tag v-else-if="scope.row.status === 'review_required'" type="warning" size="small">需复核（三元组可能无效）</el-tag>
                    <el-tag v-else type="danger" size="small">未能标准化</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="getStatusType(scope.row.status)" effect="dark">
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80" align="center">
                  <template #default="scope">
                    <el-button type="primary" link icon="Edit" @click="openEditDialog(scope.row)">
                      修正
                    </el-button>
                  </template>
                </el-table-column>
             </el-table>
             <div class="pagination-wrapper">
                 <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  layout="total, sizes, prev, pager, next, jumper"
                  :total="filteredResults.length"
                />
             </div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <!-- Edit Dialog (Same as before) -->
    <el-dialog v-model="editDialogVisible" title="修正标准化结果" width="600px">
      <el-form label-width="100px">
        <el-form-item label="原始名称">
          <el-input v-model="editingRow.original_name" disabled />
        </el-form-item>
        <el-form-item label="模态">
          <el-input v-model="editingRow.modality" disabled />
        </el-form-item>
        <el-divider content-position="left">标准化三元组 (JSON格式)</el-divider>
        <el-input
          v-model="editingJson"
          type="textarea"
          :rows="6"
          placeholder='Example: [["部位1", "部位2", "方法"], ...]'
        />
        <div class="json-hint" style="font-size: 12px; color: #909399; margin-top: 5px;">
          请严格遵守JSON数组格式: [["一级部位", "二级部位", "方法"], ...]
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCorrection" :loading="savingCorrection">
            保存修正
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { UploadFilled, Refresh, Search, Right, Plus, Edit, Loading } from '@element-plus/icons-vue'

// State
const historyTasks = ref([])
const loadingHistory = ref(false)
const currentTask = ref(null) // If null, show upload screen
const pollingInterval = ref(null)

// Upload State
const selectedFile = ref(null)
const uploading = ref(false)

// Results State
const results = ref([])
const loadingResults = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// Edit State
const editDialogVisible = ref(false)
const editingRow = ref({})
const editingJson = ref('')
const savingCorrection = ref(false)

// Lifecycle
onMounted(() => {
    loadHistory()
})

onBeforeUnmount(() => {
    if (pollingInterval.value) clearInterval(pollingInterval.value)
})

// --- History Logic ---
const loadHistory = async () => {
    loadingHistory.value = true
    try {
        const res = await axios.get('/api/v1/examination/history')
        if (res.data.success) {
            historyTasks.value = res.data.tasks
        }
    } catch (e) {
        ElMessage.error("加载历史记录失败")
    } finally {
        loadingHistory.value = false
    }
}

const createNewTask = () => {
    // Stop polling if any
    if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
    }
    currentTask.value = null // Switch to upload view
    selectedFile.value = null
    results.value = []
}

const selectTask = (task) => {
    if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
    }
    
    currentTask.value = task
    
    // If completed or failed, just load results
    if (['completed', 'failed'].includes(task.status)) {
        loadResults(task.id)
    } 
    // If processing, start polling AND load results (partial)
    if (task.status === 'processing') {
        startPolling(task.id)
        loadResults(task.id) 
    }
}

const refreshCurrentTask = () => {
    if (currentTask.value) {
        if (currentTask.value.status === 'processing') {
             // Polling handles it, but manual refresh forces check
             checkTaskStatus(currentTask.value.id)
        } else {
            // Just reload results just in case
            loadResults(currentTask.value.id)
        }
    }
}

// --- Upload Logic ---
const handleFileSelect = (uploadFile) => {
  if (uploadFile.raw) {
    selectedFile.value = uploadFile.raw
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await axios.post('/api/v1/examination/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.success) {
      const taskId = response.data.task_id
      ElMessage.success('文件上传成功，开始处理...')
      
      // Refresh history to show new task
      await loadHistory()
      
      // Find new task and select it to switch view
      const newTask = historyTasks.value.find(t => t.id === taskId)
      if (newTask) {
          selectTask(newTask)
      } else {
          // Fallback if list fetch lag
          currentTask.value = { id: taskId, filename: selectedFile.value.name, status: 'processing', processed_records: 0, total_records: 0, success_count:0, failed_count:0 }
          startPolling(taskId)
      }
      
      selectedFile.value = null
    }
  } catch (error) {
    console.error('Upload failed:', error)
    ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

// --- Polling Logic ---
const startPolling = (taskId) => {
  if (pollingInterval.value) clearInterval(pollingInterval.value)
  
  checkTaskStatus(taskId) // Immediate
  pollingInterval.value = setInterval(() => {
      // Only check if we are still looking at this task
      if (currentTask.value && currentTask.value.id === taskId) {
          checkTaskStatus(taskId)
      } else {
          clearInterval(pollingInterval.value)
      }
  }, 2000)
}

const checkTaskStatus = async (taskId) => {
    try {
        const res = await axios.get(`/api/v1/examination/tasks/${taskId}`)
        if (res.data.success) {
            // Update current task info in view
            if (currentTask.value && currentTask.value.id === taskId) {
                currentTask.value = res.data.task
                
                // If finished, stop polling
                if (['completed', 'failed'].includes(res.data.task.status)) {
                    clearInterval(pollingInterval.value)
                    pollingInterval.value = null
                    loadResults(taskId) // Final result load
                    loadHistory() // Refresh list status
                    
                    if (res.data.task.status === 'completed') {
                         ElMessage.success('任务处理完成')
                    } else {
                         ElMessage.error('任务处理失败: ' + res.data.task.error_message)
                    }
                } else {
                    // While processing, reload results periodically to show progress?
                    // Maybe every few polls. For now let's just update progress bar.
                    // User can manually refresh results if they want to see partials.
                }
            }
        }
    } catch (e) {
        console.error("Check status failed", e)
    }
}

// --- Results Logic ---
const loadResults = async (taskId) => {
  loadingResults.value = true
  try {
    const response = await axios.get(`/api/v1/examination/tasks/${taskId}/results`)
    if (response.data.success) {
      results.value = response.data.results
    }
  } catch (error) {
    ElMessage.error('加载结果失败')
  } finally {
    loadingResults.value = false
  }
}

const filteredResults = computed(() => {
  let data = results.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    data = data.filter(r => r.original_name.toLowerCase().includes(query))
  }
  if (statusFilter.value) {
    data = data.filter(r => r.status === statusFilter.value)
  }
  return data
})

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredResults.value.slice(start, end)
})

// --- Helpers ---
const progressPercentage = computed(() => {
  if (!currentTask.value || currentTask.value.total_records === 0) return 0
  return Math.round((currentTask.value.processed_records / currentTask.value.total_records) * 100)
})

const getStatusType = (status) => {
  const map = { processing: 'primary', completed: 'success', failed: 'danger', review_required: 'warning' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { processing: '处理中', completed: '已完成', failed: '失败', review_required: '需复核' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {month:'numeric', day:'numeric', hour:'numeric', minute:'numeric'})
}

// --- Export ---
const handleExportCommand = (command) => exportResults(command)
const exportResults = async (format) => {
  if (!currentTask.value) return
  try {
    const response = await axios.get(
      `/api/v1/examination/tasks/${currentTask.value.id}/export?format=${format}`,
      { responseType: 'blob' }
    )
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `results_${currentTask.value.id}.${format === 'csv' ? 'csv' : 'xlsx'}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// --- Edit Logic (Same) ---
const openEditDialog = (row) => {
  editingRow.value = { ...row }
  try {
    editingJson.value = JSON.stringify(row.standardized || [], null, 2)
  } catch (e) {
    editingJson.value = "[]"
  }
  editDialogVisible.value = true
}

const saveCorrection = async () => {
  try {
    const parsed = JSON.parse(editingJson.value)
    if (!Array.isArray(parsed)) throw new Error("Must be an array")
    parsed.forEach(item => {
        if (!Array.isArray(item) || item.length !== 3) throw new Error("Each item must be an array of 3 strings")
    })
    
    savingCorrection.value = true
    const index = results.value.findIndex(r => r.original_name === editingRow.value.original_name && r.modality === editingRow.value.modality)
    
    if (index === -1) {
        ElMessage.error("Original record not found")
        return
    }
    
    // Update local
    const updatedResults = [...results.value]
    updatedResults[index] = {
        ...updatedResults[index],
        standardized: parsed,
        status: parsed.length > 0 ? 'success' : 'failed'
    }
    
    // Update context for API
    const updatedContext = updatedResults.map(r => ({
        original_name: r.original_name,
        modality: r.modality,
        standardized: r.standardized
    }))
    
    await axios.put(`/api/v1/examination/tasks/${currentTask.value.id}/results`, { results: updatedContext })
    
    results.value = updatedResults
    editDialogVisible.value = false
    ElMessage.success("修正已保存")
    
  } catch (e) {
      ElMessage.error("保存失败: " + e.message)
  } finally {
      savingCorrection.value = false
  }
}
</script>

<style scoped>
.examination-container {
    height: calc(100vh - 120px);
    overflow: hidden;
    padding: 20px;
}
.full-height-row {
    height: 100%;
}
.history-col, .main-col {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.history-card {
    height: 100%;
}
.history-list {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
}
.history-item {
    padding: 12px;
    border-radius: 6px;
    background: #f5f7fa;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;
}
.history-item:hover {
    background: #e6e8eb;
}
.history-item.active {
    background: #ecf5ff;
    border-left-color: #409eff;
}
.item-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}
.filename {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 120px;
}
.item-meta {
    font-size: 12px;
    color: #909399;
    display: flex;
    justify-content: space-between;
}
.item-stats {
    margin-top: 6px;
    font-size: 11px;
}
.success-dot { color: #67c23a; margin-right: 8px; }
.failed-dot { color: #f56c6c; }
.empty-history { text-align: center; color: #909399; margin-top: 50px; }

/* Main Area */
.upload-card {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.upload-container {
    padding: 40px;
    text-align: center;
}
.task-detail-container {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.results-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Compact Style Overrides */
.progress-card.compact-card {
    margin-bottom: 10px;
}
.progress-card.compact-card :deep(.el-card__body) {
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.compact-header {
    display: flex; /* Hide standard header logic if needed, but we replaced content */
    display: none; /* We moved header content to body or custom div */
}

/* Since we replaced the whole card content including template #header, check structure */
/* Actually I removed template #header in previous step, so everything is in body */

.compact-header {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

/* Re-styling based on new structure */
.compact-card {
    border: none;
    background: #fff;
    border-bottom: 1px solid #ebeef5;
    border-radius: 4px;
}

.compact-card :deep(.el-card__body) {
    padding: 12px 20px !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 60px; /* Force small height */
}

.compact-header {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-right {
    display: flex;
    align-items: center;
}

.compact-stats {
    display: flex;
    align-items: center;
    gap: 15px;
    font-size: 13px;
    color: #606266;
}

.stat-group {
    display: flex;
    align-items: center;
}

.label {
    margin-right: 5px;
    color: #909399;
}

.val {
    font-weight: 600;
    font-family: monospace;
}

.success-dot { color: #67c23a; }
.failed-dot { color: #f56c6c; }


.standardized-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.triple-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.arrow-icon {
  font-size: 12px;
  color: #909399;
}
.pagination-wrapper {
    margin-top: 15px;
    display: flex;
    justify-content: flex-end;
}
</style>
