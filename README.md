# AI Travel Agent

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-69%25-yellow.svg)

一个基于 LangGraph 和 LLM 的智能旅行规划助手，能够自动收集用户偏好、搜索航班和酒店信息，并生成个性化的旅行建议。

## 功能特性

- **智能偏好收集**: 使用 LLM 从自然语言中提取结构化的旅行偏好
- **航班搜索**: 集成 SerpAPI 搜索最佳航班选项
- **酒店推荐**: 根据用户偏好推荐合适的酒店
- **工作流自动化**: 基于 LangGraph 的智能决策流程
- **邮件通知**: 自动发送旅行信息到用户邮箱
- **Web 界面**: 基于 Streamlit 的用户友好界面

## 技术栈

- **核心框架**: LangGraph, LangChain
- **LLM**: OpenAI API (支持自定义端点)
- **数据源**: SerpAPI (航班/酒店搜索)
- **邮件服务**: SendGrid
- **Web UI**: Streamlit
- **依赖管理**: Poetry
- **测试框架**: pytest

## 安装

### 前置要求

- Python 3.11+
- Poetry

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ai-travel-agent.git
cd ai-travel-agent
```

2. 安装依赖：
```bash
poetry install
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

## 使用

### 启动 Web 应用

```bash
poetry run streamlit run app.py
```

### 环境变量配置

在 `.env` 文件中配置以下变量：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key

# SerpAPI 配置 (航班和酒店搜索)
SERPAPI_API_KEY=your_serpapi_api_key

# 邮件配置 (SendGrid)
FROM_EMAIL=your_email@example.com
TO_EMAIL=recipient@example.com
EMAIL_SUBJECT=Travel Information
SENDGRID_API_KEY=your_sendgrid_api_key
```

## 测试

### 运行所有测试

```bash
poetry run pytest tests/ -v
```

### 运行特定测试

```bash
poetry run pytest tests/test_collect_preferences.py -v
```

### 查看测试覆盖率

```bash
poetry run pytest tests/ --cov=agents --cov-report=html
# 然后在浏览器中打开 htmlcov/index.html
```

### 代码质量检查

```bash
# 代码风格检查
poetry run black --check agents/ tests/

# 代码质量检查
poetry run pylint agents/ --exit-under=8.0
```

## 项目结构

```
ai-travel-agent/
├── agents/              # 核心代理逻辑
│   ├── agent.py         # 主代理类和工作流
│   ├── tools/           # 工具函数
│   │   ├── collect_preferences.py
│   │   ├── flights_finder.py
│   │   └── hotels_finder.py
│   ├── models/          # 数据模型
│   └── normalizer.py    # 数据标准化
├── tests/               # 测试文件
│   ├── test_collect_preferences.py
│   ├── test_flights_finder.py
│   ├── test_hotels_finder.py
│   └── test_agent_workflow.py
├── docs/                # 文档
│   └── TESTING.md       # 测试文档
├── app.py               # Streamlit 应用
├── pyproject.toml       # 项目配置
└── pytest.ini           # 测试配置
```

## 开发

详细的开发指南请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 分支策略

- `main` - 生产环境代码
- `develop` - 开发环境代码
- `feature/*` - 新功能分支
- `bugfix/*` - 错误修复分支

## CI/CD

项目使用 GitHub Actions 进行持续集成和持续部署：

- **自动测试**: 每次提交和 Pull Request 自动运行测试
- **代码质量检查**: 自动运行 pylint 和 black 检查
- **覆盖率报告**: 自动生成并上传测试覆盖率报告

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目开发。

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系我们。
