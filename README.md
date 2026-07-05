# FDA 医疗器械注册申报文档生成系统

自动化生成 FDA 510(k) 和 NMPA 医疗器械注册申报文档。

## 功能特性

- **多模板支持**: 510(k)、NMPA、QTMS (FDA)、QTMS (NMPA)
- **智能分析**: 自动分析产品资料，识别产品特征
- **动态目录**: 根据产品特征自动生成对应注册目录结构
- **文档生成**: 使用 AI 自动生成符合法规要求的申报文档
- **一致性验证**: 跨文档参数一致性检查与自动修复
- **多格式导出**: 支持 Word (.docx) 和 Markdown 格式导出
- **中英文切换**: 根据模板自动切换语言，支持手动切换

## 快速开始

### Docker 部署（推荐）

#### 1. 配置大模型

编辑 `config.json`：

```json
{
  "agents": {
    "defaults": {
      "model": "deepseek-v4-flash"
    }
  },
  "providers": {
    "deepseek": {
      "apiKey": "你的API Key",
      "apiBase": "http://your-api-server/v1"
    }
  }
}
```

#### 2. 启动服务

```bash
docker compose up -d
```

#### 3. 访问系统

浏览器打开：`http://localhost:8000/fda_frontend.html`

### 本地部署

#### 1. 安装依赖

```bash
pip install -e ".[fda]"
```

#### 2. 启动服务

```bash
python run.py
```

#### 3. 打开前端

浏览器打开 `fda_frontend.html`

## 使用流程

### 1. 配置工作区

1. 选择申报模板（510(k) / NMPA / QTMS）
2. 输入产品资料文件夹路径
3. 点击 **下一步**

### 2. 产品分析

系统自动分析产品特征，确认信息后继续

### 3. 生成文档

点击 **生成全部文档**，系统根据产品特征生成注册申报文档

### 4. 导出文档

- 单个文档: 点击文档后点击 **导出当前文档**
- 全部文档: 点击 **导出全部 (ZIP)**

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/workspace/init` | POST | 初始化工作区 |
| `/api/v1/workspace/analyze` | POST | 分析产品特征 |
| `/api/v1/document/tree` | GET | 获取文档目录树 |
| `/api/v1/document/generate` | POST | 生成文档 |
| `/api/v1/document/content/{id}` | GET | 获取文档内容 |
| `/api/v1/document/export/{id}` | GET | 导出单个文档 |
| `/api/v1/document/export-all` | GET | 导出全部文档 |

## 项目结构

```
fda/
├── agent_core/          # Agent框架（LLM调用）
├── fda_engine/          # FDA引擎核心代码
│   ├── api/            # API路由
│   ├── core/           # 核心引擎
│   ├── rag/            # RAG检索
│   ├── workflow/       # 工作流
│   └── ingestion/      # 文档解析
├── config.json         # 大模型配置
├── fda_frontend.html   # 前端界面
├── run.py              # 启动入口
├── Dockerfile          # Docker构建
├── docker-compose.yml  # Docker部署
└── pyproject.toml      # 项目配置
```

## 支持的模型

| 提供商 | 模型 |
|--------|------|
| DeepSeek | deepseek-v4-flash, deepseek-chat |
| OpenAI | GPT-4o, GPT-4-turbo |
| 通义千问 | qwen-max, qwen-plus |
| 其他 | 任意 OpenAI 兼容接口 |

## License

MIT License
