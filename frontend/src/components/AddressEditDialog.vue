<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑地址' : '新增地址'"
    width="600px"
    destroy-on-close
    class="address-edit-dialog"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="联系人" prop="contact_name">
            <el-input
              v-model="form.contact_name"
              placeholder="请输入收货人姓名"
              maxlength="50"
              show-word-limit
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="请输入手机号"
              maxlength="11"
              show-word-limit
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="所在地区" prop="region">
        <el-cascader
          v-model="regionValue"
          :options="regionOptions"
          :props="{ expandTrigger: 'hover' }"
          placeholder="请选择省/市/区"
          style="width: 100%"
          clearable
          @change="handleRegionChange"
        />
      </el-form-item>

      <el-form-item label="详细地址" prop="detail_address">
        <el-input
          v-model="form.detail_address"
          type="textarea"
          :rows="2"
          placeholder="请输入详细地址，如街道、门牌号等"
          maxlength="500"
          show-word-limit
          clearable
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="地址标签" prop="address_tag">
            <el-select
              v-model="form.address_tag"
              placeholder="请选择或输入标签"
              allow-create
              filterable
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="tag in tagOptions"
                :key="tag.value"
                :label="tag.label"
                :value="tag.value"
              >
                <el-tag :type="tag.type" size="small">
                  {{ tag.label }}
                </el-tag>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="设为默认">
            <el-switch
              v-model="form.is_default"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { api } from '@/api'
import type { UserAddress, UserAddressCreate, UserAddressUpdate, AddressTagOption } from '@/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  address?: UserAddress | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [address: UserAddress]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.address)

const formRef = ref<FormInstance>()
const submitting = ref(false)
const tagOptions = ref<AddressTagOption[]>([])

const regionValue = ref<string[]>([])

interface RegionOption {
  value: string
  label: string
  children?: RegionOption[]
}

const regionOptions: RegionOption[] = [
  {
    value: '北京市',
    label: '北京市',
    children: [
      {
        value: '北京市',
        label: '北京市',
        children: [
          { value: '东城区', label: '东城区' },
          { value: '西城区', label: '西城区' },
          { value: '朝阳区', label: '朝阳区' },
          { value: '海淀区', label: '海淀区' },
          { value: '丰台区', label: '丰台区' },
          { value: '石景山区', label: '石景山区' },
          { value: '通州区', label: '通州区' },
          { value: '顺义区', label: '顺义区' },
          { value: '昌平区', label: '昌平区' },
          { value: '大兴区', label: '大兴区' }
        ]
      }
    ]
  },
  {
    value: '上海市',
    label: '上海市',
    children: [
      {
        value: '上海市',
        label: '上海市',
        children: [
          { value: '黄浦区', label: '黄浦区' },
          { value: '徐汇区', label: '徐汇区' },
          { value: '长宁区', label: '长宁区' },
          { value: '静安区', label: '静安区' },
          { value: '普陀区', label: '普陀区' },
          { value: '虹口区', label: '虹口区' },
          { value: '杨浦区', label: '杨浦区' },
          { value: '浦东新区', label: '浦东新区' },
          { value: '闵行区', label: '闵行区' },
          { value: '宝山区', label: '宝山区' }
        ]
      }
    ]
  },
  {
    value: '广东省',
    label: '广东省',
    children: [
      {
        value: '广州市',
        label: '广州市',
        children: [
          { value: '越秀区', label: '越秀区' },
          { value: '海珠区', label: '海珠区' },
          { value: '荔湾区', label: '荔湾区' },
          { value: '天河区', label: '天河区' },
          { value: '白云区', label: '白云区' },
          { value: '黄埔区', label: '黄埔区' }
        ]
      },
      {
        value: '深圳市',
        label: '深圳市',
        children: [
          { value: '福田区', label: '福田区' },
          { value: '罗湖区', label: '罗湖区' },
          { value: '南山区', label: '南山区' },
          { value: '宝安区', label: '宝安区' },
          { value: '龙岗区', label: '龙岗区' },
          { value: '龙华区', label: '龙华区' }
        ]
      }
    ]
  },
  {
    value: '浙江省',
    label: '浙江省',
    children: [
      {
        value: '杭州市',
        label: '杭州市',
        children: [
          { value: '上城区', label: '上城区' },
          { value: '下城区', label: '下城区' },
          { value: '江干区', label: '江干区' },
          { value: '拱墅区', label: '拱墅区' },
          { value: '西湖区', label: '西湖区' },
          { value: '滨江区', label: '滨江区' },
          { value: '余杭区', label: '余杭区' }
        ]
      },
      {
        value: '宁波市',
        label: '宁波市',
        children: [
          { value: '海曙区', label: '海曙区' },
          { value: '江北区', label: '江北区' },
          { value: '北仑区', label: '北仑区' },
          { value: '镇海区', label: '镇海区' },
          { value: '鄞州区', label: '鄞州区' }
        ]
      }
    ]
  },
  {
    value: '江苏省',
    label: '江苏省',
    children: [
      {
        value: '南京市',
        label: '南京市',
        children: [
          { value: '玄武区', label: '玄武区' },
          { value: '秦淮区', label: '秦淮区' },
          { value: '建邺区', label: '建邺区' },
          { value: '鼓楼区', label: '鼓楼区' },
          { value: '浦口区', label: '浦口区' },
          { value: '栖霞区', label: '栖霞区' },
          { value: '雨花台区', label: '雨花台区' }
        ]
      },
      {
        value: '苏州市',
        label: '苏州市',
        children: [
          { value: '姑苏区', label: '姑苏区' },
          { value: '虎丘区', label: '虎丘区' },
          { value: '吴中区', label: '吴中区' },
          { value: '相城区', label: '相城区' },
          { value: '吴江区', label: '吴江区' },
          { value: '工业园区', label: '工业园区' }
        ]
      }
    ]
  },
  {
    value: '四川省',
    label: '四川省',
    children: [
      {
        value: '成都市',
        label: '成都市',
        children: [
          { value: '锦江区', label: '锦江区' },
          { value: '青羊区', label: '青羊区' },
          { value: '金牛区', label: '金牛区' },
          { value: '武侯区', label: '武侯区' },
          { value: '成华区', label: '成华区' },
          { value: '龙泉驿区', label: '龙泉驿区' },
          { value: '高新区', label: '高新区' }
        ]
      }
    ]
  }
]

const form = reactive<UserAddressCreate & { address_tag: string | null }>({
  contact_name: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail_address: '',
  address_tag: null,
  is_default: false
})

const rules: FormRules = {
  contact_name: [{ required: true, message: '请输入联系人姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号', trigger: 'blur' }
  ],
  region: [{ required: true, message: '请选择所在地区', trigger: 'change' }],
  detail_address: [{ required: true, message: '请输入详细地址', trigger: 'blur' }]
}

async function fetchTags() {
  try {
    tagOptions.value = await api.getAddressTags()
  } catch (error) {
    console.error('获取地址标签失败:', error)
  }
}

function handleRegionChange(value: string[]) {
  if (value && value.length === 3) {
    form.province = value[0]
    form.city = value[1]
    form.district = value[2]
  } else {
    form.province = ''
    form.city = ''
    form.district = ''
  }
}

function resetForm() {
  form.contact_name = ''
  form.phone = ''
  form.province = ''
  form.city = ''
  form.district = ''
  form.detail_address = ''
  form.address_tag = null
  form.is_default = false
  regionValue.value = []
  formRef.value?.clearValidate()
}

watch(() => props.address, (newVal) => {
  if (newVal) {
    form.contact_name = newVal.contact_name
    form.phone = newVal.phone
    form.province = newVal.province
    form.city = newVal.city
    form.district = newVal.district
    form.detail_address = newVal.detail_address
    form.address_tag = newVal.address_tag
    form.is_default = newVal.is_default
    regionValue.value = [newVal.province, newVal.city, newVal.district]
  } else {
    resetForm()
  }
}, { immediate: true })

watch(visible, (val) => {
  if (val) {
    fetchTags()
    if (!isEdit.value) {
      resetForm()
    }
  }
})

function handleCancel() {
  visible.value = false
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (!form.province || !form.city || !form.district) {
      ElMessage.warning('请选择完整的省/市/区信息')
      return
    }

    submitting.value = true
    try {
      const addressData: UserAddressCreate = {
        contact_name: form.contact_name,
        phone: form.phone,
        province: form.province,
        city: form.city,
        district: form.district,
        detail_address: form.detail_address,
        address_tag: form.address_tag || undefined,
        is_default: form.is_default
      }

      let result: UserAddress
      if (isEdit.value && props.address) {
        const updateData: UserAddressUpdate = { ...addressData }
        result = await api.updateAddress(props.address.id, updateData)
        ElMessage.success('地址更新成功')
      } else {
        result = await api.createAddress(addressData)
        ElMessage.success('地址添加成功')
      }

      emit('success', result)
      visible.value = false
    } catch (error) {
      console.error('保存地址失败:', error)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.address-edit-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
