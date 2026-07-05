# ML API Server

基于 FastAPI 的本地 ML 服务，提供文本向量化（Embedding）和重排序（Rerank）API。

## 功能

- `/api/embeddings` - 文本向量化
- `/api/rerank` - 搜索结果重排序

## 快速开始

### 1. 本地运行

```bash
# 创建虚拟环境
python -m venv myenv
myenv\Scripts\activate

# 安装依赖
pip install fastapi uvicorn pydantic sentence-transformers transformers torch

# 启动服务
python ml_server.py
```

### 2. Docker 部署

`docker-compose.yml` 提供两种部署模式：

#### 模式一：本地模型（首次需下载约 2GB）

```bash
# 构建并启动（使用本地 embedding 和 rerank 模型）
docker compose --profile local up -d

# 查看日志
docker compose --profile local logs -f

# 停止
docker compose --profile local down
```

#### 模式二：API 模式（推荐，无需下载模型）

1. 复制并编辑配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 填入你的 API 信息：
```env
API_BASE=https://api.openai.com/v1
API_KEY=sk-你的密钥
EMBED_MODEL=text-embedding-3-small
RERANK_MODEL=
```

3. 启动：
```bash
docker compose --profile api up -d
```

#### docker-compose.yml 配置说明

```yaml
services:
  # 本地模型模式
  ml-server-local:
    profiles: ["local"]
    environment:
      - MODE=local
      - HF_ENDPOINT=https://hf-mirror.com  # 国内镜像加速
    volumes:
      - model-cache:/app/models  # 模型缓存持久化

  # API 模式
  ml-server-api:
    profiles: ["api"]
    environment:
      - MODE=api
      - API_BASE=${API_BASE:-https://api.openai.com/v1}
      - API_KEY=${API_KEY:-sk-xxx}
      - EMBED_MODEL=${EMBED_MODEL:-text-embedding-3-small}
      - RERANK_MODEL=${RERANK_MODEL:-}
```

## API 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `MODE` | 运行模式：`local` 或 `api` | `local` |
| `API_BASE` | API 地址 | `https://api.openai.com/v1` |
| `API_KEY` | API 密钥 | - |
| `EMBED_MODEL` | 向量化模型名称 | `text-embedding-3-small` |
| `RERANK_MODEL` | 重排序模型名称（可选） | - |

### 支持的 API 服务

| 服务 | API_BASE |
|------|----------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| 硅基流动 | `https://api.siliconflow.cn/v1` |
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` |
| 任意 OpenAI 兼容接口 | 自定义地址 |

## API 使用示例

### 文本向量化

```bash
curl -X POST http://localhost:8000/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界"}'
```

### 搜索重排序

```bash
curl -X POST http://localhost:8000/api/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "机器学习", "documents": ["深度学习教程", "天气预报", "AI 基础入门"]}'
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `HF_ENDPOINT` | HuggingFace 镜像地址（国内使用 `https://hf-mirror.com`） |
| `HF_HOME` | 模型缓存目录 |

## License

MIT
