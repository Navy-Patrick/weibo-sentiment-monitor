import React, { useState } from 'react'
import { Table, Button, Space, Modal, Descriptions } from 'antd'
import { ReloadOutlined, CheckOutlined, EyeOutlined } from '@ant-design/icons'
import styles from './Alerts.module.css'

interface Alert {
  id: string
  type: string
  level: string
  content: string
  aiSummary: string
  createTime: string
  status: string
}

const Alerts: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [alerts, setAlerts] = useState<Alert[]>([
    { id: '1', type: '负面评论激增', level: 'high', content: '帖子#1的负面评论数量在1小时内增长了40%', aiSummary: '粉丝对剧情发展表示不满，需要关注舆论走向', createTime: '2024-04-28 14:30', status: 'pending' },
    { id: '2', type: '敏感词触发', level: 'medium', content: '检测到敏感词"退圈"出现5次', aiSummary: '部分粉丝表达退圈意向，建议及时回应', createTime: '2024-04-27 10:15', status: 'pending' },
    { id: '3', type: '负面率超标', level: 'low', content: '今日负面评论占比达到18%', aiSummary: '整体舆情正常波动，无需特别处理', createTime: '2024-04-26 08:00', status: 'handled' },
  ])
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [modalVisible, setModalVisible] = useState(false)

  const levelConfig = {
    high: { class: styles.levelHigh, text: '高风险' },
    medium: { class: styles.levelMedium, text: '中风险' },
    low: { class: styles.levelLow, text: '低风险' },
  }

  const statusConfig = {
    pending: { class: styles.statusPending, text: '待处理' },
    handled: { class: styles.statusHandled, text: '已处理' },
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (v: string) => (
        <span className={`${styles.levelTag} ${levelConfig[v as keyof typeof levelConfig].class}`}>
          {levelConfig[v as keyof typeof levelConfig].text}
        </span>
      ),
    },
    { title: '类型', dataIndex: 'type', key: 'type', width: 140 },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 150 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => (
        <span className={`${styles.statusTag} ${statusConfig[v as keyof typeof statusConfig].class}`}>
          {statusConfig[v as keyof typeof statusConfig].text}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_, record: Alert) => (
        <Space size={8}>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => { setSelectedAlert(record); setModalVisible(true) }}
            className={styles.actionBtn}
          >
            查看
          </Button>
          {record.status === 'pending' && (
            <Button
              size="small"
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => handleAlert(record.id)}
              className={styles.primaryBtn}
            >
              处理
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const handleAlert = (id: string) => {
    setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'handled' } : a))
  }

  const handleRefresh = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 1000)
  }

  return (
    <>
      <div className={styles.pageCard}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}>预警列表</h3>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} className={styles.refreshBtn}>
            刷新
          </Button>
        </div>
        <div className={styles.tableBody}>
          <Table
            columns={columns}
            dataSource={alerts}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </div>
      </div>

      <Modal
        title="预警详情"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
        className={styles.modal}
      >
        {selectedAlert && (
          <Descriptions column={1} bordered className={styles.descriptions}>
            <Descriptions.Item label="预警ID">{selectedAlert.id}</Descriptions.Item>
            <Descriptions.Item label="预警等级">
              <span className={`${styles.levelTag} ${levelConfig[selectedAlert.level as keyof typeof levelConfig].class}`}>
                {levelConfig[selectedAlert.level as keyof typeof levelConfig].text}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="预警类型">{selectedAlert.type}</Descriptions.Item>
            <Descriptions.Item label="预警内容">{selectedAlert.content}</Descriptions.Item>
            <Descriptions.Item label="AI分析摘要">{selectedAlert.aiSummary}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedAlert.createTime}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <span className={`${styles.statusTag} ${statusConfig[selectedAlert.status as keyof typeof statusConfig].class}`}>
                {statusConfig[selectedAlert.status as keyof typeof statusConfig].text}
              </span>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </>
  )
}

export default Alerts