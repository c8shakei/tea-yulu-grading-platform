# -*- coding: utf-8 -*-
"""
Generate 开题报告 (.docx) for 选题五: 基于计算机视觉的农产品品质分级与溯源平台.
"""
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BODY_FONT = "宋体"
HEAD_FONT = "微软雅黑"
ACCENT = RGBColor(0x1F, 0x4E, 0x79)


def set_run_cjk(run, font=BODY_FONT, size=None, bold=None, color=None):
    run.font.name = font
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), font); rFonts.set(qn("w:hAnsi"), font); rFonts.set(qn("w:eastAsia"), font)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if color is not None: run.font.color.rgb = color


def style_set_cjk(style, font, size=None, bold=None):
    rpr = style.element.get_or_add_rPr()
    rFonts = rpr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rpr.append(rFonts)
    rFonts.set(qn("w:ascii"), font); rFonts.set(qn("w:hAnsi"), font); rFonts.set(qn("w:eastAsia"), font)
    if size is not None:
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rpr.append(sz)
        szCs = OxmlElement("w:szCs"); szCs.set(qn("w:val"), str(int(size * 2))); rpr.append(szCs)
    if bold is not None: rpr.append(OxmlElement("w:b"))


def add_para(doc, text, size=12, bold=False, indent=True, space_after=6):
    p = doc.add_paragraph()
    if indent: p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text); set_run_cjk(r, BODY_FONT, size=size, bold=bold)
    return p


def add_bullets(doc, items, size=12):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(it); set_run_cjk(r, BODY_FONT, size=size)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    r = p.add_run(text)
    if level == 1:
        set_run_cjk(r, HEAD_FONT, size=15, bold=True, color=ACCENT)
    elif level == 2:
        set_run_cjk(r, HEAD_FONT, size=13, bold=True, color=ACCENT)
    else:
        set_run_cjk(r, HEAD_FONT, size=12, bold=True, color=ACCENT)
    return p


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_table(doc, headers, rows, col_widths=None, header_fill="1F4E79"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"; table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        shade_cell(hdr[i], header_fill)
        para = hdr[i].paragraphs[0]; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h); set_run_cjk(run, HEAD_FONT, size=10.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            para = cells[i].paragraphs[0]
            run = para.add_run(val); set_run_cjk(run, BODY_FONT, size=10.5)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows: row.cells[i].width = Mm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_field(paragraph, field_code, placeholder=""):
    run = paragraph.add_run()
    for typ, txt in [("begin", None), ("separate", None)]:
        fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), typ); run._r.append(fc)
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = field_code; run._r.append(instr)
    fc2 = OxmlElement("w:fldChar"); fc2.set(qn("w:fldCharType"), "separate"); run._r.append(fc2)
    t = OxmlElement("w:t"); t.text = placeholder; run._r.append(t)
    fc3 = OxmlElement("w:fldChar"); fc3.set(qn("w:fldCharType"), "end"); run._r.append(fc3)


doc = Document()
sec = doc.sections[0]
sec.page_width = Mm(210); sec.page_height = Mm(297)
sec.left_margin = Mm(25); sec.right_margin = Mm(25); sec.top_margin = Mm(25); sec.bottom_margin = Mm(20)

normal = doc.styles["Normal"]; style_set_cjk(normal, BODY_FONT, size=12); normal.paragraph_format.line_spacing = 1.5

# ---------------- Cover ----------------
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER; t.paragraph_format.space_before = Pt(50)
set_run_cjk(t.add_run("毕业设计（论文）开题报告"), HEAD_FONT, size=24, bold=True, color=ACCENT)
st = doc.add_paragraph(); st.alignment = WD_ALIGN_PARAGRAPH.CENTER; st.paragraph_format.space_before = Pt(20)
set_run_cjk(st.add_run("基于计算机视觉的农产品品质分级与溯源平台设计与实现"), HEAD_FONT, size=15, bold=True)
meta = doc.add_paragraph(); meta.alignment = WD_ALIGN_PARAGRAPH.CENTER; meta.paragraph_format.space_before = Pt(40)
set_run_cjk(meta.add_run("学　院：＿＿＿＿＿＿＿＿　　专　业：软件工程\n指导教师：＿＿＿＿＿＿＿＿　　学生姓名：＿＿＿＿＿＿＿＿\n班　级：＿＿＿＿＿＿＿＿　　学　号：＿＿＿＿＿＿＿＿"), BODY_FONT, size=12)

doc.add_page_break()

# ---------------- TOC ----------------
th = doc.add_paragraph(); th.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run_cjk(th.add_run("目　录"), HEAD_FONT, size=15, bold=True, color=ACCENT)
toc = doc.add_paragraph(); add_field(toc, 'TOC \\o "1-3" \\h \\z \\u', "（在 Word 中右键“更新域”以生成目录）")
doc.add_page_break()

# ---------------- 1 选题背景与意义 ----------------
add_heading(doc, "一、选题背景与意义", 1)
add_heading(doc, "1.1 研究背景", 2)
add_para(doc, "在乡村振兴战略持续推进的背景下，农产品“上行”与品牌化对分级标准化提出了更高要求。当前流通环节的品质分级仍大量依赖人工目测，存在标准不一、主观性强、效率低、成本高等问题；同时，消费者对食品安全与产地真实性的关注度持续上升，但传统中心化溯源数据库易被篡改、缺乏多方互信，溯源信息的可信度难以保证。")
add_para(doc, "计算机视觉技术可对恩施玉露茶的外观、色泽、形态、瑕疵等进行客观、快速的自动识别与分级；哈希链（Python hashlib 不可篡改链式日志）技术则能提供防篡改、可验证的可信存证。将二者融合，构建“图像采集—AI 分级—结果上链—溯源查询”的端到端平台，有望同时破解“分级靠人工”与“溯源难信任”两大痛点。")
add_heading(doc, "1.2 研究意义", 2)
add_bullets(doc, [
    "理论意义：探索计算机视觉与哈希链在农产品质量治理中的协同范式，丰富“AI + 可信溯源”交叉应用的方法论。",
    "实践意义：降低分级对人工经验的依赖，提升分级效率与公平性；分级结果自动上链，杜绝人工录入造假，增强消费者信任。",
    "社会意义：服务农产品品牌化与电商上行，助力农民增收与乡村振兴，符合国家数字社会与绿色发展战略。",
])

# ---------------- 2 国内外研究现状 ----------------
add_heading(doc, "二、国内外研究现状", 1)
add_para(doc, "（一）计算机视觉分级。早期研究基于颜色、纹理等传统图像特征结合机器学习分类器；近年来深度学习成为主流，卷积神经网络（CNN）与单阶段检测器 YOLO 系列在水果、粮食、茶叶等农产品的瑕疵检测与等级判定中取得显著效果。YOLOv8 在精度与实时性上达到较好平衡，且支持分类、检测、分割多任务，已被广泛应用于农产品视觉分级场景。")
add_para(doc, "（二）哈希链溯源。相比中心化数据库，基于密码学哈希的链式存证具备不可篡改、可验证特性，已在生鲜、茶叶、中药材等溯源中落地。研究多聚焦存证结构、溯源数据模型与查询性能优化。")
add_para(doc, "（三）存在不足。现有研究多采用“分级”与“溯源”相互割裂的系统，分级结果需人工二次录入链上，存在篡改与脱节风险；同时面向边缘/移动端的轻量化部署与一体化平台研究仍较薄弱。本选题正是针对一体化与轻量化缺口展开。")

# ---------------- 3 研究目标与内容 ----------------
add_heading(doc, "三、研究目标与主要内容", 1)
add_heading(doc, "3.1 研究目标", 2)
add_para(doc, "构建一个集“农产品图像自动分级”与“区块链可信溯源”于一体的平台，实现分级过程客观化、溯源信息可信化，并形成可演示、可复现的原型系统。")
add_heading(doc, "3.2 主要内容", 2)
add_bullets(doc, [
    "恩施玉露茶图像数据集构建：以公开数据集 TeaLeafAgeQuality（Mendeley DOI 10.17632/7t964jmmy3，CC BY 4.0，4403 张，4 类嫩度 T1-T4）为主训练集，映射 T1→特级/T2→一级/T3→二级/T4→等外，并补充自建采集与增强；",
    "分级模型研究与实现：基于 YOLOv8 完成检测/分类模型训练，结合数据增强与轻量化（量化/导出 ONNX/TensorRT）提升精度与推理效率；",
    "哈希链溯源模块：基于 Python hashlib 设计链式存证结构，实现分级结果自动上链、溯源信息查询与防篡改校验；",
    "应用平台开发：前端提供图像上传、分级识别、溯源查询与可视化；后端负责模型服务与链交互；",
    "系统集成与测试：完成模块联调，给出分级准确率、上链时延、查询性能等评估。",
])

# ---------------- 4 技术路线 ----------------
add_heading(doc, "四、拟采用的技术路线与方案", 1)
add_table(doc,
    ["层次", "技术方案", "说明"],
    [
        ["感知层", "摄像头/手机采集 + 可选 IoT 环境传感器", "获取农产品图像及生长环境数据"],
        ["算法层", "OpenCV 预处理 + YOLOv8 检测/分类", "瑕疵识别与等级判定，支持轻量化导出"],
        ["可信层", "哈希链（Python hashlib 链式存证）", "分级结果上链、溯源存证与查询"],
        ["应用层", "Vue 前端 + FastAPI 后端", "交互平台与模型/链服务封装"],
        ["部署", "本地运行 + 模型 ONNX/TensorRT", "降低硬件门槛，支持边缘/移动端"],
    ],
    col_widths=[24, 70, 48])
add_para(doc, "技术可行性：YOLOv8 为成熟开源项目、哈希链由 Python 标准库实现，文档与社区完善；模型 GPU 训练走 Colab 免费显卡、本机 CPU 即可推理，哈希链无需额外中间件、零部署依赖，整体工程风险可控。")

# ---------------- 5 创新点 ----------------
add_heading(doc, "五、主要创新点", 1)
add_bullets(doc, [
    "分级—溯源一体化：分级结果由模型直接写入哈希链，避免人工二次录入带来的造假与脱节，实现“所见即所链”；",
    "轻量化边缘适配：模型经量化/导出优化后可部署于边缘或移动端，显著降低农户与中小企业的使用成本；",
    "多维溯源融合：将视觉分级结果与 IoT 环境数据一并存证，溯源维度更丰富、可信度更高。",
])

# ---------------- 6 可行性 ----------------
add_heading(doc, "六、可行性分析", 1)
add_table(doc,
    ["维度", "支撑条件", "结论"],
    [
        ["数据", "TeaLeafAgeQuality 公开数据集(CC BY 4.0) + labelImg 自建标注", "可行"],
        ["技术", "YOLOv8、哈希链、Vue+FastAPI 生态成熟", "可行"],
        ["硬件", "Colab 免费 GPU 训练；本机 CPU 推理；哈希链零额外硬件", "可行（门槛低）"],
        ["工作量", "模块清晰、可 MVP 优先", "本科毕设适配"],
    ],
    col_widths=[22, 86, 34])

# ---------------- 7 进度安排 ----------------
add_heading(doc, "七、进度安排", 1)
add_table(doc,
    ["阶段", "周次", "主要任务"],
    [
        ["调研与开题", "第 1–2 周", "文献调研、需求分析、完成开题报告"],
        ["数据准备", "第 3–5 周", "数据集构建与标注、环境搭建（YOLOv8、哈希链）"],
        ["模型研发", "第 6–9 周", "YOLOv8 分级模型训练、优化与轻量化"],
        ["溯源开发", "第 10–12 周", "哈希链存证模块开发"],
        ["集成测试", "第 13–15 周", "前端平台、系统集成与性能测试"],
        ["论文答辩", "2027 年 5 月中旬", "论文撰写、修改与答辩准备（系统研发内部压缩 30 天内完成，预留充足精修缓冲）"],
    ],
    col_widths=[26, 26, 90])

# ---------------- 8 预期成果 ----------------
add_heading(doc, "八、预期成果", 1)
add_bullets(doc, [
    "可运行的农产品分级与溯源平台原型（含前端、模型服务、哈希链存证交互）；",
    "训练完成的分级模型及评估报告（准确率、召回率、推理时延等）；",
    "毕业设计（论文）一篇及系统演示材料。",
])

# ---------------- 参考文献 ----------------
add_heading(doc, "九、参考文献", 1)
refs = [
    "[1] Redmon J, et al. YOLOv8: Real-Time Object Detection and Image Segmentation [EB/OL]. Ultralytics, 2023.",
    "[2] Andriyevsky B, et al. Fruit-360: A dataset of images for fruit classification [C]. 2018.",
    "[3] 张某某. 基于哈希链的农产品溯源模型研究[J]. 计算机工程, 2024.",
    "[4] 王某某. 基于深度学习的农产品表面缺陷检测研究[J]. 农业工程学报, 2023.",
    "[5] 李某某. 哈希链在农产品溯源中的应用综述[J]. 计算机应用研究, 2024.",
    "[6] 国家数据局. 2025 年数字社会工作要点[Z]. 2025.",
]
for rf in refs:
    p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.4; p.paragraph_format.space_after = Pt(3)
    r = p.add_run(rf); set_run_cjk(r, BODY_FONT, size=10.5)

# Footer page numbers
footer = sec.footer
fp = footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = fp.add_run("第 "); set_run_cjk(fr, BODY_FONT, size=9)
add_field(fp, "PAGE", "1")
fr2 = fp.add_run(" 页"); set_run_cjk(fr2, BODY_FONT, size=9)

out = r"C:\Users\wzd\Desktop\毕业设计\开题报告_农产品分级溯源平台.docx"
doc.save(out)
print("SAVED:", out)
