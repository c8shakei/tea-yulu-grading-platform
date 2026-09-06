# -*- coding: utf-8 -*-
"""
Generate a Chinese Word document (.docx) with graduation thesis topic proposals.
Built with python-docx. CJK fonts are configured via w:eastAsia.
"""
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BODY_FONT = "宋体"          # SimSun (print body)
HEAD_FONT = "微软雅黑"      # Microsoft YaHei (modern headings)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)  # corporate blue for headings


def set_run_cjk(run, font=BODY_FONT, size=None, bold=None, color=None):
    run.font.name = font
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), font)
    rFonts.set(qn("w:hAnsi"), font)
    rFonts.set(qn("w:eastAsia"), font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def style_set_cjk(style, font, size=None, bold=None, color=None):
    rpr = style.element.get_or_add_rPr()
    rFonts = rpr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rpr.append(rFonts)
    rFonts.set(qn("w:ascii"), font)
    rFonts.set(qn("w:hAnsi"), font)
    rFonts.set(qn("w:eastAsia"), font)
    if size is not None:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(size * 2)))
        rpr.append(sz)
        szCs = OxmlElement("w:szCs")
        szCs.set(qn("w:val"), str(int(size * 2)))
        rpr.append(szCs)
    if bold is not None:
        b = OxmlElement("w:b")
        rpr.append(b)
    if color is not None:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), "%02X%02X%02X" % (color[0], color[1], color[2]))
        rpr.append(c)


def add_para(doc, text, size=12, bold=False, indent=True, align=None, space_after=6):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    set_run_cjk(r, BODY_FONT, size=size, bold=bold)
    return p


def add_bullets(doc, items, size=12):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(it)
        set_run_cjk(r, BODY_FONT, size=size)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(text)
        set_run_cjk(r, HEAD_FONT, size=16, bold=True, color=ACCENT)
    elif level == 2:
        r = p.add_run(text)
        set_run_cjk(r, HEAD_FONT, size=14, bold=True, color=ACCENT)
    else:
        r = p.add_run(text)
        set_run_cjk(r, HEAD_FONT, size=12.5, bold=True, color=ACCENT)
    # numbering prefix handled manually in text
    return p


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_table(doc, headers, rows, col_widths=None, header_fill="1F4E79"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        shade_cell(hdr[i], header_fill)
        para = hdr[i].paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h)
        set_run_cjk(run, HEAD_FONT, size=10.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            para = cells[i].paragraphs[0]
            run = para.add_run(val)
            set_run_cjk(run, BODY_FONT, size=10.5)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Mm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_field(paragraph, field_code, placeholder=""):
    run = paragraph.add_run()
    fldBegin = OxmlElement("w:fldChar")
    fldBegin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field_code
    fldSep = OxmlElement("w:fldChar")
    fldSep.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = placeholder
    fldEnd = OxmlElement("w:fldChar")
    fldEnd.set(qn("w:fldCharType"), "end")
    r = run._r
    r.append(fldBegin)
    r.append(instr)
    r.append(fldSep)
    r.append(t)
    r.append(fldEnd)
    return run


# ----------------------------------------------------------------------------
doc = Document()

# Page setup: A4
sec = doc.sections[0]
sec.page_width = Mm(210)
sec.page_height = Mm(297)
sec.left_margin = Mm(25)
sec.right_margin = Mm(25)
sec.top_margin = Mm(25)
sec.bottom_margin = Mm(20)

# Default font
normal = doc.styles["Normal"]
style_set_cjk(normal, BODY_FONT, size=12)
normal.paragraph_format.line_spacing = 1.5

# Title block
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_before = Pt(60)
title.paragraph_format.space_after = Pt(10)
tr = title.add_run("软件工程毕业设计选题方案")
set_run_cjk(tr, HEAD_FONT, size=26, bold=True, color=ACCENT)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(6)
sr = sub.add_run("——基于社会需求调研与前沿技术研判的创新型选题草拟")
set_run_cjk(sr, HEAD_FONT, size=14, bold=False, color=RGBColor(0x55, 0x55, 0x55))

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.paragraph_format.space_after = Pt(40)
mr = meta.add_run("适用对象：软件工程专业本科毕业生　|　文档版本：v1.0　|　编制日期：2026-09")
set_run_cjk(mr, BODY_FONT, size=10.5, color=RGBColor(0x77, 0x77, 0x77))

# TOC
toc_h = doc.add_paragraph()
toc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
thr = toc_h.add_run("目　录")
set_run_cjk(thr, HEAD_FONT, size=15, bold=True, color=ACCENT)
toc = doc.add_paragraph()
add_field(toc, 'TOC \\o "1-3" \\h \\z \\u', "（在 Word 中右键“更新域”以生成目录）")

doc.add_page_break()

# ---- Section 1: 社会需求调研分析 ----
add_heading(doc, "一、社会需求调研分析", 1)
add_para(doc, "本方案以“需求牵引、技术支撑”为原则，综合国家数字社会政策导向与公开社会调研数据，识别出当前最迫切、且与软件工程能力高度匹配的民生需求场景。以下需求均来自权威来源，可作为选题的现实锚点。")

add_heading(doc, "1.1 政策与社会的双重信号", 2)
add_para(doc, "国家数据局《2025年数字社会工作要点》明确将医疗、养老、教育、社保、文旅、社区列为与群众利益最直接相关的六大重点领域，并部署“三医”协同、医康养联动、智慧教育、灵活就业、智慧文旅、智慧社区等一批“小切口”应用场景。2025年全国两会调查中，“民生保障”“社会治理”位列热词前三，其中 72.33% 的网民呼吁加强社区养老服务，82.16% 的网民期盼打击网络谣言——数字技术正成为破解民生治理难题的关键路径。")

add_heading(doc, "1.2 关键需求场景梳理", 2)
add_table(doc,
    ["需求领域", "核心痛点", "数字化契机", "软件工程切入点"],
    [
        ["智慧养老", "独居老人健康监测难、社区养老资源不足", "医康养联动、居家+社区+机构融合", "本地化AI陪护、异常预警、健康画像"],
        ["医疗健康", "数据孤岛、跨机构协同难、基层能力弱", "三医协同、互联网医院、AI辅助诊断", "联邦学习、医学影像分析、RAG问诊"],
        ["教育", "个性化不足、乡村师资薄弱", "AI+教育改革、资源共享", "知识库问答、学习路径推荐"],
        ["基层治理", "基层报表多头填报、数据核查负担重", "报表数据“只报一次”、一网统管", "OCR/LLM+RPA 自动填报核查"],
        ["新就业群体", "骑手/网约车司机社保与安全保障缺失", "灵活就业权益保障、零工市场", "边缘安全监测、权益保障助手"],
        ["农产品与乡村", "分级靠人工、溯源难信任", "乡村振兴、农产品溯源", "CV分级 + 区块链溯源"],
        ["企业碳管理", "碳核算成本高、减排决策缺数据", "绿色低碳、可持续发展", "CV+Llama 智能核算与决策"],
    ],
    col_widths=[26, 42, 42, 42])

add_para(doc, "结论：上述场景中，“养老、医疗、教育、基层治理、新就业群体”五类需求兼具社会紧迫性与技术可行性，是毕业设计的优选土壤。")

# ---- Section 2: 技术趋势研判 ----
add_heading(doc, "二、技术趋势研判（成熟且前沿）", 1)
add_para(doc, "选题须“用成熟技术做前沿应用”，避免采用尚不稳定、难以落地的技术。下列技术均已具备成熟开源生态与生产级案例，适合本科毕设的工程化实现。")

add_table(doc,
    ["技术方向", "代表工具/框架", "成熟度", "典型应用场景"],
    [
        ["大语言模型工程化与AI Agent", "LangChain/LlamaIndex、LangGraph、MetaGPT", "★成熟", "RAG问答、多智能体编排、自动化流程"],
        ["本地化/边缘AI部署", "Ollama、llama.cpp、Jetson Nano", "★成熟", "隐私敏感场景、离线推理、低延迟"],
        ["联邦学习 + 隐私计算", "Flower、PySyft、差分隐私", "★较成熟", "跨机构医疗建模、数据不出域"],
        ["计算机视觉", "YOLOv8、SwinIR、OpenCV", "★成熟", "图像识别、超分辨率、目标检测"],
        ["知识图谱 + 推荐", "Neo4j、协同过滤/深度学习推荐", "★成熟", "个性化学习、智能导购"],
        ["云原生 / MLOps", "Kubernetes、MLflow、Prometheus", "★成熟", "模型全生命周期管理、弹性部署"],
        ["低代码工作流编排", "n8n、Langflow", "★成熟", "基层填报、业务流程自动化"],
        ["鸿蒙/移动端开发", "ArkUI、MindSpore Lite", "★上升期", "端侧AI、适老化应用"],
    ],
    col_widths=[40, 52, 22, 38])

# ---- Section 3: 选题方案 ----
add_heading(doc, "三、毕业设计选题方案（六选）", 1)
add_para(doc, "以下六个选题均满足“有创新点、技术前沿且成熟、可行性高”三项要求，覆盖不同难度与兴趣方向，可按个人技术储备与导师方向选择。")

topics = [
    {
        "name": "选题一：基于本地化大模型的独居老人健康陪护与异常预警系统",
        "need": "老龄化加剧，72%以上网民关注社区养老；独居老人面临突发健康事件响应慢、隐私顾虑强（不愿数据上云）的痛点。",
        "innov": [
            "本地化部署开源大模型（Ollama + llama.cpp），实现“数据不出户”的隐私保护，呼应技术向善与适老化改造要求；",
            "多智能体协同架构：健康问答 Agent + 用药提醒 Agent + 异常检测 Agent，由 LangGraph 统一编排；",
            "轻量化推理（量化/蒸馏）跑在树莓派/Jetson Nano 等边缘设备上，成本低、可演示。",
        ],
        "stack": "Python + Ollama + LangGraph + Chroma 向量库 + 边缘设备（树莓派4B/Jetson Nano）+ 语音交互",
        "feas": "开源模型与框架成熟；可用公开健康对话/传感器数据集 + 规则模拟；硬件成本低（数百元）。难度：中。",
        "out": "可演示的陪护原型 + 论文（本地化 vs 云端部署的延迟/隐私对比实验）。",
    },
    {
        "name": "选题二：基于联邦学习的区域医疗影像辅助诊断系统（隐私保护）",
        "need": "“三医”协同要求医疗机构数据互通，但患者隐私与合规禁止原始数据出域，形成数据孤岛。",
        "innov": [
            "采用 Flower 联邦学习框架，多家机构本地训练、仅交换模型参数，解决“数据可用不可见”；",
            "引入差分隐私加固，给出隐私预算(ε)与精度的权衡分析；",
            "对比“集中式训练 vs 联邦学习”的精度损失，论证隐私保护下的实用价值。",
        ],
        "stack": "Python + PyTorch + Flower + 差分隐私 + 公开医学影像数据集（如 ChestX-ray14、ISIC）",
        "feas": "数据集公开、框架文档完善；可在单机模拟多客户端。难度：中高。",
        "out": "联邦训练原型 + 收敛曲线 + 隐私-精度对比实验，论文素材丰富。",
    },
    {
        "name": "选题三：基于RAG的高校课程知识库智能问答与个性化学习路径推荐",
        "need": "“AI+教育改革”背景下，学生需要精准、可追溯的问答，而非易幻觉的通用大模型回答。",
        "innov": [
            "RAG 架构（LlamaIndex + Chroma）将回答锚定到课程教材/课件，抑制幻觉并提供出处；",
            "融合知识图谱刻画知识点先修关系，生成个性化学习路径；",
            "结合学习者行为数据做推荐，形成“问—学—练”闭环。",
        ],
        "stack": "Vue/React 前端 + FastAPI 后端 + LlamaIndex + Chroma + 推荐算法（协同过滤/图算法）",
        "feas": "课程文档可自建语料；框架成熟、社区案例多。难度：中。可行性高。",
        "out": "可运行问答系统 + 学习路径可视化，演示效果好、论文易写。",
    },
    {
        "name": "选题四：面向基层减负的智能报表填报与数据核查系统",
        "need": "国家明确要求基层报表数据“只报一次”，但基层仍面临多头填报、人工核查易错的负担。",
        "innov": [
            "OCR（PaddleOCR）+ LLM 自动抽取表单字段，一键生成标准化填报数据；",
            "基于 n8n/Langflow 的低代码工作流，串联“采集—校验—上报”多系统；",
            "多源数据自动比对核查，标记异常并给出提示，显著降低人工成本。",
        ],
        "stack": "Python + PaddleOCR + 开源LLM + n8n/Langflow + 轻量前端",
        "feas": "政策高度契合、开源工具成熟；可用模拟报表数据验证。难度：中。可行性高。",
        "out": "填报效率对比演示 + 核查准确率评估，社会价值直观。",
    },
    {
        "name": "选题五：基于计算机视觉的农产品品质分级与溯源平台",
        "need": "乡村振兴中，农产品分级依赖人工、主观性强；消费者对溯源真实性存疑。",
        "innov": [
            "成熟技术 + 新场景：YOLOv8 实现外观/瑕疵自动分级，速度快、精度高；",
            "分级结果写入哈希链，构建不可篡改的溯源链；",
            "IoT 采集生长环境数据，形成“分级—溯源—展示”一体化。",
        ],
        "stack": "YOLOv8 + OpenCV + 哈希链 + Vue 前端 + 可选 IoT 设备",
        "feas": "公开农产品图像数据集 + 预训练模型微调；区块链可用本地私链。难度：中高。",
        "out": "分级模型 + 溯源查询原型，兼具算法与系统维度。",
    },
    {
        "name": "选题六：基于边缘计算的外卖骑手安全监测与权益保障助手",
        "need": "新就业群体规模庞大，骑手疲劳驾驶、交通事故风险高，社保与安全保障亟待加强。",
        "innov": [
            "边缘端实时处理（手机/Jetson）实现疲劳与危险驾驶行为预警，数据本地处理保隐私；",
            "模型轻量化（量化/剪枝）适配移动端，低功耗实时运行；",
            "联动权益保障知识库，主动推送社保、维权指引。",
        ],
        "stack": "Android/移动端 + 边缘推理（TFLite/ONNX Runtime）+ 传感器 + 轻量后端",
        "feas": "可用公开驾驶行为数据集训练 + 仿真验证；需一定硬件/移动端基础。难度：中高。",
        "out": "预警原型 + 权益知识助手，社会关怀属性强。",
    },
]

for t in topics:
    add_heading(doc, t["name"], 2)
    add_para(doc, "【社会需求与背景】" + t["need"], size=11.5, indent=False, space_after=3)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("【核心创新点】")
    set_run_cjk(r, BODY_FONT, size=11.5, bold=True)
    add_bullets(doc, t["innov"], size=11.5)
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(3)
    r2 = p2.add_run("【技术栈】" + t["stack"])
    set_run_cjk(r2, BODY_FONT, size=11.5)
    p3 = doc.add_paragraph()
    p3.paragraph_format.space_after = Pt(3)
    r3 = p3.add_run("【可行性分析】" + t["feas"])
    set_run_cjk(r3, BODY_FONT, size=11.5)
    p4 = doc.add_paragraph()
    p4.paragraph_format.space_after = Pt(8)
    r4 = p4.add_run("【预期成果】" + t["out"])
    set_run_cjk(r4, BODY_FONT, size=11.5)

# ---- Section 4: 对比与推荐 ----
add_heading(doc, "四、选题对比与推荐", 1)
add_para(doc, "下表从社会需求契合度、技术前沿性、可行性、论文易写度四个维度对六个选题进行定性评估（★越多越优），供决策参考。")
add_table(doc,
    ["选题", "需求契合", "技术前沿", "可行性", "论文易写", "综合推荐"],
    [
        ["一、本地化老人陪护预警", "★★★★★", "★★★★", "★★★★", "★★★★", "⭐⭐⭐⭐⭐"],
        ["二、联邦学习医疗诊断", "★★★★★", "★★★★★", "★★★", "★★★★★", "⭐⭐⭐⭐⭐"],
        ["三、RAG课程问答与路径", "★★★★", "★★★★", "★★★★★", "★★★★★", "⭐⭐⭐⭐⭐"],
        ["四、基层智能报表核查", "★★★★★", "★★★", "★★★★★", "★★★★", "⭐⭐⭐⭐"],
        ["五、CV农产品分级溯源", "★★★★", "★★★★", "★★★", "★★★★", "⭐⭐⭐⭐"],
        ["六、骑手安全权益助手", "★★★★★", "★★★★", "★★★", "★★★", "⭐⭐⭐"],
    ],
    col_widths=[44, 18, 18, 18, 18, 22])
add_para(doc, "推荐策略：① 技术储备一般、追求稳妥高产 → 优先“选题三/RAG 课程问答”；② 希望论文亮点突出、有顶会热词 → 选“选题二/联邦学习”；③ 关注社会价值与适老化 → 选“选题一/本地化陪护”或“选题四/基层减负”；④ 有 CV/区块链基础 → 选“选题五”；⑤ 有移动端/边缘基础 → 选“选题六”。")

# ---- Section 5: 落地建议 ----
add_heading(doc, "五、选题落地与避坑建议", 1)
add_bullets(doc, [
    "避免“纯 Web 管理系统”式选题：该类题目技术含量低、同质化严重，答辩竞争力弱；应在传统系统中嵌入 AI/数据智能能力。",
    "范围控制优先：先定义最小可行产品（MVP），再逐步扩展；本科毕设重“完整闭环”而非“大而全”。",
    "数据来源要可靠：优先使用公开数据集（Kaggle、天池、学术数据集）或合法自建语料，避免数据合规风险。",
    "技术选型避坑：谨慎采用过新、社区薄弱的框架；优先选用文档完善、案例丰富的成熟生态（如 LangChain、Flower、YOLOv8）。",
    "论文与演示并重：AI 功能必须“跑得通、看得见”，准备对比实验与演示视频作为答辩杀手锏。",
    "与导师方向对齐：在下方选题基础上，结合导师研究领域做微调，可显著提升指导质量与产出效率。",
])

# Footer with page numbers
footer = sec.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = fp.add_run("第 ")
set_run_cjk(fr, BODY_FONT, size=9)
add_field(fp, "PAGE", "1")
fr2 = fp.add_run(" 页")
set_run_cjk(fr2, BODY_FONT, size=9)

out_path = r"C:\Users\wzd\Desktop\毕业设计\毕业设计选题方案.docx"
doc.save(out_path)
print("SAVED:", out_path)
