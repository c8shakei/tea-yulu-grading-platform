# 恩施玉露茶品质分级与溯源平台

基于计算机视觉的农产品品质分级与溯源平台（毕业设计）。
前端使用 Vue 3 + Vite + Element Plus + ECharts，后端使用 FastAPI + YOLOv8 + 哈希链溯源。

---

## 项目简介

本项目面向恩施玉露茶，构建一套“检测 - 分级 - 溯源”一体化 Web 平台：

- 用户上传茶叶图片，后端调用 YOLOv8 检测模型给出等级、置信度与边界框。
- 每次检测生成唯一 `trace_id`，写入本地哈希链，保证结果不可篡改。
- 前端通过低代码配置层（UI Schema）动态渲染页面，并提供可视化看板、历史记录与训练曲线。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Vue Router、Pinia、Element Plus、ECharts、Vite |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic |
| 模型 | Ultralytics YOLOv8n / YOLOv8s（检测与分类） |
| 溯源 | SHA-256 哈希链（prev_hash 链接） |
| 数据集 | TeaLeafAgeQuality（Mendeley，CC BY 4.0） |

---

## 目录结构

```
.
├── data/                     # 后端运行时数据（数据库、上传文件）
├── datasets/                 # 数据集软链接（实际数据位于 D 盘，不入仓）
├── docs/                     # 设计文档与过程性资料
├── frontend/                 # Vue 3 前端工程
│   ├── src/
│   │   ├── api/              # 后端接口封装
│   │   ├── components/       # 公共组件与图表组件
│   │   ├── layouts/          # 布局组件
│   │   ├── pages/            # 页面视图
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   └── utils/            # 工具函数
│   └── tests/e2e/            # Playwright E2E 巡检脚本
├── models/                   # 模型权重与训练曲线（大文件，不入仓）
├── scripts/                  # 启动、训练、数据准备脚本
├── src/
│   ├── backend/              # FastAPI 后端源码
│   ├── hashchain/            # 哈希链实现
│   └── inference/            # YOLO 推理封装
├── tests/                    # 后端单元/接口测试
├── data.yaml                 # 数据集配置
├── requirements-backend.txt  # Python 依赖
└── README.md
```

---

## 环境要求

- Python 3.10+
- Node.js 18+（推荐使用 22 LTS）
- Git

---

## 后端启动

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements-backend.txt

# 3. 启动服务
python scripts/start_backend.py
```

后端默认运行在 `http://127.0.0.1:8000`。
接口文档：`http://127.0.0.1:8000/docs`

---

## 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`。

### 环境变量

| 文件 | 作用 | 示例 |
|------|------|------|
| `.env.development` | 开发环境，使用 Vite proxy | `VITE_API_BASE_URL=` |
| `.env.production` | 生产环境，指向真实后端地址 | `VITE_API_BASE_URL=/api` |

---

## 模型权重下载

模型权重文件（`.pt`）体积较大，未提交到 Git 仓库。本地运行时请确保 `models/` 目录包含：

- `best_detect.pt`（YOLOv8n 检测模型）
- `best_cls.pt`（YOLOv8n 分类模型）
- `best_detect_yolov8s.pt`（YOLOv8s 检测模型，可选）
- `best_cls_yolov8s-cls.pt`（YOLOv8s 分类模型，可选）

训练脚本位于 `scripts/` 与 `Colab训练_tea_yulu_yolov8.ipynb`，可在 Colab/Kaggle 运行后导出权重。

---

## 端到端测试

```bash
cd frontend
npm run test:e2e
```

测试脚本 `tests/e2e/manual_check.cjs` 使用 Playwright，覆盖：

- 注册 / 登录 / 登出主链路
- 上传真实茶叶图片进行推理
- 使用 `trace_id` 查询溯源哈希链
- 历史记录、个人中心、训练曲线看板页面渲染
- 负向用例：超大文件、非图片文件、未登录访问受保护路由

---

## 生产构建

```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/`，可通过 Nginx 或任意静态服务器部署。

---

## 许可证

本项目为毕业设计作品，数据集来自 Mendeley（CC BY 4.0）。

---

## 贡献者

- W1：数据工程
- W2：模型训练
- W3：后端与溯源
- W4：前端与可视化
- W5：测试与文档
- 组长：统筹与批复
- 项目经理（PM）：转交与决策上传
