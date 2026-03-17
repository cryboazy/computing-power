import { ref, watch } from 'vue'
import { themes, getStoredTheme, getTheme } from '../themes'

const currentThemeKey = ref(getStoredTheme())

export function useTheme() {
  const getThemeColor = (colorName) => {
    const theme = getTheme(currentThemeKey.value)
    return theme.colors[colorName] || ''
  }
  
  const getAllColors = () => {
    const theme = getTheme(currentThemeKey.value)
    return theme.colors
  }
  
  const getChartColors = () => {
    const theme = getTheme(currentThemeKey.value)
    return {
      primary: theme.colors.chart1,
      secondary: theme.colors.chart2,
      danger: theme.colors.chart3,
      warning: theme.colors.chart4,
      success: theme.colors.chart5,
      info: theme.colors.chart6
    }
  }
  
  const getCssVar = (name) => {
    return getComputedStyle(document.documentElement).getPropertyValue(`--theme-${name}`).trim()
  }
  
  return {
    currentThemeKey,
    getThemeColor,
    getAllColors,
    getChartColors,
    getCssVar
  }
}

export function watchThemeChange(callback) {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'data-theme') {
        const newTheme = document.documentElement.getAttribute('data-theme')
        currentThemeKey.value = newTheme
        callback(newTheme)
      }
    })
  })
  
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  })
  
  return () => observer.disconnect()
}
