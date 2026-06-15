# 依赖注入与应用生命周期

## 应用容器

系统使用 `ApplicationContainer` 作为组合根（Composition Root），统一持有：

- 当前环境的 `Settings`
- PostgreSQL、Elasticsearch、Redis、Kafka 等基础设施客户端
- 工作单元（Unit of Work）工厂
- 后续新增的应用服务、仓储工厂和后台任务

每个应用进程只创建一个容器。容器存放在 `app.state.container`，其他资源不再分别写入
`app.state`，避免全局状态逐渐失控。

## FastAPI 依赖

接口通过类型化依赖获取资源：

```python
from commerce_search.infrastructure.dependencies import (
    ElasticsearchDep,
    RedisDep,
    SettingsDep,
    UnitOfWorkDep,
)


async def endpoint(
    settings: SettingsDep,
    redis: RedisDep,
    elasticsearch: ElasticsearchDep,
    uow: UnitOfWorkDep,
) -> None:
    ...
```

目前提供以下依赖类型：

| 类型 | 对应资源 |
| --- | --- |
| `ContainerDep` | 应用容器 |
| `SettingsDep` | 当前环境配置 |
| `InfrastructureDep` | 全部基础设施客户端 |
| `DatabaseManagerDep` | 数据库管理器 |
| `DatabaseSession` | 请求级异步数据库会话 |
| `ElasticsearchDep` | Elasticsearch 管理器 |
| `RedisDep` | Redis 管理器 |
| `KafkaProducerDep` | Kafka 生产者管理器 |
| `UnitOfWorkDep` | 新建的事务工作单元 |

应用层服务应在构造函数中显式接收依赖，不应在业务方法内部读取 `app.state` 或调用
`get_settings()`。FastAPI 的 `Depends` 只允许出现在 API 装配边界。

## 生命周期

生命周期按以下顺序执行：

1. 读取并校验环境配置。
2. 配置结构化日志。
3. 创建应用容器。
4. 启动容器管理的资源和后台任务。
5. 接收请求。
6. 停止后台任务并关闭所有基础设施客户端。

关闭操作具有幂等性。即使某个客户端关闭失败，其余客户端仍会继续清理，最终以聚合异常
报告所有失败。应用启动失败时也会执行同一套清理流程。

## 测试替换

`create_app()` 支持传入配置和容器工厂：

```python
app = create_app(
    test_settings,
    container_factory=lambda _: fake_container,
)
```

单个接口测试也可以使用 `app.dependency_overrides` 替换指定依赖。优先替换高层应用服务，
只有基础设施测试才直接替换数据库、缓存或消息客户端。
