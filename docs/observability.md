# 日志、请求 ID 与健康检查

## 结构化日志

系统使用 `structlog` 输出结构化日志，并接管 Python 标准日志及 Uvicorn 日志。

- 开发环境默认使用便于阅读的 `console` 格式。
- 测试、预发布和生产环境默认使用单行 JSON。
- 时间统一使用 UTC ISO 8601 格式。
- 日志包含服务名、环境、日志级别、模块名和事件名称。
- 请求日志自动包含 `request_id`、HTTP 方法和请求路径。
- 名称中包含 password、token、secret、authorization 或 cookie 的字段会被替换为
  `[REDACTED]`。

不要主动记录请求体、响应体、完整查询字符串、密码、令牌或数据库连接地址。

主要配置：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_LOG_LEVEL` | 根据环境决定 | 日志级别 |
| `APP_LOG_FORMAT` | 开发为 console，其余为 json | 日志输出格式 |
| `APP_ACCESS_LOG_ENABLED` | true | 是否记录 HTTP 访问日志 |

## 请求 ID

客户端或 API 网关可以通过 `X-Request-ID` 传入调用标识。系统只接受字母、数字、点、
下划线、冒号和连字符，长度默认不超过 128 个字符。无效或缺失的请求 ID 会被替换为
UUID。

请求 ID 会出现在：

- 结构化日志上下文
- HTTP 响应头 `X-Request-ID`
- 标准 API 响应体中的 `request_id`

响应头 `X-Response-Time-Ms` 表示服务端处理请求的耗时，单位为毫秒。

## 访问日志

每个 HTTP 请求完成后记录 `http_request_completed`，包含：

- `request_id`
- `http_method`
- `path`
- `status_code`
- `duration_ms`

发生未处理异常时还会记录 `http_request_failed` 和异常堆栈。5xx 请求的完成日志使用
warning 级别，其余请求使用 info 级别。Uvicorn 自带访问日志会被关闭，避免同一请求
重复记录。

## 健康检查

### 存活检查

`GET /api/v1/health/live`

只判断应用进程和事件循环能否响应，不访问外部依赖。容器平台可以使用它决定是否重启
进程。

### 就绪检查

`GET /api/v1/health/ready`

并行检查 PostgreSQL、Elasticsearch、Redis 和 Kafka。每个组件都有独立超时，默认
2 秒，可通过 `APP_HEALTH_CHECK_TIMEOUT_SECONDS` 调整。

全部正常时返回每个组件的探测耗时。任一组件失败或超时时返回
`503 INFRASTRUCTURE_UNAVAILABLE`，并列出所有异常组件。容器平台可以使用它决定是否
把流量转发到当前实例。
