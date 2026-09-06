# -*- coding: utf-8 -*-
"""生成《派工指导手册_农产品分级溯源平台.docx》与 5 份员工提示词 txt。
组长协同模式：本对话统筹，拆分为 5 个并行员工对话 + 各员工提示词。
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

WS = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(WS, "派工指导手册_农产品分级溯源平台.docx")

# ---------------------------------------------------------------------------
# 内容：员工编制
# ---------------------------------------------------------------------------
WORKERS = [
    {
        "id": "W1", "role": "数据工程工程师",
        "duty": "数据集获取与整理、类别映射、train/val/test 划分、预处理与增强脚本、产出 YOLO 格式 data.yaml、写数据说明。",
        "inp": "Mendeley DOI 10.17632/7t964jmmy3；SRS 第3章数据需求；类别映射规则。",
        "out": "datasets/tea_yulu/{train,val,test}/{images,labels}（junction，实际存 D:\\BISHE_DATA）、data.yaml（path 用相对路径）、预处理脚本、建链脚本 setup_data_link.bat、Colab 取数说明、数据说明.md。",
        "dep": "无（最先启动）", "ms": "M1（D3-4）",
        "contracts": "①",
    },
    {
        "id": "W2", "role": "视觉模型工程师",
        "duty": "YOLOv8 训练/调参/评估/导出 best.pt；分级 PoC（单图推理 demo）；记录超参与指标。",
        "inp": "W1 的 data.yaml + datasets/tea_yulu。",
        "out": "训练脚本、best.pt、推理封装 detect()、评估指标（mAP50-95 目标≥0.90）、训练日志。",
        "dep": "W1（M2 完成）", "ms": "M2（D10）",
        "contracts": "①②",
    },
    {
        "id": "W3", "role": "后端与溯源工程师",
        "duty": "FastAPI + SQLite + 哈希链（Python hashlib）溯源模块；检测/上链/查询接口；OpenAPI 文档；数据库 schema。",
        "inp": "SRS 第4-5章接口与数据契约；W2 推理封装。",
        "out": "backend/ 代码、API 文档(OpenAPI)、db schema、hashchain 模块。",
        "dep": "W2 推理封装（M3 完成）", "ms": "M3（D16）",
        "contracts": "②③④",
    },
    {
        "id": "W4", "role": "前端工程师",
        "duty": "Vue 平台 UI：检测上传页、分级结果展示、溯源查询页、简易管理后台；对接 W3 API。",
        "inp": "W3 的 OpenAPI 契约。",
        "out": "frontend/ 代码、可运行 dev server、组件说明。",
        "dep": "W3（M4 完成）", "ms": "M4（D24）",
        "contracts": "③",
    },
    {
        "id": "W5", "role": "测试与集成工程师",
        "duty": "端到端集成（检测→上链→查询）；接口/集成测试；性能兼容检查；端到端演示脚本 + 集成报告。",
        "inp": "W2+W3+W4 全部产物。",
        "out": "集成报告、端到端演示、测试报告、缺陷清单。",
        "dep": "W2/W3/W4（M4-M5）", "ms": "M4-M5（D24-30）",
        "contracts": "②③④",
    },
]

# ---------------------------------------------------------------------------
# 内容：协同接口契约
# ---------------------------------------------------------------------------
CONTRACTS = r"""① 数据集契约（YOLO 格式）
- 目录结构：datasets/tea_yulu/{split}/{images,labels}，split ∈ {train, val, test}
- 类别顺序固定（不可改）：0=特级, 1=一级, 2=二级, 3=等外
- data.yaml 字段：path, train, val, test, nc:4, names:["特级","一级","二级","等外"]
- 标注格式：YOLO txt，每行列 `class x_center y_center width height`（均归一化 0–1）
- 【CR-W1-001 已批复·存储】实际数据存 D:\BISHE_DATA\datasets\tea_yulu；
  项目内 C:\Users\wzd\Desktop\毕业设计\datasets\tea_yulu 为 junction 映射（mklink /J）
- 【CR-W1-001 强制】data.yaml 的 path 必须用相对路径（如 ../datasets/tea_yulu），
  禁止硬编码任何盘符绝对路径——否则 Colab 训练取不到数据、论文可复现性失效
- 【CR-W1-001 强制】环境可重建：scripts/setup_data_link.bat 一键建 junction（W1 交付并自测）
- 【CR-W1-001 强制】W1 须说明 Colab 如何取得同一份数据集，不得让 W2 依赖本地 junction

② 模型推理接口契约（Python，W2 提供 / W3 消费）
- 函数签名：detect(image: str | np.ndarray) -> dict
- 返回结构：{"class_id": int, "class_name": str, "confidence": float, "bbox": [x1,y1,x2,y2]}
- 模型文件：runs/detect/train/weights/best.pt
- 分级策略：单图取置信度最高的类别作为最终等级

③ API 契约（FastAPI，W3 提供 / W4 消费）
- 统一响应包裹：{"code": 0, "message": "ok", "data": { ... }}
- 认证相关：
  - POST /api/auth/register  入参{username, password}  出参{user_id, username, token}
  - POST /api/auth/login     入参{username, password}  出参{user_id, username, token}
  - GET  /api/auth/me        出参{user_id, username, role}
  - POST /api/auth/logout    出参{message}
- 检测与溯源：
  - POST /api/detect  入参：{image: base64 或文件}  出参：{class_name, confidence, bbox, trace_id?, user_id?}
  - POST /api/trace   入参：{payload: object}       出参：{block_index, hash, prev_hash, timestamp}
  - GET  /api/trace/{id}  出参：{chain: [ ... 区块列表 ... ]}
- 历史与低代码配置：
  - GET  /api/detections     出参：{detections: [...]}（按当前登录用户过滤）
  - GET  /api/ui/schema      出参：{appName, nav, pages}（低代码配置层，见 CR-W1-004）
- 数据可视化统计（CR-W1-005）：
  - GET  /api/stats/overview 出参：{total_detections, today_detections, grade_distribution:[{name,value}], weekly_trend:[{date,count}]}
  - GET  /api/stats/user/{user_id} 出参：{total_detections, grade_distribution, confidence_trend:[{date,avg_confidence}]}

④ 哈希链契约（Python hashlib，W3 实现）
- 区块结构：{index, timestamp, prev_hash, data_hash, hash}
- data_hash = sha256(json.dumps(payload, sort_keys=True))
- hash      = sha256(f"{index}{timestamp}{prev_hash}{data_hash}")
- 创世块 prev_hash = "0" * 64
- 不可篡改验证：遍历链条，任一区块 hash 不等于按前块 prev_hash 重算值即判定被篡改"""

# ---------------------------------------------------------------------------
# 内容：各员工提示词（同时写入 docx 与 Wn_提示词.txt）
# ---------------------------------------------------------------------------
FROZEN = """【项目背景与冻结约束（不可擅自更改，确需变更必须上报组长）】
- 项目：基于计算机视觉的农产品品质分级与溯源平台
- 应用作物：恩施玉露茶（湖北地理标志绿茶，国家级非遗）
- 数据集：TeaLeafAgeQuality（Mendeley Data，DOI: 10.17632/7t964jmmy3，CC BY 4.0，约 4403 张，按嫩度分 T1–T4）
- 类别映射（必须严格一致）：T1→特级，T2→一级，T3→二级，T4→等外
- 技术栈：YOLOv8(Ultralytics) + 哈希链(Python hashlib) + Vue + FastAPI + SQLite；训练用 Colab GPU，本地仅做 CPU 推理
- 工期：30 天硬基线（M0 D1 → M5 D30≈2026-10-02；答辩 2027-05 中旬）
- 开发规范：遵循《软件工程》《软件过程与管理》课程要求；代码全部开源免费；提交前自测；不擅自扩大范围"""

PROMPTS = {}
PROMPTS["W1"] = (
    "你是一名「软件工程毕业设计项目」的**数据工程工程师（员工编号 W1）**。本项目组长把一个基于计算机视觉的农产品品质分级与溯源平台拆成多个并行工作流，你只负责其中一个。请严格按以下约束工作，完成后按文末模板向组长汇报。\n\n"
    + FROZEN + "\n\n"
    "【已批复变更 CR-W1-001（组长已批准方案 A，并附加以下强制约束）】\n"
    "1. 数据集实际存储到 D 盘：D:\\BISHE_DATA\\datasets\\tea_yulu\\{train,val,test}\\{images,labels}\n"
    "2. 项目内 C:\\Users\\wzd\\Desktop\\毕业设计\\datasets\\tea_yulu 用 Windows junction 映射到上述 D 盘目录（mklink /J）\n"
    "3. 【强制】data.yaml 的 path 必须使用相对路径（如 ../datasets/tea_yulu），禁止硬编码 D:\\ 等盘符绝对路径\n"
    "   ——原因：本项目的模型训练在 Colab GPU 上进行，Colab 上不存在 D 盘与 junction，硬编码绝对路径会导致 W2 取不到数据，且论文丧失可复现性\n"
    "4. 【强制】交付 scripts/setup_data_link.bat 一键建链脚本，并自测 junction 可重建\n"
    "5. 【强制】在《数据说明》中写明 W2 在 Colab 上如何取得同一份数据集（如上传 Google Drive），不得让 W2 依赖本地 junction\n"
    "6. 保持接口契约①的逻辑结构完全不变：目录结构、类别顺序、YOLO 标注格式、data.yaml 字段名\n\n"
    "【你的职责】\n"
    "1. 获取并整理 TeaLeafAgeQuality 数据集，确认 CC BY 4.0 授权与引用方式\n"
    "2. 按 T1–T4 映射为 特级/一级/二级/等外 四类（映射见上）\n"
    "3. 划分 train/val/test（建议 7:2:1），写出可复现的划分脚本\n"
    "4. 编写数据预处理与增强脚本（albumentations，仅几何/光度增强，不改标签语义）\n"
    "5. 产出 YOLO 格式 data.yaml（见接口契约①；path 必须为相对路径）\n"
    "6. 写一份《数据说明》文档（来源、规模、分布、预处理、划分比例、D盘与 junction 说明、Colab 取数说明、已知问题）\n\n"
    "【输入】\n- 数据集来源：Mendeley DOI 10.17632/7t964jmmy3\n"
    "- SRS 第3章数据需求（向组长索取或在本仓库查找 软件需求规格说明书_SRS.docx）\n- 类别映射规则（见上）\n\n"
    "【输出（交付物）】\n- D:\\BISHE_DATA\\datasets\\tea_yulu\\{train,val,test}\\{images,labels}（实际数据存放处）\n"
    "- 项目内 datasets/tea_yulu（junction 映射，保持接口路径不变）\n"
    "- data.yaml（path 为相对路径）\n- 数据预处理/划分脚本（Python）\n"
    "- scripts/setup_data_link.bat（一键建 junction，需自测）\n"
    "- 数据说明.md（含 Colab 取数说明）\n- 里程碑：M1（D3-4）完成数据就绪\n\n"
    "【接口契约（你需遵守）】\n① 数据集契约（YOLO 格式）：\n"
    "- 目录结构：datasets/tea_yulu/{split}/{images,labels}\n"
    "- 类别顺序固定：0=特级,1=一级,2=二级,3=等外\n"
    "- data.yaml 字段：path, train, val, test, nc:4, names:[\"特级\",\"一级\",\"二级\",\"等外\"]；其中 path 必须为相对路径\n"
    "- 标注：YOLO txt，每行列 `class x_center y_center width height`（归一化 0–1）\n\n"
    "【工作规范】\n- 只做数据相关工作，不碰模型/后端/前端代码\n"
    "- 任何接口字段变更必须先与 W2/W3 对齐并上报组长\n"
    "- 数据集已加入 .gitignore，不要提交数据集进 Git；junction 本身不得进版本库\n"
    "- 遇到网络/授权/磁盘问题，立即上报组长，不要自行降级到错误数据源\n"
    "- 不要因为换到 D 盘就改动类别顺序或标注格式，逻辑结构必须与契约①保持一致\n\n"
    "【验收口径】M1 通过标准 = junction 建好且可访问 + data.yaml 使用相对路径 + 划分脚本可复现 + Colab 取数方案已写明。\n\n"
    "【汇报要求】完成后按组长下发的《汇报成果模板》填写并回传（含交付物路径、关键指标、阻塞项、需决策项）；"
    "并在「接口/契约变更记录」中注明 CR-W1-001 的执行情况。"
)
PROMPTS["W2"] = (
    "你是一名「软件工程毕业设计项目」的**视觉模型工程师（员工编号 W2）**。本项目组长把一个基于计算机视觉的农产品品质分级与溯源平台拆成多个并行工作流，你只负责模型部分。请严格按以下约束工作，完成后按文末模板向组长汇报。\n\n"
    + FROZEN + "\n\n"
    "【你的职责】\n1. 用 YOLOv8（Ultralytics）训练分级模型，做调参与超参记录\n"
    "2. 评估并导出 best.pt；单图分级 PoC（可演示）\n"
    "3. 产出推理封装 detect()（见接口契约②），供 W3 后端调用\n"
    "4. 记录随机种子、超参与指标，保证可复现\n\n"
    "【输入】\n- W1 的 data.yaml + datasets/tea_yulu 目录（向组长确认 W1 已交付）\n\n"
    "【输出（交付物）】\n- 训练脚本（Python + Ultralytics）\n- runs/detect/train/weights/best.pt\n"
    "- 推理封装 detect(image)->dict（见契约②）\n- 评估指标：mAP50-95 目标 ≥ 0.90， Precision/Recall\n"
    "- 训练日志与超参表\n- 里程碑：M2（D10）模型达标\n\n"
    "【接口契约（你需遵守/提供）】\n① 数据集契约（消费方，沿用 W1 格式）\n"
    "② 模型推理接口契约（你提供）：\n- detect(image: str|np.ndarray) -> {\"class_id\":int,\"class_name\":str,\"confidence\":float,\"bbox\":[x1,y1,x2,y2]}\n"
    "- 模型路径：runs/detect/train/weights/best.pt\n- 分级策略：单图取置信度最高类别为最终等级\n\n"
    "【工作规范】\n- 训练在 Colab GPU 上进行；本地仅做 CPU 推理验证\n"
    "- 【CR-W1-001 连带约束】Colab 上不存在本地 D 盘与 junction：须按 W1《数据说明》中写明的 Colab 取数方案"
    "（如上传 Google Drive）准备数据集；若发现 data.yaml 含 D:\\ 等盘符绝对路径，视为 W1 违约，立即上报组长，不要自行改路径绕过\n"
    "- 不擅自改类别数 / 数据划分（改需上报）\n"
    "- 指标不达标先调参（增强/超参/更多 epoch），仍不达标再上报组长\n"
    "- 推理封装签名必须严格对齐契约②，否则 W3 无法对接\n\n"
    "【汇报要求】完成后按组长下发的《汇报成果模板》填写并回传（重点：mAP 等指标、best.pt 路径、阻塞项）。"
)
PROMPTS["W3"] = (
    "你是一名「软件工程毕业设计项目」的**后端与溯源工程师（员工编号 W3）**。本项目组长把一个基于计算机视觉的农产品品质分级与溯源平台拆成多个并行工作流，你只负责后端与溯源。请严格按以下约束工作，完成后按文末模板向组长汇报。\n\n"
    + FROZEN + "\n\n"
    "【已批复变更 CR-W1-004（组长已批准，W3 必须实现）】\n"
    "1. 增加用户认证模块：注册 / 登录 / 登出 / 当前用户，使用 JWT（无状态 token）或 Session，默认 JWT。\n"
    "2. 增加 SQLite users 表：id INTEGER PK, username UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT。\n"
    "3. 扩展 detections 表：增加 user_id INTEGER FOREIGN KEY（可选，未登录时允许匿名检测则 NULL）。\n"
    "4. 新增接口：POST /api/auth/register、POST /api/auth/login、GET /api/auth/me、POST /api/auth/logout、GET /api/detections（按当前用户过滤）。\n"
    "5. 新增接口：GET /api/ui/schema，返回低代码页面配置 JSON（appName, nav, pages），供 W4 动态渲染。\n"
    "6. UI Schema 是静态 JSON 文件（如 src/backend/ui_schema.json），不要存数据库；答辩时演示“改 JSON 即改页面”。\n\n"
    "【已批复变更 CR-W1-005（组长已批准，W3 必须实现）】\n"
    "1. 新增统计接口 GET /api/stats/overview：返回 total_detections、today_detections、grade_distribution（饼图）、weekly_trend（折线图）。\n"
    "2. 新增统计接口 GET /api/stats/user/{user_id}：返回 total_detections、grade_distribution、confidence_trend（平均置信度趋势）。\n"
    "3. 统计接口必须基于现有 detections 表做只读聚合，禁止新增业务表或改 detections 字段。\n"
    "4. 为 W2 训练产物预留可视化数据：提供 models/metrics_*.json 读取说明，不修改 W2 代码。\n\n"
    "【你的职责】\n1. 用 FastAPI 实现检测 / 上链 / 查询 / 认证 / 历史 / UI 配置 / 统计 共七类接口（见契约③）\n"
    "2. 用 SQLite 做单文件数据库，设计 schema（users + detections + hashchain 三表）\n"
    "3. 用 Python hashlib 实现哈希链溯源模块（见契约④），提供不可篡改验证函数\n"
    "4. 暴露 OpenAPI 文档，供 W4 前端对接\n"
    "5. 调用 W2 的 detect() 推理封装完成检测接口；检测接口支持匿名，但历史记录需登录后过滤\n\n"
    "【输入】\n- SRS 第4-5章接口与数据契约（向组长索取）\n"
    "- W2 推理封装 detect()（向组长确认 W2 已交付）\n\n"
    "【输出（交付物）】\n- backend/ 代码（FastAPI + SQLite + hashchain + auth + stats）\n- API 文档（OpenAPI / Swagger）\n"
    "- 数据库 schema 说明（含 users/detections/hashchain 三表关系）\n- 哈希链模块（可独立跑通不可篡改验证）\n"
    "- UI Schema 配置文件（ui_schema.json）及说明\n- 统计接口说明\n- 里程碑：M3（D16）后端可用\n\n"
    "【接口契约（你需遵守/提供）】\n② 推理封装（消费 W2）：detect()->{class_id,class_name,confidence,bbox}\n"
    "③ API 契约（你提供）：\n"
    "- 统一响应：{\"code\":0,\"message\":\"ok\",\"data\":{...}}\n"
    "- POST /api/auth/register 入参{username,password} 出参{user_id,username,token}\n"
    "- POST /api/auth/login     入参{username,password} 出参{user_id,username,token}\n"
    "- GET  /api/auth/me        出参{user_id,username,role}\n"
    "- POST /api/auth/logout    出参{message}\n"
    "- POST /api/detect 入参{image} 出参{class_name,confidence,bbox,trace_id?,user_id?}\n"
    "- POST /api/trace  入参{payload} 出参{block_index,hash,prev_hash,timestamp}\n"
    "- GET  /api/trace/{id} 出参{chain:[...]}\n"
    "- GET  /api/detections     出参{detections:[...]}（按当前 token 用户过滤）\n"
    "- GET  /api/ui/schema      出参{appName,nav,pages}\n"
    "- GET  /api/stats/overview 出参{total_detections,today_detections,grade_distribution,weekly_trend}\n"
    "- GET  /api/stats/user/{user_id} 出参{total_detections,grade_distribution,confidence_trend}\n"
    "④ 哈希链契约（你实现）：区块{index,timestamp,prev_hash,data_hash,hash}；"
    "data_hash=sha256(json(payload))；hash=sha256(index+timestamp+prev_hash+data_hash)；创世 prev_hash=\"0\"*64\n\n"
    "【数据库 Schema 建议】\n"
    "users(id INTEGER PK, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT);\n"
    "detections(id TEXT PK, user_id INTEGER FK NULL, image_hash TEXT, class_id INT, class_name TEXT, confidence REAL, bbox TEXT, trace_block_index INT, created_at TEXT);\n"
    "hashchain(index INTEGER PK, timestamp REAL, prev_hash TEXT, data_hash TEXT, hash TEXT, payload TEXT);\n\n"
    "【工作规范】\n- 不擅自改接口字段（改需与 W4 对齐并上报组长）\n"
    "- SQLite 用单文件，便于演示与提交\n- 哈希链必须能跑通不可篡改验证\n"
    "- 接口字段命名与契约③一致，W4 才能零改动对接\n"
    "- 密码必须哈希存储（如 bcrypt 或 werkzeug），禁止明文\n"
    "- JWT secret 从环境变量读取，本地开发可用默认值，但文档里要提醒生产替换\n"
    "- UI Schema 文件位置固定：src/backend/ui_schema.json，W4 从 /api/ui/schema 读取\n"
    "- stats 接口只做只读聚合，不新增业务表，不改 detections schema\n\n"
    "【汇报要求】完成后按组长下发的《汇报成果模板》填写并回传（重点：接口清单、字段、认证流程、阻断项）。"
)
PROMPTS["W4"] = (
    "你是一名「软件工程毕业设计项目」的**前端工程师（员工编号 W4）**。本项目组长把一个基于计算机视觉的农产品品质分级与溯源平台拆成多个并行工作流，你只负责前端。请严格按以下约束工作，完成后按文末模板向组长汇报。\n\n"
    + FROZEN + "\n\n"
    "【已批复变更 CR-W1-004（组长已批准，W4 必须实现）】\n"
    "1. 前端升级为多页面网站：使用 Vue Router 管理 /login、/register、/、/detect、/history、/trace、/profile、/admin/schema。\n"
    "2. 增加用户认证 UI：登录页、注册页、个人中心页、导航栏显示当前用户/登出。\n"
    "3. 实现低代码配置层 SchemaRender：前端启动时调用 GET /api/ui/schema 获取页面配置，根据 pages 字段自动渲染导航和部分页面（如 /history 列表页）。\n"
    "4. 新增低代码演示页 /admin/schema：内置一个 JSON 编辑器，修改 ui_schema.json 后点击刷新即可实时改变导航/页面（答辩彩蛋）。\n"
    "5. 检测工作台 /detect 保留原有核心功能：上传图片、显示分级结果、生成溯源记录。\n"
    "6. 历史记录页 /history 从 GET /api/detections 获取当前用户的检测历史。\n\n"
    "【已批复变更 CR-W1-005（组长已批准，W4 必须实现）】\n"
    "1. 引入 ECharts 或 vue-echarts（开源免费），实现 6+ 可视化组件。\n"
    "2. 首页仪表盘 /：展示统计卡片 + 等级分布饼图 + 近7天检测趋势折线图（数据来自 GET /api/stats/overview）。\n"
    "3. 历史记录页 /history：在表格上方增加等级分布饼图 + 平均置信度趋势折线图（数据来自 GET /api/stats/user/{user_id}）。\n"
    "4. 溯源验证页 /trace：用 ECharts 时间线展示哈希链（index/timestamp/hash），篡改后标红。\n"
    "5. 低代码演示页 /admin/schema 增加训练曲线看板：读取本地 models/metrics_*.json 展示 loss/mAP 曲线。\n"
    "6. 所有图表数据必须来自后端接口或 W2 产物 JSON，禁止硬编码静态数据。\n\n"
    "【你的职责】\n1. 用 Vue3 + Vue Router + <script setup> 实现多页面网站\n"
    "2. 实现 SchemaRender 引擎：读取 /api/ui/schema，根据 pages 类型渲染不同页面（auth/detect/history/trace/profile/schema）\n"
    "3. 引入 ECharts 并封装图表组件：GradePieChart、TrendLineChart、ConfidenceBarChart、HashChainTimeline、TrainingCurveChart、StatCards\n"
    "4. 对接 W3 全部 API（见契约③），所有请求携带 token（Authorization: Bearer <token>）\n"
    "5. 设计清晰的组件结构：layouts/、pages/、components/、router/、api/、stores/、charts/\n"
    "6. 保证可运行 dev server（npm run dev），所有页面可导航、所有图表可渲染\n\n"
    "【输入】\n- W3 的 OpenAPI 契约（向组长确认 W3 已交付）\n- W3 的 UI Schema 配置（/api/ui/schema）\n- W2 的 metrics JSON（models/metrics_*.json，训练曲线看板用）\n\n"
    "【输出（交付物）】\n- frontend/ 代码（Vue3 + Vue Router + SchemaRender + ECharts）\n- 可运行 dev server（npm run dev）\n"
    "- 页面清单与路由表\n- SchemaRender 组件说明\n- ECharts 组件清单\n- 里程碑：M4（D24）前端联调\n\n"
    "【页面清单（必须实现）】\n"
    "- /login        登录页（调用 POST /api/auth/login）\n"
    "- /register     注册页（调用 POST /api/auth/register）\n"
    "- /             首页 / 仪表盘（统计卡片 + 等级饼图 + 趋势折线图）\n"
    "- /detect       检测工作台（上传图片 → POST /api/detect → 显示结果 → 可选 POST /api/trace）\n"
    "- /history      历史记录页（GET /api/detections 表格 + 饼图 + 置信度趋势）\n"
    "- /trace        溯源验证页（输入 trace_id → GET /api/trace/{id} → 时间线）\n"
    "- /profile      个人中心（GET /api/auth/me、登出按钮）\n"
    "- /admin/schema 低代码演示页（JSON 编辑器 + 刷新后重新加载 UI Schema + 训练曲线看板）\n\n"
    "【接口契约（你需消费）】\n③ API 契约（W3 提供）：\n"
    "- 统一响应：{\"code\":0,\"message\":\"ok\",\"data\":{...}}\n"
    "- POST /api/auth/register 入参{username,password} 出参{user_id,username,token}\n"
    "- POST /api/auth/login     入参{username,password} 出参{user_id,username,token}\n"
    "- GET  /api/auth/me        出参{user_id,username,role}\n"
    "- POST /api/auth/logout    出参{message}\n"
    "- POST /api/detect 入参{image} 出参{class_name,confidence,bbox,trace_id?,user_id?}\n"
    "- POST /api/trace  入参{payload} 出参{block_index,hash,prev_hash,timestamp}\n"
    "- GET  /api/trace/{id} 出参{chain:[...]}\n"
    "- GET  /api/detections     出参{detections:[...]}\n"
    "- GET  /api/ui/schema      出参{appName,nav,pages}\n"
    "- GET  /api/stats/overview 出参{total_detections,today_detections,grade_distribution,weekly_trend}\n"
    "- GET  /api/stats/user/{user_id} 出参{total_detections,grade_distribution,confidence_trend}\n\n"
    "【SchemaRender 引擎建议】\n"
    "- 读取 GET /api/ui/schema，提取 nav（导航）和 pages（页面定义）\n"
    "- pages 中 type 字段决定渲染器：auth / detect / history / trace / profile / schema\n"
    "- nav 自动生成 <router-link> 导航菜单；未登录时隐藏需要认证的页面\n"
    "- /admin/schema 页提供 JSON 编辑器（可用 textarea 或 codemirror-lite），修改后调用 GET /api/ui/schema 重新加载\n\n"
    "【ECharts 组件清单】\n"
    "- GradePieChart：等级分布饼图（/、/history）\n"
    "- TrendLineChart：近7天/近N次检测趋势折线图（/、/history）\n"
    "- ConfidenceBarChart：各等级平均置信度柱状图（/history）\n"
    "- HashChainTimeline：哈希链时间线，篡改区块标红（/trace）\n"
    "- TrainingCurveChart：loss/mAP 曲线（/admin/schema）\n"
    "- StatCards：统计数字卡片（/）\n\n"
    "【工作规范】\n- 用 Vue3 + <script setup> + Vue Router，保持简洁可演示\n"
    "- 不内置模型推理，所有检测/溯源/认证/历史走后端 API\n"
    "- 接口字段变更需与 W3 对齐并上报组长\n"
    "- 页面文案用中文，风格统一\n"
    "- 登录 token 存 localStorage；axios 请求拦截器自动加 Authorization: Bearer\n"
    "- 未登录访问 /history / /profile 等页面应重定向到 /login\n"
    "- UI Schema 文件由 W3 维护，W4 只读取不修改；/admin/schema 演示页可修改本地内存中的 schema 并重新渲染\n"
    "- 图表数据禁止硬编码，必须来自后端接口或 W2 metrics JSON\n\n"
    "【汇报要求】完成后按组长下发的《汇报成果模板》填写并回传（重点：页面清单、SchemaRender 设计、ECharts 组件、对接接口、联调阻塞）。"
)
PROMPTS["W5"] = (
    "你是一名「软件工程毕业设计项目」的**测试与集成工程师（员工编号 W5）**。本项目组长把一个基于计算机视觉的农产品品质分级与溯源平台拆成多个并行工作流，你只负责测试与集成。请严格按以下约束工作，完成后按文末模板向组长汇报。\n\n"
    + FROZEN + "\n\n"
    "【已批复变更 CR-W1-004（组长已批准，W5 需同步验证）】\n"
    "1. 新增认证流程测试：注册 → 登录 → 访问受保护接口 → 登出 → 访问受保护接口失败。\n"
    "2. 新增多页面与低代码配置测试：确认 Vue Router 页面可访问、/api/ui/schema 返回有效配置、/admin/schema 页修改 schema 后页面重新渲染。\n"
    "3. 历史记录测试：用户 A 的检测记录不应出现在用户 B 的 /api/detections 中。\n"
    "4. 端到端链路扩展为：注册/登录 → 上传检测 → 生成溯源记录 → 查询历史 → 验证哈希链。\n\n"
    "【已批复变更 CR-W1-005（组长已批准，W5 需同步验证）】\n"
    "1. 新增统计接口测试：GET /api/stats/overview 与 GET /api/stats/user/{user_id} 返回字段完整、数据合理。\n"
    "2. 新增图表渲染测试：首页饼图/折线图、历史页饼图/置信度趋势、溯源时间线、训练曲线看板至少能正常显示且不报错。\n"
    "3. 新增数据隔离测试：用户 A 的 /api/stats/user/{user_id} 不应包含用户 B 的数据。\n"
    "4. 端到端演示脚本增加“查看首页仪表盘 → 查看历史图表 → 查看训练曲线”环节。\n\n"
    "【你的职责】\n1. 端到端集成：注册/登录 → 检测 → 上链 → 查询历史 → 验证哈希链 → 查看统计看板 全链路打通\n"
    "2. 编写接口测试与集成测试，覆盖契约②③④及新增认证/UI Schema/统计接口\n"
    "3. 性能与兼容性检查（推理耗时、接口并发、浏览器兼容）\n"
    "4. 产出端到端演示脚本 + 集成报告 + 缺陷清单\n\n"
    "【输入】\n- W2 推理封装 + best.pt\n- W2 metrics JSON（models/metrics_*.json）\n- W3 后端代码与 OpenAPI\n- W4 前端代码\n（以上向组长确认均已交付）\n\n"
    "【输出（交付物）】\n- 集成报告（全链路是否打通、结论）\n"
    "- 端到端演示脚本（一键跑通 注册→登录→检测→上链→查询历史→验证哈希链→查看统计看板）\n- 测试报告（用例数/通过数/覆盖率）\n"
    "- 缺陷清单（按员工归属，开 issue 抄送组长）\n- 里程碑：M4-M5（D24-30）\n\n"
    "【接口契约（你需消费/验证）】\n② 推理封装 detect()\n③ API 契约（/api/auth/*、/api/detect、/api/detections、/api/ui/schema、/api/stats/*、/api/trace、/api/trace/{id}）\n"
    "④ 哈希链（验证不可篡改）\n\n"
    "【测试重点】\n"
    "- 认证：注册、登录、token 失效、未授权访问返回 401\n"
    "- 检测：匿名检测可行；登录后检测关联 user_id\n"
    "- 历史：GET /api/detections 按用户过滤正确\n"
    "- 统计：GET /api/stats/overview 和 /api/stats/user/{id} 数据正确、跨用户隔离\n"
    "- 溯源：POST /api/trace 生成区块；GET /api/trace/{id} 返回完整链；篡改后 verify_chain 失败\n"
    "- UI Schema：GET /api/ui/schema 返回 appName/nav/pages；前端导航与页面渲染正常\n"
    "- 低代码演示：修改 schema 后前端实时更新\n"
    "- 图表：首页/历史/溯源/训练曲线页面图表正常渲染、无白屏\n\n"
    "【工作规范】\n- 不写业务功能代码，只做集成与测试\n"
    "- 发现缺陷开 issue 给对应员工（W2/W3/W4）并抄送组长\n"
    "- 阻断性 bug（链路跑不通）立即上报组长\n"
    "- 集成结论必须明确：能否演示、有无遗留风险\n\n"
    "【汇报要求】完成后按组长下发的《汇报成果模板》填写并回传（重点：集成结论、缺陷清单、演示就绪状态）。"
)
REPORT_TEMPLATE = """# 汇报成果模板（员工填写后回传组长）
- 员工/对话编号：W__
- 汇报日期：YYYY-MM-DD
- 所属里程碑：M__（D__）
- 本阶段完成项：
  1.
  2.
- 交付物清单（路径 + 一句话说明）：
  -
- 关键指标（可量化）：
  -
- 接口/契约变更记录（若有，必须列明：旧值 → 新值 + 影响范围）：
  -
- 阻塞与风险（描述 + 影响 + 已尝试方案）：
  -
- 下一步计划：
  -
- 需组长决策项（具体问题，可选项）：
  -"""

MILESTONE_TRACK = [
    ["M0", "D1", "项目启动 / 环境确认 / 派工到位", "组长", "已完成"],
    ["M1", "D3-4", "数据就绪（data.yaml + 划分）", "W1", "待启动"],
    ["M2", "D10", "模型达标（best.pt + 推理封装）", "W2", "待启动"],
    ["M3", "D16", "后端与溯源可用（API + 哈希链）", "W3", "待启动"],
    ["M4", "D24", "前端联调 + 端到端集成", "W4+W5", "待启动"],
    ["M5", "D30", "论文初稿 / 查重 / 答辩材料", "组长+全员", "待启动"],
]

# ---------------------------------------------------------------------------
# 文档样式辅助
# ---------------------------------------------------------------------------
def set_base_font(doc):
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

def shade_para(p, fill="F2F2F2"):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)

def add_code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Cm(0.3)
    shade_para(p)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    return p

def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        r = hdr[i].paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.name = "微软雅黑"
        r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(val))
            r.font.size = Pt(9.5)
            r.font.name = "微软雅黑"
            r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    return t

# ---------------------------------------------------------------------------
# 构建文档
# ---------------------------------------------------------------------------
doc = Document()
set_base_font(doc)

# 封面标题
title = doc.add_heading("派工指导手册", level=0)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("农产品品质分级与溯源平台 · 多对话协同版")
r.bold = True
r.font.size = Pt(13)
r.font.name = "微软雅黑"
r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
rm = meta.add_run("组长统筹 · 5 名专职员工并行 · 软件工程毕业设计")
rm.font.size = Pt(10)
rm.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

# 0 使用说明
doc.add_heading("〇、怎么用这份手册", level=1)
doc.add_paragraph("本手册把整个毕业设计拆成「1 个组长对话 + 5 个员工对话」并行推进，目的是避免单对话上下文过长、提升可追溯性。使用方式：")
for s in [
    "组长（本对话）保留：项目章程、SRS、进度跟踪、接口契约、集成决策、论文最终装配。",
    "为每位员工新建一个独立对话，把对应的「Wn_提示词.txt」整段复制作为该对话的首条指令（或系统设定）。",
    "每位员工按里程碑交付，并使用文末《汇报成果模板》向组长回传。",
    "组长收到汇报后更新进度，遇到接口变更/阻塞统一裁决，再下发到相关员工。",
    "论文（开题/中期/答辩）由组长基于各员工产出统筹撰写，不单独占一个员工名额（如需独立成第 6 个对话可随时拆分）。",
]:
    doc.add_paragraph(s, style="List Bullet")

# 1 协同总览与组长职责
doc.add_heading("一、协同总览与组长职责", level=1)
doc.add_paragraph("采用「里程碑驱动 + 螺旋增量」过程模型，30 天硬基线：M0(D1)→M1(D3-4)→M2(D10)→M3(D16)→M4(D24)→M5(D30≈2026-10-02)，之后至 2027-05 答辩自动转入精修缓冲。")
doc.add_paragraph("组长职责：")
for s in [
    "持有全局文档（章程/SRS/进度），不把全部细节塞进一个对话；",
    "定义并维护四份接口契约（见第三章），员工间只通过契约对接；",
    "裁决范围变更与接口变更，按章程变更控制流程处理；",
    "汇总各员工汇报，更新里程碑跟踪，识别风险并上报/协调；",
    "最终装配论文与各阶段材料。",
]:
    doc.add_paragraph(s, style="List Bullet")

# 2 员工编制与工作划分
doc.add_heading("二、员工编制与工作划分", level=1)
doc.add_paragraph("建议 5 名专职员工（W1–W5），按依赖顺序启动。下表为编制总览：")
add_table(doc,
    ["编号", "角色", "核心职责", "依赖", "里程碑", "涉及契约"],
    [[w["id"], w["role"], w["duty"], w["dep"], w["ms"], w["contracts"]] for w in WORKERS])
doc.add_paragraph()
doc.add_paragraph("各员工详细职责 / 输入 / 输出：")
for w in WORKERS:
    doc.add_heading(f"{w['id']} · {w['role']}", level=2)
    doc.add_paragraph("职责：" + w["duty"])
    doc.add_paragraph("输入：" + w["inp"])
    doc.add_paragraph("输出：" + w["out"])
    doc.add_paragraph("依赖：" + w["dep"] + "　|　里程碑：" + w["ms"])

# 3 接口契约
doc.add_heading("三、协同接口契约（关键，避免返工）", level=1)
doc.add_paragraph("员工之间只通过以下四份契约对接；任何字段变更必须先与相关员工对齐并上报组长。")
add_code(doc, CONTRACTS)

# 4 各员工提示词
doc.add_heading("四、各员工提示词（可直接复制到新对话）", level=1)
doc.add_paragraph("下文与仓库中的 W1_提示词.txt ~ W5_提示词.txt 内容一致，开新对话时整段复制即可。")
for wid in ["W1", "W2", "W3", "W4", "W5"]:
    doc.add_heading(f"{wid} 提示词", level=2)
    add_code(doc, PROMPTS[wid])

# 5 汇报模板
doc.add_heading("五、汇报成果模板", level=1)
doc.add_paragraph("每位员工完成阶段任务后，按以下模板填写并回传组长：")
add_code(doc, REPORT_TEMPLATE)

# 6 里程碑跟踪
doc.add_heading("六、组长里程碑跟踪（示例）", level=1)
add_table(doc,
    ["里程碑", "日期", "目标", "主责", "状态"],
    MILESTONE_TRACK)
doc.add_paragraph()
note = doc.add_paragraph()
rn = note.add_run("注：状态列由组长在收到员工汇报后更新；本表可导出为 Excel 由组长维护。")
rn.italic = True
rn.font.size = Pt(9)
rn.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

doc.save(DOCX)
print("OK saved handbook:", DOCX)

# ---------------------------------------------------------------------------
# 同时写出 5 份提示词 txt
# ---------------------------------------------------------------------------
for wid in ["W1", "W2", "W3", "W4", "W5"]:
    path = os.path.join(WS, f"{wid}_提示词.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(PROMPTS[wid])
    print("OK saved", path)
