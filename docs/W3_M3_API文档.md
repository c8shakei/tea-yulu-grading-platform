# W3-M3 后端 API 文档

> 里程碑：M3 后端可用  
> 技术栈：FastAPI + SQLite + hashlib 哈希链  
> 作物：恩施玉露茶（湖北地理标志绿茶，国家级非遗）

## 1. 接口约定

所有接口统一返回如下结构：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code = 0` 表示成功，非 0 为业务或系统错误。
- `message` 为可读提示。
- `data` 为具体业务数据。

## 2. 环境信息

- 后端入口：`src/backend/main.py`
- 启动方式：
  ```bash
  cd c:/Users/wzd/Desktop/毕业设计
  python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- OpenAPI JSON：http://localhost:8000/openapi.json
- CORS：已开启 `allow_origins=["*"]`，供 W4 Vue 前端本地开发调用。

## 3. 接口列表

### 3.1 健康检查

- **GET** `/health`
- **说明**：服务存活探针。
- **响应示例**：
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": { "status": "up" }
  }
  ```

### 3.2 茶叶品质检测

- **POST** `/api/detect`
- **Content-Type**：`multipart/form-data`
- **请求参数**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | image | file | 待检测的茶青/干茶图像 |
- **响应字段（data）**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | class_id | int | 0 特级 / 1 一级 / 2 二级 / 3 等外 |
  | class_name | string | 特级、一级、二级、等外 |
  | confidence | float | 置信度 |
  | bbox | list[float] | [x1, y1, x2, y2] 检测框 |
  | trace_id | string | 本次检测唯一溯源 ID，供后续上链 |
- **响应示例**：
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "class_id": 0,
      "class_name": "特级",
      "confidence": 0.8912,
      "bbox": [62.50, 70.00, 320.00, 290.00],
      "trace_id": "d5dd0dc39b254c2191c0c4fbc96fe764"
    }
  }
  ```
- **当前实现**：调用 `src/backend/mock_detector.py` 随机模拟检测结果；W2 完成 YOLOv8 权重交付后，仅替换该文件签名保持不变。

### 3.3 写入溯源区块

- **POST** `/api/trace`
- **Content-Type**：`application/json`
- **请求参数**：
  | 字段 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | trace_id | string | 是 | 检测端返回的 trace_id |
  | details | object | 否 | 业务详情（操作人、动作、地点等） |
  | ... | any | 否 | 允许额外字段，会一并写入 data_hash |
- **响应字段（data）**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | trace_id | string | 本次上链的 trace_id |
  | block_index | int | 区块高度（创世块为 0） |
  | hash | string | 当前区块 SHA-256 哈希 |
  | prev_hash | string | 前一区块哈希 |
  | timestamp | float | 区块时间戳（Unix 秒） |
- **响应示例**：
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "trace_id": "d5dd0dc39b254c2191c0c4fbc96fe764",
      "block_index": 1,
      "hash": "a3f2...",
      "prev_hash": "0000...",
      "timestamp": 1756972800.123
    }
  }
  ```

### 3.4 查询溯源链

- **GET** `/api/trace/{trace_id}`
- **路径参数**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | trace_id | string | 检测端返回的 trace_id |
- **响应字段（data）**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | chain | list | 按 index 升序排列的完整区块列表 |
- **chain 单条结构**：
  ```json
  {
    "index": 0,
    "timestamp": 1756972800.000,
    "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "data_hash": "e3b0...",
    "hash": "5f28...",
    "payload": { "message": "genesis", "trace_id": "..." }
  }
  ```

## 4. 哈希链规则（契约④）

```text
data_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
hash      = sha256(f"{index}{timestamp}{prev_hash}{data_hash}".encode()).hexdigest()
创世块 prev_hash = "0" * 64
```

- `payload` 使用 UTF-8 编码，JSON 键按字母排序。
- 区块通过 `prev_hash` 串联，任一区块被篡改都会导致 `verify_chain()` 返回 `False`。

## 5. 错误响应

统一返回结构仍为 `{code, message, data}`，HTTP 状态码：

| 场景 | HTTP | code | message |
|------|------|------|---------|
| trace_id 缺失 | 400 | 400 | trace_id is required |
| 溯源链不存在 | 404 | 404 | trace_id xxx not found |
| 服务端异常 | 500 | 500 | Internal error: ... |

## 6. W4 前端对接提示

1. 检测接口使用 `multipart/form-data` 上传图片。
2. 拿到 `trace_id` 后调用 `/api/trace` 写入溯源信息。
3. 查询页调用 `/api/trace/{trace_id}` 渲染时间线与哈希验证结果。
4. 所有接口均支持跨域，开发环境可直接调用 `http://localhost:8000`。
