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
    normalizeTerms(terms) {
        return api.post('/terminology/normalize', { terms })
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
    queryPolicy(question) {
        return api.post('/explanation/query', null, {
            params: { question }
        })
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

    // Governance (Data Assets)
    getDataAssets(params = {}) {
        return api.get('/governance/assets', { params })
    },

    getAsset(assetId) {
        return api.get(`/governance/assets/${assetId}`)
    },

    createDataAsset(data) {
        return api.post('/governance/assets', data)
    },

    updateDataAsset(assetId, data) {
        return api.put(`/governance/assets/${assetId}`, data)
    },

    getAssetLineage(assetId) {
        return api.get(`/governance/assets/${assetId}/lineage`)
    },

    getQualityReport() {
        return api.get('/governance/quality/report')
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
