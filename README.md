# Large-scale E-commerce Search & Recommendation

面向大型电商场景的商品搜索与个性化推荐系统。项目采用 Python、FastAPI、
Elasticsearch、PostgreSQL、Redis 和 Kafka，使用模块化单体作为起点，并通过清晰的
领域边界为后续独立部署和服务拆分保留空间。

## Architecture

```text
Client
  |
  v
FastAPI (API / Application)
  |
  +-- Catalog Domain
  +-- Search Domain -------- Elasticsearch
  +-- Recommendation Domain - Redis / Feature Store
  +-- User Domain ----------- PostgreSQL
  |
  +-------------------------- Kafka
```

代码遵循依赖倒置原则：领域层不依赖 Web 框架、数据库或消息系统；应用层编排用例；
基础设施层实现外部系统适配器；API 层只负责协议转换。

## Quick Start

要求 Python 3.12+，推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境。

```bash
cp .env.example .env
uv sync --all-groups
uv run uvicorn commerce_search.main:app --reload
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
uv sync --all-groups
uv run uvicorn commerce_search.main:app --reload
```

### 使用 pip

如果没有安装 `uv`，也可以使用 Python 自带的 `venv` 和 `pip`。第三方依赖仍从
`pyproject.toml` 安装，不需要单独维护 `requirements.txt`。

Linux / macOS:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m uvicorn commerce_search.main:app --reload
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m uvicorn commerce_search.main:app --reload
```

启动完整的本地基础设施：

```bash
docker compose up -d
```

服务启动后访问：

- API 文档: http://localhost:8000/docs
- 存活检查: http://localhost:8000/api/v1/health/live
- 就绪检查: http://localhost:8000/api/v1/health/ready

## Development

```bash
make format
make lint
make test
```

主要目录：

```text
src/commerce_search/
├── api/              # HTTP 协议、路由、请求/响应模型
├── application/      # 用例编排、命令、查询
├── domain/           # 领域实体、值对象、仓储接口
├── infrastructure/   # Elasticsearch、Redis、DB、Kafka 适配器
└── shared/           # 配置、日志、异常等跨模块能力
```

详细设计见 [docs/architecture.md](docs/architecture.md)。

API 响应与异常约定见 [docs/api-conventions.md](docs/api-conventions.md)。

开发、测试和生产环境配置见 [docs/configuration.md](docs/configuration.md)。

数据库连接池与事务约定见 [docs/database.md](docs/database.md)。

Elasticsearch、Redis 和 Kafka 客户端约定见
[docs/infrastructure-clients.md](docs/infrastructure-clients.md)。

依赖注入与应用生命周期约定见
[docs/dependency-injection.md](docs/dependency-injection.md)。
