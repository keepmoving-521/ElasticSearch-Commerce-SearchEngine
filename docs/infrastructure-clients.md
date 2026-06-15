# Elasticsearch、Redis 与 Kafka 客户端

## 统一原则

三个客户端由 FastAPI 应用进程统一持有，并遵循以下规则：

1. 客户端采用惰性创建，应用启动时不会立即连接外部服务。
2. 每个应用进程只创建一个客户端实例，复用其内部连接池。
3. 应用关闭时统一释放连接、后台任务和网络资源。
4. API 或应用层通过依赖获取管理器，不在业务代码中重复创建客户端。
5. `/api/v1/health/ready` 并行检查 PostgreSQL、Elasticsearch、Redis 和 Kafka。

## Elasticsearch

`ElasticsearchManager` 封装官方异步客户端 `AsyncElasticsearch`：

```python
manager = ElasticsearchManager.from_settings(settings)
response = await manager.client.search(index="products", query={"match_all": {}})
```

主要配置：

| 环境变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch 地址 |
| `ELASTICSEARCH_REQUEST_TIMEOUT` | 3 | 单次请求超时时间，单位为秒 |
| `ELASTICSEARCH_MAX_RETRIES` | 3 | 请求失败后的最大重试次数 |

## Redis

`RedisManager` 使用 `redis.asyncio`，统一处理键前缀和 JSON 序列化：

```python
await redis.set_json("product:1", product_data, ttl_seconds=300)
product = await redis.get_json("product:1")
```

所有键都会自动添加 `REDIS_KEY_PREFIX`，避免开发、测试和生产环境之间发生键冲突。

主要配置：

| 环境变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 地址和数据库编号 |
| `REDIS_KEY_PREFIX` | `commerce-search` | 所有缓存键的统一前缀 |
| `REDIS_MAX_CONNECTIONS` | 50 | 每个应用进程的最大连接数 |
| `REDIS_SOCKET_TIMEOUT` | 3 | 建连与读写超时时间，单位为秒 |

## Kafka

`KafkaProducerManager` 使用 `AIOKafkaProducer`，默认启用幂等生产和 `acks=all`：

```python
await kafka.publish_json(
    "product.changed",
    {"product_id": "1", "operation": "updated"},
    key="1",
)
```

消息体统一编码为 UTF-8 JSON。相同实体应使用稳定的消息键，使同一商品的事件进入同一
分区并保持顺序。

主要配置：

| 环境变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Broker 地址，多个地址使用逗号分隔 |
| `KAFKA_CLIENT_ID` | `commerce-search` | Kafka 客户端标识 |
| `KAFKA_REQUEST_TIMEOUT_MS` | 30000 | 请求超时时间，单位为毫秒 |

当前阶段只封装生产者。消费者需要结合具体事件、消费组、幂等策略、重试和死信队列设计，
将在商品实时同步功能中实现。
