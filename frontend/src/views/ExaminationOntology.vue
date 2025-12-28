<template>
  <div class="kg-dashboard">
    <el-container class="dashboard-container">
      <!-- Left Sidebar: Control & Schema -->
      <el-aside width="320px" class="sidebar">
        <div class="sidebar-header">
          <div class="logo-area">
            <el-icon :size="24" color="#409eff"><Connection /></el-icon>
            <span class="app-title">图谱探索 (Cytoscape)</span>
          </div>
          <div class="db-selector">
            <el-select 
              v-model="currentDb" 
              placeholder="Select Database" 
              class="db-select-input"
              @change="handleDbChange"
            >
              <template #prefix><el-icon><DataAnalysis /></el-icon></template>
              <el-option v-for="db in dbRegistry" :key="db" :label="formatDbName(db)" :value="db">
                <span style="float: left">{{ formatDbName(db) }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ db }}</span>
              </el-option>
            </el-select>
          </div>
        </div>

        <el-scrollbar class="sidebar-scroll">
          <div class="stats-section">
            <div class="section-title">
              <el-icon><Coin /></el-icon> 数据概览
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
                  :class="{ active: filterLabel === stat.label }"
                  @click="toggleLabelFilter(stat.label)"
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
            <!-- Layout Controls -->
            <div class="tool-group">
                <el-radio-group v-model="currentLayout" size="small" @change="runLayout">
                    <el-radio-button label="fcose">快速力导向 (Fast Force)</el-radio-button>
                    <el-radio-button label="cola">平滑物理 (Smooth Physics)</el-radio-button>
                    <el-radio-button label="concentric">同心圆 (Concentric)</el-radio-button>

                </el-radio-group>
            </div>

            <div class="search-bar">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索节点..."
                  @keyup.enter="performSearch"
                  clearable
                >
                  <template #prefix><el-icon><Search /></el-icon></template>
                </el-input>
                <el-button type="primary" circle :icon="Search" @click="performSearch" :loading="loadingGraph" />
            </div>

            <!-- Toolbar -->
            <div class="header-tools">
              <el-tooltip content="Refresh Layout"><el-button circle :icon="Refresh" @click="runLayout" /></el-tooltip>
              <el-tooltip content="Fit View"><el-button circle :icon="FullScreen" @click="fitView" /></el-tooltip>
            </div>
        </div>

        <!-- Graph Container -->
        <div class="graph-wrapper" v-loading="loadingGraph" element-loading-text="Querying Graph...">
          <div id="cy" class="cy-container"></div>
          
          <div class="empty-placeholder" v-if="!loadingGraph && isEmptyGraph">
            <el-empty description="暂无数据">
               <el-button type="primary" plain @click="loadInitialSample">加载示例数据</el-button>
            </el-empty>
          </div>

          <!-- Hover Tooltip / Detail Panel -->
          <transition name="fade">
              <div v-if="selectedNode" class="details-panel">
                  <div class="panel-header">
                      <div class="title">
                          <span class="dot-lg" :style="{ background: getColor(selectedNode.labels[0]) }"></span>
                          {{ selectedNode.name }}
                      </div>
                      <el-button link :icon="Close" @click="selectedNode = null" />
                  </div>
                  <div class="panel-body">
                      <div class="detail-item">
                          <span class="label">ID</span>
                          <div class="value">{{ selectedNode.id }}</div>
                      </div>
                      <div class="detail-item">
                          <span class="label">Labels</span>
                          <div class="value tags">
                              <el-tag v-for="l in selectedNode.labels" :key="l" size="small">{{ l }}</el-tag>
                          </div>
                      </div>
                      <el-divider v-if="Object.keys(selectedNode.properties).length > 0">Properties</el-divider>
                      <div class="detail-item" v-for="(val, key) in selectedNode.properties" :key="key">
                          <span class="label">{{ key }}</span>
                          <div class="value">{{ val }}</div>
                      </div>
                      <div class="panel-actions" style="margin-top: 20px;">
                          <el-button type="primary" size="small" @click="expandNode(selectedNode.rawNode)" :loading="expanding">展开邻居 (Expand)</el-button>
                          <el-button type="warning" size="small" @click="collapseNode(selectedNode.rawNode)">折叠 (Collapse)</el-button>
                      </div>
                  </div>
              </div>
          </transition>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'

import cola from 'cytoscape-cola'
import { 
  Connection, DataAnalysis, Coin, ArrowRight, Search, 
  Refresh, FullScreen, Close 
} from '@element-plus/icons-vue'

// Register Extensions
cytoscape.use(fcose)

cytoscape.use(cola)



// --- State ---
const dbRegistry = ref([])
const currentDb = ref('neo4j')
const loadingStats = ref(false)
const stats = reactive({ labels: [], relationships: [] })

const filterLabel = ref('')
const searchQuery = ref('')
const currentLayout = ref('fcose')

const loadingGraph = ref(false)
const isEmptyGraph = ref(true)
const selectedNode = ref(null)
const expanding = ref(false)

// Cytoscape Instance
let cy = null
const expandedNodeIds = new Set()

// Color Palette
const colorPalette = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', 
  '#909399', '#9C27B0', '#009688', '#FF5722', '#2196F3', '#E91E63'
]
const labelColorMap = reactive({})

// --- Lifecycle ---
onMounted(async () => {
  initCytoscape()
  await loadDatabases()
  await loadStats()
  window.addEventListener('resize', handleResize)
  loadInitialSample()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (cy) cy.destroy()
})

// --- Control Logic ---
const loadDatabases = async () => {
  try {
    const res = await axios.get('/api/v1/graph/databases')
    if (res.data.success) {
        dbRegistry.value = res.data.databases
        if(dbRegistry.value.length > 0 && !dbRegistry.value.includes(currentDb.value)) {
            currentDb.value = dbRegistry.value[0]
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
    filterLabel.value = ''
    searchQuery.value = ''
    selectedNode.value = null
    expandedNodeIds.clear()
    cy.elements().remove()
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

const toggleLabelFilter = (label) => {
    if (filterLabel.value === label) {
        filterLabel.value = ''
        // Show all
        cy.elements().removeClass('faded')
    } else {
        filterLabel.value = label
        // Fade interaction
        cy.batch(() => {
             cy.elements().removeClass('faded')
             const targets = cy.nodes(`[label = "${label}"]`)
             if (targets.length > 0) {
                 cy.elements().not(targets).addClass('faded')
                 // Also keep edges connecting two filtered nodes?
                 // Or just highlight the nodes.
             }
        })
    }
}

// --- Cytoscape Init ---
const initCytoscape = () => {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            // Core style
            {
                selector: 'node',
                style: {
                    'label': 'data(name)',
                    'width': 30,
                    'height': 30,
                    'background-color': 'data(color)',
                    'color': '#333',
                    'font-size': '10px',
                    'text-valign': 'top',
                    'text-halign': 'center',
                    'text-wrap': 'wrap',
                    'text-max-width': '80px',
                    'border-width': 2,
                    'border-color': '#fff',
                    // Optimization: hide labels on zoom out
                    'min-zoomed-font-size': 8
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#409EFF',
                    'background-color': '#ecf5ff',
                    'text-background-color': 'rgba(255,255,255,0.8)',
                    'text-background-opacity': 1,
                    'z-index': 999
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 0.8,
                    'opacity': 0.8
                    // Label? 'label': 'data(type)'
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'width': 3,
                    'line-color': '#409EFF',
                    'target-arrow-color': '#409EFF'
                }
            },
            // Classes for interactions
            {
                selector: '.faded',
                style: {
                    'opacity': 0.1,
                    'text-opacity': 0
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'border-color': '#E6A23C',
                    'border-width': 4
                }
            },
            {
                selector: '.hovered',
                style: {
                    'overlay-color': '#ccc',
                    'overlay-opacity': 0.2
                }
            }
        ],
        wheelSensitivity: 0.3
    })

    // Event Handlers
    cy.on('tap', 'node', (evt) => {
        const node = evt.target
        handleNodeClick(node)
    })

    cy.on('tap', (evt) => {
        if (evt.target === cy) {
            // Clicked background
            selectedNode.value = null
            cy.elements().removeClass('faded highlighted')
            filterLabel.value = ''
        }
    })

    cy.on('mouseover', 'node', (evt) => {
        document.body.style.cursor = 'pointer'
        // Optional: Highlight neighbors (lightweight)
        // const node = evt.target
        // node.neighborhood().addClass('hover-neighbor')
    })
    
    cy.on('mouseout', 'node', () => {
        document.body.style.cursor = 'default'
    })
}

// --- Graph Logic ---
const loadInitialSample = () => {
    // Just search for "Head" or get random?
    // We'll perform a generic search to get some roots.
    searchQuery.value = ''
    performSearch()
}

const performSearch = async () => {
    loadingGraph.value = true
    selectedNode.value = null
    cy.elements().remove() 
    
    try {
        const payload = { 
            database: currentDb.value, 
            limit: 2000,
            query: searchQuery.value
        }

        const res = await axios.post('/api/v1/graph/search', payload)
        if (res.data.success) {
             const nodes = res.data.nodes.map(n => formatCytoscapeNode(n))
             const links = (res.data.links || []).map(l => formatCytoscapeEdge(l))
             
             if (nodes.length === 0) {
                 isEmptyGraph.value = true
             } else {
                 isEmptyGraph.value = false
                 cy.batch(() => {
                     cy.add(nodes)
                     cy.add(links)
                 })
                 runLayout()
             }
        }
    } catch (e) {
        ElMessage.error('Search failed')
    } finally {
        loadingGraph.value = false
    }
}

const expandNode = async (rawNode) => {
    if (!rawNode) return
    expanding.value = true
    
    try {
        const res = await axios.post('/api/v1/graph/expand', { 
            database: currentDb.value, 
            node_id: rawNode.id 
        })
        
        if (res.data.success) {
            const newNodes = res.data.nodes.map(n => formatCytoscapeNode(n))
            const newEdges = res.data.links.map(l => formatCytoscapeEdge(l))
            
            // Filter existing
            const existingNodeIds = new Set(cy.nodes().map(n => n.id()))
            const existingEdgeIds = new Set(cy.edges().map(e => e.id()))
            
            const nodesToAdd = newNodes.filter(n => !existingNodeIds.has(n.data.id))
            const edgesToAdd = newEdges.filter(e => !existingEdgeIds.has(e.data.id))
            
            if (nodesToAdd.length === 0 && edgesToAdd.length === 0) {
                ElMessage.info('No new neighbors.')
            } else {
                cy.batch(() => {
                    cy.add(nodesToAdd)
                    cy.add(edgesToAdd)
                })
                expandedNodeIds.add(String(rawNode.id))
                
                // Smart Layout: Only layout new elements + source? 
                // Or full layout?
                // For 'fcose', we can just run it on all, or keep others fixed (lock).
                runLayout()
                ElMessage.success(`Expanded ${nodesToAdd.length} nodes`)
            }
        }
    } catch (e) {
        ElMessage.error('Expansion failed')
    } finally {
        expanding.value = false
    }
}

const collapseNode = (rawNode) => {
    // Logic: Remove all leaf neighbors connected to this node
    const nodeId = String(rawNode.id)
    const node = cy.getElementById(nodeId)
    if (node.empty()) return
    
    // Find neighbors that only have degree 1 (connected only to this node)
    const neighbors = node.neighborhood().nodes()
    const leaves = neighbors.filter(n => n.degree(false) === 1)
    
    if (leaves.length > 0) {
        cy.remove(leaves) // Edges automatically removed
        ElMessage.success(`Collapsed ${leaves.length} nodes`)
        expandedNodeIds.delete(nodeId)
    } else {
        ElMessage.warning('No leaf nodes to collapse')
    }
}

const handleNodeClick = (node) => {
    // Focus effect
    cy.batch(() => {
        cy.elements().removeClass('highlighted faded')
        const neighbors = node.neighborhood().add(node)
        cy.elements().not(neighbors).addClass('faded')
        neighbors.addClass('highlighted')
    })

    // Set Details
    selectedNode.value = {
        id: node.id(),
        name: node.data('name'),
        labels: node.data('labels'),
        properties: node.data('properties'),
        rawNode: { id: node.id() },
        color: node.data('color')
    }
    
    // Auto-center (Focus)
    cy.animate({
        center: { eles: node },
        zoom: 1.5,
        duration: 500
    })
}

// --- Layouts ---
const runLayout = () => {
    if (!cy || cy.nodes().length === 0) return
    
    // Stop any running layout
    cy.layout({ name: 'preset' }).stop()
    
    let layoutConfig = {
        animate: true,
        animationDuration: 500,
        fit: true, 
        padding: 50
    }
    
    switch (currentLayout.value) {
        case 'fcose':
            layoutConfig = {
                name: 'fcose',
                quality: 'default',
                randomize: false,
                animationDuration: 1000,
                nodeDimensionsIncludeLabels: true,
                uniformNodeDimensions: false,
                packingEnabled: true,
                nodeRepulsion: 4500,
                idealEdgeLength: 100,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,   
                tilingPaddingVertical: 10,
                tilingPaddingHorizontal: 10,
                ...layoutConfig
            }
            break
        case 'cola':
            layoutConfig = {
                name: 'cola',
                animate: true,
                refresh: 1, 
                maxSimulationTime: 4000,
                ungrabifyWhileSimulating: false,
                fit: true,
                padding: 50,
                nodeSpacing: 20,
                edgeLength: 150, // Making edges longer for cleaner look
                randomize: false, // Keep current positions as starting point if possible
                handleDisconnected: true,
                convergenceThreshold: 0.01,
                // Cola physics
                flow: undefined,
                alignment: undefined,
                ...layoutConfig
            }
            break
        case 'concentric':
             layoutConfig = {
                name: 'concentric',
                concentric: function( node ){
                    // Simple centrality based on degree
                    return node.degree();
                },
                levelWidth: function( nodes ){
                    return 2; // Granularity
                },
                minNodeSpacing: 50,
                ...layoutConfig
            }
            break

    }
    
    // Run layout
    const layout = cy.layout(layoutConfig)
    layout.run()
}


const fitView = () => {
    cy.animate({ fit: { padding: 50 } })
}

const handleResize = () => {
    cy.resize()
    cy.fit()
}

// --- Helpers ---
const assignColors = (labels) => {
    labels.forEach((l, idx) => {
        if(!labelColorMap[l]) labelColorMap[l] = colorPalette[idx % colorPalette.length]
    })
}

const getColor = (label) => labelColorMap[label] || '#909399'

const formatCytoscapeNode = (n) => {
    const mainLabel = n.labels && n.labels.length > 0 ? n.labels[0] : 'Unknown'
    const name = n.properties.name || n.properties.title || n.properties.code || String(n.id)
    return {
        group: 'nodes',
        data: {
            id: String(n.id),
            name: name,
            label: mainLabel,
            labels: n.labels,
            properties: n.properties,
            color: getColor(mainLabel)
        }
    }
}

const formatCytoscapeEdge = (l) => {
    return {
        group: 'edges',
        data: {
            id: `${l.source}-${l.target}-${l.type}`,
            source: String(l.source),
            target: String(l.target),
            type: l.type
        }
    }
}

const formatNumber = (num) => num ? num.toLocaleString() : '0'

</script>

<style scoped>
.kg-dashboard {
  height: calc(100vh - 80px);
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

.db-selector { width: 100%; }
.sidebar-scroll { flex: 1; }
.stats-section { padding: 20px; }
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

.stat-group { margin-bottom: 25px; }
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
.stat-item:hover { background: #f5f7fa; }
.stat-item.active { background: #ecf5ff; border-color: #d9ecff; }

.stat-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}
.dot { width: 8px; height: 8px; border-radius: 50%; }

/* Main Canvas */
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
  z-index: 10;
}

.tool-group {
    display: flex;
    gap: 10px;
}

.search-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
  max-width: 500px;
  background: #f4f6f9;
  padding: 6px 12px;
  border-radius: 50px;
  margin: 0 auto;
}

.search-bar :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent !important;
}

.graph-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #fafafa;
}

.cy-container {
  width: 100%;
  height: 100%;
}

.empty-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.empty-placeholder .el-button {
    pointer-events: auto;
}

/* Details Panel */
.details-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 40px);
  overflow: hidden;
  z-index: 20;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-header .title {
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot-lg { width: 12px; height: 12px; border-radius: 4px; }

.panel-body {
  padding: 16px;
  overflow-y: auto;
}

.detail-item {
  margin-bottom: 12px;
}
.detail-item .label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 2px;
}
.detail-item .value {
  font-size: 13px;
  color: #303133;
  word-break: break-all;
}
.tags { display: flex; gap: 5px; flex-wrap: wrap; }

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
