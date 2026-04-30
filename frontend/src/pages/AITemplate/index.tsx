import React, { useState, useEffect } from 'react'
import { Input, Button, message, Spin } from 'antd'
import axios from 'axios'
import styles from './AITemplate.module.css'

const { TextArea } = Input

const AITemplate: React.FC = () => {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [saveLoading, setSaveLoading] = useState(false)

  const defaultPrompt = `你是一个专业的舆情分析师，请分析以下微博评论的情感倾向。

评论内容：{text}

分析要求：
1. 结合微博语境理解评论含义，注意网络用语、表情符号、粉丝用语
2. "老公"、"老婆"、"哥哥"、"姐姐"等称呼在粉丝语境下是正面表达
3. "棒"、"赞"、"爱了"、"绝了"、"yyds"等是正面词
4. "差"、"烂"、"无语"、"失望"、"恶心"等是负面词
5. 纯转发、@他人、无情感倾向的内容为中性

请严格按以下JSON格式返回，不要添加任何其他内容：
{"sentiment": "positive/neutral/negative", "score": 0.0-1.0, "reason": "简短理由"}

评分标准：
- positive（正面）: score > 0.6，表示喜爱、支持、赞美等积极情感
- neutral（中性）: score 在 0.4-0.6 之间，表示无明确情感倾向
- negative（负面）: score < 0.4，表示批评、不满、愤怒等消极情感`

  useEffect(() => {
    loadPrompt()
  }, [])

  const loadPrompt = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/settings/config')
      if (res.data && res.data.ai_prompt) {
        setPrompt(res.data.ai_prompt)
      } else {
        setPrompt(defaultPrompt)
      }
    } catch (e) {
      setPrompt(defaultPrompt)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaveLoading(true)
    try {
      const res = await axios.post('/api/settings/save-config', {
        ai_prompt: prompt
      })
      if (res.data.success) {
        message.success('提示词已保存')
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '保存失败')
    } finally {
      setSaveLoading(false)
    }
  }

  const handleReset = () => {
    setPrompt(defaultPrompt)
  }

  return (
    <div className={styles.pageCard}>
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>AI 情感分析提示词模板</h3>
      </div>
      {loading ? (
        <div className={styles.loadingWrap}><Spin /></div>
      ) : (
        <div className={styles.formBody}>
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>提示词配置</h4>
            <p className={styles.hint}>
              此提示词用于 AI 情感分析。使用 <code>{'{text}'}</code> 作为评论内容的占位符。
            </p>
            <TextArea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={20}
              className={styles.textarea}
              placeholder="输入提示词..."
            />
          </div>
          <div className={styles.footer}>
            <Button type="primary" onClick={handleSave} loading={saveLoading}>
              保存提示词
            </Button>
            <Button onClick={handleReset} style={{ marginLeft: 12 }}>
              恢复默认
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AITemplate