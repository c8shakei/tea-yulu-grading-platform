"""
生成 W1 数据集存储位置变更申请报告（CR-W1-001）
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_heading_style(doc):
    # 标题
    style = doc.styles["Title"]
    font = style.font
    font.name = "Microsoft YaHei"
    font.size = Pt(22)
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    # 正文
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Microsoft YaHei"
    font.size = Pt(11)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def add_heading_zh(doc, text, level=1):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(16 if level == 1 else 14 if level == 2 else 12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return h


def add_para(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(11)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    return p


def main():
    doc = Document()
    set_heading_style(doc)

    # 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("变更申请报告")
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(22)
    run.font.bold = True
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    run = title.add_run("\nChange Request Report")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    # 基本信息表
    table = doc.add_table(rows=7, cols=4)
    table.style = "Table Grid"
    cells = [
        ("变更编号", "CR-W1-001"),
        ("项目名称", "基于计算机视觉的农产品品质分级与溯源平台"),
        ("申请人", "W1（数据工程工程师）"),
        ("申请日期", "2026-09-04"),
        ("关联里程碑", "M1（D3–D4）数据就绪"),
        ("变更类型", "□ 需求变更  □ 设计变更  ☑ 环境与部署变更  □ 接口变更"),
        ("优先级", "高（阻塞 M1 交付）"),
    ]
    for i, (k, v) in enumerate(cells):
        row = table.rows[i]
        row.cells[0].text = k
        row.cells[1].text = v
        row.cells[2].text = ""
        row.cells[3].text = ""
        # 合并后两列
        row.cells[1].merge(row.cells[3])
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.name = "Microsoft YaHei"
                    r.font.size = Pt(11)
                    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    doc.add_paragraph()

    # 一、变更内容
    add_heading_zh(doc, "一、变更内容", level=1)
    add_para(doc, "建议将 TeaLeafAgeQuality 数据集的实际存储位置从项目所在 C 盘变更为 D 盘，并在项目根目录通过 Windows 目录 junction 保持接口契约路径不变。")
    add_para(doc, "具体路径规划：", bold=True)
    add_para(doc, "• 实际数据目录：D:\\BISHE_DATA\\datasets\\tea_yulu\\{train,val,test}\\{images,labels}")
    add_para(doc, "• 项目接口路径：C:\\Users\\wzd\\Desktop\\毕业设计\\datasets\\tea_yulu（junction 映射）")
    add_para(doc, "• 接口契约文件：data.yaml 中的 path 字段指向 D 盘实际路径")

    # 二、变更原因
    add_heading_zh(doc, "二、变更原因", level=1)
    add_para(doc, "1. C 盘可用空间仅剩约 6.0 GB，而 TeaLeafAgeQuality 全量 zip 约 4.59 GB，解压后图像、标注及增强输出将远超 6 GB，无法在 C 盘完成 M1 交付。")
    add_para(doc, "2. D 盘可用空间约 278 GB，足以容纳全量数据、中间文件及未来模型训练产物。")
    add_para(doc, "3. 该变更属于存储位置调整，不改变接口契约①（目录结构、类别顺序、YOLO 格式、data.yaml 字段）中定义的任何字段。")

    # 三、影响分析
    add_heading_zh(doc, "三、影响分析", level=1)
    add_para(doc, "对下游工作流影响如下：", bold=True)

    impact = doc.add_table(rows=5, cols=3)
    impact.style = "Table Grid"
    hdr = impact.rows[0].cells
    hdr[0].text = "受影响方"
    hdr[1].text = "影响内容"
    hdr[2].text = "风险等级"
    rows = [
        ("W1 数据工程", "需在 D 盘执行下载、解压、划分、增强", "低"),
        ("W2 视觉模型", "data.yaml 路径指向 D 盘，模型训练直接读取 junction 路径即可", "低"),
        ("W3 后端", "无影响（后端运行时读取的是推理结果，不直接读取训练集）", "无"),
        ("W4 前端", "无影响", "无"),
    ]
    for i, (who, what, risk) in enumerate(rows, start=1):
        row = impact.rows[i]
        row.cells[0].text = who
        row.cells[1].text = what
        row.cells[2].text = risk
    for row in impact.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.name = "Microsoft YaHei"
                    r.font.size = Pt(11)
                    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    add_para(doc, "版本管理影响：", bold=True)
    add_para(doc, "• datasets/ 目录已加入 .gitignore，不会进入 Git 版本库，因此 junction 对仓库提交无影响。")
    add_para(doc, "• 若其他协作者拉取代码，需自行在本地建立对应 junction 或直接将数据集放至 datasets/tea_yulu。")

    # 四、可选方案
    add_heading_zh(doc, "四、可选方案", level=1)
    add_para(doc, "方案 A（推荐）：D 盘存储 + Windows 目录 junction", bold=True)
    add_para(doc, "优点：空间充足、对现有接口契约无侵入、可逆；缺点：需在 Windows 创建 junction（非管理员账户可用 mklink /J）。")
    add_para(doc, "方案 B：清理/扩容 C 盘", bold=True)
    add_para(doc, "优点：保持单一盘符；缺点：4.59 GB 数据 + 增强后图像仍可能很快再次吃紧，且清理操作存在误删风险。")
    add_para(doc, "方案 C：仅使用 annotated 子集并大幅压缩数据规模", bold=True)
    add_para(doc, "优点：可留在 C 盘；缺点：偏离项目基线（SRS 第 5.1 节采用全量公开数据集），可能影响模型精度与论文可复现性。")

    # 五、建议决策
    add_heading_zh(doc, "五、建议决策", level=1)
    add_para(doc, "建议采用方案 A。W1 已预留脚本位置与目录结构，待组长批复后可立即执行 junction 创建并继续完成 M1 数据就绪。")

    # 六、组长审批
    add_heading_zh(doc, "六、组长审批", level=1)
    approval = doc.add_table(rows=3, cols=2)
    approval.style = "Table Grid"
    approval.rows[0].cells[0].text = "审批意见"
    approval.rows[0].cells[1].text = "☑ 同意方案 A    □ 同意方案 B    □ 同意方案 C    □ 驳回，理由："
    approval.rows[1].cells[0].text = "审批人"
    approval.rows[1].cells[1].text = ""
    approval.rows[2].cells[0].text = "审批日期"
    approval.rows[2].cells[1].text = ""
    for row in approval.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.name = "Microsoft YaHei"
                    r.font.size = Pt(11)
                    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    out_path = "C:/Users/wzd/Desktop/毕业设计/变更申请_CR-W1-001_数据集存储位置.docx"
    doc.save(out_path)
    print(f"已生成: {out_path}")


if __name__ == "__main__":
    main()
