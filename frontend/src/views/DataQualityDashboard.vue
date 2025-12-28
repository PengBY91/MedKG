<template>
  <div class="quality-dashboard">
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">数据质量监控中心</h2>
        <p class="subtitle">实时监控 HIS/LIS 数据资产质量，预警脏数据并执行自动质控脚本</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Search" @click="showScanDialog = true">资产扫描</el-button>
        <el-button :icon="Refresh" @click="fetchAssets">刷新数据</el-button>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="summary-grid">
      <el-card shadow="never" class="stat-card">
        <div class="stat-label">资产总数</div>
        <div class="stat-value">{{ summary.total_assets || 0 }}</div>
        <div class="stat-footer">
          <span class="trend">HIS/LIS/PACS 系统</span>
        </div>
      </el-card>
      <el-card shadow="never" class="stat-card excellent">
        <div class="stat-label">平均质量得分</div>
        <div class="stat-value">{{ Math.round((summary.average_quality || 0) * 100) }}%</div>
        <div class="stat-footer">
          <span class="trend positive">较上月提高 2%</span>
        </div>
      </el-card>
      <el-card shadow="never" class="stat-card warning">
        <div class="stat-label">待处理告警</div>
        <div class="stat-value">{{ summary.quality_distribution?.poor + summary.quality_distribution?.fair || 0 }}</div>
        <div class="stat-footer">
          <span class="trend negative">风险记录数 1.2k</span>
        </div>
      </el-card>
    </div>

    <div class="main-layout">
      <!-- Left: Asset List -->
      <el-card class="asset-list-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>数据资产目录</span>
          </div>
        </template>
        <el-table :data="assets" style="width: 100%" @row-click="selectAsset" highlight-current-row v-loading="loading">
          <el-table-column prop="name" label="名称" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.type === 'table' ? '' : 'success'">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quality_score" label="质量得分" width="100">
            <template #default="{ row }">
              <span :style="{ color: getScoreColor(row.quality_score), fontWeight: 'bold' }">
                {{ Math.round(row.quality_score * 100) }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Right: Detail Panel -->
      <div class="detail-panel" v-if="selectedAsset">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="detail-header">
              <div class="asset-title">
                <h3>{{ selectedAsset.name }}</h3>
                <el-tag size="small">{{ selectedAsset.metadata?.source_system || 'Internal' }}</el-tag>
              </div>
              <el-button type="primary" size="small" @click="runCheck" :loading="checking">执行质控巡检</el-button>
            </div>
          </template>

          <div v-if="selectedAsset.quality_report && selectedAsset.quality_report.total_records" class="report-content">
            <div class="report-summary">
              <div class="desc">本次巡检覆盖 <b>{{ selectedAsset.quality_report.total_records }}</b> 条记录，
                共发现 <b>{{ selectedAsset.quality_report.failed_records }}</b> 条违规数据。</div>
            </div>

            <div class="violation-list">
              <div v-for="(v, id) in selectedAsset.quality_report.violations_by_rule" :key="id" class="violation-item">
                <div class="violation-meta">
                  <span class="v-id">{{ id }}</span>
                  <el-tag :type="v.severity === 'error' ? 'danger' : 'warning'" size="small">{{ v.severity }}</el-tag>
                </div>
                <div class="v-name">{{ v.name }}</div>
                <div class="v-desc">{{ v.description }}</div>
                <div class="v-count">影响记录: <b>{{ v.count }}</b></div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无质控报告，请点击上方执行巡检" />
        </el-card>
      </div>
      <el-empty v-else class="empty-detail" description="从左侧资产列表中选择一个表进行详细质量分析" />
    </div>

    <!-- Scan Dialog -->
    <el-dialog v-model="showScanDialog" title="资产扫描引擎" width="500px">
      <el-form label-position="top">
        <el-form-item label="目标系统类型">
          <el-select v-model="scanForm.type" style="width: 100%">
            <el-option label="HIS (临床信息系统)" value="HIS" />
            <el-option label="LIS (实验室系统)" value="LIS" />
            <el-option label="PACS (影像归档)" value="PACS" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据库地址">
          <el-input v-model="scanForm.host" placeholder="localhost" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showScanDialog = false">取消</el-button>
        <el-button type="primary" :loading="scanning" @click="handleScan">开始扫描</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import api from '../services/api'

const assets = ref([])
const summary = ref({})
const loading = ref(false)
const scanning = ref(false)
const checking = ref(false)
const showScanDialog = ref(false)
const selectedAsset = ref(null)

const scanForm = reactive({
  type: 'HIS',
  host: '127.0.0.1'
})

const fetchAssets = async () => {
  loading.value = true
  try {
    const res = await api.getDataAssets()
    assets.value = res.data.items
    
    const reportRes = await api.getQualityReport()
    summary.value = reportRes.data
  } catch (e) {
    ElMessage.error('加载资产失败')
  } finally {
    loading.value = false
  }
}

const selectAsset = async (row) => {
  try {
    const res = await api.getAsset(row.id)
    selectedAsset.value = res.data
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

const handleScan = async () => {
  scanning.value = true
  try {
    await api.scanCatalog(scanForm)
    ElMessage.success('系统扫描完成，已同步目录记录')
    showScanDialog.value = false
    fetchAssets()
  } catch (e) {
    ElMessage.error('扫描失败')
  } finally {
    scanning.value = false
  }
}

const runCheck = async () => {
  if (!selectedAsset.value) return
  checking.value = true
  try {
    // Demo data for scanning
    const demoData = [
      {"patient_id": "P001", "gender": "Male", "age": 45, "diagnosis": "Hypertension", "systolic_bp": 130, "diastolic_bp": 85},
      {"patient_id": "P002", "gender": "Female", "age": 30, "diagnosis": "Uterine Fibroids", "systolic_bp": 115, "diastolic_bp": 75},
      {"patient_id": "P003", "gender": "Male", "age": 60, "diagnosis": "Uterine Fibroids", "systolic_bp": 140, "diastolic_bp": 90},
      {"patient_id": "P004", "gender": "Female", "age": 160, "diagnosis": "Pneumonia", "systolic_bp": 120, "diastolic_bp": 80},
      {"patient_id": "P005", "gender": "Male", "age": 50, "diagnosis": "Diabetes", "systolic_bp": 110, "diastolic_bp": 120}
    ]
    const res = await api.runQualityCheck(selectedAsset.value.id, demoData)
    ElMessage.success(`巡检完成，得分: ${Math.round(res.data.quality_score * 100)}%`)
    selectAsset(selectedAsset.value)
    fetchAssets()
  } catch (e) {
    ElMessage.error('执行失败')
  } finally {
    checking.value = false
  }
}

const getScoreColor = (score) => {
  if (score >= 0.9) return '#10b981'
  if (score >= 0.7) return '#f59e0b'
  return '#ef4444'
}

onMounted(fetchAssets)
</script>

<style scoped>
.quality-dashboard {
  padding-bottom: 30px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}

.title { font-size: 26px; font-weight: 700; color: #1e293b; margin: 0 0 4px 0; }
.subtitle { color: #64748b; margin: 0; }

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.stat-label { font-size: 14px; color: #64748b; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.stat-footer { font-size: 12px; }

.positive { color: #10b981; }
.negative { color: #ef4444; }

.main-layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 20px;
  min-height: 500px;
}

.asset-list-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.detail-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  height: 100%;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-title h3 { margin: 0 0 4px 0; font-size: 18px; }

.report-summary {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 14px;
}

.violation-list {
  display: grid;
  gap: 12px;
}

.violation-item {
  padding: 16px;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  background: white;
}

.violation-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.v-id { font-family: monospace; font-weight: 600; color: #64748b; }
.v-name { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.v-desc { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.v-count { font-size: 13px; border-top: 1px solid #f1f5f9; padding-top: 8px; }

.empty-detail {
  background: #f8fafc;
  border-radius: 16px;
  display: flex;
  align-items: center;
}
</style>
