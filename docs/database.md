# 数据库连接与事务管理

## 连接池

系统使用 SQLAlchemy 2.x 的异步会话，并通过 `asyncpg` 驱动连接 PostgreSQL。
`DatabaseManager` 在每个应用进程中维护一个数据库引擎和连接池（Connection Pool）。
连接池采用惰性创建方式：只有首次执行数据库操作时才会真正建立，并在 FastAPI 应用
关闭时统一释放。

`/api/v1/health/live` 只检查服务进程是否存活。`/api/v1/health/ready` 会执行
`SELECT 1` 检查数据库连接；当 PostgreSQL 无法正常执行查询时，接口返回
`503 DATABASE_UNAVAILABLE`。

连接池配置如下：

| 环境变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `POSTGRES_POOL_SIZE` | 10 | 每个应用进程长期保持的连接数量 |
| `POSTGRES_MAX_OVERFLOW` | 20 | 连接池满后允许临时创建的额外连接数量 |
| `POSTGRES_POOL_TIMEOUT` | 30 | 等待空闲连接的最长时间，单位为秒 |
| `POSTGRES_POOL_RECYCLE` | 1800 | 连接被回收重建前的存活时间，单位为秒 |
| `POSTGRES_ECHO` | false | 是否输出 SQL 语句，仅建议在开发排查时开启 |

连接池参数对每个应用工作进程分别生效。例如，部署 4 个工作进程且
`POSTGRES_POOL_SIZE=20` 时，应用最多可能长期占用 80 个数据库连接。因此，生产环境的
连接池大小必须结合 PostgreSQL 最大连接数、应用副本数和工作进程数进行配置。

## 请求级数据库会话

API 接口可以通过统一依赖获取异步数据库会话：

```python
from commerce_search.infrastructure.database.dependencies import DatabaseSession


async def endpoint(session: DatabaseSession) -> None:
    ...
```

该依赖会为每个请求创建独立的 `AsyncSession`，并在请求完成后关闭会话。如果异常从
接口中抛出，会话会自动执行回滚。

请求级会话不会自动提交事务。事务的提交边界应由应用层用例负责，避免接口层在不清楚
完整业务流程的情况下提前提交数据。

## 事务边界

涉及数据库写入的应用层用例应使用工作单元（Unit of Work）：

```python
async with SqlAlchemyUnitOfWork(database.session_factory) as uow:
    assert uow.session is not None
    uow.session.add(model)
```

工作单元遵循以下规则：

- 代码块正常执行完成时自动提交事务。
- 代码块中出现异常时自动回滚事务。
- 无论提交还是回滚，最后都会关闭数据库会话。
- 异常不会被工作单元吞掉，会继续向上层传播并由统一异常处理器处理。

一个事务通常只覆盖一个应用层业务用例。例如，“创建商品”可以作为一个事务，但不应
为了保持数据库事务而长时间等待 Elasticsearch、Kafka 或第三方 HTTP 服务响应。

## 使用约定

1. API 层只负责获取会话或调用应用层用例，不直接定义事务规则。
2. 应用层负责确定事务边界，并通过工作单元提交或回滚。
3. 仓储实现使用工作单元提供的同一个 `AsyncSession`，保证多次数据库操作属于同一事务。
4. 领域层不得依赖 SQLAlchemy、PostgreSQL 或具体数据库模型。
5. 不要在日志中输出数据库密码或包含密码的完整连接地址。
