#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 CR-W1-005 变更申请与批复书 docx。"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

OUT_DIR = r"C:\Users\wzd\Desktop\毕业设计"

def set_heading_style(doc):
    for lvl in range(1, 4):
        style = doc.styles[f"Heading {lvl}"]
        font = style.font
        font.name = "Microsoft YaHei"
        font.size = Pt(16 - lvl * 2)
        font.bold = True
        font.color.rgb = RGBColor(0x00, 0x00, 0x00)
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    style.font.size = Pt(10.5)


def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def add_heading(doc, text, level=1):
    p = doc.add_heading(level=level)
    run = p.add_run(text)
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def add_para(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(10.5)
    run.font.bold = bold
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    return p


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.name = "Microsoft YaHei"
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.name = "Microsoft YaHei"
                    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    return table


def generate_request():
    doc = Document()
    set_heading_style(doc)
    add_title(doc, "变更申请 CR-W1-005")
    add_para(doc, "申请日期：2026-09-05")
    add_para(doc, "申请人：W4（前端工程师）")
    add_para(doc, "变更主题：增加数据可视化、统计看板与哈希链可视化")

    add_heading(doc, "一、变更原因", 1)
    add_para(doc, "1. 当前前端仅包含单页检测工作台，答辩演示场景单一，难以充分展示系统完整性。")
    add_para(doc, "2. 用户反馈希望系统具备更丰富的可视化能力，能够直观展示茶叶分级结果、历史趋势与溯源链不可篡改性。")
    add_para(doc, "3. 在已批准的 CR-W1-004（用户认证 + 多页面 + 低代码配置层）基础上，进一步增加 ECharts 数据可视化模块，可在不推翻现有设计的前提下显著提升答辩表现力。")

    add_heading(doc, "二、变更范围", 1)
    add_para(doc, "本次变更为前端展示层与后端统计接口的增量扩展，项目核心数据流与模型推理链路保持不变。")
    table = add_table(doc, ["模块", "是否变更", "变更内容"], [
        ["W1 数据工程", "否", "数据格式、data.yaml、划分策略不变"],
        ["W2 视觉模型", "否", "detect() 接口契约不变，仅新增 metrics JSON 消费"],
        ["W3 后端", "是", "新增 /api/stats/* 统计接口；补充历史聚合查询"],
        ["W4 前端", "是", "引入 ECharts，增加 6+ 图表组件与 3+ 可视化页面"],
        ["W5 测试", "是", "补充 stats 接口测试与图表渲染测试"],
    ])

    add_heading(doc, "三、新增页面与交互点", 1)
    add_para(doc, "最终系统包含 8 个页面，每个页面均具备可交互元素，答辩演示路径显著丰富。")
    table = add_table(doc, ["页面", "URL", "可视化/交互点"], [
        ["首页/仪表盘", "/", "统计卡片 + 等级分布饼图 + 近7天检测趋势折线图"],
        ["登录页", "/login", "表单交互"],
        ["注册页", "/register", "表单交互"],
        ["检测工作台", "/detect", "上传图片 + 检测 + 结果卡片 + 检测框 + 生成溯源记录"],
        ["历史记录页", "/history", "检测列表 + 等级分布饼图 + 置信度趋势折线图"],
        ["溯源验证页", "/trace/:id", "哈希链可视化时间线 + 篡改标红"],
        ["个人中心", "/profile", "用户信息 + 检测次数 + 登出"],
        ["低代码演示页", "/admin/schema", "JSON编辑器 + 实时刷新页面"],
    ])

    add_heading(doc, "四、新增/调整接口", 1)
    add_para(doc, "接口契约③扩展以下内容：")
    add_para(doc, "GET /api/stats/overview")
    add_para(doc, "返回平台级统计：total_detections、today_detections、grade_distribution（饼图数据）、weekly_trend（折线图数据）。")
    add_para(doc, "GET /api/stats/user/{user_id}")
    add_para(doc, "返回用户级统计：total_detections、grade_distribution、confidence_trend（平均置信度趋势）。")
    add_para(doc, "GET /api/stats/chain/{trace_id}（可选，可直接复用 /api/trace/{id}）")
    add_para(doc, "前端消费 /api/trace/{id} 后，用返回的 chain 数组绘制哈希链时间线。")

    add_heading(doc, "五、ECharts 组件清单", 1)
    table = add_table(doc, ["组件", "用途", "数据来源"], [
        ["GradePieChart", "等级分布饼图", "/api/stats/overview 或 /api/stats/user/{id}"],
        ["TrendLineChart", "近7天/近N次检测趋势折线图", "/api/stats/overview 或 /api/stats/user/{id}"],
        ["ConfidenceBarChart", "各等级平均置信度柱状图", "/api/stats/user/{id}"],
        ["HashChainTimeline", "哈希链时间线", "/api/trace/{id}"],
        ["TrainingCurveChart", "模型训练曲线（loss/mAP）", "models/metrics_*.json"],
        ["StatCards", "统计数字卡片", "/api/stats/overview"],
    ])

    add_heading(doc, "六、建议方案", 1)
    add_para(doc, "方案 A（推荐）：立即引入 ECharts，按上述清单实现可视化组件，新增 /api/stats/* 后端接口。")
    add_para(doc, "方案 B：仅在前端做静态 mock 图表。不推荐，答辩时无法体现数据真实性。")
    add_para(doc, "方案 C：引入第三方 BI 工具（如 Grafana）。不推荐，增加部署成本，与“全部开源免费”约束冲突。")

    add_heading(doc, "七、影响与工期", 1)
    add_para(doc, "对 W1/W2 无影响；W3 增加约 0.5 天；W4 增加约 1 天；W5 增加约 0.5 天。")
    add_para(doc, "预计总工期增加：约 1.5 天，仍在 30 天硬基线内。")

    add_heading(doc, "八、申请人签字", 1)
    add_para(doc, "申请人：W4")
    add_para(doc, "日期：2026-09-05")

    doc.save(f"{OUT_DIR}/变更申请_CR-W1-005_增加数据可视化统计看板与哈希链可视化.docx")


def generate_approval():
    doc = Document()
    set_heading_style(doc)
    add_title(doc, "变更批复书 CR-W1-005")
    add_para(doc, "批复日期：2026-09-05")
    add_para(doc, "批复人：项目组长")
    add_para(doc, "对应变更申请：CR-W1-005")

    add_heading(doc, "一、批复结论", 1)
    add_para(doc, "批准方案 A：立即引入 ECharts 数据可视化、统计看板与哈希链可视化。", bold=True)

    add_heading(doc, "二、批准理由", 1)
    add_para(doc, "1. 可视化模块能显著提升答辩表现力，使系统从“可用工具”升级为“可演示平台”。")
    add_para(doc, "2. 本变更为增量扩展，不动核心数据流、模型训练与推理接口，风险可控。")
    add_para(doc, "3. 所需新增后端接口均为只读统计接口，不破坏现有哈希链与检测接口稳定性。")

    add_heading(doc, "三、最终页面与交互确认", 1)
    table = add_table(doc, ["页面数", "可视化组件数", "可演示场景数", "工期增量"], [
        ["8 个", "≥6 个 ECharts 组件", "≥6 个", "约 1.5 天"],
    ])

    add_heading(doc, "四、关键约束", 1)
    add_para(doc, "1. W3 必须新增 /api/stats/overview 与 /api/stats/user/{user_id}，返回格式符合契约③统一响应。")
    add_para(doc, "2. W4 图表数据必须从后端接口获取，禁止在前端硬编码静态数据。")
    add_para(doc, "3. 训练曲线看板可读取 W2 产出的 metrics JSON（models/metrics_*.json），无需 W2 改代码。")
    add_para(doc, "4. 哈希链可视化必须展示 index、timestamp、hash、prev_hash，并在篡改后校验失败时标红。")
    add_para(doc, "5. 新增 ECharts 依赖必须开源免费（echarts 或 vue-echarts）。")

    add_heading(doc, "五、同步更新文件", 1)
    add_para(doc, "- 接口契约③：已增加 /api/stats/*")
    add_para(doc, "- 派工指导手册：已重新生成")
    add_para(doc, "- W3/W4/W5_提示词.txt：已固化 CR-W1-005 约束")

    add_heading(doc, "六、后续动作", 1)
    add_para(doc, "1. W3 在 M3 中实现 stats 统计接口。")
    add_para(doc, "2. W4 在 M4 中实现 ECharts 组件与可视化页面。")
    add_para(doc, "3. W5 在端到端测试中补充 stats 接口与图表渲染测试。")

    add_heading(doc, "七、批复人签字", 1)
    add_para(doc, "批复人：项目组长")
    add_para(doc, "日期：2026-09-05")

    doc.save(f"{OUT_DIR}/变更批复书_CR-W1-005.docx")


if __name__ == "__main__":
    generate_request()
    generate_approval()
    print("CR-W1-005 变更申请与批复书已生成。")
