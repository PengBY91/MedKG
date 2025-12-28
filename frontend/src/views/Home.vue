<template>
  <div class="home-container">
    <div class="welcome-banner">
      <div class="banner-content">
        <h1 class="welcome-title">医疗数据治理与知识资产平台</h1>
        <p class="welcome-subtitle">统一监管、智能中台、资产沉淀</p>
      </div>
      <div class="banner-stats">
        <div class="banner-stat-item">
          <div class="val">{{ totalAssets }}</div>
          <div class="lab">数据知识资产</div>
        </div>
        <div class="banner-stat-divider"></div>
        <div class="banner-stat-item">
          <div class="val">{{ systemScore }}%</div>
          <div class="lab">系统健康度</div>
        </div>
      </div>
    </div>

    <!-- Module Overviews -->
    <el-row :gutter="20" class="module-row">
      <!-- Terminology Hub Summary -->
      <el-col :span="8">
        <el-card shadow="hover" class="module-card terminology" @click="$router.push('/terminology')">
          <div class="module-header">
            <el-icon class="m-icon"><Edit /></el-icon>
            <span class="m-title">智能术语中台</span>
          </div>
          <div class="m-content">
            <div class="m-stat">
              <span class="m-val">{{ terminologyStats.standard_count }}</span>
              <span class="m-lab">标准术语集</span>
            </div>
            <div class="m-desc">支持 ICD-10/11、LONIC 多源标准，语义中台赋能临床文本结构化。</div>
          </div>
        </el-card>
      </el-col>

      <!-- Governance Summary -->
      <el-col :span="8">
        <el-card shadow="hover" class="module-card governance" @click="$router.push('/quality')">
          <div class="module-header">
            <el-icon class="m-icon"><Tools /></el-icon>
            <span class="m-title">质量治理中心</span>
          </div>
          <div class="m-content">
            <div class="m-stat">
              <span class="m-val">{{ governanceStats.violation_count }}</span>
              <span class="m-lab">待修复告警</span>
            </div>
            <div class="m-desc">覆盖 HIS/LIS/PACS 实时监控，自动执行 50+ 项质控巡检规则。</div>
          </div>
        </el-card>
      </el-col>

      <!-- Knowledge Assets Summary -->
      <el-col :span="8">
        <el-card shadow="hover" class="module-card assets" @click="$router.push('/catalog')">
          <div class="module-header">
            <el-icon class="m-icon"><Reading /></el-icon>
            <span class="m-title">数据知识资产</span>
          </div>
          <div class="m-content">
            <div class="m-stat">
              <span class="m-val">{{ assetStats.graph_nodes }}</span>
              <span class="m-lab">知识图谱节点</span>
            </div>
            <div class="m-desc">构建全方位数据血缘与知识链路，实现资产可追溯、价值可量化。</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="bottom-row">
      <!-- Task Management (Integrated from Workbench) -->
      <el-col :span="16">
        <!-- Activity Stream -->
        <el-card class="activity-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>系统动态</span>
            </div>
          </template>
          <div class="activity-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in activities"
                :key="index"
                :type="activity.type"
                :color="activity.color"
                :timestamp="activity.time"
                hollow
              >
                <div class="activity-item">
                  <span class="act-user">{{ activity.user }}</span>
                  <span class="act-action">{{ activity.action }}</span>
                  <el-tag size="small" :type="activity.tagType" class="act-tag">{{ activity.target }}</el-tag>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>

      <!-- Quick Actions / Shortcuts -->
      <el-col :span="8">
        <el-card class="shortcut-card" shadow="never">
          <template #header><span>快捷入口</span></template>
          <div class="shortcut-grid">
            <div class="shortcut-item" @click="$router.push('/nlp')">
              <el-icon><Cpu /></el-icon>
              <span>逻辑提取</span>
            </div>
            <div class="shortcut-item" @click="$router.push('/upload')">
              <el-icon><Upload /></el-icon>
              <span>上传政策</span>
            </div>
            <div class="shortcut-item" @click="$router.push('/explanation')">
              <el-icon><ChatDotRound /></el-icon>
              <span>辅助决策</span>
            </div>
            <div class="shortcut-item" @click="$router.push('/system-config')">
              <el-icon><Setting /></el-icon>
              <span>配置中心</span>
            </div>
          </div>
        </el-card>

        <el-card class="health-card" shadow="never" style="margin-top: 20px">
          <template #header><span>运行状态</span></template>
          <div class="health-stats">
            <div class="health-item">
              <span class="h-label">系统版本</span>
              <el-tag size="small" type="info">v2.4.0-Enterprise</el-tag>
            </div>
            <div class="health-item">
              <span class="h-label">API 服务</span>
              <el-tag size="small" type="success">Running</el-tag>
            </div>
            <div class="health-item">
              <span class="h-label">Neo4j 数据库</span>
              <el-tag size="small" type="success">Connected</el-tag>
            </div>
            <div class="health-item">
              <span class="h-label">Vector Store</span>
              <el-tag size="small" type="success">Ready</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Edit, Tools, Reading, Refresh, Cpu, Upload, ChatDotRound, Setting, 
  List
} from '@element-plus/icons-vue'
import api from '../services/api'

const totalAssets = ref(0)
const systemScore = ref(98)
const terminologyStats = ref({ standard_count: 5240 })
const governanceStats = ref({ violation_count: 12 })
const assetStats = ref({ graph_nodes: 12840 })


const activities = ref([
  { user: '系统', action: '完成自动化质控巡检', target: '结算数据资产', time: '10分钟前', type: 'primary' },
  { user: 'Admin', action: '执行术语对齐任务', target: 'ICD-10 标准化', time: '25分钟前', type: 'success' },
  { user: '系统', action: '新资产自动发现', target: 'LIS-检验表', time: '1小时前', type: 'warning' }
])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const fetchDashboardData = async () => {
  try {
    const assetRes = await api.getDataAssets()
    totalAssets.value = assetRes.data.items.length
    
    const qualityRes = await api.getQualityReport()
    governanceStats.value.violation_count = qualityRes.data.quality_distribution?.poor + qualityRes.data.quality_distribution?.fair || 0
    systemScore.value = Math.round(qualityRes.data.average_quality * 100)
  } catch (e) {
    console.error('Home stats failed to load')
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-banner {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 20px;
  padding: 40px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.welcome-title {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
}

.welcome-subtitle {
  font-size: 16px;
  opacity: 0.8;
  margin: 0;
}

.banner-stats {
  display: flex;
  gap: 40px;
  align-items: center;
}

.banner-stat-item { text-align: right; }
.banner-stat-item .val { font-size: 36px; font-weight: 800; line-height: 1; margin-bottom: 8px; }
.banner-stat-item .lab { font-size: 14px; opacity: 0.7; }

.banner-stat-divider { width: 1px; height: 50px; background: rgba(255,255,255,0.1); }

.module-row {
  margin-bottom: 30px;
}

.module-card {
  border-radius: 20px;
  cursor: pointer;
  height: 100%;
  transition: all 0.3s;
  border: 1px solid #e2e8f0;
}

.module-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.module-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.m-icon {
  font-size: 24px;
  padding: 10px;
  border-radius: 12px;
}

.terminology .m-icon { background: #e0f2fe; color: #0ea5e9; }
.governance .m-icon { background: #fef2f2; color: #ef4444; }
.assets .m-icon { background: #f0fdf4; color: #22c55e; }

.m-title { font-size: 18px; font-weight: 700; color: #1e293b; }

.m-stat { margin-bottom: 12px; }
.m-val { font-size: 28px; font-weight: 800; color: #1e293b; margin-right: 8px; }
.m-lab { font-size: 14px; color: #64748b; }
.m-desc { font-size: 13px; color: #94a3b8; line-height: 1.6; }

.activity-card, .shortcut-card, .health-card {
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.activity-timeline {
  padding: 10px 0;
}

.activity-item {
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.act-user { font-weight: 700; color: #1e293b; }
.act-action { color: #64748b; }
.act-tag { font-weight: 600; }

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.shortcut-item {
  background: #f8fafc;
  padding: 20px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.shortcut-item:hover {
  background: white;
  border-color: #3b82f6;
  color: #3b82f6;
}

.shortcut-item .el-icon { font-size: 24px; }
.shortcut-item span { font-size: 13px; font-weight: 600; }

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
}

.h-label { color: #64748b; }
</style>
