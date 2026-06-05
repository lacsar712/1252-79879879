<template>
  <div class="announcement-container">
    <template v-for="announcement in bannerAnnouncements" :key="`banner-${announcement.id}`">
      <AnnouncementBanner
        :announcement="announcement"
        @close="handleAnnouncementClose"
      />
    </template>

    <template v-for="announcement in listAnnouncements" :key="`list-${announcement.id}`">
      <AnnouncementListItem
        :announcement="announcement"
        @close="handleAnnouncementClose"
      />
    </template>

    <AnnouncementModal
      v-if="modalAnnouncement && showModal"
      :announcement="modalAnnouncement"
      v-model="showModal"
      @close="handleModalClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import type { Announcement } from '@/types'
import AnnouncementBanner from './AnnouncementBanner.vue'
import AnnouncementModal from './AnnouncementModal.vue'
import AnnouncementListItem from './AnnouncementListItem.vue'

const props = defineProps<{
  position: string
}>()

const route = useRoute()
const announcements = ref<Announcement[]>([])
const closedIds = ref<number[]>([])
const showModal = ref(false)
const modalIndex = ref(0)

const bannerAnnouncements = computed(() =>
  announcements.value.filter(
    (a) => a.display_type === 'banner' && !closedIds.value.includes(a.id)
  )
)

const listAnnouncements = computed(() =>
  announcements.value.filter(
    (a) => a.display_type === 'list' && !closedIds.value.includes(a.id)
  )
)

const modalAnnouncements = computed(() =>
  announcements.value.filter(
    (a) => a.display_type === 'modal' && !closedIds.value.includes(a.id)
  )
)

const modalAnnouncement = computed(() =>
  modalAnnouncements.value[modalIndex.value] || null
)

async function loadAnnouncements() {
  try {
    const data = await api.getDisplayAnnouncements(props.position)
    announcements.value = data
    modalIndex.value = 0
    if (modalAnnouncements.value.length > 0) {
      showModal.value = true
    }
  } catch (error) {
    console.error('加载公告失败:', error)
  }
}

function handleAnnouncementClose(id: number) {
  closedIds.value.push(id)
}

function handleModalClose(id: number) {
  closedIds.value.push(id)
  modalIndex.value++
  if (modalIndex.value < modalAnnouncements.value.length) {
    setTimeout(() => {
      showModal.value = true
    }, 300)
  }
}

watch(() => props.position, () => {
  closedIds.value = []
  modalIndex.value = 0
  loadAnnouncements()
})

watch(() => route.fullPath, () => {
  closedIds.value = []
  modalIndex.value = 0
  loadAnnouncements()
})

onMounted(() => {
  loadAnnouncements()
})
</script>

<style scoped>
.announcement-container {
  width: 100%;
}
</style>
