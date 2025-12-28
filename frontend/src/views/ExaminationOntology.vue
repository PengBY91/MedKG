<template>
  <div class="kg-dashboard">
    <el-container class="dashboard-container">
      <!-- Left Sidebar: Control & Schema -->
      <el-aside width="340px" class="sidebar">
        <div class="sidebar-header">
          <div class="logo-area">
            <div class="logo-icon-wrapper">
              <el-icon :size="28" color="#409eff"><Connection /></el-icon>
            </div>
            <div class="title-group">
              <span class="app-title">检验项目图谱</span>
              <span class="app-subtitle">Knowledge Graph Explorer</span>
            </div>
          </div>
          <div class="db-selector">
            <el-select 
              v-model="currentDb" 
              placeholder="选择数据库" 
              class="db-select-input"
              @change="handleDbChange"
              size="large"
            >
              <template #prefix><el-icon><DataAnalysis /></el-icon></template>
              <el-option v-for="db in dbRegistry" :key="db" :label="formatDbName(db)" :value="db">
                <div class="db-option">
                  <span class="db-name">{{ formatDbName(db) }}</span>
                  <el-tag size="small" type="info" effect="plain">{{ db }}</el-tag>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>

        <el-scrollbar class="sidebar-scroll">
          <!-- Stats Summary Card -->
          <div class="stats-summary-card">
            <div class="summary-title">
              <el-icon><PieChart /></el-icon>
              <span>图谱统计</span>
            </div>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-value">{{ formatNumber(totalNodes) }}</div>
                <div class="summary-label">节点总数</div>
              </div>
              <div class="summary-item">
                <div class="summary-value">{{ formatNumber(totalRelationships) }}</div>
                <div class="summary-label">关系总数</div>
              </div>
              <div class="summary-item">
                <div class="summary-value">{{ stats.labels.length }}</div>
                <div class="summary-label">节点类型</div>
              </div>
              <div class="summary-item">
                <div class="summary-value">{{ stats.relationships.length }}</div>
                <div class="summary-label">关系类型</div>
              </div>
            </div>
          </div>

          <div class="stats-section">
            <div class="section-title">
              <el-icon><Coin /></el-icon> 
              <span>节点类型</span>
              <el-tag size="small" type="info" effect="plain" style="margin-left: auto;">
                {{ stats.labels.length }} 类
              </el-tag>
            </div>
            
            <div v-if="loadingStats" class="loading-state">
              <el-skeleton :rows="4" animated />
            </div>
            
            <div v-else class="stats-list">
              <!-- Node Labels -->
              <div class="stat-group">
                <div 
                  v-for="(stat, idx) in stats.labels" 
                  :key="stat.label"
                  class="stat-item"
                  :class="{ active: filterLabel === stat.label }"
                  @click="toggleLabelFilter(stat.label)"
                >
                  <div class="stat-label">
                    <span class="dot" :style="{ background: getColor(stat.label) }"></span>
                    <span class="label-text">{{ stat.label }}</span>
                  </div>
                  <el-tag 
                    size="small" 
                    :type="filterLabel === stat.label ? 'primary' : 'info'" 
                    effect="plain" 
                    round
                  >
                    {{ formatNumber(stat.count) }}
                  </el-tag>
                </div>
              </div>

              <!-- Relationships -->
              <div class="stat-group" v-if="stats.relationships.length > 0">
                <div class="section-title" style="margin-top: 20px;">
                  <el-icon><Connection /></el-icon> 
                  <span>关系类型</span>
                  <el-tag size="small" type="info" effect="plain" style="margin-left: auto;">
                    {{ stats.relationships.length }} 类
                  </el-tag>
                </div>
                <div v-for="rel in stats.relationships" :key="rel.type" class="stat-item rel-item">
                  <div class="stat-label">
                    <el-icon class="rel-icon"><ArrowRight /></el-icon>
                    <span class="label-text">{{ rel.type }}</span>
                  </div>
                  <el-tag size="small" type="success" effect="plain" round>
                    {{ formatNumber(rel.count) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </el-aside>

      <!-- Main Content Area -->
      <el-main class="main-canvas">
        <div class="canvas-header">
            <!-- Header Title -->
            <div class="header-title-section">
              <h3 class="canvas-title">图谱可视化</h3>
              <el-tag v-if="!isEmptyGraph" size="small" type="success" effect="plain">
                显示 {{ cy ? cy.nodes().length : 0 }} 节点 / {{ cy ? cy.edges().length : 0 }} 关系
              </el-tag>
            </div>

            <!-- Search Bar -->
            <div class="search-bar">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索节点名称、代码或属性..."
                  @keyup.enter="performSearch"
                  clearable
                  size="large"
                >
                  <template #prefix><el-icon><Search /></el-icon></template>
                  <template #suffix>
                    <el-button 
                      text 
                      type="primary" 
                      :icon="Search" 
                      @click="performSearch" 
                      :loading="loadingGraph"
                    >
                      搜索
                    </el-button>
                  </template>
                </el-input>
            </div>

            <!-- Layout & Tools -->
            <div class="header-tools-section">
              <el-dropdown @command="handleLayoutChange" size="large">
                <el-button>
                  <el-icon><Grid /></el-icon>
                  布局: {{ layoutLabels[currentLayout] }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="fcose">
                      <el-icon><Share /></el-icon> 力导向布局
                    </el-dropdown-item>
                    <el-dropdown-item command="cola">
                      <el-icon><Operation /></el-icon> 物理布局
                    </el-dropdown-item>
                    <el-dropdown-item command="concentric">
                      <el-icon><PieChart /></el-icon> 同心圆布局
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-divider direction="vertical" />

              <el-tooltip content="刷新布局" placement="bottom">
                <el-button circle :icon="Refresh" @click="runLayout" />
              </el-tooltip>
              <el-tooltip content="适应视图" placement="bottom">
                <el-button circle :icon="FullScreen" @click="fitView" />
              </el-tooltip>
              <el-tooltip content="放大" placement="bottom">
                <el-button circle :icon="ZoomIn" @click="zoomIn" />
              </el-tooltip>
              <el-tooltip content="缩小" placement="bottom">
                <el-button circle :icon="ZoomOut" @click="zoomOut" />
              </el-tooltip>
            </div>
        </div>

        <!-- Graph Container -->
        <div class="graph-wrapper" v-loading="loadingGraph" element-loading-text="正在加载图谱数据...">
          <div id="cy" class="cy-container"></div>
          
          <!-- Mini Map (optional, can be toggled) -->
          <div class="minimap-toggle" v-if="!isEmptyGraph">
            <el-tooltip content="显示/隐藏缩略图" placement="left">
              <el-button circle size="small" :icon="Monitor" @click="toggleMinimap" />
            </el-tooltip>
          </div>
          
          <div class="empty-placeholder" v-if="!loadingGraph && isEmptyGraph">
            <el-empty description="暂无图谱数据">
              <template #image>
                <el-icon :size="80" color="#909399"><Connection /></el-icon>
              </template>
              <template #description>
                <p style="color: #909399; margin-bottom: 16px;">
                  暂未加载任何图谱数据
                </p>
              </template>
              <el-space>
                <el-button type="primary" @click="loadInitialSample" :icon="DataAnalysis">
                  加载示例数据
                </el-button>
                <el-button @click="performSearch" :icon="Search">
                  开始搜索
                </el-button>
              </el-space>
            </el-empty>
          </div>

          <!-- Node Detail Panel (Enhanced) -->
          <transition name="slide-fade">
              <div v-if="selectedNode" class="details-panel">
                  <div class="panel-header">
                      <div class="title">
                          <span class="dot-lg" :style="{ background: getColor(selectedNode.labels[0]) }"></span>
                          <div class="title-content">
                            <h4>{{ selectedNode.name }}</h4>
                            <span class="node-id">ID: {{ selectedNode.id }}</span>
                          </div>
                      </div>
                      <el-button link :icon="Close" @click="closeDetailPanel" size="large" />
                  </div>
                  <el-scrollbar class="panel-body-scroll">
                    <div class="panel-body">
                        <div class="detail-section">
                          <div class="section-label">
                            <el-icon><Tickets /></el-icon>
                            节点类型
                          </div>
                          <div class="detail-item">
                              <div class="value tags">
                                  <el-tag 
                                    v-for="l in selectedNode.labels" 
                                    :key="l" 
                                    size="large"
                                    :color="getColor(l)"
                                    style="color: white; border: none;"
                                  >
                                    {{ l }}
                                  </el-tag>
                              </div>
                          </div>
                        </div>

                        <el-divider v-if="Object.keys(selectedNode.properties).length > 0" />

                        <div class="detail-section" v-if="Object.keys(selectedNode.properties).length > 0">
                          <div class="section-label">
                            <el-icon><DocumentCopy /></el-icon>
                            节点属性
                          </div>
                          <div class="detail-item" v-for="(val, key) in selectedNode.properties" :key="key">
                              <span class="label">{{ key }}</span>
                              <div class="value">{{ val }}</div>
                          </div>
                        </div>
                        
                        <el-divider />

                        <div class="detail-section">
                          <div class="section-label">
                            <el-icon><Connection /></el-icon>
                            节点关系
                          </div>
                          <div class="connection-info">
                            <div class="connection-stat">
                              <el-icon><Link /></el-icon>
                              <span>连接数: <strong>{{ getNodeDegree(selectedNode.id) }}</strong></span>
                            </div>
                          </div>
                        </div>

                        <div class="panel-actions">
                            <el-button 
                              type="primary" 
                              :icon="Plus" 
                              @click="expandNode(selectedNode.rawNode)" 
                              :loading="expanding"
                              size="large"
                              style="width: 100%;"
                            >
                              展开邻居节点
                            </el-button>
                            <el-button 
                              type="warning" 
                              :icon="Minus" 
                              @click="collapseNode(selectedNode.rawNode)"
                              size="large"
                              style="width: 100%;"
                            >
                              折叠子节点
                            </el-button>
                        </div>
                    </div>
                  </el-scrollbar>
              </div>
          </transition>

          <!-- Legend Panel -->
          <transition name="fade">
            <div class="legend-panel" v-if="showLegend && !isEmptyGraph">
              <div class="legend-header">
                <span class="legend-title">图例</span>
                <el-button link :icon="Close" @click="showLegend = false" size="small" />
              </div>
              <div class="legend-content">
                <div class="legend-item" v-for="label in stats.labels.slice(0, 8)" :key="label.label">
                  <span class="legend-dot" :style="{ background: getColor(label.label) }"></span>
                  <span class="legend-label">{{ label.label }}</span>
                  <span class="legend-count">({{ formatNumber(label.count) }})</span>
                </div>
              </div>
            </div>
          </transition>

          <!-- Quick Stats Overlay -->
          <div class="quick-stats" v-if="!isEmptyGraph && !loadingGraph">
            <el-tooltip content="切换图例" placement="left">
              <el-button circle size="small" @click="showLegend = !showLegend" :icon="PieChart" />
            </el-tooltip>
          </div>
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
  Refresh, FullScreen, Close, PieChart, Grid, Share,
  Operation, ArrowDown, ZoomIn, ZoomOut, Monitor,
  Plus, Minus, Tickets, DocumentCopy, Link
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
const showLegend = ref(true)

const loadingGraph = ref(false)
const isEmptyGraph = ref(true)
const selectedNode = ref(null)
const expanding = ref(false)

// Cytoscape Instance
let cy = null
const expandedNodeIds = new Set()

// Layout Labels
const layoutLabels = {
  fcose: '力导向',
  cola: '物理布局',
  concentric: '同心圆'
}

// Color Palette (Enhanced)
const colorPalette = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', 
  '#9C27B0', '#00BCD4', '#009688', '#FF5722', 
  '#2196F3', '#E91E63', '#673AB7', '#4CAF50'
]
const labelColorMap = reactive({})

// Computed Properties
const totalNodes = computed(() => {
  return stats.labels.reduce((sum, label) => sum + label.count, 0)
})

const totalRelationships = computed(() => {
  return stats.relationships.reduce((sum, rel) => sum + rel.count, 0)
})

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
    ElMessage.error('无法加载数据库列表')
  }
}

const formatDbName = (name) => {
    return name === 'neo4j' ? '默认数据库' : name === 'system' ? '系统数据库' : name
}

const handleDbChange = () => {
    filterLabel.value = ''
    searchQuery.value = ''
    selectedNode.value = null
    expandedNodeIds.clear()
    if (cy) cy.elements().remove()
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
        ElMessage.warning('无法获取图谱统计信息')
    } finally {
        loadingStats.value = false
    }
}

const toggleLabelFilter = (label) => {
    if (filterLabel.value === label) {
        filterLabel.value = ''
        cy.elements().removeClass('faded')
    } else {
        filterLabel.value = label
        cy.batch(() => {
             cy.elements().removeClass('faded')
             const targets = cy.nodes(`[label = "${label}"]`)
             if (targets.length > 0) {
                 cy.elements().not(targets).addClass('faded')
             }
        })
        // Fit to filtered nodes
        const filteredNodes = cy.nodes(`[label = "${label}"]`)
        if (filteredNodes.length > 0) {
          cy.animate({
            fit: { eles: filteredNodes, padding: 80 },
            duration: 500
          })
        }
    }
}

const handleLayoutChange = (command) => {
  currentLayout.value = command
  runLayout()
}

const toggleMinimap = () => {
  ElMessage.info('缩略图功能即将推出')
}

const closeDetailPanel = () => {
  selectedNode.value = null
  cy.elements().removeClass('faded highlighted')
  filterLabel.value = ''
}

const getNodeDegree = (nodeId) => {
  if (!cy) return 0
  const node = cy.getElementById(nodeId)
  return node.empty() ? 0 : node.degree(false)
}

// --- Cytoscape Init ---
const initCytoscape = () => {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            // Core node style
            {
                selector: 'node',
                style: {
                    'label': 'data(name)',
                    'width': 40,
                    'height': 40,
                    'background-color': 'data(color)',
                    'color': '#303133',
                    'font-size': '12px',
                    'font-weight': '500',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'text-margin-y': 5,
                    'border-width': 3,
                    'border-color': '#fff',
                    'border-opacity': 1,
                    'box-shadow': '0 2px 8px rgba(0,0,0,0.15)',
                    'min-zoomed-font-size': 8,
                    'transition-property': 'background-color, border-color, border-width',
                    'transition-duration': '0.3s'
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 5,
                    'border-color': '#409EFF',
                    'background-color': '#ecf5ff',
                    'text-background-color': 'rgba(255,255,255,0.95)',
                    'text-background-opacity': 1,
                    'text-background-padding': '4px',
                    'text-background-shape': 'roundrectangle',
                    'box-shadow': '0 4px 16px rgba(64,158,255,0.4)',
                    'z-index': 999
                }
            },
            {
                selector: 'node:active',
                style: {
                    'overlay-color': '#409EFF',
                    'overlay-opacity': 0.2
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2.5,
                    'line-color': '#dcdfe6',
                    'target-arrow-color': '#dcdfe6',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.2,
                    'opacity': 0.8,
                    'transition-property': 'line-color, width',
                    'transition-duration': '0.3s'
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'width': 4,
                    'line-color': '#409EFF',
                    'target-arrow-color': '#409EFF',
                    'opacity': 1
                }
            },
            // Interactive classes
            {
                selector: '.faded',
                style: {
                    'opacity': 0.15,
                    'text-opacity': 0
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'border-color': '#E6A23C',
                    'border-width': 5,
                    'box-shadow': '0 4px 16px rgba(230,162,60,0.5)'
                }
            },
            {
                selector: '.hovered',
                style: {
                    'overlay-color': '#67C23A',
                    'overlay-opacity': 0.15
                }
            }
        ],
        wheelSensitivity: 0.2,
        minZoom: 0.1,
        maxZoom: 4
    })

    // Enhanced Event Handlers
    cy.on('tap', 'node', (evt) => {
        const node = evt.target
        handleNodeClick(node)
    })

    cy.on('tap', (evt) => {
        if (evt.target === cy) {
            closeDetailPanel()
        }
    })

    cy.on('mouseover', 'node', (evt) => {
        document.body.style.cursor = 'pointer'
        const node = evt.target
        node.addClass('hovered')
        // Show edge labels on hover
        node.connectedEdges().style('opacity', 1)
    })
    
    cy.on('mouseout', 'node', (evt) => {
        document.body.style.cursor = 'default'
        const node = evt.target
        node.removeClass('hovered')
        node.connectedEdges().style('opacity', 0.8)
    })

    cy.on('mouseover', 'edge', (evt) => {
        document.body.style.cursor = 'pointer'
        evt.target.style('width', 4)
    })

    cy.on('mouseout', 'edge', (evt) => {
        document.body.style.cursor = 'default'
        if (!evt.target.selected()) {
          evt.target.style('width', 2.5)
        }
    })
}

// --- Graph Logic ---
const loadInitialSample = () => {
    searchQuery.value = ''
    performSearch()
}

const performSearch = async () => {
    loadingGraph.value = true
    selectedNode.value = null
    if (cy) cy.elements().remove()
    
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
                 ElMessage.info('未找到匹配的节点')
             } else {
                 isEmptyGraph.value = false
                 cy.batch(() => {
                     cy.add(nodes)
                     cy.add(links)
                 })
                 runLayout()
                 ElMessage.success(`成功加载 ${nodes.length} 个节点`)
             }
        }
    } catch (e) {
        ElMessage.error('搜索失败，请重试')
        console.error('Search failed:', e)
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
            
            const existingNodeIds = new Set(cy.nodes().map(n => n.id()))
            const existingEdgeIds = new Set(cy.edges().map(e => e.id()))
            
            const nodesToAdd = newNodes.filter(n => !existingNodeIds.has(n.data.id))
            const edgesToAdd = newEdges.filter(e => !existingEdgeIds.has(e.data.id))
            
            if (nodesToAdd.length === 0 && edgesToAdd.length === 0) {
                ElMessage.info('没有新的邻居节点')
            } else {
                cy.batch(() => {
                    cy.add(nodesToAdd)
                    cy.add(edgesToAdd)
                })
                expandedNodeIds.add(String(rawNode.id))
                runLayout()
                ElMessage.success(`成功展开 ${nodesToAdd.length} 个邻居节点`)
            }
        }
    } catch (e) {
        ElMessage.error('展开失败，请重试')
        console.error('Expansion failed:', e)
    } finally {
        expanding.value = false
    }
}

const collapseNode = (rawNode) => {
    const nodeId = String(rawNode.id)
    const node = cy.getElementById(nodeId)
    if (node.empty()) return
    
    const neighbors = node.neighborhood().nodes()
    const leaves = neighbors.filter(n => n.degree(false) === 1)
    
    if (leaves.length > 0) {
        cy.remove(leaves)
        ElMessage.success(`成功折叠 ${leaves.length} 个节点`)
        expandedNodeIds.delete(nodeId)
    } else {
        ElMessage.warning('没有可折叠的子节点')
    }
}

const handleNodeClick = (node) => {
    cy.batch(() => {
        cy.elements().removeClass('highlighted faded')
        const neighbors = node.neighborhood().add(node)
        cy.elements().not(neighbors).addClass('faded')
        neighbors.addClass('highlighted')
    })

    selectedNode.value = {
        id: node.id(),
        name: node.data('name'),
        labels: node.data('labels'),
        properties: node.data('properties'),
        rawNode: { id: node.id() },
        color: node.data('color')
    }
    
    cy.animate({
        center: { eles: node },
        zoom: Math.min(cy.zoom() * 1.2, 2),
        duration: 500,
        easing: 'ease-in-out-cubic'
    })
}

// --- Layouts ---
const runLayout = () => {
    if (!cy || cy.nodes().length === 0) return
    
    cy.layout({ name: 'preset' }).stop()
    
    let layoutConfig = {
        animate: true,
        animationDuration: 800,
        animationEasing: 'ease-in-out-cubic',
        fit: true, 
        padding: 60
    }
    
    switch (currentLayout.value) {
        case 'fcose':
            layoutConfig = {
                name: 'fcose',
                quality: 'default',
                randomize: false,
                animate: true,
                animationDuration: 1200,
                nodeDimensionsIncludeLabels: true,
                uniformNodeDimensions: false,
                packingEnabled: true,
                nodeRepulsion: 5000,
                idealEdgeLength: 120,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,   
                tilingPaddingVertical: 15,
                tilingPaddingHorizontal: 15,
                fit: true,
                padding: 60
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
                padding: 60,
                nodeSpacing: 25,
                edgeLength: 180,
                randomize: false,
                handleDisconnected: true,
                convergenceThreshold: 0.01
            }
            break
        case 'concentric':
             layoutConfig = {
                name: 'concentric',
                concentric: function( node ){
                    return node.degree()
                },
                levelWidth: function( nodes ){
                    return 2
                },
                minNodeSpacing: 60,
                animate: true,
                animationDuration: 800,
                fit: true,
                padding: 60
            }
            break
    }
    
    const layout = cy.layout(layoutConfig)
    layout.run()
}

const fitView = () => {
    if (!cy) return
    cy.animate({ 
      fit: { padding: 60 },
      duration: 500,
      easing: 'ease-in-out-cubic'
    })
}

const zoomIn = () => {
    if (!cy) return
    cy.animate({
        zoom: Math.min(cy.zoom() * 1.3, 4),
        duration: 300
    })
}

const zoomOut = () => {
    if (!cy) return
    cy.animate({
        zoom: Math.max(cy.zoom() * 0.7, 0.1),
        duration: 300
    })
}

const handleResize = () => {
    if (!cy) return
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
/* === Main Container === */
.kg-dashboard {
  height: calc(100vh - 80px);
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  overflow: hidden;
}

.dashboard-container {
  height: 100%;
}

/* === Sidebar === */
.sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.03);
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.logo-icon-wrapper {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  letter-spacing: -0.5px;
}

.app-subtitle {
  font-size: 11px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.db-selector { 
  width: 100%; 
}

.db-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.db-name {
  font-weight: 500;
  color: #303133;
}

.sidebar-scroll { 
  flex: 1;
  padding: 16px 0;
}

/* === Stats Summary Card === */
.stats-summary-card {
  margin: 16px 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.summary-item {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 14px;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.summary-item:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* === Stats Section === */
.stats-section { 
  padding: 0 20px; 
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  text-transform: uppercase;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.5px;
}

.stat-group { 
  margin-bottom: 24px; 
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  background: #f8f9fa;
}

.stat-item:hover { 
  background: #e8f4ff;
  transform: translateX(4px);
  border-color: #c6e2ff;
}

.stat-item.active { 
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #606266;
  flex: 1;
}

.label-text {
  font-weight: 500;
}

.dot { 
  width: 10px; 
  height: 10px; 
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.rel-icon {
  color: #67c23a;
}

.rel-item {
  background: #f5f7fa;
}

.rel-item:hover {
  background: #e5f8e8;
}

/* === Main Canvas === */
.main-canvas {
  padding: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: #fafafa;
}

.canvas-header {
  min-height: 72px;
  background: white;
  border-bottom: 2px solid #f0f2f5;
  display: flex;
  align-items: center;
  padding: 16px 28px;
  gap: 24px;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
}

.header-title-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 180px;
}

.canvas-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.search-bar {
  flex: 1;
  max-width: 600px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 8px 20px;
}

.search-bar :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.header-tools-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.graph-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: linear-gradient(to bottom right, #fafafa 0%, #f0f2f5 100%);
}

.cy-container {
  width: 100%;
  height: 100%;
  background: #ffffff;
}

/* === Empty State === */
.empty-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 5;
}

/* === Details Panel === */
.details-panel {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 360px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 48px);
  overflow: hidden;
  z-index: 20;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f2f5;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
}

.panel-header .title {
  font-weight: 700;
  font-size: 16px;
  color: #303133;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.title-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-content h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

.node-id {
  font-size: 11px;
  color: #909399;
  font-weight: 400;
}

.dot-lg { 
  width: 14px; 
  height: 14px; 
  border-radius: 4px;
  margin-top: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.panel-body-scroll {
  flex: 1;
  overflow-y: auto;
}

.panel-body {
  padding: 20px 24px;
}

.detail-section {
  margin-bottom: 20px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  text-transform: uppercase;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.detail-item {
  margin-bottom: 14px;
}

.detail-item .label {
  font-size: 12px;
  color: #909399;
  font-weight: 600;
  display: block;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.detail-item .value {
  font-size: 14px;
  color: #303133;
  word-break: break-word;
  line-height: 1.6;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 8px;
}

.tags { 
  display: flex; 
  gap: 8px; 
  flex-wrap: wrap;
  padding: 0;
  background: none;
}

.connection-info {
  background: #f5f7fa;
  padding: 14px;
  border-radius: 10px;
}

.connection-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.panel-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f2f5;
}

/* === Legend Panel === */
.legend-panel {
  position: absolute;
  bottom: 24px;
  left: 24px;
  width: 240px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
  z-index: 15;
}

.legend-header {
  padding: 14px 18px;
  background: linear-gradient(to right, #667eea, #764ba2);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.legend-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-content {
  padding: 16px;
  max-height: 280px;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.legend-item:hover {
  background: #f5f7fa;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.legend-label {
  flex: 1;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.legend-count {
  font-size: 12px;
  color: #909399;
}

/* === Quick Stats Overlay === */
.quick-stats {
  position: absolute;
  top: 24px;
  left: 24px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.minimap-toggle {
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 10;
}

/* === Animations === */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  transform: translateX(40px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(40px);
  opacity: 0;
}

/* === Scrollbar Styling === */
:deep(.el-scrollbar__bar) {
  opacity: 0.6;
}

:deep(.el-scrollbar__thumb) {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

:deep(.el-scrollbar__thumb:hover) {
  background: rgba(0, 0, 0, 0.3);
}

/* === Loading State === */
.loading-state {
  padding: 20px;
}
</style>
