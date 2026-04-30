# 微博舆情监控系统

一个基于 AI 的明星舆情智能监控系统，自动采集明星微博数据，通过大模型分析粉丝评论情感，实时推送舆情报告到飞书。

## 功能特性

- **数据采集**：基于 CDP 协议自动采集微博帖子和评论，绕过反爬机制
- **AI 情感分析**：集成百炼大模型分析评论情感，支持自定义提示词模板
- **数据看板**：ECharts 可视化展示舆情趋势、情感分布、热门话题
- **飞书推送**：自动推送舆情分析报告到飞书机器人
- **系统配置**：支持 AI 模型参数配置、监控参数配置

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + ECharts |
| 后端 | FastAPI + SQLite + SQLAlchemy |
| AI | 百炼 qwen3.5-flash 大模型 |
| 推送 | 飞书开放平台 API |
| 采集 | Chrome DevTools Protocol |

## 项目结构

```
weibo-sentiment-monitor/
├── backend/                    # 后端服务
│   ├── main.py                # FastAPI 入口
│   ├── requirements.txt       # Python 依赖
│   ├── routers/               # API 路由
│   │   ├── collection.py      # 数据采集 API
│   │   ├── dashboard.py       # 仪表盘 API
│   │   ├── feishu.py          # 飞书推送 API
│   │   ├── sentiment.py       # 情感分析 API
│   │   ├── settings.py        # 系统设置 API
│   │   └── posts.py           # 帖子管理 API
│   └── services/              # 业务服务
│       ├── database.py        # 数据库模型
│       ├── crawler.py         # CDP 爬虫服务
│       └── scheduler.py       # 定时任务
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   │   ├── Dashboard/     # 数据看板
│   │   │   ├── Posts/         # 帖子管理
│   │   │   ├── Comments/      # 评论列表
│   │   │   ├── DataCollection/# 数据采集
│   │   │   ├── AITemplate/    # AI 模板
│   │   │   └── Settings/      # 系统设置
│   │   ├── layouts/           # 布局组件
│   │   └── services/          # API 服务
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Chrome 浏览器（用于 CDP 采集）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端服务运行在 http://localhost:8000

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 http://localhost:3000

### CDP 代理启动（数据采集需要）

```bash
# 启动 Chrome 并开启 CDP 端口
chrome.exe --remote-debugging-port=3456

# 或使用 CDP 代理服务
node cdp-proxy.js
```

## 配置说明

### 百炼 AI 配置

1. 访问 [百炼控制台](https://dashscope.console.aliyun.com/) 获取 API Key
2. 在系统设置页面填写：
   - 百炼 API 地址：`https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
   - 百炼 API Key：`sk-xxx`
   - AI 模型：`qwen3.5-flash`

### 飞书推送配置

1. 访问 [飞书开放平台](https://open.feishu.cn/) 创建应用
2. 开通权限：
   - `im:message` - 获取与发送消息
   - `im:message:send_as_bot` - 以应用身份发消息
3. 获取 App ID 和 App Secret
4. 获取用户 Open ID（在飞书开放平台调试工具中查看）
5. 在系统设置页面填写配置

## 使用流程

```
1. 数据采集
   └─ 输入微博用户 ID
   └─ 设置采集数量
   └─ 点击"开始采集"

2. AI 情感分析
   └─ 进入帖子管理
   └─ 点击"AI分析"按钮
   └─ 等待分析完成

3. 查看结果
   └─ 数据看板查看整体趋势
   └─ 帖子管理查看详情
   └─ 评论列表查看情感分布

4. 推送报告
   └─ 系统设置点击"推送到飞书"
   └─ 飞书接收舆情报告
```

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger API 文档

### 主要 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/collection/start` | POST | 启动数据采集 |
| `/api/collection/status` | GET | 获取采集状态 |
| `/api/sentiment/analyze-post/{id}` | POST | 分析帖子情感 |
| `/api/posts` | GET | 获取帖子列表 |
| `/api/posts/{id}/comments` | GET | 获取评论列表 |
| `/api/dashboard/stats` | GET | 获取统计数据 |
| `/api/feishu/push-analysis` | POST | 推送到飞书 |
| `/api/settings/config` | GET/POST | 系统配置 |

## 数据库表结构

| 表名 | 说明 |
|------|------|
| stars | 明星信息表 |
| weibo_posts | 微博帖子表 |
| comments | 评论表 |
| collection_tasks | 采集任务表 |
| system_config | 系统配置表 |

## 自定义 AI 提示词

在"AI 模板"页面可以自定义情感分析提示词，使用 `{text}` 作为评论内容占位符。

默认提示词已针对微博语境优化：
- 识别粉丝用语（"老公"、"老婆"等为正面表达）
- 识别网络用语（"yyds"、"绝了"等）
- 支持表情符号情感识别

## 部署说明

### Docker 部署（推荐）

```bash
# 构建镜像
docker build -t weibo-monitor .

# 运行容器
docker run -d -p 8000:8000 -p 3000:3000 weibo-monitor
```

### 手动部署

1. 后端部署：使用 Gunicorn 或 Uvicorn
2. 前端部署：`npm run build` 后使用 Nginx 托管
3. 配置反向代理和 HTTPS

## 注意事项

- 数据采集需要登录微博，请确保 Chrome 已登录微博账号
- AI 分析会消耗 API 调用额度，请合理设置采集数量
- 飞书推送需要应用权限已开通并发布版本
- 数据库文件 `data.db` 包含敏感数据，请勿提交到公开仓库

## License

MIT License

## Author

zavay

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ant Design](https://ant.design/)
- [ECharts](https://echarts.apache.org/)
- [百炼大模型](https://dashscope.console.aliyun.com/)
- [飞书开放平台](https://open.feishu.cn/)
