import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

const themeConfig = {
  token: {
    colorPrimary: '#3370ff',
    colorSuccess: '#34c724',
    colorWarning: '#ff9800',
    colorError: '#f54a45',
    colorInfo: '#3370ff',
    borderRadius: 6,
    fontSize: 14,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  components: {
    Card: {
      borderRadiusLG: 12,
      boxShadowTertiary: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#eef4ff',
      itemSelectedColor: '#3370ff',
      itemHoverBg: '#f5f7fa',
      itemColor: '#646a73',
    },
    Table: {
      headerBg: '#f5f7fa',
      borderColor: '#ebeef5',
    },
  },
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={themeConfig}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>,
)