<template>
  <div class="theme-switcher">
    <div class="theme-btn" @click="showPanel = !showPanel">
      <span class="theme-icon">{{ currentTheme.icon }}</span>
    </div>
    
    <Transition name="fade">
      <div v-if="showPanel" class="theme-panel">
        <div class="panel-title">选择配色主题</div>
        <div class="theme-list">
          <div 
            v-for="(theme, key) in themes" 
            :key="key"
            class="theme-item"
            :class="{ active: currentThemeKey === key }"
            @click="selectTheme(key)"
          >
            <div class="theme-preview" :style="getPreviewStyle(theme)">
              <span class="preview-dot" :style="{ background: theme.colors.primary }"></span>
              <span class="preview-dot" :style="{ background: theme.colors.secondary }"></span>
            </div>
            <div class="theme-info">
              <span class="theme-name">{{ theme.name }}</span>
              <span v-if="currentThemeKey === key" class="check-icon">✓</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
    
    <div v-if="showPanel" class="theme-overlay" @click="showPanel = false"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { themes, applyTheme, getStoredTheme, getTheme } from '../themes'

const showPanel = ref(false)
const currentThemeKey = ref('ocean')

const currentTheme = computed(() => getTheme(currentThemeKey.value))

const selectTheme = (key) => {
  currentThemeKey.value = key
  applyTheme(key)
  showPanel.value = false
}

const getPreviewStyle = (theme) => {
  return {
    background: `linear-gradient(135deg, ${theme.colors.bgStart} 0%, ${theme.colors.bgMiddle} 50%, ${theme.colors.bgEnd} 100%)`
  }
}

onMounted(() => {
  const stored = getStoredTheme()
  currentThemeKey.value = stored
  applyTheme(stored)
})
</script>

<style lang="scss" scoped>
.theme-switcher {
  position: relative;
  z-index: 1000;
}

.theme-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--theme-panel-bg-start) 0%, var(--theme-panel-bg-end) 100%);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  .theme-icon {
    font-size: 18px;
  }
  
  &:hover {
    border-color: var(--theme-primary);
    box-shadow: 0 0 15px var(--theme-shadow);
    transform: scale(1.05);
  }
}

.theme-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  width: 240px;
  background: linear-gradient(180deg, var(--theme-panel-bg-start) 0%, var(--theme-panel-bg-end) 100%);
  border: 1px solid var(--theme-border-heavy);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 20px var(--theme-shadow);
  backdrop-filter: blur(10px);
  overflow: hidden;
  
  .panel-title {
    padding: 14px 16px;
    font-size: 14px;
    font-weight: bold;
    color: var(--theme-primary);
    border-bottom: 1px solid var(--theme-border-light);
    background: linear-gradient(90deg, var(--theme-shadow) 0%, transparent 100%);
  }
  
  .theme-list {
    padding: 8px;
    max-height: 320px;
    overflow-y: auto;
  }
  
  .theme-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: var(--theme-shadow);
    }
    
    &.active {
      background: linear-gradient(90deg, var(--theme-shadow-heavy) 0%, transparent 100%);
      border: 1px solid var(--theme-border);
    }
    
    .theme-preview {
      width: 40px;
      height: 28px;
      border-radius: 4px;
      border: 1px solid var(--theme-border);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      
      .preview-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }
    }
    
    .theme-info {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .theme-name {
        font-size: 13px;
        color: var(--theme-text);
      }
      
      .check-icon {
        color: var(--theme-secondary);
        font-weight: bold;
      }
    }
  }
}

.theme-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
