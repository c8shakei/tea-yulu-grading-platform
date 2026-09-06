# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""生成《变更申请报告_CR-W1-003.docx》——W1 就「训练平台迁移 Colab→Kaggle + 脚本平台可移植化」提交组长审批。
格式严格对齐已归档的《变更申请_CR-W1-002_训练脚本yolov8s多规模支持.docx》。"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

WS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WS, "变更申请_CR-W1-003_训练平台迁移Kaggle与脚本可移植化.docx")


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


def field(doc, label, value, bold_label=True):
    """基本信息字段：标签段 + 值段（与 CR-W1-002 申请报告一致，堆叠呈现）。"""
    p1 = doc.add_paragraph()
    r1 = p1.add_run(label)
    r1.bold = bold_label
    r1.font.size = Pt(10.5)
    r1.font.name = "微软雅黑"
    r1.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    p2 = doc.add_paragraph()
    r2 = p2.add_run(value)
    r2.font.size = Pt(10.5)
    r2.font.name = "微软雅黑"
    r2.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


doc = Document()
set_base_font(doc)

# ---------------- 标题 ----------------
doc.add_heading("变更申请报告", level=0)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = sub.add_run("Change Request Report · CR-W1-003 · 训练平台迁移（Colab→Kaggle）与脚本平台可移植化")
rs.bold = True
rs.font.size = Pt(12)

# ---------------- 基本信息 ----------------
field(doc, "变更编号", "CR-W1-003")
field(doc, "项目名称", "基于计算机视觉的农产品品质分级与溯源平台")
field(doc, "申请人", "W1（数据工程工程师）")
field(doc, "申请日期", "2026-09-05")
field(doc, "关联里程碑", "M2（模型训练）· yolov8s 追加实验 + 训练平台迁移")
field(doc, "变更类型", "□ 需求变更  □ 设计变更  ☑ 环境与部署变更  □ 接口变更")
field(doc, "优先级", "中（yolov8s 实验因 Colab 免费 GPU 限额中断，须换平台续训；不阻塞已交付的 yolov8n 基线）")

# ---------------- 一、变更内容 ----------------
doc.add_heading("一、变更内容", level=1)
doc.add_paragraph(
    "为支撑 CR-W1-002 已批复的 yolov8s 追加实验继续推进，对 M2 训练相关脚本做「平台可移植化」改造，"
    "并将训练执行环境由 Colab 免费 T4 迁移至 Kaggle 免费 P100。具体变更如下："
)
content = [
    "train_detect.py / train_cls.py / sync_checkpoints.py 新增三个环境变量 WORK_DIR / SYNC_TARGET / DATA_ROOT，"
    "实现「平台可移植」：默认行为仍走 Colab + Google Drive（旧流程完全兼容）；在 Kaggle 等无 Drive 环境设 SYNC_TARGET 即把产物存到本地目录、不挂 Drive。",
    "数据集定位逻辑改造：优先读取 WORK_DIR/datasets/tea_yulu（Kaggle 解压落点），其次退回 Colab 本地目录，再到 Drive zip，自动适配两平台。",
    "resolve_data_yaml() 改为写到可写目录（Kaggle 的 /kaggle/input 为只读，写回会失败），规避 Kaggle 只读输入目录报错导致训练无法启动。",
    "yolov8s 实验执行环境由 Colab T4 迁移至 Kaggle 免费 P100 GPU（约 30h/周滚动额度）；训练脚本、数据、超参与产物命名规则均不变，仅执行环境切换。",
]
for c in content:
    doc.add_paragraph(c, style="List Bullet")

# ---------------- 二、变更原因 ----------------
doc.add_heading("二、变更原因", level=1)
reasons = [
    "2026-09-05，yolov8s 检测训练在 Colab 免费 T4 上因「已达到 Colab 的使用量限额（GPU）」中断——Colab 免费档 GPU 为滚动窗口限额，短期不可恢复，且 Google 未公开固定重置时刻。",
    "免费 Colab 无法稳定支撑多次长跑（yolov8n 已占用一轮窗口、yolov8s 又一轮），继续等待配额重置会拖慢 M2 进度；临近答辩周期，依赖不可控配额风险过高。",
    "Kaggle 免费提供 P100 GPU（性能优于 Colab T4），额度约 30h/周滚动，足以完成一次 yolov8s 检测+分类训练，且不受 Colab 抢卡影响，是最稳妥的零成本替代。",
    "原脚本把产物路径写死 /content/drive，在 Kaggle 上会直接崩溃；须先改造脚本做平台可移植，再迁移，避免重复踩坑并保证 yolov8n 基线在 Colab 旧流程中零改动。",
]
for r in reasons:
    doc.add_paragraph(r, style="List Bullet")

# ---------------- 三、影响分析 ----------------
doc.add_heading("三、影响分析", level=1)
add_table(doc, ["受影响方", "影响内容", "风险等级"], [
    ["W1 数据工程",
     "改造 train_detect.py / train_cls.py / sync_checkpoints.py（环境变量 + 可移植同步逻辑）；已通过 py_compile 与两路径逻辑自检（Colab/Drive 默认路径 + Kaggle/SYNC_TARGET 路径均验证）",
     "低"],
    ["W2 视觉模型（执行人）",
     "平台由 Colab 改为 Kaggle：需建 Notebook、开 GPU、上传数据集 zip 与三脚本、设 SYNC_TARGET 后 %run；训练配置与数据不变",
     "低"],
    ["W3 后端",
     "模型产物文件名与接口契约②（best_detect.pt / best_detect_yolov8s.pt）完全不变；仅存放位置由 Drive 变 Kaggle 输出，下载到本地 models\\ 后路径一致",
     "低"],
    ["W4 前端",
     "依赖 W3 接口；随 W3 不变",
     "低"],
    ["版本管理",
     "三脚本改动进入 Git 版本库；Kaggle 输出与 Drive 双份产物不进版本库（.gitignore 范围）",
     "低"],
    ["数据集",
     "需重新上传 tea_yulu_dataset.zip（约 778MB）至 Kaggle（单数据集上限 20GB，充足）",
     "低"],
])

# ---------------- 四、可选方案 ----------------
doc.add_heading("四、可选方案", level=1)
doc.add_paragraph("方案 A（推荐）：脚本平台可移植改造 + 迁移 Kaggle（已实施改造部分）")
doc.add_paragraph("优点：默认仍走 Colab+Drive（完全兼容，yolov8n 流程零改动）；Kaggle 下用 SYNC_TARGET 指本地、不挂 Drive；一次改造两平台通用；产物命名/基线隔离不变。", style="List Bullet")
doc.add_paragraph("缺点：需一次性上传数据集（778MB）+ 三脚本到 Kaggle，有迁移操作成本（约 15min）。", style="List Bullet")

doc.add_paragraph("方案 B：等 Colab 免费 GPU 配额自然重置后续训")
doc.add_paragraph("优点：零改动、零费用。", style="List Bullet")
doc.add_paragraph("缺点：重置时间不可控（滚动窗口，数小时~次日），阻塞 M2 进度、不可控，临近答辩风险高。否决。", style="List Bullet")

doc.add_paragraph("方案 C：升级 Colab Pro / 按量购买计算单元")
doc.add_paragraph("优点：立即可用。", style="List Bullet")
doc.add_paragraph("缺点：产生费用（约 $10/月或按量），且 Colab 免费档历史已多次限额，属治标不治本。否决。", style="List Bullet")

doc.add_paragraph("方案 D：改用本地 GPU 训练")
doc.add_paragraph("优点：完全可控。", style="List Bullet")
doc.add_paragraph("缺点：本机无独显，CPU 训练 yolov8s 不现实（单轮数十小时起）。否决。", style="List Bullet")

# ---------------- 五、建议决策 ----------------
doc.add_heading("五、建议决策", level=1)
doc.add_paragraph(
    "建议采用方案 A。脚本平台可移植改造已完成并通过语法校验；待组长批复后即可在 Kaggle 启动 yolov8s 追加实验。"
    "yolov8n 基线（已交付、存于本地 models\\ 与 Drive BISHE/models/）完全不受影响，M2 基线交付已达成。"
)
doc.add_paragraph(
    "待决策项（请组长裁定，影响执行授权边界）：① 是否认可「训练平台由 Colab 迁移至 Kaggle」作为 CR-W1-002 追加实验的执行环境调整"
    "（属环境与部署变更，不改变模型结构与接口契约②）；② 若 Kaggle 同样遇额度中断，是否授权 W1 在「免费平台轮换」框架内"
    "（Colab/Kaggle 间）自行续训、并沿用同一套可移植脚本，无需就每次平台切换二次批复，以降低答辩周期阻塞风险。"
)

# ---------------- 六、组长审批 ----------------
doc.add_heading("六、组长审批", level=1)
doc.add_paragraph("审批意见")
doc.add_paragraph("□ 同意方案 A    □ 同意方案 B    □ 同意方案 C    □ 驳回，理由：")
doc.add_paragraph("审批人：________________")
doc.add_paragraph("审批日期：________________")

doc.save(OUT)
print("OK saved:", OUT)
