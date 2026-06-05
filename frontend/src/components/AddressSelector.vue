<template>
  <div class="address-selector">
    <div
      v-if="selectedAddress"
      class="selected-address"
      @click="handleOpenSelector"
    >
      <div class="address-header">
        <div class="address-icon">
          <el-icon :size="22" color="#409eff"><Location /></el-icon>
        </div>
        <div class="address-info">
          <div class="address-top">
            <span class="contact-name">{{ selectedAddress.contact_name }}</span>
            <span class="contact-phone">{{ selectedAddress.phone }}</span>
            <el-tag
              v-if="selectedAddress.is_default"
              type="danger"
              size="small"
              effect="dark"
            >
              默认
            </el-tag>
            <el-tag
              v-if="selectedAddress.address_tag"
              size="small"
            >
              {{ selectedAddress.address_tag }}
            </el-tag>
          </div>
          <div class="address-detail">{{ selectedAddress.full_address }}</div>
        </div>
        <div class="address-actions">
          <el-button type="primary" link @click.stop="handleEditSelected">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button link @click.stop="handleRefresh">
            <el-icon :class="{ spinning: refreshing }"><Refresh /></el-icon>
            刷新
          </el-button>
          <el-icon class="arrow-right"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <div
      v-else-if="!loading"
      class="empty-address"
      @click="handleAddAddress"
    >
      <el-empty description="请添加收货地址" :image-size="80">
        <template #image>
          <el-icon :size="60" color="#dcdfe6"><Location /></el-icon>
        </template>
        <el-button type="primary">
          <el-icon><Plus /></el-icon>
          添加收货地址
        </el-button>
      </el-empty>
    </div>

    <div v-else class="loading-placeholder">
      <el-skeleton :rows="2" animated />
    </div>

    <el-drawer
      v-model="selectorVisible"
      title="选择收货地址"
      size="500px"
      direction="rtl"
      class="address-selector-drawer"
    >
      <div class="drawer-content">
        <div class="drawer-header">
          <el-button type="primary" link @click="handleAddNew">
            <el-icon><Plus /></el-icon>
            新增地址
          </el-button>
          <el-button link @click="handleRefresh">
            <el-icon :class="{ spinning: refreshing }"><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <div v-if="addresses.length > 0" class="address-list">
          <div
            v-for="address in addresses"
            :key="address.id"
            class="address-item"
            :class="{
              active: selectedAddress?.id === address.id,
              'is-default': address.is_default
            }"
            @click="handleSelect(address)"
          >
            <div class="item-radio">
              <el-radio :value="address.id" v-model="selectedId" />
            </div>
            <div class="item-content">
              <div class="item-top">
                <span class="contact-name">{{ address.contact_name }}</span>
                <span class="contact-phone">{{ address.phone }}</span>
                <el-tag
                  v-if="address.is_default"
                  type="danger"
                  size="small"
                  effect="dark"
                >
                  默认
                </el-tag>
                <el-tag
                  v-if="address.address_tag"
                  size="small"
                >
                  {{ address.address_tag }}
                </el-tag>
              </div>
              <div class="item-address">{{ address.full_address }}</div>
            </div>
            <div class="item-actions">
              <el-button type="primary" link size="small" @click.stop="handleEdit(address)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </div>
          </div>
        </div>

        <div v-else class="empty-list">
          <el-empty description="暂无收货地址" :image-size="100">
            <template #image>
              <el-icon :size="70" color="#dcdfe6"><Location /></el-icon>
            </template>
            <el-button type="primary" @click="handleAddNew">
              <el-icon><Plus /></el-icon>
              添加地址
            </el-button>
          </el-empty>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="selectorVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="!selectedAddress"
            @click="handleConfirmSelect"
          >
            确认选择
          </el-button>
        </div>
      </template>
    </el-drawer>

    <AddressEditDialog
      v-model="editDialogVisible"
      :address="editingAddress"
      @success="handleEditSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '@/api'
import type { UserAddress } from '@/types'
import { ElMessage } from 'element-plus'
import { Location, Edit, Refresh, ArrowRight, Plus } from '@element-plus/icons-vue'
import AddressEditDialog from './AddressEditDialog.vue'

const props = defineProps<{
  modelValue: UserAddress | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: UserAddress | null]
  'change': [address: UserAddress]
}>()

const loading = ref(false)
const refreshing = ref(false)
const addresses = ref<UserAddress[]>([])
const selectorVisible = ref(false)
const editDialogVisible = ref(false)
const editingAddress = ref<UserAddress | null>(null)
const selectedId = ref<number | null>(null)

const selectedAddress = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

watch(() => selectedAddress.value, (val) => {
  selectedId.value = val?.id || null
})

async function fetchAddresses() {
  loading.value = true
  try {
    const response = await api.getAddresses()
    addresses.value = response.items
    
    if (!selectedAddress.value && addresses.value.length > 0) {
      const defaultAddr = addresses.value.find(a => a.is_default)
      if (defaultAddr) {
        selectedAddress.value = defaultAddr
        emit('change', defaultAddr)
      } else {
        selectedAddress.value = addresses.value[0]
        emit('change', addresses.value[0])
      }
    }
  } catch (error) {
    console.error('获取地址列表失败:', error)
  } finally {
    loading.value = false
  }
}

async function handleRefresh() {
  refreshing.value = true
  try {
    const response = await api.getAddresses()
    addresses.value = response.items
    
    if (selectedAddress.value) {
      const updated = addresses.value.find(a => a.id === selectedAddress.value!.id)
      if (updated) {
        selectedAddress.value = updated
        emit('change', updated)
      } else if (addresses.value.length > 0) {
        const defaultAddr = addresses.value.find(a => a.is_default) || addresses.value[0]
        selectedAddress.value = defaultAddr
        emit('change', defaultAddr)
      } else {
        selectedAddress.value = null
      }
    }
    
    ElMessage.success('刷新成功')
  } catch (error) {
    console.error('刷新地址失败:', error)
  } finally {
    refreshing.value = false
  }
}

function handleOpenSelector() {
  selectorVisible.value = true
}

function handleSelect(address: UserAddress) {
  selectedId.value = address.id
}

function handleConfirmSelect() {
  const selected = addresses.value.find(a => a.id === selectedId.value)
  if (selected) {
    selectedAddress.value = selected
    emit('change', selected)
    selectorVisible.value = false
    ElMessage.success('已选择收货地址')
  }
}

function handleEdit(address: UserAddress) {
  editingAddress.value = address
  editDialogVisible.value = true
}

function handleEditSelected() {
  if (selectedAddress.value) {
    editingAddress.value = selectedAddress.value
    editDialogVisible.value = true
  }
}

function handleAddNew() {
  editingAddress.value = null
  editDialogVisible.value = true
}

function handleAddAddress() {
  editingAddress.value = null
  editDialogVisible.value = true
}

async function handleEditSuccess(address: UserAddress) {
  await fetchAddresses()
  
  if (!selectedAddress.value || editingAddress.value?.id === selectedAddress.value.id) {
    selectedAddress.value = address
    emit('change', address)
  }
}

onMounted(() => {
  fetchAddresses()
})
</script>

<style scoped>
.address-selector {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.selected-address {
  padding: 20px;
  cursor: pointer;
  transition: background 0.2s ease;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
}

.selected-address:hover {
  background: #f5f7fa;
  border-color: #409eff;
}

.address-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.address-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #ecf5ff;
  border-radius: 50%;
  flex-shrink: 0;
}

.address-info {
  flex: 1;
  min-width: 0;
}

.address-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.contact-name {
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.contact-phone {
  font-size: 15px;
  color: #606266;
  font-family: monospace;
}

.address-detail {
  font-size: 15px;
  color: #606266;
  line-height: 1.5;
}

.address-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.arrow-right {
  color: #c0c4cc;
  font-size: 18px;
}

.empty-address {
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.empty-address:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.loading-placeholder {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
}

.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.drawer-header {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.address-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
}

.address-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.address-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.address-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.address-item.is-default {
  border-color: #f56c6c;
}

.address-item.is-default.active {
  border-color: #409eff;
}

.item-radio {
  flex-shrink: 0;
  padding-top: 2px;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.item-top .contact-name {
  font-size: 16px;
}

.item-top .contact-phone {
  font-size: 14px;
}

.item-address {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.item-actions {
  flex-shrink: 0;
}

.empty-list {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.address-selector-drawer :deep(.el-drawer__body) {
  display: flex;
  flex-direction: column;
  padding: 20px;
}
</style>
