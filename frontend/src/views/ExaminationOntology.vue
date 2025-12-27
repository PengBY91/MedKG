<template>
  <div class="kg-dashboard">
    <el-container class="dashboard-container">
      <!-- Left Sidebar: Control & Schema -->
      <el-aside width="320px" class="sidebar">
        <div class="sidebar-header">
          <div class="logo-area">
            <el-icon :size="24" color="#409eff"><Connection /></el-icon>
            <span class="app-title">图谱探索</span>
          </div>
          <div class="db-selector">
            <el-select 
              v-model="currentDb" 
              placeholder="Select Database" 
              class="db-select-input"
              @change="handleDbChange"
            >
              <template #prefix><el-icon><DataAnalysis /></el-icon></template>
              <el-option v-for="db in databases" :key="db" :label="formatDbName(db)" :value="db">
                <span style="float: left">{{ formatDbName(db) }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ db }}</span>
              </el-option>
            </el-select>
          </div>
        </div>

        <el-scrollbar class="sidebar-scroll">
          <div class="stats-section">
            <div class="section-title">
              <el-icon><Coin /></el-icon> 数据概览 (Statistics)
            </div>
            
            <div v-if="loadingStats" class="loading-state">
              <el-skeleton :rows="3" animated />
            </div>
            
            <div v-else class="stats-list">
              <!-- Node Labels -->
              <div class="stat-group">
                <div class="group-header">Node Labels</div>
                <div 
                  v-for="(stat, idx) in stats.labels" 
                  :key="stat.label"
                  class="stat-item"
                  :class="{ active: selectedLabel === stat.label }"
                  @click="selectLabel(stat.label)"
                >
                  <div class="stat-label">
                    <span class="dot" :style="{ background: getColor(stat.label) }"></span>
                    {{ stat.label }}
                  </div>
                  <el-tag size="small" effect="plain" round>{{ formatNumber(stat.count) }}</el-tag>
                </div>
              </div>

              <!-- Relationships -->
              <div class="stat-group" v-if="stats.relationships.length > 0">
                <div class="group-header">Relationships</div>
                <div v-for="rel in stats.relationships" :key="rel.type" class="stat-item rel-item">
                  <div class="stat-label">
                    <el-icon><ArrowRight /></el-icon>
                    {{ rel.type }}
                  </div>
                  <span class="count-text">{{ formatNumber(rel.count) }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </el-aside>

      <!-- Main Content Area -->
      <el-main class="main-canvas">
        <div class="canvas-header">
          <!-- Search Bar -->
          <div class="search-bar" :class="{ 'cypher-mode': searchMode === 'cypher' }">
            <div class="mode-switch">
              <el-tooltip content="Switch Search Mode" placement="bottom">
                <el-switch
                  v-model="searchMode"
                  active-value="cypher"
                  inactive-value="simple"
                  active-text="Cypher"
                  inactive-text="Visual"
                  inline-prompt
                  style="--el-switch-on-color: #e6a23c; --el-switch-off-color: #409eff"
                />
              </el-tooltip>
            </div>

            <div class="input-area">
              <template v-if="searchMode === 'simple'">
                <el-tag 
                  v-if="selectedLabel" 
                  closable 
                  @close="selectedLabel = ''"
                  class="filter-tag"
                  :style="{ color: getColor(selectedLabel), borderColor: getColor(selectedLabel) }"
                >
                  {{ selectedLabel }}
                </el-tag>
                <el-input
                  v-model="searchQuery"
                  placeholder="Search by name, property or ID..."
                  @keyup.enter="performSearch"
                  clearable
                >
                  <template #prefix><el-icon><Search /></el-icon></template>
                </el-input>
              </template>
              <template v-else>
                <el-input
                  v-model="cypherQuery"
                  placeholder="MATCH (n) RETURN n LIMIT 25"
                  class="cypher-input"
                  @keyup.enter="performSearch"
                >
                  <template #prefix><el-icon><Monitor /></el-icon></template>
                </el-input>
              </template>
            </div>
            
            <el-button type="primary" circle :icon="Search" @click="performSearch" :loading="loadingGraph" />
          </div>

          <!-- Toolbar -->
          <div class="header-tools">
            <el-tooltip content="Refresh Layout"><el-button circle :icon="Refresh" @click="renderGraph" /></el-tooltip>
            <el-tooltip content="Fit View"><el-button circle :icon="FullScreen" @click="resetZoom" /></el-tooltip>
          </div>
        </div>

        <!-- Graph Container -->
        <div class="graph-wrapper" v-loading="loadingGraph" element-loading-text="Querying Graph...">
          <div ref="graphContainer" class="echarts-container"></div>
          
          <div class="empty-placeholder" v-if="!loadingGraph && graphData.nodes.length === 0">
            <el-empty description="No Data Found">
               <el-button type="primary" plain @click="loadInitialSample">Load Sample Data</el-button>
            </el-empty>
          </div>


        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  Connection, DataAnalysis, Coin, ArrowRight, Search, Monitor, 
  Refresh, FullScreen, Close, ZoomIn 
} from '@element-plus/icons-vue'

// --- State ---
const databases = ref([])
const currentDb = ref('neo4j')
const loadingStats = ref(false)
const stats = reactive({ labels: [], relationships: [] })

const searchMode = ref('simple') // 'simple' | 'cypher'
const selectedLabel = ref('')
const searchQuery = ref('')
const cypherQuery = ref('')

const loadingGraph = ref(false)
const graphData = ref({ nodes: [], links: [] })
const selectedNode = ref(null)

// --- Visualization ---
const graphContainer = ref(null)
let chartInstance = null
const colorPalette = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', 
  '#909399', '#9C27B0', '#009688', '#FF5722'
]
const labelColorMap = reactive({})

// --- Lifecycle ---
onMounted(async () => {
  await loadDatabases()
  await loadStats()
  loadInitialSample()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// --- Control Logic ---
const loadDatabases = async () => {
  try {
    const res = await axios.get('/api/v1/graph/databases')
    if (res.data.success) {
        databases.value = res.data.databases
        if(databases.value.length > 0 && !databases.value.includes(currentDb.value)) {
            currentDb.value = databases.value[0]
        }
    }
  } catch (e) {
    ElMessage.error('Failed to load databases')
  }
}

const formatDbName = (name) => {
    return name === 'neo4j' ? 'Default DB (neo4j)' : name === 'system' ? 'System DB' : name
}

const handleDbChange = () => {
    selectedLabel.value = ''
    searchQuery.value = ''
    cypherQuery.value = ''
    selectedNode.value = null
    graphData.value = { nodes: [], links: [] }
    expandedNodeIds.value.clear()
    loadStats()
    loadInitialSample()
}

const loadStats = async () => {
    loadingStats.value = true
    try {
        const res = await axios.get('/api/v1/graph/stats', { params: { database: currentDb.value } })
        if (res.data.success) {
            stats.labels = res.data.labels
            stats.relationships = res.data.relationships
            assignColors(stats.labels.map(l => l.label))
        }
    } catch (e) {
        ElMessage.warning('Could not fetch graph statistics')
    } finally {
        loadingStats.value = false
    }
}

const selectLabel = (label) => {
    selectedLabel.value = selectedLabel.value === label ? '' : label
    performSearch()
}

const loadInitialSample = () => {
    searchMode.value = 'simple'
    searchQuery.value = ''
    selectedLabel.value = ''
    performSearch()
}

// --- Search & Graph ---
const performSearch = async () => {
    loadingGraph.value = true
    selectedNode.value = null
    
    try {
        let payload = { database: currentDb.value, limit: 100 }
        
        if (searchMode.value === 'cypher') {
             // For now, search endpoint doesn't support raw cypher directly in this refactor plan yet.
             // But we can simulate it via query param if backend supported it or fallback to simple.
             // Reviewing backend `search_graph`: it handles label/query.
             // Backend doesn't have a direct /query endpoint in the file I saw earlier.
             // I will implement a client-side warning or basic mapping.
             ElMessage.warning('Custom Cypher execution requires backend support update. Performing simple search instead.')
             searchMode.value = 'simple'
             // Fallback
             payload.query = cypherQuery.value
        } else {
             payload.label = selectedLabel.value
             payload.query = searchQuery.value
        }

        const res = await axios.post('/api/v1/graph/search', payload)
        if (res.data.success) {
             const nodes = res.data.nodes.map(formatNode)
             // Initially just nodes, links need expansion or separate query.
             // Explorer usually starts with nodes.
             graphData.value = { nodes, links: [] }
             renderGraph()
        }
    } catch (e) {
        ElMessage.error('Search failed')
    } finally {
        loadingGraph.value = false
    }
}

const expandedNodeIds = ref(new Set())

const handleNodeClick = (node) => {
    selectedNode.value = node
    if (expandedNodeIds.value.has(node.id)) {
        collapseNode(node)
    } else {
        expandNode(node)
    }
}

const expandNode = async (node) => {
    try {
        const res = await axios.post('/api/v1/graph/expand', { 
            database: currentDb.value, 
            node_id: node.id 
        })
        if (res.data.success) {
            // Merge
            const newNodes = res.data.nodes.map(formatNode)
            const newLinks = res.data.links.map(formatLink)
            
            // Deduplicate Nodes
            const nodeIds = new Set(graphData.value.nodes.map(n => n.id))
            newNodes.forEach(n => {
                if(!nodeIds.has(n.id)) {
                    graphData.value.nodes.push(n)
                    nodeIds.add(n.id)
                }
            })
            
            // Deduplicate Links
            const linkIds = new Set(graphData.value.links.map(l => l.id))
            newLinks.forEach(l => {
                if(!linkIds.has(l.id)) {
                    graphData.value.links.push(l)
                    linkIds.add(l.id)
                }
            })
            
            expandedNodeIds.value.add(node.id)
            renderGraph()
            
            if (newNodes.length > 0) {
                 ElMessage.success(`Expanded ${newNodes.length} neighbors`)
            } else {
                 ElMessage.info('No new neighbors found')
            }
        }
    } catch (e) {
        ElMessage.error('Expansion failed: ' + (e.response?.data?.error || e.message))
    }
}

const collapseNode = (node) => {
    // 1. Find links connected to this node where this node is the source/target
    // AND the other end is NOT connected to anything else in the current view?
    // Simplified Collapse: Remove all links connected to this node that were likely added by expansion?
    // Hard to track exactly which.
    // Standard approach: Remove all links connected to `node` (except those connecting to other visible roots?)
    // Better heuristic: Remove links connected to `node`. Then remove nodes that have degree 0.
    
    // BUT: If a link connects `node` <-> `root`, we shouldn't remove it if `root` is the main anchor.
    // Actually, "Collapse" usually means undoing the expansion.
    // Let's remove all links incident to `node`.
    // Wait, that would isolate `node` itself!
    // We should remove links where `node` is one end, AND the other end is not supported by other links?
    
    // Let's iterate links.
    const nodeId = node.id
    
    // Identify neighbors to potentially remove
    const neighbors = new Set()
    graphData.value.links.forEach(l => {
        if (l.source === nodeId) neighbors.add(l.target)
        if (l.target === nodeId) neighbors.add(l.source)
    })
    
    // Remove links connected to this node
    // BE CAREFUL: Do we remove ALL links? If I expanded A->B, then expanded B->C.
    // Collapsing A should remove A->B. B might become isolated if B has no other links?
    // If I collapse A, I want to hide B (if B is only connected to A).
    // But what if B is connected to C? C will also become isolated if B is removed.
    // Recursive collapse? Or just 1-hop?
    // "Toggle" implies 1-hop collapse usually.
    
    // Simple implementation:
    // Remove all links connected to `node`. (This might be too aggressive if graph is cyclic or highly connected).
    // Let's try: Remove all links incident to `node` EXCEPT those that existed before? We don't track history.
    
    // Alternative: Just remove the links. Then remove isolated nodes EXCEPT `node` itself.
    // We must keep `node` itself visible.
    
    const oldLinks = graphData.value.links
    const newLinks = oldLinks.filter(l => l.source !== nodeId && l.target !== nodeId)
    
    // Check isolation
    // Calculate degree of all nodes based on NEW links
    const degrees = new Map()
    graphData.value.nodes.forEach(n => degrees.set(n.id, 0))
    
    newLinks.forEach(l => {
        degrees.set(l.source, (degrees.get(l.source) || 0) + 1)
        degrees.set(l.target, (degrees.get(l.target) || 0) + 1)
    })
    
    // Keep nodes with degree > 0 OR the current node (don't remove self) OR nodes that were "roots" (search results)?
    // We don't rigidly track roots.
    // But we MUST keep `node`.
    degrees.set(nodeId, 999) 
    
    // Also, we should probably keep nodes that were originally loaded (search results)? 
    // Risky to delete them.
    // For now, let's just remove nodes that have degree 0.
    
    const newNodes = graphData.value.nodes.filter(n => (degrees.get(n.id) || 0) > 0)
    
    // Update
    // Wait! This removes the link that connected `node` to its parent!
    // If I expanded Root->A. Now I click A.
    // I want to collapse A's children (A->B, A->C).
    // I do NOT want to remove Root->A.
    // So I should only remove links where `node` is source? Or how do I know direction?
    // Neo4j relationships are directed. But user navigation might be "upstream".
    
    // REVISED STRATEGY: 
    // Only remove links that were NOT present when `node` was first loaded? Too complex.
    // User request: "Click again to collapse".
    // Maybe just remove ALL neighbors that are Leaf Nodes connected to `node`?
    // i.e., Remove (Node->Neighbor) if Neighbor has degree 1 (only connected to Node).
    
    const linksToRemove = []
    const nodesToRemove = new Set()
    
    // Re-calculate degrees including all current links
    const currentDegrees = new Map()
    graphData.value.links.forEach(l => {
        currentDegrees.set(l.source, (currentDegrees.get(l.source) || 0) + 1)
        currentDegrees.set(l.target, (currentDegrees.get(l.target) || 0) + 1)
    })
    
    // Find neighbors of `node`
    const adjacentLinks = graphData.value.links.filter(l => l.source === nodeId || l.target === nodeId)
    
    adjacentLinks.forEach(l => {
        const neighborId = l.source === nodeId ? l.target : l.source
        // If neighbor is a leaf (degree 1), it effectively "belongs" to this expansion (or is a dead end).
        // If degree > 1, it's connected to something else, so we keep it.
        if (currentDegrees.get(neighborId) === 1) {
            linksToRemove.push(l)
            nodesToRemove.add(neighborId)
        }
    })
    
    if (nodesToRemove.size === 0 && adjacentLinks.length > 0) {
        // This happens if I expanded, but all neighbors are connected to others?
        // Or maybe I want to force remove them?
        // Let's stick to safe "Leaf Styling Removal" for now.
        // If user wants to "Hide" a highly connected node, that's different.
        ElMessage.warning('Cannot collapse: all neighbors are connected to other nodes')
        return
    }
    
    graphData.value.links = graphData.value.links.filter(l => !linksToRemove.includes(l))
    graphData.value.nodes = graphData.value.nodes.filter(n => !nodesToRemove.has(n.id))
    
    expandedNodeIds.value.delete(nodeId)
    renderGraph()
    ElMessage.success(`Collapsed ${nodesToRemove.size} nodes`)
}

// --- Echarts ---
const assignColors = (labels) => {
    labels.forEach((l, idx) => {
        if(!labelColorMap[l]) labelColorMap[l] = colorPalette[idx % colorPalette.length]
    })
}

const getColor = (label) => labelColorMap[label] || '#909399'

const formatNode = (n) => ({
    id: String(n.id),
    name: n.properties.name || n.properties.title || n.properties.code || String(n.id),
    value: n.labels.join(', '),
    symbolSize: 24,
    itemStyle: { color: getColor(n.labels[0]) },
    labels: n.labels,
    properties: n.properties
})

const formatLink = (l) => ({
    id: `${l.source}-${l.target}-${l.type}`,
    source: String(l.source),
    target: String(l.target),
    value: l.type
})

const renderGraph = () => {
    if (!graphContainer.value) return
    if (!chartInstance) {
        chartInstance = echarts.init(graphContainer.value)
        chartInstance.on('click', (params) => {
            if (params.dataType === 'node') {
                handleNodeClick(params.data)
            }
        })
    }
    
    const options = {
        tooltip: {
            trigger: 'item',
            formatter: (p) => {
                if(p.dataType === 'node') {
                    return `<strong>${p.data.name}</strong><br/>${p.data.labels.join(', ')}`
                }
                return p.data.value
            }
        },
        series: [{
            type: 'graph',
            layout: 'force',
            draggable: true, // Enable dragging
            data: graphData.value.nodes,
            links: graphData.value.links,
            roam: true,
            label: {
                show: true,
                position: 'bottom',
                fontSize: 12,
                color: '#606266'
            },
            force: {
                repulsion: 300,        
                edgeLength: [60, 150],
                gravity: 0.1,
                friction: 0.2          
            },
            lineStyle: {
                color: '#DCDFE6',
                curveness: 0.1,
                width: 2
            },
            emphasis: {
                focus: 'adjacency',
                lineStyle: { width: 4 }
            }
        }]
    }
    chartInstance.setOption(options)
}

const resetZoom = () => {
    chartInstance?.dispatchAction({ type: 'restore' })
}

const handleResize = () => chartInstance?.resize()
const formatNumber = (num) => num ? num.toLocaleString() : '0'

</script>

<style scoped>
.kg-dashboard {
  height: calc(100vh - 80px); /* Adjust for app header */
  background: #f0f2f5;
  overflow: hidden;
}

.dashboard-container {
  height: 100%;
}

/* Sidebar */
.sidebar {
  background: white;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(to bottom, #fff, #fafafa);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.db-selector {
  width: 100%;
}

.db-select-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
}

.sidebar-scroll {
  flex: 1;
}

.stats-section {
  padding: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-group {
  margin-bottom: 25px;
}

.group-header {
  font-size: 12px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.stat-item:hover {
  background: #f5f7fa;
}

.stat-item.active {
  background: #ecf5ff;
  border-color: #d9ecff;
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.rel-item {
  pointer-events: none; /* Rels are just for display now */
}

/* Main Area */
.main-canvas {
  padding: 0;
  display: flex;
  flex-direction: column;
  position: relative;
}

.canvas-header {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 20px;
}

.search-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
  max-width: 800px;
  background: #f4f6f9;
  padding: 6px 12px;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.search-bar.cypher-mode {
  background: #fff8e6;
  border: 1px solid #faecd8;
}

.input-area {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-tag {
  border-radius: 4px;
}

.search-bar :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent !important;
}

.cypher-input :deep(.el-input__inner) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.graph-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #fafafa;
}

.echarts-container {
  width: 100%;
  height: 100%;
}

.empty-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* Details Panel */
.details-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 340px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 40px);
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header .title {
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot-lg {
  width: 12px;
  height: 12px;
  border-radius: 4px;
}

.panel-body {
  padding: 20px;
  overflow-y: auto;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.detail-item .value {
  font-size: 14px;
  color: #303133;
  word-break: break-all;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.props-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prop-item {
  background: #f9fafc;
  padding: 10px;
  border-radius: 8px;
  font-size: 13px;
}

.prop-key {
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
  display: block;
}

.prop-val {
  color: #303133;
  line-height: 1.5;
}

.panel-footer {
  margin-top: 24px;
}

/* Animations */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
