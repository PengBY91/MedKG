<template>
  <el-card class="page-card">
    <template #header>
      <div class="card-header">
        <span>租户管理</span>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增租户
        </el-button>
      </div>
    </template>

    <!-- Tenant Table -->
    <el-table :data="tenants" v-loading="loading" border style="width: 100%">
      <el-table-column prop="name" label="租户名称" min-width="200" />
      <el-table-column prop="code" label="租户编码" width="150" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="scope">
          <el-tag :type="getTypeColor(scope.row.type)">
            {{ getTypeLabel(scope.row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
            {{ scope.row.status === 'active' ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="scope">
          <el-button size="small" @click="viewStats(scope.row)">统计</el-button>
          <el-button size="small" @click="showEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增租户' : '编辑租户'"
      width="600px"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="租户编码" prop="code">
          <el-input v-model="formData.code" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="formData.type" style="width: 100%">
            <el-option label="医院" value="hospital" />
            <el-option label="保险公司" value="insurance" />
            <el-option label="监管机构" value="regulator" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status" v-if="dialogMode === 'edit'">
          <el-radio-group v-model="formData.status">
            <el-radio label="active">激活</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="配置" prop="config">
          <el-input
            v-model="configJson"
            type="textarea"
            :rows="6"
            placeholder='{"max_users": 100, "features": ["terminology", "rules"]}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Stats Dialog -->
    <el-dialog v-model="statsVisible" title="租户统计" width="600px">
      <el-descriptions v-if="currentStats" :column="2" border>
        <el-descriptions-item label="总用户数">{{ currentStats.total_users }}</el-descriptions-item>
        <el-descriptions-item label="活跃用户">{{ currentStats.active_users }}</el-descriptions-item>
        <el-descriptions-item label="文档数">{{ currentStats.total_documents }}</el-descriptions-item>
        <el-descriptions-item label="规则数">{{ currentStats.total_rules }}</el-descriptions-item>
        <el-descriptions-item label="术语数">{{ currentStats.total_terms }}</el-descriptions-item>
        <el-descriptions-item label="存储使用">{{ currentStats.storage_used_gb }} GB</el-descriptions-item>
        <el-descriptions-item label="今日API调用" :span="2">{{ currentStats.api_calls_today }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../services/api'

const loading = ref(false)
const tenants = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)
const formRef = ref(null)
const statsVisible = ref(false)
const currentStats = ref(null)

const formData = reactive({
  name: '',
  code: '',
  type: 'hospital',
  status: 'active',
  config: {}
})

const configJson = ref('')

const formRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入租户编码', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const loadTenants = async () => {
  loading.value = true
  try {
    const response = await api.getTenants()
    tenants.value = response.data
  } catch (error) {
    ElMessage.error('加载租户列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  Object.assign(formData, {
    name: '',
    code: '',
    type: 'hospital',
    status: 'active',
    config: {}
  })
  configJson.value = '{}'
  dialogVisible.value = true
}

const showEditDialog = (tenant) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: tenant.id,
    name: tenant.name,
    code: tenant.code,
    type: tenant.type,
    status: tenant.status,
    config: tenant.config
  })
  configJson.value = JSON.stringify(tenant.config, null, 2)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  // Parse config JSON
  try {
    formData.config = JSON.parse(configJson.value || '{}')
  } catch (e) {
    ElMessage.error('配置JSON格式错误')
    return
  }

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await api.createTenant(formData)
      ElMessage.success('租户创建成功')
    } else {
      await api.updateTenant(formData.id, formData)
      ElMessage.success('租户更新成功')
    }
    dialogVisible.value = false
    loadTenants()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (tenant) => {
  try {
    await ElMessageBox.confirm(`确定要删除租户 "${tenant.name}" 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.deleteTenant(tenant.id)
    ElMessage.success('租户删除成功')
    loadTenants()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const viewStats = async (tenant) => {
  try {
    const response = await api.getTenantStats(tenant.id)
    currentStats.value = response.data
    statsVisible.value = true
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

const getTypeColor = (type) => {
  const colors = {
    hospital: 'primary',
    insurance: 'success',
    regulator: 'warning'
  }
  return colors[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    hospital: '医院',
    insurance: '保险公司',
    regulator: '监管机构'
  }
  return labels[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTenants()
})
</script>

<style scoped>
.page-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
