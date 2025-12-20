<template>
  <div class="governance-review">
    <header class="review-header">
      <h2>Governance Review Workbench</h2>
      <div class="stats">
        <span>Pending: {{ pendingTasks.length }}</span>
      </div>
    </header>

    <div class="review-workspace" v-if="currentTask">
      
      <!-- MODE 1: Rule Review (List View) -->
      <div v-if="currentTask.task_type === 'rule_review'" class="full-panel">
        <h3>Rule Extraction Review ({{ currentTask.doc_id }})</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Rule Type</th>
              <th>Subject</th>
              <th>Predicate</th>
              <th>Limit</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(rule, idx) in currentTask.extracted_data.rules" :key="idx">
              <td>
                <span :class="['badge', rule.status === 'success' ? 'success' : 'error']">{{ rule.status }}</span>
              </td>
              <td>{{ rule.rule_type || 'N/A' }}</td>
              <td>{{ rule.subject || 'N/A' }}</td>
              <td>{{ rule.predicate || 'N/A' }}</td>
              <td>{{ rule.object_value || 'N/A' }}</td>
              <td>
                <button class="btn-sm btn-primary">Edit</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- MODE 2: Terminology Review (List View) -->
      <div v-else-if="currentTask.task_type === 'term_review'" class="full-panel">
        <h3>Terminology Normalization Review ({{ currentTask.doc_id }})</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Original Term</th>
              <th>Suggested Code</th>
              <th>Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(term, idx) in currentTask.extracted_data.entities" :key="idx">
              <td>{{ term.term }}</td>
              <td>
                <input v-model="term.suggestion" class="table-input">
              </td>
              <td>
                <div :class="['confidence-bar', getConfClass(term.confidence)]">
                  {{ (term.confidence * 100).toFixed(0) }}%
                </div>
              </td>
              <td>
                <button @click="term.approved = !term.approved" :class="['btn-sm', term.approved ? 'btn-success' : 'btn-secondary']">
                  {{ term.approved ? 'Approved' : 'Approve' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- MODE 3: Generic Entity Review (Split View) -->
      <div v-else class="split-view">
        <!-- Left Panel: Source Document -->
        <div class="panel source-panel">
          <h3>Source Text ({{ currentTask.doc_id }})</h3>
          <div class="text-viewer">
            {{ currentTask.extracted_data.text_first_500 }}... (Full text hidden in mock)
          </div>
        </div>

        <!-- Right Panel: Extracted Data Editor -->
        <div class="panel data-panel">
          <h3>Extracted Knowledge (Confidence: {{ (currentTask.confidence * 100).toFixed(1) }}%)</h3>
          
          <div class="entity-list">
            <div v-for="(entity, idx) in currentTask.extracted_data.entities" :key="idx" class="entity-card">
              <div class="field-group">
                <label>Entity:</label>
                <input v-model="entity.entity" :class="{ 'low-conf': entity.confidence < 0.9 }">
              </div>
              <div class="field-group">
                <label>Type:</label>
                <select v-model="entity.type">
                  <option>Disease</option>
                  <option>Drug</option>
                  <option>Symptom</option>
                </select>
              </div>
              <div class="actions">
                <button @click="removeEntity(idx)" class="btn-danger">✗</button>
              </div>
            </div>
            <button @click="addEntity" class="btn-secondary">+ Add Entity</button>
          </div>
        </div>
      </div>

      <!-- Global Actions -->
      <div class="global-actions">
        <button @click="submitDecision('approve')" class="btn-primary">Approve Task & Sync</button>
        <button @click="submitDecision('reject')" class="btn-danger">Reject Task</button>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>No pending tasks. Good job!</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { ElMessage } from 'element-plus'

export default {
  setup() {
    const pendingTasks = ref([])
    const currentTask = ref(null)

    const fetchTasks = async () => {
        try {
            const response = await api.getPendingReviews()
            pendingTasks.value = response.data
            if (pendingTasks.value.length > 0) {
              currentTask.value = JSON.parse(JSON.stringify(pendingTasks.value[0]))
            } else {
              currentTask.value = null
            }
        } catch (error) {
            console.error("Failed to fetch governance tasks", error)
        }
    }

    onMounted(async () => {
      fetchTasks()
    })

    const removeEntity = (idx) => {
      currentTask.value.extracted_data.entities.splice(idx, 1)
    }

    const addEntity = () => {
      currentTask.value.extracted_data.entities.push({ entity: "", type: "Disease", confidence: 1.0 })
    }
    
    const getConfClass = (score) => {
        if(score > 0.9) return 'high';
        if(score > 0.7) return 'med';
        return 'low';
    }

    const submitDecision = async (decision) => {
      try {
          // 1. Submit Decision to Governance Service
          await api.submitReviewDecision(currentTask.value.id, decision, currentTask.value.extracted_data)
          
          // 2. If approved, persist to Knowledge Store
          if (decision === 'approve') {
              if (currentTask.value.task_type === 'rule_review') {
                  for (const rule of currentTask.value.extracted_data.rules) {
                      await api.saveRule(rule)
                  }
                  ElMessage.success('规则已同步至知识库')
              } else if (currentTask.value.task_type === 'term_review') {
                  const items = currentTask.value.extracted_data.entities.map(e => ({
                      term: e.term,
                      code: e.suggestion,
                      status: 'APPROVED',
                      display: e.term,
                      system: 'SNOMED-CT'
                  }))
                  for (const item of items) {
                      await api.submitFeedback(item)
                  }
                  ElMessage.success('术语已同步至标准库')
              }
          }

          ElMessage.success(`任务已${decision === 'approve' ? '通过' : '处理'}`)
          fetchTasks()
      } catch (error) {
          ElMessage.error('操作失败')
      }
    }


    return {
      pendingTasks,
      currentTask,
      removeEntity,
      addEntity,
      getConfClass,
      submitDecision
    }
  }
}
</script>

<style scoped>
.governance-review {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.review-header {
  padding: 1rem;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
}
.review-workspace {
  display: flex;
  flex: 1;
  flex-direction: column; 
  overflow: hidden;
  padding: 1rem;
  background: #f4f6f8;
}
.full-panel {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    flex: 1;
    overflow: auto;
}
.split-view {
    display: flex;
    flex: 1;
    gap: 20px;
    overflow: hidden;
}
.panel {
  flex: 1;
  padding: 1rem;
  background: #fff;
  border-radius: 8px;
  overflow-y: auto;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.source-panel {
  background: #fff; 
}
.text-viewer {
    white-space: pre-wrap;
    font-family: monospace;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
}
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
.data-table th, .data-table td {
    border: 1px solid #eee;
    padding: 12px;
    text-align: left;
}
.data-table th { background: #f8f9fa; font-weight: 600; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge.success { background: #d4edda; color: #155724; }
.badge.error { background: #f8d7da; color: #721c24; }
.confidence-bar { padding: 2px 6px; border-radius: 10px; text-align: center; width: 60px; font-size: 12px; color: white;}
.confidence-bar.high { background: #28a745; }
.confidence-bar.med { background: #ffc107; color: #333; }
.confidence-bar.low { background: #dc3545; }
.table-input { width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px;}

.entity-card {
  border: 1px solid #eee;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  display: flex;
  gap: 10px;
  align-items: center;
  background: #fff;
}

.global-actions {
    margin-top: 15px;
    padding: 15px;
    background: #fff;
    border-radius: 8px;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
}

button {
  padding: 8px 16px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
}
.btn-primary { background: #007bff; color: white; }
.btn-warning { background: #ffc107; color: black; }
.btn-danger { background: #dc3545; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-sm { padding: 4px 8px; font-size: 12px; }
</style>
