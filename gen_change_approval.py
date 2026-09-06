# -*- coding: utf-8 -*-
"""生成《变更批复书_CR-W1-001.docx》——组长对 W1 变更申请的裁决。"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

WS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WS, "变更批复书_CR-W1-001.docx")


def set_base_font(doc):
    st = doc.styles["Normal"]
    st.font.name = "微软雅黑"
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
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
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9.5)
            r.font.name = "微软雅黑"
            r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    return t


def shade(p, fill="F2F2F2"):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def callout(doc, text, fill="FFF4E5"):
    """单段强调块：左边框 + 底纹"""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)
    pbdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:color"), "E8A33D")
    pbdr.append(left)
    pPr.append(pbdr)
    r = p.add_run("  " + text)
    r.font.size = Pt(10)
    r.font.name = "微软雅黑"
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    return p


def code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3)
    shade(p, "F2F2F2")
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(9)
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    return p


doc = Document()
set_base_font(doc)

# ---------------- 标题 ----------------
doc.add_heading("变更批复书", level=0)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = sub.add_run("Change Request Approval · CR-W1-001 · 数据集存储位置变更")
rs.bold = True
rs.font.size = Pt(12)

# ---------------- 基本信息 ----------------
doc.add_heading("一、基本信息", level=1)
add_table(doc, ["项", "内容"], [
    ["变更编号", "CR-W1-001"],
    ["项目名称", "基于计算机视觉的农产品品质分级与溯源平台"],
    ["申请人", "W1（数据工程工程师）"],
    ["申请日期", "2026-09-04"],
    ["批复人", "项目组长"],
    ["批复日期", "2026-09-04"],
    ["关联里程碑", "M1（D3–D4）数据就绪"],
    ["变更类型", "环境与部署变更"],
    ["优先级", "高（阻塞 M1 交付）"],
    ["批复结论", "有条件批准 —— 准予实施方案 A，须满足第四节三项强制约束"],
])

# ---------------- 裁决结论 ----------------
doc.add_heading("二、裁决结论", level=1)
add_table(doc, ["候选方案", "裁决", "理由摘要"], [
    ["方案 A：D 盘存储 + junction 映射", "准予实施（附加约束）",
     "空间充足、对接口契约逻辑结构无侵入、可逆；需补齐相对路径与建链脚本"],
    ["方案 B：清理 / 扩容 C 盘", "否决",
     "治标不治本，4.59 GB 原始数据叠加增强输出仍将持续吃紧，且清理有误删风险"],
    ["方案 C：仅用 annotated 子集压缩规模", "否决",
     "偏离 SRS 第 5.1 节“采用全量公开数据集”基线，削弱模型精度与论文可复现性"],
])
callout(doc, "结论：批准 W1 建议的方案 A，但属「有条件批准」——未满足下方三项强制约束前，不得视为 M1 交付达成。")

# ---------------- 批准内容 ----------------
doc.add_heading("三、批准内容", level=1)
doc.add_paragraph("准予按以下方式调整数据集物理存储位置，接口契约①的逻辑结构保持不变：")
code(doc,
     "实际数据目录：D:\\BISHE_DATA\\datasets\\tea_yulu\\{train,val,test}\\{images,labels}\n"
     "项目接口路径：C:\\Users\\wzd\\Desktop\\毕业设计\\datasets\\tea_yulu   （junction 映射，mklink /J）\n"
     "契约保持不变：目录结构 / 类别顺序 / YOLO 标注格式 / data.yaml 字段名")
doc.add_paragraph(
    "说明：C 盘剩余约 6.0 GB，全量压缩包约 4.59 GB，叠加解压与增强输出后确已无法承载 M1；"
    "D 盘可用约 278 GB，方案在容量上成立。认可 W1「仅为存储位置调整、不改变契约逻辑结构」的判断。"
)

# ---------------- 附加强制约束 ----------------
doc.add_heading("四、附加强制约束（未满足则 M1 不予验收）", level=1)

doc.add_heading("约束 1：data.yaml 的 path 必须使用相对路径", level=2)
doc.add_paragraph(
    "禁止在 data.yaml 中硬编码 D:\\ 或任何盘符开头的绝对路径。正确写法示例："
)
code(doc, "path: ../datasets/tea_yulu\ntrain: images/train\nval: images/val\nnc: 4\nnames: [\"特级\", \"一级\", \"二级\", \"等外\"]")
doc.add_paragraph("原因：本项目的冻结约束明确「训练用 Colab GPU，本地仅做 CPU 推理」，即 W2 的模型训练主要发生在 Colab 环境。"
                  "Colab 上不存在 D 盘，也不存在本机的 junction 映射；一旦 data.yaml 写死 D:\\ 路径，W2 在 Colab 将无法定位数据集，"
                  "直接阻塞 M2。同时论文要求实验可复现，硬编码本机盘符会使第三方无法复现，属学术硬伤。")

doc.add_heading("约束 2：交付 scripts/setup_data_link.bat 一键建链脚本并自测", level=2)
doc.add_paragraph(
    "junction 属本地环境状态、不进版本库。缺少可一键重建的脚本，将导致环境不可还原，"
    "换机或重装后 W2 / W5 无法恢复数据路径。脚本须包含目录创建、mklink /J 建链、建链结果校验三段，并由 W1 自测通过。"
)

doc.add_heading("约束 3：《数据说明》须写明 Colab 取数方案", level=2)
doc.add_paragraph(
    "须明确 W2 在 Colab 上如何取得同一份数据集（如上传 Google Drive 后挂载，或直接从 Mendeley 重新拉取），"
    "不得让 W2 依赖本机 junction。此项是 M1 与 M2 之间的衔接前提。"
)

# ---------------- 对影响分析的修正 ----------------
doc.add_heading("五、对原申请影响分析的修正（重要）", level=1)
doc.add_paragraph("原申请第三节影响分析中，W2 一行记为：")
code(doc, "W2 视觉模型 | data.yaml 路径指向 D 盘，模型训练直接读取 junction 路径即可 | 风险等级：低")
doc.add_paragraph("该判断不成立，现予更正：")
add_table(doc, ["项", "原评估", "组长更正"], [
    ["W2 受影响等级", "低", "中（须以 Colab 取数方案到位为前提）"],
    ["依据", "假定训练在本机进行", "冻结约束规定训练在 Colab GPU 进行，junction 仅在本机 Windows 生效"],
    ["前置条件", "无", "W1 交付 Colab 取数方案后，W2 方可启动 M2 训练"],
])
callout(doc, "这是本次变更最容易被忽略的一处连带风险：junction 是本机机制，跨到 Colab 即失效。"
             "本条已同步写入 W1 与 W2 的员工提示词，作为双方的行为约束。")

# ---------------- 生效范围 ----------------
doc.add_heading("六、生效范围与后续动作", level=1)
add_table(doc, ["对象", "须执行动作"], [
    ["W1", "按本批复执行；M1 交付须含建链脚本、相对路径 data.yaml、Colab 取数说明、数据说明.md"],
    ["W2", "按 W1《数据说明》在 Colab 准备数据集；发现 data.yaml 含盘符绝对路径时立即上报组长，不得自行改路径绕过"],
    ["W3", "无影响，无需动作（后端运行时读取推理结果，不直读训练集）"],
    ["W4", "无影响，无需动作"],
    ["W5", "M4 集成时须验证「检测→上链→查询」全链路不依赖数据集物理路径"],
    ["组长", "已同步更新接口契约①、派工指导手册、W1 / W2 提示词"],
])

# ---------------- 同步更新记录 ----------------
doc.add_heading("七、已同步更新记录", level=1)
add_table(doc, ["受影响文件", "更新内容"], [
    ["接口契约①（数据集契约）", "新增 D 盘存储 + junction 约定，及三条强制约束"],
    ["派工指导手册", "W1 交付物定义更新（新增建链脚本、Colab 取数说明）"],
    ["W1_提示词.txt", "新增 CR-W1-001 强制约束、验收口径、汇报要求"],
    ["W2_提示词.txt", "新增 CR-W1-001 连带约束（Colab 取数 / 绝对路径违约上报）"],
])

# ---------------- 验收口径 ----------------
doc.add_heading("八、M1 验收口径", level=1)
doc.add_paragraph("以下四项全部满足，方视为 M1「数据就绪」达成：")
for i, s in enumerate([
    "junction 建好且可从项目路径正常访问数据；",
    "data.yaml 的 path 为相对路径（无盘符绝对路径）；",
    "划分脚本可复现（固定随机种子，重复执行结果一致）；",
    "Colab 取数方案已在《数据说明》中写明且可操作。",
], 1):
    doc.add_paragraph(f"{i}. {s}")

# ---------------- 签署 ----------------
doc.add_heading("九、批复签署", level=1)
add_table(doc, ["项", "内容"], [
    ["批复人", "项目组长"],
    ["批复日期", "2026-09-04"],
    ["生效日期", "2026-09-04（即刻生效）"],
    ["申请人确认", "W1 签收：____________    日期：____________"],
])

tip = doc.add_paragraph()
rt = tip.add_run("注：本批复书为组长的正式裁决文件，与 W1 提交的《变更申请报告 CR-W1-001》配套存档，"
                 "作为 M1 验收与论文过程管理（变更控制）的追溯依据。")
rt.italic = True
rt.font.size = Pt(9)
rt.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

doc.save(OUT)
print("OK saved:", OUT)
