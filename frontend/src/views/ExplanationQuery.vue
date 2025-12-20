<template>
  <div class="chat-wrapper">
    <!-- Chat Header -->
    <div class="chat-header">
      <div class="header-main">
        <el-icon :size="24" class="ai-icon"><ChatDotRound /></el-icon>
        <div class="title-group">
          <h2>政策智能助手</h2>
          <el-tag size="small" type="success" effect="plain">GraphRAG Enabled</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-button circle :icon="Refresh" @click="clearChat" title="清空对话" />
      </div>
    </div>

    <!-- Message List -->
    <div class="message-container" ref="messageBox">
      <div v-if="messages.length === 0" class="welcome-guide">
        <div class="welcome-icon">
          <el-icon :size="48"><DataAnalysis /></el-icon>
        </div>
        <h3>您好，我是您的医保政策智能助手</h3>
        <p>基于知识图谱与大模型协同，为您提供精准、权威的政策解答</p>
        <div class="quick-queries">
          <el-button 
            v-for="q in suggestedQuestions" 
            :key="q" 
            round 
            @click="policyForm.question = q; queryPolicy()"
          >
            {{ q }}
          </el-button>
        </div>
      </div>

      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        :class="['message-row', msg.role]"
      >
        <div class="avatar-wrap">
          <el-avatar 
            :size="36" 
            :icon="msg.role === 'user' ? User : ChatDotRound" 
            :class="msg.role"
          />
        </div>
        <div class="message-bubble">
          <div class="message-content">
            <template v-if="msg.loading">
              <div class="typing-loader">
                <span></span><span></span><span></span>
              </div>
            </template>
            <template v-else>
              <div class="text-payload">{{ msg.content }}</div>
              
              <!-- Synergy Trace for AI -->
              <div v-if="msg.reasoning_trace" class="synergy-trace">
                <el-collapse>
                  <el-collapse-item name="trace">
                    <template #title>
                      <el-icon class="trace-icon"><Connection /></el-icon>
                      <span class="trace-label">图谱协同推理链路</span>
                    </template>
                    <div class="trace-steps">
                      <div v-for="(t, idx) in msg.reasoning_trace" :key="idx" class="trace-step">
                        <div class="step-dot"></div>
                        <div class="step-desc">
                          <span class="step-name">{{ t.step }}</span>
                          <span class="step-detail">{{ t.detail }}</span>
                        </div>
                      </div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- Sources for AI -->
              <div v-if="msg.sources && msg.sources.length > 0" class="grounded-sources">
                <div class="source-header">依据条文:</div>
                <el-scrollbar max-height="120px">
                  <div class="source-chips">
                    <el-popover
                      v-for="(s, sIdx) in msg.sources"
                      :key="sIdx"
                      placement="top"
                      :width="300"
                      trigger="click"
                    >
                      <template #reference>
                        <el-tag size="small" class="source-tag" @click="viewSource(s)">
                          {{ s.name }}
                        </el-tag>
                      </template>
                      <div class="source-detail-popover">
                        <div class="pop-title">{{ s.name }}</div>
                        <div class="pop-content">{{ s.content }}</div>
                        <div class="pop-footer">{{ s.parent_doc }} | {{ s.reference }}</div>
                      </div>
                    </el-popover>
                  </div>
                </el-scrollbar>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-container">
      <div class="input-wrap">
        <el-input
          v-model="policyForm.question"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 5 }"
          placeholder="问问我关于医保政策的信息..."
          @keydown.enter.prevent="queryPolicy"
          resize="none"
          autocomplete="off"
        />
        <el-button 
          type="primary" 
          circle 
          :icon="Top" 
          :disabled="!policyForm.question.trim()"
          :loading="queryingPolicy"
          @click="queryPolicy"
        />
      </div>
      <div class="input-hint">
        按下 Enter 键发送咨询
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ChatDotRound, User, Connection, Top, Refresh, 
  DataAnalysis, Search 
} from '@element-plus/icons-vue'
import api from '../services/api'

const policyForm = reactive({
  question: ''
})

const messages = ref([])
const queryingPolicy = ref(false)
const messageBox = ref(null)

const suggestedQuestions = [
  "门诊透析的报销限额是多少？",
  "如何办理异地就医备案？",
  "糖尿病的门诊特殊疾病待遇政策",
  "2024年个人缴费标准是否有变动？"
]

const scrollToBottom = async () => {
  await nextTick()
  if (messageBox.value) {
    messageBox.value.scrollTop = messageBox.value.scrollHeight
  }
}

const queryPolicy = async () => {
  const query = policyForm.question.trim()
  if (!query) return

  // Add user message
  messages.value.push({
    role: 'user',
    content: query
  })
  
  const currentQuestion = query
  policyForm.question = ''
  
  // Add placeholder AI message
  const aiMsgIdx = messages.value.length
  messages.value.push({
    role: 'ai',
    content: '',
    loading: true
  })
  
  await scrollToBottom()
  queryingPolicy.value = true

  // Ensure minimum typing time for real feel and to prevent flicker
  const minDelay = new Promise(resolve => setTimeout(resolve, 800))

  try {
    const [response] = await Promise.all([
      api.queryPolicy(currentQuestion),
      minDelay
    ])
    const data = response.data
    
    // Update AI message with real data
    messages.value[aiMsgIdx] = {
      role: 'ai',
      content: data.answer,
      sources: data.sources,
      reasoning_trace: data.reasoning_trace,
      loading: false
    }
  } catch (error) {
    await minDelay
    messages.value[aiMsgIdx] = {
      role: 'ai',
      content: '抱歉，我现在遇到一点技术困难，请稍后再试。',
      loading: false
    }
    // Only show error if it's a real issue
    console.error('Policy query failed:', error)
  } finally {
    queryingPolicy.value = false
    await scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = []
}

const viewSource = (s) => {
  // Logic to view full source document if needed
}
</script>

<style scoped>
.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
  overflow: hidden;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  will-change: contents;
}

.chat-header {
  padding: 16px 24px;
  background: #fcfcfc;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-icon {
  color: #409eff;
  background: #eef5ff;
  padding: 8px;
  border-radius: 50%;
}

.title-group h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
  min-height: 400px;
}

.welcome-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  text-align: center;
  min-height: 400px;
}

.welcome-icon {
  margin-bottom: 20px;
  color: #409eff;
  opacity: 0.8;
}

.quick-queries {
  margin-top: 30px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.message-row {
  display: flex;
  margin-bottom: 24px;
  gap: 12px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-bubble {
  max-width: 80%;
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.6;
}

.user .message-bubble {
  background: #409eff;
  color: white;
  border-top-right-radius: 4px;
}

.ai .message-bubble {
  background: #f4f6f8;
  color: #303133;
  border-top-left-radius: 4px;
}

.avatar-wrap {
  flex-shrink: 0;
}

.el-avatar.ai {
  background: #eef5ff;
  color: #409eff;
}

.el-avatar.user {
  background: #409eff;
  color: white;
}

.text-payload {
  white-space: pre-wrap;
}

.synergy-trace {
  margin-top: 12px;
  border-top: 1px solid #e4e7ed;
  padding-top: 8px;
}

.synergy-trace :deep(.el-collapse) {
  border: none;
}

.synergy-trace :deep(.el-collapse-item__header) {
  height: 32px;
  background: transparent;
  border: none;
  font-size: 12px;
  color: #409eff;
}

.trace-steps {
  padding: 8px 0;
}

.trace-step {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.step-dot {
  width: 6px;
  height: 6px;
  background: #409eff;
  border-radius: 50%;
  margin-top: 6px;
}

.step-desc {
  display: flex;
  flex-direction: column;
}

.step-name {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.step-detail {
  font-size: 11px;
  color: #909399;
}

.grounded-sources {
  margin-top: 12px;
  padding: 8px;
  background: white;
  border-radius: 8px;
}

.source-header {
  font-size: 11px;
  color: #909399;
  margin-bottom: 6px;
  font-weight: 600;
}

.source-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.source-tag {
  cursor: pointer;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.input-container {
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
}

.input-wrap {
  background: #f4f6f8;
  border-radius: 24px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s;
}

.input-wrap:focus-within {
  background: white;
  box-shadow: 0 0 0 2px rgba(64,158,255,0.2);
}

.input-wrap :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 8px 0;
  font-size: 15px;
}

.input-hint {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 8px;
  text-align: center;
}

.typing-loader {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-loader span {
  width: 6px;
  height: 6px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1s infinite ease-in-out;
}

.typing-loader span:nth-child(1) { animation-delay: 0s; }
.typing-loader span:nth-child(2) { animation-delay: 0.2s; }
.typing-loader span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.3; }
  50% { transform: translateY(-4px); opacity: 1; }
}

.source-detail-popover {
  padding: 8px;
}

.pop-title {
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 4px;
}

.pop-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 8px;
}

.pop-footer {
  font-size: 11px;
  color: #909399;
}

/* Responsive adjustments for smaller screens */
@media (max-width: 768px) {
  .chat-wrapper {
    min-width: 100%;
    max-width: 100%;
    border-radius: 0;
    height: calc(100vh - 60px);
  }
  
  .quick-queries {
    flex-direction: column;
  }
  
  .message-bubble {
    max-width: 90%;
  }
}
</style>
