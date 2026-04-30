import React, { useState, useEffect } from 'react'
import { Form, Input, InputNumber, Button, message, Spin, Alert, List, Tag } from 'antd'
import { PlayCircleOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons'
import axios from 'axios'
import styles from './DataCollection.module.css'

interface StarInfo {
  id: number
  weibo_uid: string
  nickname: string
  fans_count: number
}

interface CollectionStatus {
  is_running: boolean
  last_collection: string | null
  result: {
    success: boolean
    message: string
    star?: StarInfo
    posts_count?: number
    comments_count?: number
  } | null
}

const DataCollection: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [configLoading, setConfigLoading] = useState(true)
  const [stars, setStars] = useState<StarInfo[]>([])
  const [status, setStatus] = useState<CollectionStatus>({
    is_running: false,
    last_collection: null,
    result: null,
  })

  useEffect(() => {
    loadConfig()
    loadStatus()
  }, [])

  const loadConfig = async () => {
    try {
      const res = await axios.get('/api/collection/config')
      setStars(res.data.stars || [])
      form.setFieldsValue(res.data.default_config)
    } catch (e) {
      console.error(e)
    } finally {
      setConfigLoading(false)
    }
  }

  const loadStatus = async () => {
    try {
      const res = await axios.get('/api/collection/status')
      setStatus(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  const startCollection = async () => {
    const values = form.getFieldsValue()
    if (!values.weibo_uid) {
      message.warning('请输入微博用户ID')
      return
    }

    setLoading(true)
    try {
      const res = await axios.post('/api/collection/start', values)
      if (res.data.success) {
        message.success('采集任务已启动')
        setStatus({ ...status, is_running: true })
        // 定时检查状态
        const timer = setInterval(async () => {
          const statusRes = await axios.get('/api/collection/status')
          setStatus(statusRes.data)
          if (!statusRes.data.is_running) {
            clearInterval(timer)
            if (statusRes.data.result?.success) {
              message.success(statusRes.data.result.message)
              loadConfig()
            } else {
              message.error(statusRes.data.result?.message || '采集失败')
            }
          }
        }, 2000)
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '启动失败')
    } finally {
      setLoading(false)
    }
  }

  const stopCollection = async () => {
    try {
      await axios.post('/api/collection/stop')
      message.info('已标记停止')
      setStatus({ ...status, is_running: false })
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className={styles.pageCard}>
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>数据采集</h3>
        <Button icon={<ReloadOutlined />} onClick={() => { loadConfig(); loadStatus(); }}>
          刷新
        </Button>
      </div>

      {configLoading ? (
        <div className={styles.loadingWrap}><Spin /></div>
      ) : (
        <div className={styles.formBody}>
          {/* 已配置的明星 */}
          {stars.length > 0 && (
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>已采集的明星</h4>
              <List
                dataSource={stars}
                renderItem={(star) => (
                  <List.Item className={styles.starItem}>
                    <div className={styles.starInfo}>
                      <span className={styles.starName}>{star.nickname || '未知'}</span>
                      <Tag color="blue">UID: {star.weibo_uid}</Tag>
                      <span className={styles.starFans}>粉丝: {star.fans_count?.toLocaleString()}</span>
                    </div>
                  </List.Item>
                )}
              />
            </div>
          )}

          {/* 采集状态 */}
          {status.is_running && (
            <Alert
              type="info"
              message="采集进行中..."
              showIcon
              className={styles.statusAlert}
            />
          )}
          {status.result && !status.is_running && (
            <Alert
              type={status.result.success ? 'success' : 'error'}
              message={status.result.message}
              showIcon
              className={styles.statusAlert}
            />
          )}

          {/* 采集表单 */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>采集配置</h4>
            <Form form={form} layout="vertical" className={styles.form}>
              <Form.Item label="微博用户ID" name="weibo_uid" required>
                <Input placeholder="如: 6452389674" className={styles.input} />
              </Form.Item>

              <div className={styles.inlineRow}>
                <Form.Item label="帖子数量" name="posts_count" className={styles.inlineItem}>
                  <InputNumber min={1} max={200} className={styles.numberInput} />
                </Form.Item>
                <Form.Item label="每帖评论数" name="comments_per_post" className={styles.inlineItem}>
                  <InputNumber min={0} max={200} className={styles.numberInput} />
                </Form.Item>
              </div>

              <div className={styles.footer}>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={startCollection}
                  loading={loading || status.is_running}
                  className={styles.startBtn}
                >
                  开始采集
                </Button>
                {status.is_running && (
                  <Button
                    icon={<StopOutlined />}
                    onClick={stopCollection}
                    className={styles.stopBtn}
                  >
                    停止
                  </Button>
                )}
              </div>
            </Form>
          </div>

          {/* 使用说明 */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>使用说明</h4>
            <div className={styles.helpText}>
              <p>1. 在"系统设置"页面配置百炼 AI API Key，用于情感分析</p>
              <p>2. 在下方填入要采集的微博用户ID</p>
              <p>3. 点击"开始采集"按钮开始采集数据</p>
              <p>4. 采集完成后，在"帖子管理"页面点击"AI分析"进行情感分析</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataCollection