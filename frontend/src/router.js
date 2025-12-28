import { createRouter, createWebHistory } from 'vue-router'
import PolicyUpload from './views/PolicyUpload.vue'
import RuleReview from './views/RuleReview.vue'
import TerminologyWorkbench from './views/TerminologyWorkbench.vue'
import ExplanationQuery from './views/ExplanationQuery.vue'
import ExplanationQueryEnhanced from './views/ExplanationQueryEnhanced.vue'
import UserManagement from './views/UserManagement.vue'
import TenantManagement from './views/TenantManagement.vue'
import TaskWorkbench from './views/TaskWorkbench.vue'
import DataCatalog from './views/DataCatalog.vue'
import GovernancePipeline from './views/GovernancePipeline.vue'
import ExaminationStandardization from './views/ExaminationStandardization.vue'
import ExaminationOntology from './views/ExaminationOntology.vue'
import SystemConfig from './views/SystemConfig.vue'
import Login from './views/Login.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        redirect: '/tasks'
    },
    {
        path: '/pipeline',
        name: 'GovernancePipeline',
        component: GovernancePipeline
    },
    {
        path: '/upload',
        name: 'PolicyUpload',
        component: PolicyUpload
    },
    {
        path: '/rules',
        name: 'RuleReview',
        component: RuleReview
    },
    {
        path: '/terminology',
        name: 'TerminologyWorkbench',
        component: TerminologyWorkbench
    },
    {
        path: '/explanation',
        name: 'ExplanationQuery',
        component: ExplanationQueryEnhanced  // 使用增强版组件
    },
    {
        path: '/explanation-legacy',  // 保留旧版本
        name: 'ExplanationQueryLegacy',
        component: ExplanationQuery
    },
    {
        path: '/users',
        name: 'UserManagement',
        component: UserManagement
    },
    {
        path: '/tenants',
        name: 'TenantManagement',
        component: TenantManagement
    },
    {
        path: '/tasks',
        name: 'TaskWorkbench',
        component: TaskWorkbench
    },
    {
        path: '/examination',
        name: 'ExaminationStandardization',
        component: ExaminationStandardization,
        meta: { requiresAuth: true }
    },
    {
        path: '/examination/ontology',
        name: 'ExaminationOntology',
        component: ExaminationOntology,
        meta: { requiresAuth: true }
    },
    {
        path: '/catalog',
        name: 'DataCatalog',
        component: DataCatalog
    },
    {
        path: '/system-config',
        name: 'SystemConfig',
        component: SystemConfig,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const requiresAuth = to.meta.requiresAuth !== false

    if (requiresAuth && !token) {
        next('/login')
    } else if (to.path === '/login' && token) {
        next('/tasks')
    } else {
        next()
    }
})

export default router
