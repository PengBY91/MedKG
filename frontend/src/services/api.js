import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor to add token
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        const url = config.url
        console.log(`[API Request] ${config.method.toUpperCase()} ${url} - Token exists: ${!!token}`)

        if (token) {
            config.headers = config.headers || {}
            config.headers['Authorization'] = `Bearer ${token}`
            console.log(`[API Request] Token attached to ${url}`)
        } else {
            console.warn(`[API Request] Missing token for ${url}`)
        }
        return config
    },
    error => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
    }
)


// Response interceptor to handle auth errors
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            // Only redirect to login if we're not already on the login page
            // and if the request was not to the login endpoint
            const isLoginPage = window.location.pathname === '/login'
            const isLoginRequest = error.config?.url?.includes('/auth/login')

            if (!isLoginPage && !isLoginRequest) {
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export default {
    // Auth
    login(username, password) {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },

    getCurrentUser() {
        return api.get('/auth/me')
    },

    // Policies
    uploadPolicy(file) {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/policies/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    getPolicies(params) {
        return api.get('/policies', { params })
    },

    getPolicyStatistics() {
        return api.get('/policies/statistics')
    },

    getPolicy(id) {
        return api.get(`/policies/${id}`)
    },

    downloadPolicy(id) {
        return api.get(`/policies/${id}/download`, { responseType: 'blob' })
    },

    updatePolicy(id, data) {
        return api.put(`/policies/${id}`, data)
    },

    deletePolicy(id) {
        return api.delete(`/policies/${id}`)
    },

    // Ingestion
    uploadDocument(file) {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/ingest/document', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    getUploadHistory(params = {}) {
        return api.get('/ingest/history', { params })
    },

    getUploadDetail(uploadId) {
        return api.get(`/ingest/history/${uploadId}`)
    },

    deleteUpload(uploadId) {
        return api.delete(`/ingest/history/${uploadId}`)
    },

    // Terminology
    normalizeTerms(terms, method = 'hybrid') {
        return api.post(`/terminology/normalize?method=${method}`, { terms })
    },

    getTerminology() {
        return api.get('/terminology')
    },

    deleteTerminology(term) {
        return api.delete(`/terminology/${term}`)
    },

    uploadTerms(file) {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/terminology/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    submitFeedback(data) {
        return api.post('/terminology/feedback', data)
    },

    extractNlp(text) {
        return api.post('/terminology/nlp/extract', { text })
    },


    // Rules
    compileRule(policyText) {
        return api.post('/rules/compile', { policy_text: policyText })
    },

    testRule(shaclContent, testDataset = 'last_month_patients') {
        return api.post('/rules/test', {
            shacl_content: shaclContent,
            test_dataset: testDataset
        })
    },

    getRules() {
        return api.get('/rules')
    },

    deleteRule(id) {
        return api.delete(`/rules/${id}`)
    },

    saveRule(ruleData) {
        return api.post('/rules', ruleData)
    },

    // Explanation
    // Explanation Query (Multi-turn conversation support)
    queryPolicy(question, sessionId = null) {
        return api.post('/explanation/query', {
            question,
            session_id: sessionId,
            use_history: true
        })
    },

    // Streaming Query (实时流式问答)
    async queryPolicyStream(question, sessionId = null, callbacks = {}) {
        const {
            onThinking,       // 思考过程片段
            onThinkingDone,   // 思考完成
            onAnswerStart,    // 答案开始
            onChunk,          // 答案片段
            onMetadata,       // 元数据
            onDone,           // 完成
            onError           // 错误
        } = callbacks

        const token = localStorage.getItem('token')
        const url = `${API_BASE}/explanation/query-stream`

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    question,
                    session_id: sessionId,
                    use_history: true
                })
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n\n')

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6))

                            if (data.type === 'metadata' && onMetadata) {
                                onMetadata(data.data)
                            } else if (data.type === 'thinking_start') {
                                // 思考开始（可用于UI状态切换）
                            } else if (data.type === 'thinking' && onThinking) {
                                onThinking(data.content)
                            } else if (data.type === 'thinking_done' && onThinkingDone) {
                                onThinkingDone()
                            } else if (data.type === 'answer_start' && onAnswerStart) {
                                onAnswerStart()
                            } else if (data.type === 'chunk' && onChunk) {
                                onChunk(data.content)
                            } else if (data.type === 'done' && onDone) {
                                onDone(data)
                            } else if (data.type === 'error' && onError) {
                                onError(new Error(data.error))
                            }
                        } catch (e) {
                            console.error('Failed to parse SSE data:', e)
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Stream query failed:', error)
            if (onError) onError(error)
        }
    },

    // Conversations Management
    createConversation(title = '新对话') {
        return api.post('/conversations/conversations', { title })
    },

    listConversations(limit = 50, offset = 0) {
        return api.get('/conversations/conversations', {
            params: { limit, offset }
        })
    },

    getConversation(sessionId) {
        return api.get(`/conversations/conversations/${sessionId}`)
    },

    getConversationMessages(sessionId, limit = 100) {
        return api.get(`/conversations/conversations/${sessionId}/messages`, {
            params: { limit }
        })
    },

    updateConversation(sessionId, title) {
        return api.put(`/conversations/conversations/${sessionId}`, { title })
    },

    deleteConversation(sessionId) {
        return api.delete(`/conversations/conversations/${sessionId}`)
    },

    clearConversations() {
        return api.delete('/conversations/conversations')
    },

    getWorkflowInstances(params = {}) {
        return api.get('/workflows/instances', { params })
    },

    getWorkflowInstance(id) {
        return api.get(`/workflows/instances/${id}`)
    },

    getUserTasks(params = {}) {
        return api.get('/workflows/tasks', { params })
    },
    completeTask(taskId, taskData) {
        return api.post(`/workflows/tasks/${taskId}/complete`, taskData)
    },

    // Catalog (Data & Knowledge Assets)
    getDataAssets(params = {}) {
        return api.get('/catalog/assets', { params })
    },

    getAsset(assetId) {
        return api.get('/catalog/assets/' + assetId)
    },

    createDataAsset(data) {
        return api.post('/catalog/assets', data)
    },

    updateDataAsset(assetId, data) {
        return api.put('/catalog/assets/' + assetId, data)
    },

    getAssetLineage(assetId) {
        return api.get('/catalog/assets/' + assetId + '/lineage')
    },

    getQualityReport() {
        return api.get('/governance/quality/report')
    },

    // Ontology (Knowledge Graph)
    getOntologyInfo() {
        return api.get('/catalog/ontology')
    },

    importOntologyData(file, clearExisting = false) {
        const formData = new FormData()
        formData.append('file', file)
        return api.post(`/catalog/ontology/import?clear_existing=${clearExisting}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    getGraphStats() {
        return api.get('/catalog/ontology/graph/stats')
    },

    getGraphTree() {
        return api.get('/catalog/ontology/graph/tree')
    },

    // Governance (Reviews)
    getPendingReviews() {
        return api.get('/governance/reviews/pending')
    },

    submitReviewDecision(taskId, decision, data) {
        return api.post(`/governance/reviews/${taskId}/decision`, {
            decision,
            corrected_data: data
        })
    },

    // Governance (Quality & Catalog) [NEW]
    runQualityCheck(assetId, data) {
        return api.post(`/governance/assets/${assetId}/quality-check`, data)
    },

    addQualityRule(ruleData) {
        return api.post('/governance/quality/rules', ruleData)
    },

    scanCatalog(connectionInfo) {
        return api.post('/catalog/scan', connectionInfo)
    },

    // Users
    getUsers(params = {}) {
        return api.get('/users', { params })
    },

    getUser(userId) {
        return api.get(`/users/${userId}`)
    },

    createUser(userData) {
        return api.post('/users', userData)
    },

    updateUser(userId, userData) {
        return api.put(`/users/${userId}`, userData)
    },

    deleteUser(userId) {
        return api.delete(`/users/${userId}`)
    },

    getUserStats(userId) {
        return api.get(`/users/${userId}/stats`)
    },

    // Tenants
    getTenants(params = {}) {
        return api.get('/tenants', { params })
    },

    getTenant(tenantId) {
        return api.get(`/tenants/${tenantId}`)
    },

    getTenantByCode(code) {
        return api.get(`/tenants/code/${code}`)
    },

    createTenant(tenantData) {
        return api.post('/tenants', tenantData)
    },

    updateTenant(tenantId, tenantData) {
        return api.put(`/tenants/${tenantId}`, tenantData)
    },

    deleteTenant(tenantId) {
        return api.delete(`/tenants/${tenantId}`)
    },

    getTenantStats(tenantId) {
        return api.get(`/tenants/${tenantId}/stats`)
    }
}
