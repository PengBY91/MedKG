<template>
  <div class="explanation-container">
    <!-- 对话历史侧边栏 -->
    <div class="conversations-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h3 v-if="!sidebarCollapsed">对话历史</h3>
        <div class="header-actions">
          <el-button 
            v-if="!sidebarCollapsed"
            :icon="Plus" 
            circle 
            size="small"
            @click="createNewConversation"
            title="新建对话"
          />
          <el-button 
            :icon="sidebarCollapsed ? Expand : Fold" 
            circle 
            size="small"
            @click="toggleSidebar"
          />
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="conversations-list">
        <el-scrollbar style="flex: 1;">
          <div
            v-for="conv in conversations"
            :key="conv.session_id"
            class="conversation-item"
            :class="{ active: currentSessionId === conv.session_id }"
            @click="switchConversation(conv.session_id)"
          >
            <div class="conv-content">
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-meta">
                <span class="conv-count">{{ conv.message_count }} 条消息</span>
                <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
              </div>
            </div>
            <el-dropdown trigger="click" @command="handleConvAction">
              <el-icon class="conv-more"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{ action: 'rename', id: conv.session_id }">
                    <el-icon><Edit /></el-icon>
                    重命名
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'delete', id: conv.session_id }" divided>
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div v-if="conversations.length === 0" class="empty-conversations">
            <el-empty description="暂无对话历史" />
          </div>
        </el-scrollbar>

        <div class="sidebar-footer">
          <el-button text @click="clearAllConversations" :icon="Delete">
            清空所有对话
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主对话区域 -->
    <div class="chat-wrapper" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Chat Header -->
      <div class="chat-header">
        <div class="header-main">
          <el-icon :size="24" class="ai-icon"><ChatDotRound /></el-icon>
          <div class="title-group">
            <h2>{{ currentConversationTitle }}</h2>
            <el-tag size="small" type="success" effect="plain">多轮对话 v2</el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button circle :icon="Refresh" @click="clearChat" title="清空当前对话" />
        </div>
      </div>

      <!-- Message List -->
      <div class="message-container" ref="messageBox">
        <div v-if="messages.length === 0" class="welcome-guide">
          <div class="welcome-icon">
            <el-icon :size="48"><DataAnalysis /></el-icon>
          </div>
          <h3>您好，我是您的医保政策智能助手</h3>
          <p>支持多轮对话，理解上下文，为您提供精准、权威的政策解答</p>
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
          <div class="message-bubble" :class="{ 'error-message': msg.isError }">
            <div class="message-content">
              <template v-if="msg.loading">
                <div class="typing-loader">
                  <span></span><span></span><span></span>
                </div>
              </template>
              <template v-else>
                <!-- Contextualized Query Hint -->
                <div v-if="msg.contextualized_question && msg.contextualized_question !== msg.content" class="context-hint">
                  <el-icon><InfoFilled /></el-icon>
                  <span>理解为：{{ msg.contextualized_question }}</span>
                </div>

                <!-- AI 专属内容：思考过程放在最上面 -->
                <template v-if="msg.role === 'ai'">
                  <!-- Thinking Process (思考过程) - 放在回答前面，流式生成时自动展开 -->
                  <div v-if="msg.thinking || msg.thinkingExpanded" class="thinking-section">
                    <div class="thinking-header-static" v-if="msg.thinking">
                      <el-icon class="thinking-icon"><DataAnalysis /></el-icon>
                      <span class="thinking-label">💡 AI 思考过程</span>
                      <el-tag size="small" type="warning" effect="plain" v-if="!msg.loading">已完成</el-tag>
                      <el-tag size="small" type="warning" effect="plain" v-else>生成中...</el-tag>
                    </div>
                    <div class="thinking-content-static" v-if="msg.thinking">
                      {{ msg.thinking }}
                      <span v-if="msg.loading" class="thinking-cursor">▋</span>
                    </div>
                  </div>
                </template>

                <!-- 回答内容 -->
                <div class="text-payload">{{ msg.content }}</div>
                
                <!-- AI 其他内容：推理链路、来源 -->
                <template v-if="msg.role === 'ai'">
                  
                  <!-- Synergy Trace for AI -->
                  <div v-if="msg.reasoning_trace && msg.reasoning_trace.length > 0" class="synergy-trace">
                  <el-collapse>
                    <el-collapse-item name="trace">
                      <template #title>
                        <el-icon class="trace-icon"><Connection /></el-icon>
                        <span class="trace-label">推理链路</span>
                      </template>
                      <div class="trace-steps">
                        <div v-for="(t, idx) in msg.reasoning_trace" :key="idx" class="trace-step">
                          <div class="step-dot" :class="t.status.toLowerCase()"></div>
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
                            <el-tag size="small" class="source-tag">
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
          <span>按下 Enter 键发送咨询</span>
          <span v-if="currentSessionId" class="session-info">
            <el-icon><ChatDotRound /></el-icon>
            对话 ID: {{ currentSessionId.slice(-8) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatDotRound, User, Connection, Top, Refresh, 
  DataAnalysis, Plus, Fold, Expand, MoreFilled,
  Edit, Delete, InfoFilled
} from '@element-plus/icons-vue'
import api from '../services/api'

const policyForm = reactive({
  question: ''
})

const messages = ref([])
const conversations = ref([])
const currentSessionId = ref(null)
const currentConversationTitle = ref('新对话')
const queryingPolicy = ref(false)
const messageBox = ref(null)
const sidebarCollapsed = ref(false)

const suggestedQuestions = [
  "门诊透析的报销限额是多少？",
  "如何办理异地就医备案？",
  "糖尿病的门诊特殊疾病待遇政策",
  "2024年个人缴费标准是否有变动？"
]

onMounted(() => {
  loadConversations()
})

const scrollToBottom = async () => {
  await nextTick()
  if (messageBox.value) {
    messageBox.value.scrollTop = messageBox.value.scrollHeight
  }
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const loadConversations = async () => {
  try {
    const response = await api.listConversations(50, 0)
    conversations.value = response.data.data.items
  } catch (error) {
    console.error('Failed to load conversations:', error)
  }
}

const createNewConversation = () => {
  currentSessionId.value = null
  currentConversationTitle.value = '新对话'
  messages.value = []
}

const switchConversation = async (sessionId) => {
  try {
    currentSessionId.value = sessionId
    
    // 加载对话消息
    const response = await api.getConversationMessages(sessionId)
    const conversation = await api.getConversation(sessionId)
    
    currentConversationTitle.value = conversation.data.data.title
    
    // 格式化消息
    messages.value = response.data.data.messages.map(msg => ({
      role: msg.role,
      content: msg.content,
      sources: msg.metadata?.sources || [],
      reasoning_trace: msg.metadata?.reasoning_trace || [],
      contextualized_question: msg.metadata?.contextualized_question
    }))
    
    await scrollToBottom()
  } catch (error) {
    ElMessage.error('加载对话失败')
    console.error('Failed to load conversation:', error)
  }
}

const handleConvAction = async ({ action, id }) => {
  if (action === 'rename') {
    ElMessageBox.prompt('请输入新的对话标题', '重命名对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    }).then(async ({ value }) => {
      try {
        await api.updateConversation(id, value)
        await loadConversations()
        if (currentSessionId.value === id) {
          currentConversationTitle.value = value
        }
        ElMessage.success('重命名成功')
      } catch (error) {
        ElMessage.error('重命名失败')
      }
    }).catch(() => {})
  } else if (action === 'delete') {
    ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      type: 'warning'
    }).then(async () => {
      try {
        await api.deleteConversation(id)
        await loadConversations()
        if (currentSessionId.value === id) {
          createNewConversation()
        }
        ElMessage.success('删除成功')
      } catch (error) {
        ElMessage.error('删除失败')
      }
    }).catch(() => {})
  }
}

const clearAllConversations = () => {
  ElMessageBox.confirm('确定要清空所有对话吗？此操作不可恢复！', '警告', {
    type: 'warning',
    confirmButtonText: '确定清空',
    cancelButtonText: '取消'
  }).then(async () => {
    try {
      await api.clearConversations()
      conversations.value = []
      createNewConversation()
      ElMessage.success('已清空所有对话')
    } catch (error) {
      ElMessage.error('清空失败')
    }
  }).catch(() => {})
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
    thinking: '',  // 思考过程
    thinkingExpanded: true,  // 默认展开思考过程
    loading: true,
    sources: [],
    reasoning_trace: []
  })
  
  await scrollToBottom()
  queryingPolicy.value = true

  try {
    // 使用流式 API，支持思考过程
    await api.queryPolicyStream(
      currentQuestion,
      currentSessionId.value,
      {
        // onThinking: 接收思考过程片段
        onThinking: (chunk) => {
          console.log('[Thinking Chunk]:', chunk)
          messages.value[aiMsgIdx].thinking += chunk
          scrollToBottom()
        },
        // onThinkingDone: 思考完成
        onThinkingDone: () => {
          console.log('[Thinking Done] Total thinking:', messages.value[aiMsgIdx].thinking)
        },
        // onAnswerStart: 答案开始
        onAnswerStart: () => {
          console.log('[Answer Start]')
          messages.value[aiMsgIdx].loading = false
        },
        // onChunk: 接收答案片段
        onChunk: (chunk) => {
          messages.value[aiMsgIdx].content += chunk
          scrollToBottom()
        },
        // onMetadata: 接收推理链路和来源
        onMetadata: (metadata) => {
          console.log('[Metadata]:', metadata)
          messages.value[aiMsgIdx].sources = metadata.sources || []
          messages.value[aiMsgIdx].reasoning_trace = metadata.reasoning_trace || []
          messages.value[aiMsgIdx].entities = metadata.entities || []
          
          // 更新 session ID（从元数据中）
          if (metadata.session_id && !currentSessionId.value) {
            currentSessionId.value = metadata.session_id
            currentConversationTitle.value = currentQuestion.slice(0, 30) + (currentQuestion.length > 30 ? '...' : '')
          }
        },
        // onDone: 完成
        onDone: async (data) => {
          console.log('[Done]:', data)
          messages.value[aiMsgIdx].loading = false
          queryingPolicy.value = false
          
          // 更新 session ID
          if (data.session_id && !currentSessionId.value) {
            currentSessionId.value = data.session_id
            currentConversationTitle.value = currentQuestion.slice(0, 30) + (currentQuestion.length > 30 ? '...' : '')
          }
          
          // 刷新对话列表
          await loadConversations()
          await scrollToBottom()
        },
        // onError: 错误处理
        onError: (error) => {
          console.error('Stream query failed:', error)
          
          let errorMessage = '抱歉，我现在遇到一点技术困难，请稍后再试。'
          
          if (error.message && error.message.includes('503')) {
            errorMessage = '⚠️ LLM 服务暂时不可用\n\n请检查系统配置中的 OPENAI_API_KEY 和 OPENAI_BASE_URL 设置。\n\n您可以在"系统配置"页面进行配置。'
            ElMessage.error({
              message: 'LLM 服务不可用，请联系管理员配置',
              duration: 5000,
              showClose: true
            })
          } else if (error.message && error.message.includes('401')) {
            errorMessage = '登录已过期，请重新登录'
            setTimeout(() => {
              window.location.href = '/login'
            }, 2000)
          }
          
          messages.value[aiMsgIdx].content = errorMessage
          messages.value[aiMsgIdx].loading = false
          messages.value[aiMsgIdx].isError = true
          queryingPolicy.value = false
          scrollToBottom()
        }
      }
    )
  } catch (error) {
    console.error('Policy query failed:', error)
    messages.value[aiMsgIdx].content = '抱歉，我现在遇到一点技术困难，请稍后再试。'
    messages.value[aiMsgIdx].loading = false
    queryingPolicy.value = false
  }
}

const clearChat = () => {
  ElMessageBox.confirm('确定要清空当前对话吗？', '提示', {
    type: 'warning'
  }).then(() => {
    messages.value = []
    currentSessionId.value = null
    currentConversationTitle.value = '新对话'
  }).catch(() => {})
}

const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  
  return date.toLocaleDateString()
}
</script>

<style scoped>
.explanation-container {
  display: flex;
  height: calc(100vh - 80px);
  gap: 0;
  margin-top: 0;
  overflow: hidden;
}

/* 侧边栏样式 */
.conversations-sidebar {
  width: 280px;
  background: #f8f9fa;
  border-right: 1px solid #e4e7ed;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  max-height: 100%;
  overflow: hidden;
}

.conversations-sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.conversations-list {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.conversation-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversation-item:hover {
  background: #e9ecef;
}

.conversation-item.active {
  background: #e3f2fd;
  border-left: 3px solid #409eff;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.conv-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.conv-more {
  font-size: 16px;
  color: #909399;
  cursor: pointer;
}

.conv-more:hover {
  color: #409eff;
}

.empty-conversations {
  padding: 40px 20px;
  text-align: center;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

/* 主对话区域 */
.chat-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 0 16px 16px 0;
  overflow: hidden;
  transition: all 0.3s;
  max-height: 100%;
}

.chat-wrapper.sidebar-collapsed {
  border-radius: 16px;
}

.chat-header {
  padding: 12px 24px;
  background: #fcfcfc;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
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
  overflow-x: hidden;
  padding: 24px;
  scroll-behavior: smooth;
  min-height: 0;
  max-height: 100%;
}

.welcome-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  text-align: center;
  padding: 40px 20px;
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
  max-width: 70%;
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

.ai .message-bubble.error-message {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
  color: #f56c6c;
}

.context-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #409eff;
  background: #ecf5ff;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.text-payload {
  white-space: pre-wrap;
}

.synergy-trace {
  margin-top: 12px;
  border-top: 1px solid #e4e7ed;
  padding-top: 8px;
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

.step-dot.success {
  background: #67c23a;
}

.step-dot.skipped {
  background: #e6a23c;
}

.grounded-sources {
  margin-top: 12px;
  padding: 8px;
  background: white;
  border-radius: 8px;
}

.source-tag {
  cursor: pointer;
  max-width: 150px;
}

.input-container {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: white;
  flex-shrink: 0;
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

.input-hint {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
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

@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.3; }
  50% { transform: translateY(-4px); opacity: 1; }
}

/* === Thinking Process Styles === */
.thinking-section {
  margin-bottom: 16px;
  background: linear-gradient(135deg, #fffbf0 0%, #fff9e6 100%);
  border: 2px solid #ffeaa7;
  border-left: 4px solid #fdcb6e;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(253, 203, 110, 0.15);
}

.thinking-header-static {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ffeaa7;
}

.thinking-icon {
  color: #e17055;
  font-size: 18px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.thinking-label {
  flex: 1;
  color: #d63031;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.3px;
}

.thinking-content-static {
  color: #5f3e31;
  line-height: 1.8;
  font-size: 13px;
  white-space: pre-wrap;
  word-wrap: break-word;
  position: relative;
}

.thinking-cursor {
  display: inline-block;
  color: #e17055;
  animation: blink 1s step-end infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@media (max-width: 768px) {
  .explanation-container {
    height: calc(100vh - 60px);
  }
  
  .conversations-sidebar {
    width: 60px;
  }
  
  .sidebar-header h3 {
    display: none;
  }
  
  .message-bubble {
    max-width: 85%;
  }
}
</style>

