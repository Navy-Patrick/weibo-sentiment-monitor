import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Table, Button, Spin, message, Tag } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import styles from './Comments.module.css'

interface Comment {
  id: number
  content: string
  user_name: string
  likes_count: number
  sentiment: string
  created_at: string
}

const Comments: React.FC = () => {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [postContent, setPostContent] = useState('')
  const [totalComments, setTotalComments] = useState(0)
  const [comments, setComments] = useState<Comment[]>([])

  useEffect(() => {
    if (postId) {
      fetchComments()
    }
  }, [postId])

  const fetchComments = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/api/posts/${postId}/comments`)
      if (!response.ok) {
        throw new Error('获取评论失败')
      }
      const data = await response.json()
      setPostContent(data.post_content || '')
      setTotalComments(data.total_comments || 0)
      setComments(data.comments || [])
    } catch (error) {
      message.error('获取评论失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '用户', dataIndex: 'user_name', key: 'user_name', width: 150 },
    {
      title: '评论内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => text?.substring(0, 80) + (text?.length > 80 ? '...' : '')
    },
    {
      title: '点赞',
      dataIndex: 'likes_count',
      key: 'likes_count',
      width: 80,
      render: (v: number) => v?.toLocaleString() || 0
    },
    {
      title: '情感',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 80,
      render: (v: string) => {
        if (!v) {
          return <span style={{ color: '#999' }}>未分析</span>
        }
        const color = v === 'positive' ? '#52c41a' : v === 'negative' ? '#ff4d4f' : '#faad14'
        const text = v === 'positive' ? '正面' : v === 'negative' ? '负面' : '中性'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '采集时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150
    },
  ]

  return (
    <div className={styles.pageCard}>
      <div className={styles.cardHeader}>
        <div className={styles.headerLeft}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/posts')} className={styles.backBtn}>
            返回
          </Button>
          <h3 className={styles.cardTitle}>评论列表 ({totalComments} 条)</h3>
        </div>
      </div>
      <div className={styles.postInfo}>
        <span className={styles.postLabel}>帖子内容：</span>
        <span className={styles.postContent}>{postContent}</span>
      </div>
      <div className={styles.tableBody}>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={comments}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
          />
        </Spin>
      </div>
    </div>
  )
}

export default Comments