<template>
  <div class="system-config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">⚙️ 系统设置</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="demo-tabs">
        <!-- LLM Configuration Tab -->
        <el-tab-pane label="LLM 配置" name="llm">
          <div class="tab-content">
            <el-alert
              title="配置大语言模型 (OpenAI API Compatible)"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <el-form label-width="120px" :model="llmForm" :rules="llmRules" ref="llmFormRef" v-loading="loadingLLM">
              <el-form-item label="Base URL" prop="base_url">
                <el-input v-model="llmForm.base_url" placeholder="https://api.openai.com/v1" />
              </el-form-item>
              <el-form-item label="API Key" prop="api_key">
                <el-input v-model="llmForm.api_key" placeholder="sk-..." show-password />
              </el-form-item>
              <el-form-item label="Model" prop="model">
                <el-input v-model="llmForm.model" placeholder="gpt-4" />
              </el-form-item>
              
              <el-form-item>
                <div class="form-actions">
                  <el-button type="primary" @click="saveLLMConfig" :loading="savingLLM">
                    保存配置
                  </el-button>
                  <el-button type="success" @click="testLLMConnection" :loading="testingLLM">
                    测试连接
                  </el-button>
                  <span v-if="llmStatus" class="status-indicator">
                    <el-tag :type="llmStatus.success ? 'success' : 'danger'">
                      {{ llmStatus.message }}
                    </el-tag>
                  </span>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- KG Configuration Tab -->
        <el-tab-pane label="知识图谱配置" name="kg">
          <div class="tab-content">
            <el-alert
              title="配置 Neo4j 知识图谱连接"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <el-form label-width="120px" :model="kgForm" :rules="kgRules" ref="kgFormRef" v-loading="loadingKG">
              <el-form-item label="Bolt URI" prop="uri">
                <el-input v-model="kgForm.uri" placeholder="bolt://localhost:7687" />
              </el-form-item>
              <el-form-item label="Username" prop="user">
                <el-input v-model="kgForm.user" placeholder="neo4j" />
              </el-form-item>
              <el-form-item label="Password" prop="password">
                <el-input v-model="kgForm.password" placeholder="***" show-password />
                <div class="input-tip">留空则保持现有密码不变</div>
              </el-form-item>
              
              <el-form-item>
                <div class="form-actions">
                  <el-button type="primary" @click="saveKGConfig" :loading="savingKG">
                    保存配置
                  </el-button>
                  <el-button type="success" @click="testKGConnection" :loading="testingKG">
                    测试连接
                  </el-button>
                  <span v-if="kgStatus" class="status-indicator">
                    <el-tag :type="kgStatus.success ? 'success' : 'danger'">
                      {{ kgStatus.message }}
                    </el-tag>
                  </span>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const activeTab = ref('llm')

// --- LLM Logic ---
const llmForm = ref({ api_key: '', base_url: '', model: '' })
const llmFormRef = ref(null)
const loadingLLM = ref(false)
const savingLLM = ref(false)
const testingLLM = ref(false)
const llmStatus = ref(null)

const llmRules = {
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }]
}

const loadLLMConfig = async () => {
    loadingLLM.value = true
    try {
        const res = await axios.get('/api/v1/system/config/llm')
        if (res.data.success) {
            llmForm.value = res.data.config
        }
    } catch (e) {
        ElMessage.error("加载 LLM 配置失败")
    } finally {
        loadingLLM.value = false
    }
}

const saveLLMConfig = async () => {
    if (!llmFormRef.value) return
    await llmFormRef.value.validate(async (valid) => {
        if (valid) {
            savingLLM.value = true
            llmStatus.value = null
            try {
                const res = await axios.post('/api/v1/system/config/llm', llmForm.value)
                if (res.data.success) {
                    ElMessage.success("LLM 配置已保存")
                }
            } catch (e) {
                ElMessage.error("保存失败: " + e.message)
            } finally {
                savingLLM.value = false
            }
        }
    })
}

const testLLMConnection = async () => {
    testingLLM.value = true
    llmStatus.value = null
    try {
        const res = await axios.post('/api/v1/system/test/llm')
        llmStatus.value = {
            success: res.data.success,
            message: res.data.success ? "连接成功" : "连接失败: " + res.data.message
        }
    } catch (e) {
        llmStatus.value = { success: false, message: "连接错误" }
    } finally {
        testingLLM.value = false
    }
}

// --- KG Logic ---
const kgForm = ref({ uri: '', user: '', password: '' })
const kgFormRef = ref(null)
const loadingKG = ref(false)
const savingKG = ref(false)
const testingKG = ref(false)
const kgStatus = ref(null)

const kgRules = {
  uri: [{ required: true, message: '请输入 URI', trigger: 'blur' }],
  user: [{ required: true, message: '请输入 Username', trigger: 'blur' }]
}

const loadKGConfig = async () => {
    loadingKG.value = true
    try {
        const res = await axios.get('/api/v1/system/config/kg')
        if (res.data.success) {
            kgForm.value = res.data.config
        }
    } catch (e) {
        ElMessage.error("加载 KG 配置失败")
    } finally {
        loadingKG.value = false
    }
}

const saveKGConfig = async () => {
    if (!kgFormRef.value) return
    await kgFormRef.value.validate(async (valid) => {
        if (valid) {
            savingKG.value = true
            kgStatus.value = null
            try {
                const res = await axios.post('/api/v1/system/config/kg', kgForm.value)
                if (res.data.success) {
                    ElMessage.success(res.data.message)
                }
            } catch (e) {
                ElMessage.error("保存失败: " + e.message)
            } finally {
                savingKG.value = false
            }
        }
    })
}

const testKGConnection = async () => {
    testingKG.value = true
    kgStatus.value = null
    // Pass current form data to test with entered (but unsaved) credentials?
    // Or just test established connection?
    // Let's test with FORM data to verify before save.
    
    // Note: Backend endpoint accepts optional config.
    const configToTest = {
        uri: kgForm.value.uri,
        user: kgForm.value.user,
        password: kgForm.value.password === '***' ? null : kgForm.value.password 
    }
    
    try {
        const res = await axios.post('/api/v1/system/test/kg', configToTest)
        kgStatus.value = {
            success: res.data.success,
            message: res.data.success ? "连接成功" : "连接失败: " + res.data.message
        }
    } catch (e) {
        kgStatus.value = { success: false, message: "连接错误" }
    } finally {
        testingKG.value = false
    }
}

onMounted(() => {
    loadLLMConfig()
    loadKGConfig()
})
</script>

<style scoped>
.config-card {
  height: 100%;
}
.tab-content {
  padding: 20px 0;
  max-width: 800px; /* Keep form readable */
}
.form-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.input-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
}
</style>
