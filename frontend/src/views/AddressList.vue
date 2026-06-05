<template>
  <div class="address-list" v-loading="loading">
    <div class="page-header">
      <h1>收货地址管理</h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增地址
      </el-button>
    </div>

    <div v-if="addresses.length > 0" class="address-cards">
      <div
        v-for="address in addresses"
        :key="address.id"
        class="address-card"
        :class="{ 'is-default': address.is_default }"
      >
        <div class="card-header">
          <div class="contact-info">
            <span class="contact-name">{{ address.contact_name }}</span>
            <span class="contact-phone">{{ address.phone }}</span>
            <el-tag
              v-if="address.is_default"
              type="danger"
              size="small"
              effect="dark"
              class="default-tag"
            >
              默认
            </el-tag>
            <el-tag
              v-if="address.address_tag"
              :type="getTagType(address.address_tag)"
              size="small"
            >
              {{ address.address_tag }}
            </el-tag>
          </div>
          <div class="card-actions">
            <el-button type="primary" link @click="handleEdit(address)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              v-if="!address.is_default"
              type="success"
              link
              @click="handleSetDefault(address.id)"
            >
              <el-icon><Star /></el-icon>
              设为默认
            </el-button>
            <el-button type="danger" link @click="handleDelete(address)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
        <div class="card-body">
          <div class="full-address">
            <el-icon><Location /></el-icon>
            <span>{{ address.full_address }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无收货地址" :image-size="120">
        <template #image>
          <div class="empty-icon">
            <el-icon :size="80" color="#dcdfe6"><Location /></el-icon>
          </div>
        </template>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加第一个地址
        </el-button>
      </el-empty>
    </div>

    <AddressEditDialog
      v-model="editDialogVisible"
      :address="editingAddress"
      @success="handleEditSuccess"
    />

    <el-dialog
      v-model="reassignDialogVisible"
      title="请重新指定默认地址"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="reassign-default-dialog"
    >
      <div class="reassign-tip">
        <el-icon color="#e6a23c" :size="24"><Warning /></el-icon>
        <span>您删除了默认地址，请从以下地址中选择一个新的默认地址：</span>
      </div>
      <div class="reassign-list">
        <div
          v-for="addr in remainingAddresses"
          :key="addr.id"
          class="reassign-item"
          :class="{ active: selectedNewDefaultId === addr.id }"
          @click="selectedNewDefaultId = addr.id"
        >
          <el-radio :value="addr.id" v-model="selectedNewDefaultId" />
          <div class="reassign-item-content">
            <div class="reassign-contact">
              <span>{{ addr.contact_name }}</span>
              <span class="phone">{{ addr.phone }}</span>
            </div>
            <div class="reassign-address">{{ addr.full_address }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="handleSkipReassign" :disabled="remainingAddresses.length <= 1">
          稍后设置
        </el-button>
        <el-button
          type="primary"
          :disabled="!selectedNewDefaultId"
          @click="handleConfirmReassign"
        >
          确认设置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { UserAddress, AddressTagOption } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Star, Location, Warning } from '@element-plus/icons-vue'
import AddressEditDialog from '@/components/AddressEditDialog.vue'

const loading = ref(false)
const addresses = ref<UserAddress[]>([])
const editDialogVisible = ref(false)
const editingAddress = ref<UserAddress | null>(null)
const reassignDialogVisible = ref(false)
const remainingAddresses = ref<Array<{ id: number; contact_name: string; phone: string; full_address: string }>>([])
const selectedNewDefaultId = ref<number | null>(null)

const tagTypeMap: Record<string, AddressTagOption['type']> = {
  '家': 'success',
  '公司': '',
  '学校': 'warning',
  '其他': 'info'
}

function getTagType(tag: string): AddressTagOption['type'] {
  return tagTypeMap[tag] || 'info'
}

async function fetchAddresses() {
  loading.value = true
  try {
    const response = await api.getAddresses()
    addresses.value = response.items
  } catch (error) {
    console.error('获取地址列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  editingAddress.value = null
  editDialogVisible.value = true
}

function handleEdit(address: UserAddress) {
  editingAddress.value = address
  editDialogVisible.value = true
}

function handleEditSuccess() {
  fetchAddresses()
}

async function handleSetDefault(id: number) {
  try {
    await ElMessageBox.confirm(
      '确认将此地址设为默认收货地址吗？',
      '设置默认地址',
      { confirmButtonText: '确认设置', cancelButtonText: '取消', type: 'warning' }
    )
    await api.setDefaultAddress(id)
    ElMessage.success('已设为默认地址')
    fetchAddresses()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置默认地址失败:', error)
    }
  }
}

async function handleDelete(address: UserAddress) {
  try {
    await ElMessageBox.confirm(
      `确认删除"${address.contact_name}"的收货地址吗？`,
      '删除地址',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    
    const result = await api.deleteAddress(address.id)
    ElMessage.success(result.message)
    
    if (result.need_reassign_default && result.remaining_addresses) {
      remainingAddresses.value = result.remaining_addresses
      selectedNewDefaultId.value = null
      reassignDialogVisible.value = true
    } else {
      fetchAddresses()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除地址失败:', error)
    }
  }
}

async function handleConfirmReassign() {
  if (!selectedNewDefaultId.value) return
  
  try {
    await api.reassignDefaultAddress({
      new_default_address_id: selectedNewDefaultId.value
    })
    ElMessage.success('默认地址已更新')
    reassignDialogVisible.value = false
    fetchAddresses()
  } catch (error) {
    console.error('重新指定默认地址失败:', error)
  }
}

function handleSkipReassign() {
  reassignDialogVisible.value = false
  fetchAddresses()
}

onMounted(() => {
  fetchAddresses()
})
</script>

<style scoped>
.address-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.address-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.address-card {
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

.address-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.address-card.is-default {
  border-color: #f56c6c;
  background: linear-gradient(to right, #fff5f5, #ffffff);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.contact-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.contact-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.contact-phone {
  font-size: 16px;
  color: #606266;
  font-family: monospace;
}

.default-tag {
  margin-left: 4px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-body {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.full-address {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #606266;
  font-size: 15px;
  line-height: 1.6;
}

.full-address .el-icon {
  margin-top: 3px;
  color: #909399;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}

.empty-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.reassign-tip {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fdf6ec;
  border-radius: 6px;
  margin-bottom: 20px;
}

.reassign-tip span {
  flex: 1;
  color: #e6a23c;
  font-size: 15px;
  line-height: 1.5;
}

.reassign-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.reassign-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reassign-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.reassign-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.reassign-item-content {
  flex: 1;
}

.reassign-contact {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.reassign-contact span:first-child {
  font-weight: 600;
  color: #303133;
}

.reassign-contact .phone {
  color: #909399;
  font-family: monospace;
  font-size: 14px;
}

.reassign-address {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.reassign-default-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}
</style>
