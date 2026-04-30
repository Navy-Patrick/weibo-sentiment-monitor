import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  AlertOutlined,
  SettingOutlined,
  CloudDownloadOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import styles from './MainLayout.module.css'

const { Sider, Content, Header } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '数据看板' },
  { key: '/collection', icon: <CloudDownloadOutlined />, label: '数据采集' },
  { key: '/posts', icon: <FileTextOutlined />, label: '帖子管理' },
  { key: '/alerts', icon: <AlertOutlined />, label: '舆情预警' },
  { key: '/ai-template', icon: <RobotOutlined />, label: 'AI模板' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
]

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const handleMenuClick = (key: string) => {
    navigate(key)
  }

  const getPageTitle = () => {
    if (location.pathname.startsWith('/posts/') && location.pathname.includes('/comments')) {
      return '评论列表'
    }
    const currentItem = menuItems.find(item => item.key === location.pathname)
    return currentItem?.label || '数据看板'
  }

  const isMenuActive = (key: string) => {
    if (key === '/posts' && location.pathname.startsWith('/posts')) {
      return true
    }
    return location.pathname === key
  }

  return (
    <Layout className={styles.layout}>
      <Sider
        className={`${styles.sider} ${collapsed ? styles.siderCollapsed : ''}`}
        collapsed={collapsed}
        width={220}
        collapsedWidth={64}
      >
        <div className={styles.logo}>
          <span className={styles.logoIcon}>W</span>
          {!collapsed && <span className={styles.logoText}>白菜-月退微博舆情监控</span>}
        </div>

        <nav className={styles.menu}>
          {menuItems.map(item => (
            <div
              key={item.key}
              className={`${styles.menuItem} ${isMenuActive(item.key) ? styles.menuItemActive : ''}`}
              onClick={() => handleMenuClick(item.key)}
            >
              <span className={styles.menuIcon}>{item.icon}</span>
              {!collapsed && <span className={styles.menuLabel}>{item.label}</span>}
            </div>
          ))}
        </nav>

        <div className={styles.collapseBtn} onClick={() => setCollapsed(!collapsed)}>
          <span>{collapsed ? '>' : '<'}</span>
        </div>
      </Sider>

      <Layout className={`${styles.main} ${collapsed ? styles.mainCollapsed : ''}`}>
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            <h1 className={styles.pageTitle}>{getPageTitle()}</h1>
          </div>
          <div className={styles.headerRight}>
            <span className={styles.time}>2026-04-29</span>
          </div>
        </Header>

        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout