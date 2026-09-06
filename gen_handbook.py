# -*- coding: utf-8 -*-
"""生成《AI 指挥手册：零基础如何命令 AI 完成毕业设计》Word 文档"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CJK = "微软雅黑"; HEI = "黑体"
doc = Document()
def set_cjk(run, name=CJK, size=None, bold=False):
    run.font.name = name; run.font.size = Pt(size) if size else None; run.bold = bold
    rPr = run._element.get_or_add_rPr(); rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None: rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), name); rFonts.set(qn('w:ascii'), name); rFonts.set(qn('w:hAnsi'), name)
normal = doc.styles['Normal']; normal.font.name = CJK; normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), CJK)
def H(text, level=1):
    p = doc.add_heading(level=level); r = p.add_run(text)
    set_cjk(r, HEI if level<=2 else CJK, size=16 if level==1 else (13 if level==2 else 11.5), bold=True); return p
def P(text, bold=False, size=10.5, color=None, italic=False):
    p = doc.add_paragraph(); r = p.add_run(text); set_cjk(r, CJK, size, bold); r.italic = italic
    if color: r.font.color.rgb = color; return p
def B(text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level==0 else 'List Bullet 2'); r = p.add_run(text); set_cjk(r, CJK, 10.5); return p
def NUM(text):
    p = doc.add_paragraph(style='List Number'); r = p.add_run(text); set_cjk(r, CJK, 10.5); return p
def CODE(text):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.6)
    r = p.add_run(text); set_cjk(r, "Consolas", 9.5, False)
    r.font.color.rgb = RGBColor(0x1a,0x1a,0x1a)
    pPr = p._p.get_or_add_pPr(); shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),'clear'); shd.set(qn('w:fill'),'F2F2F2'); pPr.append(shd); return p
def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=""; r=c.paragraphs[0].add_run(h); set_cjk(r,HEI,10,bold=True); c.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            cells[i].text=""; r=cells[i].paragraphs[0].add_run(str(v)); set_cjk(r,CJK,9.5)
    if widths:
        for i,w in enumerate(widths):
            for row in t.rows: row.cells[i].width=Cm(w)
    return t

# 封面
t = doc.add_paragraph(); t.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=t.add_run("AI 指挥手册"); set_cjk(r,HEI,24,bold=True)
s=doc.add_paragraph(); s.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=s.add_run("零基础如何命令 AI 完成毕业设计"); set_cjk(r,CJK,13,bold=True)
s2=doc.add_paragraph(); s2.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=s2.add_run("农产品品质分级与溯源平台（YOLOv8 + 哈希链溯源）  |  配套《项目章程 V1.1》"); set_cjk(r,CJK,10)
doc.add_paragraph()

# 0
H("零、给非技术同学的话", 1)
P("你不需要会写代码、不需要懂 YOLOv8 / 哈希链 / Python 是什么。你只需要做两件事：")
B("【下指令】把本手册里标好的“提示词”复制粘贴给 AI（WorkBuddy / Cursor 等对话窗口），让它干活；")
B("【做验收】按每节的“你怎么验收”清单，确认 AI 干完了、能跑起来。")
P("所有技术细节由 AI 落地，架构与进度由《项目章程》兜底。你是指挥官，AI 是施工队。", bold=True)
P("⚠️ 黄金法则：AI 给的代码如果报错，不要自己改——把整段红色报错文字原样贴回给 AI，说“报错了，请修复并说明原因”，它会自己修。", color=RGBColor(0xC0,0x39,0x2B))

# 1
H("一、给 AI 的 5 条通用指令法则（每次都适用）", 1)
NUM("目标清楚：说“我要做什么”，别说“帮我弄一下”。例：“用 FastAPI 写一个接收图片、返回分级结果的接口”。")
NUM("给上下文：第一次对话先贴一句“我们做农产品分级溯源平台，技术栈是 YOLOv8+哈希链+Vue+SQLite，代码全由你生成”。")
NUM("要“可运行”：每次都加一句“请给出可直接运行的完整代码，不要省略，不要只给片段”。")
NUM("要“测试/验证”：加一句“写完后告诉我怎么启动、怎么验证它真的跑通了”。")
NUM("要“解释”：加一句“用一句话解释你刚写的每段在干嘛，我要给导师讲”。")

# 2 环境
H("二、环境准备（复制给 AI 执行）", 1)
P("你只需在终端（或让 AI 代执行）跑下面命令。哈希链零依赖无需安装；YOLOv8 用本机 GPU 训练，也不用 Colab。", italic=True)
P("1）建立代码仓库（让 AI 帮你初始化，或复制给 AI）：", bold=True)
CODE("mkdir grain-trace && cd grain-trace && git init && mkdir data weights src web hashchain docs")
P("2）训练环境（本机 GPU）：", bold=True)
CODE("让 AI 用 pip 安装：torch torchvision ultralytics opencv-python（PyTorch CUDA 版自带 CUDA 运行时）。装完验证 torch.cuda.is_available() 返回 True 即成功。")
P("3）写 README（仓库根目录）：", bold=True)
CODE("echo '# 毕业设计：农产品分级+哈希链溯源，技术栈见章程' > README.md")
P("完成后在仓库根目录建一个 README.md，写一句“本项目为毕业设计：农产品分级+哈希链溯源，技术栈见章程”。", italic=True)

# 3 阶段指令
H("三、分阶段“命令 AI”提示词模板（核心）", 1)
P("按《章程》里程碑顺序推进。每个阶段复制对应提示词给 AI 即可。", italic=True)

H("阶段 P0 — 启动（Day 1）", 2)
P("提示词①（生成需求文档 SRS）：", bold=True)
CODE("你是我毕业设计的 AI 开发助手。项目：基于 YOLOv8 的农产品品质分级 + 哈希链溯源平台，技术栈 Python/YOLOv8/哈希链(Python hashlib)/FastAPI/Vue/SQLite，代码全由你生成。请产出《软件需求规格说明书 SRS》，含：项目目标、功能需求（分级、上链、查询、前端展示）、非功能需求（精度/性能/安全）、用例清单、数据模型初稿。用中文，Markdown 格式，可直接交导师审阅。")
P("提示词②（建仓库结构）：", bold=True)
CODE("请为上面项目初始化一个清晰的目录结构（data/ weights/ src/ web/ hashchain/ docs/），并写出每个目录放什么，生成即可运行的脚手架 README。")

H("阶段 P1 — 架构 + 双 PoC（Day 2-4）", 2)
P("提示词③（YOLOv8 推理 PoC）：", bold=True)
CODE("写一个最小可运行脚本：用 ultralytics 的 YOLOv8n 预训练模型，加载一张测试图片，输出检测框和类别。用 Python，给出 pip 安装命令、完整代码、运行方式。我本地没 GPU 也能跑（用 CPU）。")
P("提示词④（哈希链存证 PoC）：", bold=True)
CODE("用 Python 标准库 hashlib 实现一个最小哈希链存证模块：每条分级记录含(产品ID, 分级结果, 时间戳, 上一记录哈希)，计算并链接 SHA-256 哈希；提供 save_grade() 和 query_trace(产品ID) 两个函数；演示篡改任一历史记录会导致后续哈希校验失败。给出完整代码、如何运行、以及如何验证“改一条旧记录=链式校验不通过”。")
P("【你怎么验收】两张图：① 一张带检测框的农产品图片；② 哈希链 query_trace 返回的 JSON 溯源链（含每条记录的哈希）。两者都出来 = PoC 通过。", bold=True)

H("阶段 P2 — 训练分级模型（Day 4-10，Colab 免费 GPU）", 2)
P("提示词⑤（Colab 免费 GPU 训练 Notebook）：", bold=True)
CODE("用 Colab 写一个训练 Notebook（train.ipynb）：1) 在 Colab 免费 GPU 环境（菜单 运行时→更改运行时类型→GPU）里，从 Mendeley 下载 TeaLeafAgeQuality 数据集（DOI 10.17632/7t964jmmy3，CC BY 4.0）并解压；2) 用 ultralytics 训练 YOLOv8n 做分级（data.yaml 类别 T1-T4 映射为 特级/一级/二级/等外）；3) 训练 50 epoch，输出 mAP@0.5；4) 导出 best.pt 到 weights/。要求：每步有注释，支持断点续训；数据集只用 CC BY 等宽松许可。本机 CPU 环境仅用于推理与轻量验证。")
P("提示词⑥（推理 API）：", bold=True)
CODE("用 FastAPI 写一个接口 /predict：接收图片上传，调用上面训练好的 YOLOv8 权重做分级，返回 JSON（类别、置信度、建议等级）。给出完整代码、requirements.txt、启动命令、以及如何用 curl 测试。")
P("【你怎么验收】用一张图 curl 一下，返回带“等级”的 JSON；测试集 mAP@0.5 ≥ 0.85（AI 会打印这个数）。", bold=True)

H("阶段 P3 — 哈希链溯源（Day 8-16，与 P2 并行）", 2)
P("提示词⑦（溯源 API + 联动）：", bold=True)
CODE("在已有 FastAPI 项目里加两个接口：/upload-grade（把分级结果写入哈希链 save_grade）和 /trace（调用 query_trace 返回溯源链）。哈希链用前面 PoC 的模块。给出完整代码、配置说明、以及如何验证写入后查询一致、篡改历史记录会被校验拦住。")
P("【你怎么验收】调用一次 /upload-grade，再用 /trace 查，两次返回的等级一致 = 溯源闭环通过。", bold=True)

H("阶段 P4 — Vue 前端（Day 14-24）", 2)
P("提示词⑧（前端页面）：", bold=True)
CODE("用 Vue3 + Vite + TypeScript 写一个网页：① 上传图片调用后端 /predict 显示分级结果；② 输入产品ID调用 /trace 显示溯源链条；③ 用图表展示统计。界面参考现代 SaaS 风格，响应式。给出完整项目结构、依赖、启动命令。我不太懂前端，请注释关键文件作用。")
P("【你怎么验收】npm run dev 后能打开网页，上传图看到分级、输入ID看到溯源链。", bold=True)

H("阶段 P5 — 集成测试（Day 22-24）", 2)
P("提示词⑨（端到端测试）：", bold=True)
CODE("为上面的系统写一份端到端验证脚本/清单：从上传图片→分级→上链→查询，全程跑通。列出每一步的预期结果与如何判断通过；并给出常见报错及排查。")

H("阶段 P6 — 论文（Day 22-30）", 2)
P("提示词⑩（论文章节）：", bold=True)
CODE("帮我按毕业设计论文结构写初稿各章：绪论、相关技术（YOLOv8/哈希链原理，用通俗语言）、需求分析、系统设计（架构图用文字描述+我提供图）、模型训练与实验（用我给的数据：mAP=__、数据集规模=__）、系统实现、总结。每章 1500-2500 字，中文，术语首次出现给解释。先列大纲给我确认再写。")
P("提示词⑪（降重）：", bold=True)
CODE("下面这段论文文字查重率偏高，请在保持原意和专业性的前提下改写降重，并标注改了哪些表述：[粘贴你的段落]。")
P("【你怎么验收】论文结构完整、能讲清“做了什么+怎么做的+效果如何”；查重率低于学校阈值。", bold=True)

# 4 验收总表
H("四、全局验收清单（D30 前逐项打勾）", 1)
table(["验收项","判据","对应里程碑"],
[["分级模型跑通","一张图能出等级，mAP≥0.85","M2"],
 ["溯源上链可查","上链后查询一致，100%成功","M3"],
 ["网页能用","上传/查询两个功能正常","M4"],
 ["系统端到端演示","现场走完“检测→上链→查询”","M4"],
 ["论文初稿","结构完整，可讲清三要素","M5"],
 ["查重通过","低于学校阈值","M5"],
 ["答辩PPT+预答辩","材料齐全，讲过一遍","M5"]],
 widths=[3.5,8.5,2.5])

# 5 救火
H("五、卡壳救火：报错了怎么办", 1)
B("把红色报错整段复制，贴给 AI，加一句：“这是完整报错，请定位原因并给出修复后的完整代码，别只说思路。”")
B("环境装不上（如 PyTorch GPU/CUDA）：直接说“我在 Windows，装 XX 失败了，报错是…，请给我最简替代方案或一步步排查”。")
B("Colab GPU 训练中断：说“训练到第 X epoch 断了/Colab 会话超时，请改成支持断点续训的代码，并把权重定期存到 Google 云端硬盘”。")
B("AI 改崩了之前能跑的代码：说“回退到上一版能跑的状态，只做 XX 这一处改动，改完告诉我”。")
B("任何“看不懂 AI 在干嘛”的时刻：说“用大白话解释你刚才做了什么、为什么，我要给导师汇报”。")

# 6 你拍板
H("六、哪些时刻必须你拍板（不要交给 AI 擅自决定）", 1)
B("范围变更：要不要加新功能 → 你定，走章程变更控制。")
B("技术分叉已代定项：溯源=Python 哈希链、数据库 SQLite、前端 Vue（你可推翻重选）。")
B("数据集类别：应用品牌已定为恩施玉露茶（湖北地理标志绿茶）；训练主用公开集 TeaLeafAgeQuality（CC BY 4.0，4 类嫩度 T1-T4→特级/一级/二级/等外），可补少量自建标注，分特级/一级/二级标注。")
B("答辩日期已确认：2027 年 5 月中旬；中期检查日期待学校通知；学校论文模板与查重阈值 → 你提供，我据此调格式。")
B("论文结论与“创新点”表述 → 你把关，AI 只起草。")

# 7 术语
H("七、术语一句话小抄", 1)
table(["术语","大白话"],
[["YOLOv8","一个“看图片认物体”的 AI 模型，这里用来给农产品分级"],
 ["哈希链","一条用密码学哈希串起来的“谁都改不了”的存证链，用来存分级结果防篡改"],
 ["存证模块","你项目里用 Python 写的“存分级/查分级”小程序（hashlib 实现）"],
 ["GPU/CUDA","让你的显卡帮 PyTorch 算数，训练比 CPU 快几十倍；PyTorch 自带 CUDA 运行时"],
 ["API","两个程序之间“递纸条”的接口，前端靠它拿数据"],
 ["Vue","做网页前端的一套工具，你已选它"],
 ["SQLite","一个文件就是一个数据库，零配置"],
 ["训练脚本 train.py","你让 AI 写的 YOLOv8 训练程序，在本机 GPU 上跑，输出 best.pt 权重文件"],
 ["mAP@0.5","衡量分级准不准的指标，≥0.85 算达标"]],
 widths=[3.0,11.5])

# 附录
H("附录：与《项目章程》的对应关系", 1)
B("本手册是《项目章程 V1.1》的操作层配套：章程管“为什么/做什么/何时”，本手册管“怎么让 AI 做”。")
B("里程碑 M0–M5 与手册阶段 P0–P6 一一对应；卡任何阶段先看章程对应节，再回本手册找提示词。")

doc.save("AI指挥手册_农产品分级溯源平台.docx")
print("OK saved handbook")
