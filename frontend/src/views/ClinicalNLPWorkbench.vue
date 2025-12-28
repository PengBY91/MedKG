<template>
  <div class="nlp-container">
    <div class="page-header">
      <div class="header-content">
        <h2 class="title">临床自然语言处理 (Clinical NLP)</h2>
        <p class="subtitle">自动从病历摘要、主诉中提取医疗实体，并实现标准术语映射 (KAG Pipeline)</p>
      </div>
    </div>

    <div class="main-grid">
      <!-- Input Card -->
      <el-card class="input-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>非结构化临床文本输入</span>
            <el-button type="primary" :loading="processing" @click="handleAnalyze" :icon="MagicStick">智能解析</el-button>
          </div>
        </template>
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="8"
          placeholder="请输入临床病历描述，例如：患者三年前患有原发性高血压，近日自觉心前区压榨性疼痛，疑为急性心肌梗死..."
          class="premium-textarea"
        />
        <div class="input-presets">
          <span class="label">示例：</span>
          <el-button size="small" link @click="inputText = '患者主诉右下腹剧烈疼痛3小时，伴恶心呕吐，既往有2型糖尿病史。'">急性阑尾炎案例</el-button>
          <el-button size="small" link @click="inputText = '长期咳嗽咳痰，近日出现气促。检查示：双肺呼吸音粗，初步诊断：肺炎？哮喘？'">呼吸科案例</el-button>
        </div>
      </el-card>

      <!-- Analysis Results -->
      <div class="results-panel" v-if="results.entities && results.entities.length > 0">
        <div class="panel-title">结构化解析报告 (Entity & Schema Mapping)</div>
        
        <div v-for="(entity, idx) in results.entities" :key="idx" class="entity-item">
          <div class="entity-main">
            <div class="entity-tag" :class="entity.entity_type.toLowerCase()">
              {{ getEntityTypeZh(entity.entity_type) }}
            </div>
            <div class="entity-name">{{ entity.original_term }}</div>
            
            <div class="mapping-arrow"><el-icon><Right /></el-icon></div>
            
            <div class="standard-mapping" v-if="entity.standard_match">
              <el-tag size="small" effect="dark" type="success">{{ entity.standard_match.code }}</el-tag>
              <span class="standard-name">{{ entity.standard_match.standard_name }}</span>
            </div>
            <div class="no-mapping" v-else>
              <el-tag size="small" type="info">暂无精确匹配</el-tag>
              <span class="guess-name" v-if="entity.best_guess">推荐案: {{ entity.best_guess }}</span>
            </div>
          </div>
          
          <div class="entity-context">
            <span class="ctx-label">上下文：</span>
            <span class="ctx-text">"...{{ entity.context }}..."</span>
          </div>
        </div>
      </div>
      <el-empty v-else-if="!processing" description="在上方输入文本并点击解析，体验自动后结构化流程" />
      <div v-else class="loading-state">
        <el-skeleton :rows="5" animated />
        <p>AI 正在分析语义实体并检索知识图谱...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Right } from '@element-plus/icons-vue'
import api from '../services/api'

const inputText = ref('')
const processing = ref(false)
const results = ref({ entities: [] })

const handleAnalyze = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入临床描述')
    return
  }
  
  processing.value = true
  try {
    const res = await api.extractNlp(inputText.value)
    results.value = res.data
    ElMessage.success(`解析完成，提取到 ${res.data.entity_count} 个医疗实体`)
  } catch (e) {
    ElMessage.error('NLP 解析服务异常')
  } finally {
    processing.value = false
  }
}

const getEntityTypeZh = (type) => {
  const map = {
    'Symptom': '症状',
    'Disease': '疾病',
    'Medication': '药物',
    'Procedure': '手术/操作',
    'BodyPart': '身体部位'
  }
  return map[type] || type
}
</script>

<style scoped>
.nlp-container {
  padding-bottom: 40px;
}

.page-header {
  margin-bottom: 24px;
}

.title { font-size: 26px; font-weight: 700; color: #1e293b; margin: 0 0 4px 0; }
.subtitle { color: #64748b; margin: 0; }

.main-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-presets {
  margin-top: 12px;
  font-size: 13px;
  color: #94a3b8;
}

.results-panel {
  display: grid;
  gap: 12px;
}

.panel-title {
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.entity-item {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.entity-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.05);
}

.entity-main {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.entity-tag {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.disease { background: #ef4444; }
.symptom { background: #f59e0b; }
.medication { background: #10b981; }
.procedure { background: #3b82f6; }
.bodypart { background: #8b5cf6; }

.entity-name {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.mapping-arrow {
  color: #cbd5e1;
}

.standard-name {
  margin-left: 8px;
  font-weight: 600;
  color: #3b82f6;
}

.guess-name {
  margin-left: 8px;
  font-size: 13px;
  color: #94a3b8;
}

.entity-context {
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 6px;
}

.ctx-label { font-weight: 600; }

.loading-state {
  text-align: center;
  padding: 40px;
  color: #64748b;
}
</style>
