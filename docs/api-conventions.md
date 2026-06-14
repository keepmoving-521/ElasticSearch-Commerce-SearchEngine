# API Conventions

## 成功响应

所有业务接口统一返回以下结构：

```json
{
  "code": "SUCCESS",
  "message": "Success",
  "data": {
    "status": "ok"
  },
  "request_id": "7f31c850-54a8-48aa-a938-dcab5b62a534",
  "errors": null
}
```

HTTP 状态码表达协议结果，`code` 表达业务结果。分页信息应放在 `data` 中，不改变外层结构。

## 错误响应

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "data": null,
  "request_id": "7f31c850-54a8-48aa-a938-dcab5b62a534",
  "errors": [
    {
      "field": "query.page",
      "message": "Input should be greater than or equal to 1",
      "type": "greater_than_equal"
    }
  ]
}
```

系统会统一处理：

- `AppError` 及其子类表示可预期的业务异常。
- FastAPI 参数校验异常返回 `VALIDATION_ERROR`。
- 404、405 等 HTTP 异常返回对应的标准错误码。
- 未处理异常返回 `INTERNAL_ERROR`，不会向客户端暴露内部错误细节。

业务模块可以声明更具体的错误码：

```python
raise ResourceNotFoundError(
    "Product was not found",
    code="PRODUCT_NOT_FOUND",
)
```

## Request ID

客户端可以通过 `X-Request-ID` 传入请求标识。未传入时系统自动生成 UUID。响应头和响应体
中的 `request_id` 始终保持一致，可用于日志检索和调用链排查。
