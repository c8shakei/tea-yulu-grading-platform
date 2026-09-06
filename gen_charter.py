# -*- coding: utf-8 -*-
"""生成《毕业设计项目章程与进度计划》Word 文档（30天压缩基线版）"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CJK = "微软雅黑"; HEI = "黑体"; SONG = "宋体"
doc = Document()

def set_cjk(run, name=CJK, size=None, bold=False):
    run.font.name = name; run.font.size = Pt(size) if size else None; run.bold = bold
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), name); rFonts.set(qn('w:ascii'), name); rFonts.set(qn('w:hAnsi'), name)

normal = doc.styles['Normal']; normal.font.name = CJK; normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), CJK)

def H(text, level=1):
    p = doc.add_heading(level=level); r = p.add_run(text)
    set_cjk(r, HEI if level <= 2 else CJK, size=16 if level==1 else (13 if level==2 else 11.5), bold=True); return p
def P(text, bold=False, size=10.5, color=None, italic=False):
    p = doc.add_paragraph(); r = p.add_run(text); set_cjk(r, CJK, size, bold); r.italic = italic
    if color: r.font.color.rgb = color; return p
def BULLET(text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level==0 else 'List Bullet 2'); r = p.add_run(text); set_cjk(r, CJK, 10.5); return p
def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""; r = hdr[i].paragraphs[0].add_run(h); set_cjk(r, HEI, 10, bold=True); hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(val)); set_cjk(r, CJK, 9.5)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows: row.cells[i].width = Cm(w)
    return t

# 封面
title = doc.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("毕业设计项目章程与进度计划（30天压缩基线）"); set_cjk(r, HEI, 20, bold=True)
sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("基于计算机视觉的农产品品质分级与溯源平台（YOLOv8 + 哈希链溯源）"); set_cjk(r, CJK, 12, bold=True)
meta = doc.add_paragraph(); meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = meta.add_run("版本 V1.1（30天硬基线）  |  制定日期：2026-09-03  |  制定人：Diana（项目架构师 / PM）"); set_cjk(r, CJK, 10)
doc.add_paragraph()

P("目录（打开后右键“更新域”→“更新整个目录”即可生成）", italic=True, size=9.5, color=RGBColor(0x66,0x66,0x66))
toc = doc.add_paragraph(); run = toc.add_run()
fldBegin = OxmlElement('w:fldChar'); fldBegin.set(qn('w:fldCharType'), 'begin')
instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = 'TOC \\o "1-3" \\h \\z \\u'
fldSep = OxmlElement('w:fldChar'); fldSep.set(qn('w:fldCharType'), 'separate')
fldText = OxmlElement('w:t'); fldText.text = "右键更新域生成目录"
fldEnd = OxmlElement('w:fldChar'); fldEnd.set(qn('w:fldCharType'), 'end')
run._r.append(fldBegin); run._r.append(instr); run._r.append(fldSep); run._r.append(fldText); run._r.append(fldEnd)
doc.add_page_break()

# 一、章程
H("一、项目章程（Project Charter）", 1)
H("1.1 项目愿景与背景", 2)
P("本毕业设计面向乡村振兴与农产品质量安全的现实需求，构建一套“分级—溯源”一体化的可信平台：")
BULLET("分级侧：以计算机视觉（YOLOv8）替代人工目测，实现农产品外观品质的自动、客观、可量化分级；")
BULLET("溯源侧：以基于哈希链（Python hashlib 不可篡改链式日志）记录分级结果与流通节点，解决传统溯源“中心化易篡改、信任难建立”的痛点；")
BULLET("创新点：将分级结果作为可信数据直接上链，打通“检测—上链—查询”闭环。")
H("1.2 项目目标（SMART）", 2)
table(["维度","目标描述","可度量指标"],
[["Specific","完成一套端到端可演示的分级+溯源平台（含模型、哈希链存证模块、前后端）","系统可运行 demo 1 套"],
 ["Measurable","分级模型达到可用精度，溯源上链查询正确率 100%","mAP@0.5 ≥ 0.85；上链/查询成功率 100%"],
 ["Achievable","基于公开数据集+AI全量编码，技术路线成熟可控","PoC 阶段已验证可行性"],
 ["Relevant","紧扣专业方向（软件工程+AI），符合毕业设计选题要求","通过开题评审"],
 ["Time-bound","30 天内完成系统+论文初稿；答辩按学校日历","见第四节 30 天甘特"]],
 widths=[2.2,9.5,4.5])
H("1.3 范围（冻结，防范围蔓延）", 2)
P("【范围内 In-Scope】", bold=True)
BULLET("单一农产品类别的分级模型（首版聚焦 1 类：恩施玉露茶，预留多类扩展）；")
BULLET("YOLOv8 训练、推理 API、哈希链存证模块、Vue 前端、端到端集成；")
BULLET("论文及答辩全套材料（初稿在 D30 就绪）。")
P("【范围外 Out-of-Scope】", bold=True)
BULLET("多模态（气味/硬度）传感分级；面向消费者的移动 App；跨企业分布式账本运营（本版为本地哈希链存证，不做多节点共识）。")
P("⚠️ 任何新增功能须走“变更控制”（见 1.5），不得擅自并入主干。", italic=True, color=RGBColor(0xC0,0x39,0x2B))
H("1.4 干系人与角色职责", 2)
table(["角色","承担者","职责"],
[["产品负责人 / 决策者","你（学生）","需求与范围裁定、关键决策、论文内容把关、与导师/学校对接"],
 ["项目架构师 / PM","Diana（我）","章程与计划制定、架构设计、进度统筹、AI编码指挥、风险监控"],
 ["开发执行","AI 编码代理","按 DESIGN.md / SRS 生成代码、单元测试、文档初稿"],
 ["指导老师 / 学校","外部","开题/中期/答辩评审，流程节点约束"]],
 widths=[3.5,3.0,9.7])
H("1.5 决策与变更控制协议", 2)
BULLET("日常推进由 Diana 按章程自主执行，无需每步确认；")
BULLET("出现方案分歧 / 范围冲突时，交你（产品负责人）最终裁定，不自动调和；")
BULLET("新增需求须经：提出→影响评估（工期/风险）→你审批→更新章程版本号→方可纳入；")
BULLET("章程每次变更递增版本号（V1.1→V1.2…），旧版归档不删。")
H("1.6 已锁定的技术决策", 2)
table(["决策项","选定","理由（一句话）"],
[["前端框架","Vue（你指定）","你指定；Vue 生态成熟、AI 编码友好"],
 ["溯源实现","Python（Diana 代定）","哈希链用 Python hashlib 实现，零依赖最简单"],
 ["数据库","SQLite（Diana 代定）","零配置单文件库，最适合单人毕设 demo"],
 ["训练算力","本地 NVIDIA GPU（你指定）","本机独显训练，更快、数据不出本机"],
 ["开源合规","务实开源（你指定）","YOLOv8 学术免费 + CUDA 免费层（PyTorch 自带运行时）"],
 ["许可把关","仅用宽松许可数据集","CC0/CC-BY/Apache/MIT，可溯源可答辩"]],
 widths=[2.6,4.2,8.4])

# 二、过程模型
H("二、过程模型与理论依据", 1)
H("2.1 选用模型：里程碑驱动的螺旋-增量混合模型", 2)
BULLET("螺旋模型（风险驱动）：每一轮迭代先做风险分析+POC验证，再进入构建——应对 CV 训练精度、哈希链实现正确性两大技术风险；")
BULLET("增量模型（快速交付）：系统分三个增量（分级核心→溯源链→平台集成）逐步交付，每增量可独立演示；")
BULLET("RUP 四阶段 + 阶段门（Phase Gate）：启动→细化→构建→过渡，每个阶段结束设里程碑评审门；")
BULLET("里程碑驱动：严格对齐学校强制节点（开题✓/中期/查重/答辩）。")
H("2.2 理论出处对照", 2)
table(["理论要点","出处","落地"],
[["生命周期模型（瀑布/原型/增量/螺旋/RUP/敏捷）","《软件工程》生命周期模型章","螺旋-增量混合，阶段门控"],
 ["项目章程/WBS/里程碑/关键路径CPM","《软件过程与管理》项目计划章","第三节WBS、第四节里程碑"],
 ["风险管理","《软件过程与管理》风险管理章","第六节风险登记册"],
 ["配置管理","《软件过程与管理》配置管理章","第七节配置管理"]],
 widths=[6.5,5.5,4.2])
H("2.3 阶段划分与阶段门", 2)
table(["阶段","目标","退出门（Gate）判据"],
[["P0 启动","锁范围、定计划、备数据、搭环境","章程V1.1批准 + 数据集就位 + 仓库就绪"],
 ["P1 细化","架构定稿 + 双PoC跑通","架构评审过 + YOLOv8推理PoC + 哈希链存证PoC"],
 ["P2 构建","三增量交付可用系统","M2分级达标 + M3溯源闭环 + M4端到端可演示"],
 ["P3 过渡","论文定稿 + 答辩","M5论文查重通过 + 答辩PPT + 预答辩"]],
 widths=[2.0,6.5,7.7])

# 三、WBS
H("三、工作分解结构（WBS）", 1)
table(["WBS","工作包","主要交付物","负责"],
[["1.0","项目管理与章程","项目章程V1.1、进度看板","Diana/你"],
 ["2.0","需求工程","软件需求规格说明书 SRS","Diana(生成)/你(审)"],
 ["3.0","架构与设计","C4架构图、技术选型、DESIGN.md","Diana"],
 ["4.0","数据工程","数据集、标注、增强、版本管理","你/AI"],
 ["5.0","算法开发","YOLOv8训练、调参、评估脚本","AI/Diana"],
 ["6.0","区块链","哈希链存证模块、溯源API","AI/Diana"],
 ["7.0","后端服务","FastAPI推理/溯源API、集成","AI"],
 ["8.0","前端平台","Vue管理/查询端（DESIGN.md驱动）","AI"],
 ["9.0","集成与测试","端到端测试、性能/精度报告","AI/Diana"],
 ["10.0","论文与答辩","论文初稿/定稿、PPT、预答辩","你/Diana"]],
 widths=[1.3,4.0,7.0,3.9])

# 四、30天里程碑
H("四、里程碑计划与进度估算（30 天硬基线）", 1)
P("基准日 2026-09-03（Day 1）。用户要求总工期压缩至 30 天内（系统+论文初稿就绪），且因后续实习安排，30 天为硬性交付窗口。答辩日期已确认：2027 年 5 月中旬。本计划按 30 天硬基线排布，M5（D30≈2026-10-02）产出可答辩的全套交付（系统+论文+PPT）；之后至 2027-05 约 7 个月自动转为论文精修与答辩准备缓冲期，工期风险大幅降低。", italic=True, size=9.5, color=RGBColor(0x66,0x66,0x66))
table(["里程碑","天次","日期(估)","关键交付","退出标准"],
[["M0 章程批准","D1","09-03","章程V1.1、SRS、仓库","范围冻结、计划共识"],
 ["M1 架构+双PoC","D3-4","09-06前","架构图、YOLOv8推理PoC、哈希链存证PoC","架构过审、两PoC跑通"],
 ["M2 分级达标","D10","09-12前","训练模型、推理API、评估","mAP@0.5≥0.85"],
 ["M3 溯源闭环","D16","09-18前","哈希链存证模块、溯源API","上链/查询100%"],
 ["M4 系统可演示","D24","09-26前","Vue前端、端到端集成","中期/演示材料齐"],
 ["M5 论文+答辩","D30","10-02前","论文定稿、PPT、预答辩","查重通过、可答辩"]],
 widths=[2.6,1.2,2.8,5.5,3.1])
H("4.1 关键路径（CPM）与压缩策略", 2)
P("最长路径：数据工程(D2-10) → 模型训练迭代(D4-10) → 论文撰写(D22-30)。编码（API/前端）因 AI 全量生成而脱离关键路径。")
P("30 天压缩靠三点：(1) 阶段并行——溯源(D8起)与分级(D4起)重叠；(2) 用 Colab 免费 GPU 训练免去本机环境依赖；(3) 论文边做边记，不最后突击。", bold=True)
P("⚠️ 风险预警：30 天为硬性交付窗口（因实习安排）。答辩 2027-05 中旬已确认，D30(2026-10-02) 完成可答辩全套交付，之后约 7 个月为精修缓冲期，工期风险已大幅降低；仍须守住 30 天内产出系统+论文初稿，切勿为赶工牺牲模型精度与查重。", color=RGBColor(0xC0,0x39,0x2B))

# 五、风险
H("五、风险管理登记册", 1)
table(["ID","风险","概率/影响","应对措施"],
[["R1","分级模型精度不达标","中/高","螺旋迭代：数据增强、换backbone；设精度门槛不过则回退"],
 ["R2","哈希链实现正确性/防篡改验证","高/中","先用单文件PoC验证链式哈希与防篡改；存证模块单测先行"],
 ["R3","数据集不足/质量差","中/中","公开数据集兜底（Kaggle等）；少量自建微调"],
 ["R4","Colab GPU训练中断/显存不足","中/中","训练脚本支持断点续训；权重定期存档；本机CPU可兜底推理"],
 ["R5","论文进度滞后","中/高","增量产出、边做边记实验数据；模板化章节"],
 ["R6","范围蔓延","中/高","章程冻结+变更控制(1.5)；新增必走审批"]],
 widths=[1.0,4.5,2.2,8.6])

# 六、质量
H("六、质量与验收标准", 1)
BULLET("分级模型：测试集 mAP@0.5 ≥ 0.85，单图推理延迟 < 500ms；")
BULLET("溯源：上链成功率 100%、查询正确率 100%、不可篡改性可演示；")
BULLET("系统：端到端 demo 可现场演示，含异常输入处理；")
BULLET("工程：代码可运行、关键模块有测试、README 完备；")
BULLET("论文：字数达标、查重率 < 学校阈值、结构符合模板。")

# 七、配置
H("七、配置管理", 1)
BULLET("代码：Git 仓库（main/dev 分支），提交信息含 WBS 编号；")
BULLET("数据：独立 data/ 目录 + README 说明来源/许可/划分；")
BULLET("模型：weights/ 版本化（如 yolov8n_tea_mAP085_0912.pt）；")
BULLET("文档：本章程、SRS、论文均带版本号，旧版归档不删；")
BULLET("基线：M1~M5 各打一个可回溯基线 tag。")

# 八、节奏
H("八、沟通节奏与统筹机制", 1)
BULLET("实训期：每日一次简短同步——你告知进展/阻塞，我推进并产出；")
BULLET("每达成一个里程碑（M0~M5）做一次正式评审（你+我），不过门不进下一阶段；")
BULLET("看板：任务列表跟踪 WBS 10 包状态（待办/进行/完成/阻塞）；")
BULLET("决策：分歧交你裁定，不自动调和；详细操作见《AI 指挥手册》。")

# 九、Day-1
H("九、明日（Day-1）8 小时冲刺计划", 1)
P("目标：完成 P0 启动阶段，使项目进入“可编码”状态。", bold=True)
table(["时段","时长","任务","产出"],
[["09:00-09:30","0.5h","确认章程与冻结范围（阅读本节，标注调整项）","章程V1.1共识"],
 ["09:30-11:00","1.5h","产出 SRS 需求规格说明书（我生成，你审）","SRS v0.1"],
 ["11:00-12:30","1.5h","数据集决策与获取：定类别+下载公开数据集+写数据README","数据集就位"],
 ["14:00-15:30","1.5h","技术栈终锁定+环境清单（Colab GPU/本机CPU/哈希链/Vue，列安装命令）","环境清单"],
 ["15:30-17:30","2.0h","仓库与目录结构初始化 + 进度看板（任务列表）建立","仓库+看板"],
 ["17:30-18:00","0.5h","收尾：确认明日产出，设定下次同步时间","下次同步约定"]],
 widths=[2.6,1.2,7.5,3.1])

# 附录
H("附录：假设与待确认项", 1)
BULLET("答辩确切日期已确认：2027 年 5 月中旬（D30≈2026-10-02 完成可答辩交付，之后进入精修缓冲期）；中期检查日期待学校通知；")
BULLET("首选农产品类别已定为恩施玉露茶（湖北地理标志绿茶，国家级非遗蒸青工艺），数据集与标注方案据此锁定；")
BULLET("学校论文模板与查重阈值（影响第六、十节验收标准）；")
BULLET("已定项（无需再确认）：数据集=TeaLeafAgeQuality(CC BY 4.0)公开集为主、算力=Colab GPU(主)+本机CPU(辅)、前端=Vue、溯源=哈希链、数据库=SQLite、开源合规=务实开源。")

doc.save("项目章程与进度计划_农产品分级溯源平台.docx")
print("OK saved charter 30d")
