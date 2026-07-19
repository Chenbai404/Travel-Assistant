# Contributing to AI Travel Agent

感谢你对 AI Travel Agent 项目的关注！我们欢迎任何形式的贡献。

## 开发环境设置

### 前置要求
- Python 3.11+
- Poetry (用于依赖管理)
- Git

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ai-travel-agent.git
cd ai-travel-agent
```

2. 安装依赖：
```bash
poetry install --with dev
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

## 开发流程

### 分支策略
- `main` - 生产环境代码
- `develop` - 开发环境代码
- `feature/*` - 新功能分支
- `bugfix/*` - 错误修复分支

### 提交规范
使用语义化提交信息：
- `feat:` - 新功能
- `fix:` - 错误修复
- `docs:` - 文档更新
- `test:` - 测试相关
- `refactor:` - 代码重构
- `style:` - 代码格式调整

### 代码质量

运行代码检查：
```bash
# 代码风格检查
poetry run black --check agents/ tests/

# 代码质量检查
poetry run pylint agents/ --exit-under=8.0
```

### 测试

运行所有测试：
```bash
poetry run pytest tests/ -v
```

运行特定测试：
```bash
poetry run pytest tests/test_collect_preferences.py -v
```

查看测试覆盖率：
```bash
poetry run pytest tests/ --cov=agents --cov-report=html
# 然后在浏览器中打开 htmlcov/index.html
```

## Pull Request 流程

1. 从 `develop` 分支创建新的功能分支
2. 进行开发和测试
3. 确保所有测试通过
4. 提交 Pull Request 到 `develop` 分支
5. 等待代码审查和 CI/CD 检查通过

## 项目结构

```
ai-travel-agent/
├── agents/              # 核心代理逻辑
│   ├── agent.py         # 主代理类
│   ├── tools/           # 工具函数
│   └── models/          # 数据模型
├── tests/               # 测试文件
├── docs/                # 文档
├── app.py               # Streamlit 应用
└── pyproject.toml       # 项目配置
```

## 添加新功能

1. 在 `agents/tools/` 中创建新的工具函数
2. 在 `tests/` 中添加对应的测试
3. 在 `agents/agent.py` 中注册新工具
4. 更新相关文档

## 报告问题

如果你发现了 bug 或有功能建议，请在 GitHub Issues 中提交。

## 行为准则

- 尊重所有贡献者
- 建设性的反馈
- 关注代码和想法，而不是个人
- 接受并给予建设性的批评

## 联系方式

如有问题，请通过 GitHub Issues 联系我们。
