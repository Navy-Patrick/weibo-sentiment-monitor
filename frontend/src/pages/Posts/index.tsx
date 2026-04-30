import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Input, Button, Space, message, Modal, Progress, Tag } from 'antd'
import { SearchOutlined, ReloadOutlined, EyeOutlined, RobotOutlined } from '@ant-design/icons'
import styles from './Posts.module.css'

interface Post {
  id: number
  content: string
  created_at: string
  likes_count: number
  comments_count: number
  reposts_count: number
  sentiment: string
  sentiment_score: number
  source: string
}

const Posts: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [posts, setPosts] = useState<Post[]>([])
  const [analyzingPostId, setAnalyzingPostId] = useState<number | null>(null)
  const [analysisResult, setAnalysisResult] = useState<any>(null)

  // 获取帖子列表
  const fetchPosts = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/posts')
      const data = await response.json()
      setPosts(data)
    } catch (error) {
      message.error('获取帖子列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPosts()
  }, [])

  // AI 分析帖子情感
  const handleAIAnalyze = async (postId: number) => {
    setAnalyzingPostId(postId)
    try {
      const response = await fetch(`http://localhost:8000/api/sentiment/analyze-post/${postId}`, {
        method: 'POST'
      })
      const result = await response.json()

      if (result.success) {
        message.success(`分析完成！共分析 ${result.analyzed_comments} 条评论`)
        setAnalysisResult(result)
        // 刷新列表
        fetchPosts()
      } else {
        message.warning(result.message || '分析失败')
      }
    } catch (error) {
      message.error('AI分析失败')
      console.error(error)
    } finally {
      setAnalyzingPostId(null)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string, record: Post) => (
        <a
          href={record.source}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#1890ff', textDecoration: 'underline', cursor: 'pointer' }}
        >
          {text?.substring(0, 50) + (text?.length > 50 ? '...' : '')}
        </a>
      )
    },
    {
      title: '点赞',
      dataIndex: 'likes_count',
      key: 'likes_count',
      width: 90,
      render: (v: number) => v?.toLocaleString() || 0
    },
    {
      title: '评论',
      dataIndex: 'comments_count',
      key: 'comments_count',
      width: 90,
      render: (v: number) => v?.toLocaleString() || 0
    },
    {
      title: '情感',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 100,
      render: (v: string, record: Post) => {
        if (!v) {
          return <span style={{ color: '#999' }}>未分析</span>
        }
        const score = record.sentiment_score
        const color = v === 'positive' ? '#52c41a' : v === 'negative' ? '#ff4d4f' : '#faad14'
        const text = v === 'positive' ? '正面' : v === 'negative' ? '负面' : '中性'
        return (
          <Tag color={color}>
            {text} {score ? `(${(score * 100).toFixed(0)}%)` : ''}
          </Tag>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: Post) => (
        <Space size="small">
          <Button
            size="small"
            icon={<RobotOutlined />}
            onClick={() => handleAIAnalyze(record.id)}
            loading={analyzingPostId === record.id}
            type="primary"
            ghost
          >
            AI分析
          </Button>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/posts/${record.id}/comments`)}
          >
            评论
          </Button>
        </Space>
      ),
    },
  ]

  const handleRefresh = () => {
    fetchPosts()
  }

  const filteredPosts = posts.filter(p =>
    p.content?.toLowerCase().includes(searchText.toLowerCase())
  )

  return (
    <div className={styles.pageCard}>
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>帖子列表 ({posts.length} 条)</h3>
        <Space size={12}>
          <Input
            placeholder="搜索帖子内容"
            prefix={<SearchOutlined style={{ color: '#909399' }} />}
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            className={styles.searchInput}
          />
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} className={styles.refreshBtn}>
            刷新
          </Button>
        </Space>
      </div>
      <div className={styles.tableBody}>
        <Table
          columns={columns}
          dataSource={filteredPosts}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
        />
      </div>

      {/* 分析结果弹窗 */}
      <Modal
        title="AI 情感分析结果"
        open={!!analysisResult}
        onCancel={() => setAnalysisResult(null)}
        footer={null}
      >
        {analysisResult && (
          <div>
            <p>分析评论数: {analysisResult.analyzed_comments}</p>
            <p>正面评论: {analysisResult.positive_count}</p>
            <p>负面评论: {analysisResult.negative_count}</p>
            <p>中性评论: {analysisResult.neutral_count}</p>
            <p style={{ fontWeight: 'bold', marginTop: 16 }}>
              帖子整体情感: {analysisResult.post_sentiment === 'positive' ? '正面' : analysisResult.post_sentiment === 'negative' ? '负面' : '中性'}
              ({(analysisResult.post_sentiment_score * 100).toFixed(0)}%)
            </p>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Posts
