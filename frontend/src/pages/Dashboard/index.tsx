import React, { useState, useEffect, useRef } from 'react'
import { Row, Col, Table, Tag } from 'antd'
import * as echarts from 'echarts'
import styles from './Dashboard.module.css'

interface Stats {
  totalPosts: number
  totalComments: number
  totalLikes: number
  positiveCount: number
  neutralCount: number
  negativeCount: number
  starCount: number
}

interface HotTopic {
  id: number
  title: string
  star_name: string
  sentiment: string
  hot_value: number
  created_at: string
}

interface SentimentTrend {
  date: string
  positive: number
  neutral: number
  negative: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    totalPosts: 0,
    totalComments: 0,
    totalLikes: 0,
    positiveCount: 0,
    neutralCount: 0,
    negativeCount: 0,
    starCount: 0,
  })
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([])
  const [sentimentTrend, setSentimentTrend] = useState<SentimentTrend[]>([])

  const sentimentChartRef = useRef<HTMLDivElement>(null)
  const wordCloudRef = useRef<HTMLDivElement>(null)

  // 获取统计数据
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/stats')
        const data = await response.json()
        setStats({
          totalPosts: data.total_posts || 0,
          totalComments: data.total_comments || 0,
          totalLikes: data.total_likes || 0,
          positiveCount: data.positive_count || 0,
          neutralCount: data.neutral_count || 0,
          negativeCount: data.negative_count || 0,
          starCount: data.star_count || 0,
        })
      } catch (error) {
        console.error('获取统计数据失败', error)
      }
    }

    const fetchHotTopics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/hot-topics')
        const data = await response.json()
        setHotTopics(data || [])
      } catch (error) {
        console.error('获取热门话题失败', error)
      }
    }

    const fetchSentimentTrend = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/sentiment-trend')
        const data = await response.json()
        setSentimentTrend(data || [])
      } catch (error) {
        console.error('获取情感趋势失败', error)
      }
    }

    fetchStats()
    fetchHotTopics()
    fetchSentimentTrend()
  }, [])

  useEffect(() => {
    if (sentimentChartRef.current && sentimentTrend.length > 0) {
      initSentimentChart()
    }
    if (wordCloudRef.current && hotTopics.length > 0) {
      initWordCloud()
    }
  }, [sentimentTrend, hotTopics])

  const initSentimentChart = () => {
    const chart = echarts.init(sentimentChartRef.current!)
    const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#e4e7ed',
        borderWidth: 1,
        textStyle: { color: '#1f2329' },
      },
      legend: {
        data: ['正面', '负面', '中性'],
        bottom: 0,
        icon: 'roundRect',
        itemWidth: 12,
        itemHeight: 4,
        textStyle: { color: '#646a73' },
      },
      grid: {
        left: 40,
        right: 20,
        top: 20,
        bottom: 40,
      },
      xAxis: {
        type: 'category',
        data: sentimentTrend.map(d => d.date.substring(5)), // 只显示月-日
        axisLine: { lineStyle: { color: '#e4e7ed' } },
        axisTick: { show: false },
        axisLabel: { color: '#646a73' },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#646a73' },
        splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } },
      },
      series: [
        {
          name: '正面',
          type: 'line',
          data: sentimentTrend.map(d => d.positive),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#34c724' },
          itemStyle: { color: '#34c724' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(52, 199, 36, 0.15)' },
              { offset: 1, color: 'rgba(52, 199, 36, 0)' },
            ]),
          },
        },
        {
          name: '负面',
          type: 'line',
          data: sentimentTrend.map(d => d.negative),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#f54a45' },
          itemStyle: { color: '#f54a45' },
        },
        {
          name: '中性',
          type: 'line',
          data: sentimentTrend.map(d => d.neutral),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#8f959e' },
          itemStyle: { color: '#8f959e' },
        },
      ],
    }
    chart.setOption(option)
    window.addEventListener('resize', () => chart.resize())
  }

  const initWordCloud = () => {
    const chart = echarts.init(wordCloudRef.current!)
    // 将热门话题转换为饼图数据
    const pieData = hotTopics.slice(0, 5).map((topic, index) => ({
      value: topic.hot_value,
      name: topic.title.substring(0, 10) + (topic.title.length > 10 ? '...' : ''),
      itemStyle: {
        color: ['#3370ff', '#5e8cff', '#8fafff', '#ff9800', '#34c724'][index % 5]
      }
    }))

    const option = {
      tooltip: {
        backgroundColor: '#fff',
        borderColor: '#e4e7ed',
        borderWidth: 1,
        textStyle: { color: '#1f2329' },
      },
      series: [{
        type: 'pie',
        radius: ['35%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          color: '#646a73',
          fontSize: 12,
        },
        labelLine: {
          length: 8,
          length2: 8,
          lineStyle: { color: '#e4e7ed' },
        },
        data: pieData.length > 0 ? pieData : [{ value: 1, name: '暂无数据', itemStyle: { color: '#ccc' } }],
      }],
    }
    chart.setOption(option)
    window.addEventListener('resize', () => chart.resize())
  }

  const formatHotValue = (value: number) => {
    if (value >= 1000000) {
      return '100w+'
    }
    return value.toLocaleString()
  }

  const recentPostsColumns = [
    { title: '内容', dataIndex: 'title', key: 'title', width: 350, ellipsis: true },
    { title: '明星', dataIndex: 'star_name', key: 'star_name', width: 120 },
    {
      title: '评论数',
      dataIndex: 'hot_value',
      key: 'hot_value',
      width: 120,
      render: (v: number) => formatHotValue(v)
    },
  ]

  // 计算负面率
  const totalAnalyzed = stats.positiveCount + stats.neutralCount + stats.negativeCount
  const negativeRate = totalAnalyzed > 0
    ? ((stats.negativeCount / totalAnalyzed) * 100).toFixed(1) + '%'
    : '0%'

  const statCards = [
    { key: 'posts', label: '帖子总数', value: stats.totalPosts, color: '#3370ff' },
    { key: 'comments', label: '评论总数', value: stats.totalComments.toLocaleString(), color: '#34c724' },
    { key: 'negative', label: '负面率', value: negativeRate, color: '#f54a45' },
    { key: 'likes', label: '总点赞', value: stats.totalLikes.toLocaleString(), color: '#ff9800' },
  ]

  return (
    <div className={styles.dashboard}>
      {/* 统计卡片 */}
      <Row gutter={20} className={styles.statRow}>
        {statCards.map(card => (
          <Col span={6} key={card.key}>
            <div className={styles.statCard}>
              <div className={styles.statIndicator} style={{ background: card.color }} />
              <div className={styles.statContent}>
                <span className={styles.statLabel}>{card.label}</span>
                <span className={styles.statValue} style={{ color: card.key === 'negative' ? '#f54a45' : '#1f2329' }}>
                  {card.value}
                </span>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      {/* 情感趋势图 */}
      <div className={styles.chartCard}>
        <div className={styles.cardHeader}>
          <h3 className={styles.cardTitle}>情感趋势</h3>
        </div>
        <div ref={sentimentChartRef} className={styles.chartBody} />
      </div>

      {/* 词云和热门帖子 */}
      <Row gutter={20} className={styles.bottomRow}>
        <Col span={8}>
          <div className={styles.chartCard}>
            <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}>热门话题</h3>
            </div>
            <div ref={wordCloudRef} className={styles.chartBody} />
          </div>
        </Col>
        <Col span={16}>
          <div className={styles.chartCard}>
            <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}>近期热门帖子</h3>
            </div>
            <div className={styles.tableBody}>
              <Table
                columns={recentPostsColumns}
                dataSource={hotTopics}
                rowKey="id"
                pagination={false}
                size="middle"
              />
            </div>
          </div>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
