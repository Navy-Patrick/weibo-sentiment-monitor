import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Switch, Select, Divider, message, Spin, Alert } from 'antd'
import { SendOutlined, CheckCircleOutlined } from '@ant-design/icons'
import axios from 'axios'
import styles from './Settings.module.css'

const { TextArea } = Input

const Settings: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [pushLoading, setPushLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [configLoading, setConfigLoading] = useState(true)
  const [pushResult, setPushResult] = useState<{success: boolean; message: string} | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const res = await axios.get('/api/settings/config')
      if (res.data) {
        form.setFieldsValue({
          feishuAppId: res.data.feishu_app_id || '',
          feishuAppSecret: res.data.feishu_app_secret || '',
          feishuUserId: res.data.feishu_user_id || '',
          bailianApiKey: res.data.bailian_api_key || '',
          bailianApiUrl: res.data.bailian_api_url || 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
          aiModel: 'qwen3.5-flash',
          autoMonitor: res.data.auto_monitor === true || res.data.auto_monitor === 'true',
          alertThreshold: res.data.alert_threshold || 'medium',
          monitorInterval: parseInt(res.data.monitor_interval) || 30,
        })
      }
    } catch (e) {
      console.error('加载配置失败', e)
    } finally {
      setConfigLoading(false)
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      const res = await axios.post('/api/settings/save-config', {
        feishu_app_id: values.feishuAppId,
        feishu_app_secret: values.feishuAppSecret,
        feishu_user_id: values.feishuUserId,
        bailian_api_key: values.bailianApiKey,
        bailian_api_url: values.bailianApiUrl,
        auto_monitor: values.autoMonitor,
        alert_threshold: values.alertThreshold,
        monitor_interval: values.monitorInterval,
      })
      if (res.data.success) {
        message.success('配置保存成功')
      } else {
        message.error('保存失败')
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTestPush = async () => {
    const values = form.getFieldsValue()
    if (!values.feishuAppId || !values.feishuAppSecret || !values.feishuUserId) {
      message.warning('请先填写完整的飞书配置')
      return
    }

    setTestLoading(true)
    try {
      const res = await axios.post('/api/feishu/test')
      if (res.data.success) {
        message.success('测试消息已发送，请查看飞书')
      } else {
        message.error(res.data.message || '发送失败')
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '发送失败')
    } finally {
      setTestLoading(false)
    }
  }

  const handlePushToFeishu = async () => {
    setPushLoading(true)
    setPushResult(null)
    try {
      const res = await axios.post('/api/feishu/push-analysis')
      if (res.data.success) {
        setPushResult({
          success: true,
          message: `成功推送 ${res.data.pushed_count} 条舆情分析报告到飞书`
        })
      } else {
        setPushResult({
          success: false,
          message: res.data.message || '推送失败'
        })
      }
    } catch (e: any) {
      setPushResult({
        success: false,
        message: e.response?.data?.detail || '推送失败'
      })
    } finally {
      setPushLoading(false)
    }
  }

  return (
    <div className={styles.pageCard}>
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>系统设置</h3>
      </div>
      {configLoading ? (
        <div className={styles.loadingWrap}><Spin /></div>
      ) : (
        <div className={styles.formBody}>
          <Form
            form={form}
            layout="vertical"
            className={styles.form}
          >
            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>飞书推送配置</h4>
              <p className={styles.sectionDesc}>
                配置飞书机器人，将舆情分析结果推送到飞书。需要先在
                <a href="https://open.feishu.cn" target="_blank" rel="noopener noreferrer">飞书开放平台</a>
                创建应用并获取 App ID 和 App Secret。
              </p>
              <Form.Item label="飞书 App ID" name="feishuAppId" className={styles.formItem}>
                <Input placeholder="cli_xxxxxx" className={styles.input} />
              </Form.Item>
              <Form.Item label="飞书 App Secret" name="feishuAppSecret" className={styles.formItem}>
                <Input.Password placeholder="应用密钥" className={styles.input} />
              </Form.Item>
              <Form.Item label="飞书用户 Open ID" name="feishuUserId" className={styles.formItem}>
                <Input placeholder="ou_xxxxxx 格式的用户ID" className={styles.input} />
              </Form.Item>
              <Button
                type="default"
                onClick={handleTestPush}
                loading={testLoading}
                style={{ marginBottom: 16 }}
              >
                发送测试消息
              </Button>
            </div>

            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>百炼 AI 配置</h4>
              <Form.Item label="百炼 API 地址" name="bailianApiUrl" className={styles.formItem}>
                <Input placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" className={styles.input} />
              </Form.Item>
              <Form.Item label="百炼 API Key" name="bailianApiKey" className={styles.formItem}>
                <Input.Password placeholder="sk-xxx" className={styles.input} />
              </Form.Item>
              <Form.Item label="AI 模型" name="aiModel" className={styles.formItem}>
                <Input placeholder="qwen3.5-flash" className={styles.input} disabled />
              </Form.Item>
            </div>

            <div className={styles.section}>
              <h4 className={styles.sectionTitle}>监控配置</h4>
              <div className={styles.inlineRow}>
                <Form.Item label="自动监控" name="autoMonitor" valuePropName="checked" className={styles.inlineItem}>
                  <Switch />
                </Form.Item>
                <Form.Item label="监控间隔(分钟)" name="monitorInterval" className={styles.inlineItem}>
                  <Input type="number" min={5} max={120} className={styles.smallInput} />
                </Form.Item>
              </div>
              <Form.Item label="预警阈值" name="alertThreshold" className={styles.formItem}>
                <Select
                  options={[
                    { value: 'high', label: '高风险才预警' },
                    { value: 'medium', label: '中风险及以上预警' },
                    { value: 'low', label: '所有风险等级预警' },
                  ]}
                  className={styles.select}
                />
              </Form.Item>
            </div>

            {/* 推送结果提示 */}
            {pushResult && (
              <Alert
                type={pushResult.success ? 'success' : 'error'}
                message={pushResult.message}
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <div className={styles.footer}>
              <Button type="primary" onClick={handleSave} loading={loading} className={styles.saveBtn}>
                保存配置
              </Button>
              <Button
                type="default"
                icon={<SendOutlined />}
                onClick={handlePushToFeishu}
                loading={pushLoading}
                style={{ marginLeft: 12 }}
              >
                推送舆情报告到飞书
              </Button>
            </div>
          </Form>
        </div>
      )}
    </div>
  )
}

export default Settings