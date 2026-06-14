# Environment Configuration

## 加载顺序

配置按以下优先级加载，越靠后的来源优先级越高：

1. 代码中的安全默认值
2. 项目根目录 `.env`
3. 当前环境文件 `.env.<environment>`
4. 操作系统环境变量

`APP_ENV` 用于选择环境，支持：

- `development`：本地开发，默认开启调试和 API 文档。
- `test`：自动化测试，默认关闭调试。
- `staging`：预发布环境，默认关闭调试。
- `production`：生产环境，关闭 API 文档并启用安全校验。

旧值 `local` 会自动映射为 `development`。

## 本地开发

Windows PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env.development.example .env.development
python -m uvicorn commerce_search.main:app --reload
```

Linux / macOS:

```bash
cp .env.example .env
cp .env.development.example .env.development
python -m uvicorn commerce_search.main:app --reload
```

## 测试环境

测试进程应显式设置环境，避免误用开发数据库：

```powershell
$env:APP_ENV = "test"
python -m pytest
```

CI 中同样设置 `APP_ENV=test`。测试环境会加载 `.env` 和 `.env.test`，操作系统变量仍可
覆盖文件配置。

## 生产环境

生产部署推荐由 Kubernetes Secret、云密钥服务或部署平台注入环境变量，不应将真实
密码写入或提交到 `.env.production`。

生产环境启动时会拒绝以下不安全配置：

- `APP_DEBUG=true`
- PostgreSQL 使用默认密码
- PostgreSQL、Elasticsearch、Redis 或 Kafka 指向本机地址

生产环境默认关闭 `/docs` 和 `/redoc`。
