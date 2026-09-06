# -*- coding: utf-8 -*-
"""生成《软件需求规格说明书(SRS)》Word 文档 —— 农产品品质分级与溯源平台。
与技术栈对齐：YOLOv8 + Python 哈希链溯源 + Vue 前端 + FastAPI + SQLite + 本地CPU/Colab GPU。
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PRODUCT = "农产品品质分级与溯源平台"
SUBJECT = "【农产品类别：恩施玉露茶（湖北地理标志绿茶，国家级非遗蒸青工艺） —— 已冻结，全文以此为准】"

doc = Document()

# ---- 基础样式 ----
def set_base_style():
    st = doc.styles['Normal']
    st.font.name = '宋体'
    st.font.size = Pt(10.5)
    st._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    for sec in doc.sections:
        sec.top_margin = Inches(0.9); sec.bottom_margin = Inches(0.9)
        sec.left_margin = Inches(1.0); sec.right_margin = Inches(1.0)

def h1(text):
    p = doc.add_heading(level=1)
    r = p.add_run(text); r.font.name = '黑体'; r.font.size = Pt(15)
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    return p

def h2(text):
    p = doc.add_heading(level=2)
    r = p.add_run(text); r.font.name = '黑体'; r.font.size = Pt(12.5)
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    return p

def h3(text):
    p = doc.add_heading(level=3)
    r = p.add_run(text); r.font.name = '黑体'; r.font.size = Pt(11)
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    return p

def para(text, bold=False, size=10.5, align=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(size)
    r.font.name = '宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    if align: p.alignment = align
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Inches(0.3 + 0.25*level)
    r = p.add_run(text); r.font.size = Pt(10.5)
    r.font.name = '宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    return p

def numbered(text):
    p = doc.add_paragraph(style='List Number')
    r = p.add_run(text); r.font.size = Pt(10.5)
    r.font.name = '宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    return p

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, htext in enumerate(headers):
        hdr[i].text = ''
        run = hdr[i].paragraphs[0].add_run(htext)
        run.bold = True; run.font.size = Pt(9.5); run.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        run.font.name = '黑体'; run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:fill'),'1F4E78')
        hdr[i]._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(9.5)
            run.font.name = '宋体'; run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t

def add_toc_field():
    p = doc.add_paragraph()
    run = p.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'TOC \\o "1-3" \\h \\z \\u')
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '右键“更新域”生成目录'
    r.append(t); fld.append(r); p._p.append(fld)

# ============== 封面 ==============
set_base_style()
title = doc.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run('软件需求规格说明书'); r.bold = True; r.font.size = Pt(24)
r.font.name = '黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run(f'（{PRODUCT}）'); r.font.size = Pt(16); r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体')
doc.add_paragraph()
meta = doc.add_paragraph(); meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
for line, sz in [('项目名称：'+PRODUCT, 12), (SUBJECT, 10.5), ('版本：V1.0（草案，待评审冻结）', 11), ('文档类型：软件需求规格说明书（SRS）', 11), ('', 6)]:
    pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = pp.add_run(line); rr.font.size = Pt(sz); rr.font.name='宋体'; rr._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')
doc.add_paragraph()
note = doc.add_paragraph(); note.alignment = WD_ALIGN_PARAGRAPH.CENTER
rr = note.add_run('说明：本文档依据《软件工程》《软件过程与管理》需求工程章节编制，\n作为 P0 启动阶段 M0 退出门的交付物；所有需求条目均可追溯至项目章程。'); rr.font.size = Pt(9.5); rr.font.color.rgb = RGBColor(0x80,0x80,0x80)
doc.add_page_break()

# 目录
h1('目录')
add_toc_field()
doc.add_page_break()

# ============== 1 引言 ==============
h1('1. 引言')
h2('1.1 编写目的')
para('本文档旨在对“'+PRODUCT+'”的功能需求、非功能需求、数据需求与接口需求进行结构化定义，作为后续系统设计、编码实现、测试验收与论文撰写的规格基线。文档经评审冻结后，任何需求变更须走项目章程规定的变更控制流程（影响评估 → 用户审批 → 版本升级）。')
h2('1.2 项目背景')
para('乡村振兴与农产品上行背景下，传统分级高度依赖人工目测，标准不一、效率低、可追溯性弱；消费者难以核验产地与品质，出现质量争议时缺乏权威证据链。本项目以计算机视觉自动分级替代人工目测，并以哈希链为每一批次分级结果生成不可篡改溯源凭证，实现“分级—存证—查询”一体化。')
h2('1.3 范围')
para('本版范围（与章程一致，已冻结）：单类农产品 + Web 端。明确不包含：多模态融合分级、移动 App、跨企业真实分布式账本运营、SaaS 多租户。')
table(['维度','本版包含','本版排除'],
      [['农产品','恩施玉露茶（1 类，已冻结）','多类并行、跨品类通用'],
       ['终端','Web 管理/查询端','移动 App、微信小程序'],
       ['溯源','本地哈希链存证','多节点共识联盟链、跨境溯源'],
       ['用户','管理员 + 普通查询用户','供应商自助入驻、第三方审计']],
      widths=[1.2,2.6,2.6])
h2('1.4 术语与缩略语')
table(['术语','含义'],
      [['YOLOv8','You Only Look Once v8，单阶段目标检测/分级模型'],
       ['哈希链','以 SHA-256 将前一条记录哈希值串联进当前记录，形成不可篡改链'],
       ['mAP@0.5','IoU 阈值为 0.5 时的平均精度均值，分级模型核心精度指标'],
       ['PoC','概念验证（Proof of Concept）'],
       ['M0–M5','项目章程定义的 6 个里程碑']],
      widths=[1.4,5.0])
h2('1.5 参考资料')
bullet('《软件工程》（生命周期模型、需求工程章节）')
bullet('《软件过程与管理》（项目章程、需求基线、变更控制章节）')
bullet('项目章程与进度计划 V1.1（30 天基线）')
bullet('开题报告 V1.0（农产品分级溯源平台）')
bullet('AI 指挥手册 V1.0')

# ============== 2 总体描述 ==============
h1('2. 总体描述')
h2('2.1 产品前景')
para('平台服务于农产品收购商、质检人员与终端消费者：收购端批量上传/采集农产品图像，系统自动分级并上链存证；查询端输入批次号即可查看分级结论与溯源链，验证真伪。目标是把“凭经验分级”升级为“凭模型分级 + 凭密码学存证”。')
h2('2.2 用户特征')
table(['角色','特征','核心诉求'],
      [['管理员','具备基本计算机操作，非技术人员','批量导入图像、查看分级统计、管理批次'],
       ['质检员','现场操作，可能用手机/相机采集','快速上传、即时获分级结果'],
       ['消费者/查询用户','仅访问公开查询页','输入批次号核验分级与溯源']],
      widths=[1.3,2.4,2.5])
h2('2.3 运行环境')
para('服务端：Python 3.13 + FastAPI + SQLite；模型推理：Ultralytics YOLOv8（本地 CPU 推理，GPU 训练走 Colab）。前端：Vue 3 + Vite + Tailwind。溯源：Python hashlib 哈希链（无需 Docker/区块链节点）。')
h2('2.4 设计与实现约束')
bullet('全部技术栈须开源免费（已审计：YOLOv8 学术非商用免费、其余 Apache/MIT）。')
bullet('数据集须采用 CC0 / CC-BY / Apache 等宽松许可，来源与许可写入 data/README 可追溯。主训练集：TeaLeafAgeQuality（CC BY 4.0，4403 张，4 类嫩度 T1-T4），映射 T1→特级/T2→一级/T3→二级/T4→等外；恩施玉露茶为应用品牌。')
bullet('模型权重、数据集、代码均纳入 Git 版本管理与基线 tag。')
h2('2.5 假设与依赖')
bullet('假设：存在公开、许可合规的该类农产品图像数据集；用户具备浏览器与基本上网能力。')
bullet('依赖：GitHub/Gitee 账号（代码备份）、Colab 账号（GPU 训练）、Python 运行环境。')

# ============== 3 功能需求 ==============
h1('3. 功能需求')
h2('3.1 功能模块总览')
table(['编号','模块','说明'],
      [['FR-01','图像采集与导入','批量上传/单张上传农产品图像，支持常见格式'],
       ['FR-02','自动分级','YOLOv8 推理，输出等级（恩施玉露茶：特级/一级/二级）与置信度'],
       ['FR-03','分级结果管理','查看/导出/复核分级记录，支持人工校正'],
       ['FR-04','哈希链溯源','对每条分级记录生成哈希并串联成链，提供校验'],
       ['FR-05','溯源查询','按批次号查询分级结论与完整溯源链'],
       ['FR-06','统计看板','分级分布、批次量、精度等可视化'],
       ['FR-07','用户与权限','管理员/查询用户两类角色，基础鉴权'],
       ['FR-08','系统配置','阈值、模型版本、数据集路径等配置']],
      widths=[0.8,1.8,4.0])

h2('3.2 FR-01 图像采集与导入')
numbered('用户选择本地图像文件或文件夹批量导入。')
numbered('系统校验格式（jpg/png/bmp）、尺寸与完整性，拒绝损坏文件。')
numbered('图像存入链下存储（本地文件系统目录，按批次组织），并记录元数据（文件名、大小、导入时间、批次号）。')
para('验收：导入 100 张图像，成功率 ≥ 99%；损坏文件被拒绝并提示。', bold=True)

h2('3.3 FR-02 自动分级')
numbered('对导入图像调用 YOLOv8 推理接口，返回等级标签与置信度。')
numbered('支持等级体系可配置（默认 3 级，对齐恩施玉露茶感官标准：特级/一级/二级）。')
numbered('单张推理耗时在 CPU 上 ≤ 2s（演示数据集下）。')
para('验收：测试集 mAP@0.5 ≥ 0.85；置信度低于阈值时标记为“待人工复核”。', bold=True)

h2('3.4 FR-03 分级结果管理')
numbered('以列表/卡片展示分级记录，支持按批次、等级、时间筛选。')
numbered('支持导出 CSV / Excel。')
numbered('支持人工校正：管理员可修改等级，校正记录留痕（写入溯源链）。')

h2('3.5 FR-04 哈希链溯源（核心创新）')
numbered('每条分级记录计算 SHA-256 哈希，并包含上一条记录的哈希（创世块哈希为固定盐值）。')
numbered('哈希链存储于本地文件/SQLite，按批次索引。')
numbered('提供“校验整链”功能：从创世块重算至最新，任一记录被篡改即校验失败并定位。')
para('验收：篡改链中任意一条记录后，校验函数 100% 检测到不一致并指出位置。', bold=True)

h2('3.6 FR-05 溯源查询')
numbered('查询用户输入批次号，返回该批次分级结论、各记录哈希与上链顺序。')
numbered('返回结果附带“链完整性：通过/失败”标识。')
numbered('（可选）提供查询结果的文本/图片导出作为凭证。')

h2('3.7 FR-06 统计看板')
numbered('展示分级等级分布饼图、近 N 日批次量折线、模型精度指标。')
numbered('数据来源于分级记录与训练评估输出。')

h2('3.8 FR-07 用户与权限')
numbered('管理员：全部功能；查询用户：仅 FR-05 查询与看板公开部分。')
numbered('登录采用轻量会话鉴权（SQLite 存用户，密码加盐哈希）。')

h2('3.9 FR-08 系统配置')
numbered('可配置等级数、置信度阈值、模型权重路径、数据集目录。')

# ============== 4 非功能需求 ==============
h1('4. 非功能需求')
table(['编号','类别','需求'],
      [['NFR-01','性能','单张 CPU 推理 ≤ 2s；溯源校验 1000 条记录 ≤ 1s'],
       ['NFR-02','精度','测试集 mAP@0.5 ≥ 0.85'],
       ['NFR-03','可用性','核心流程（导入→分级→查询）成功率 ≥ 99%'],
       ['NFR-04','安全性','用户密码加盐哈希；溯源链防篡改；接口基础鉴权'],
       ['NFR-05','可维护性','模块化（数据/算法/服务/前端分层）；Git 管理；文档齐全'],
       ['NFR-06','可移植性','纯 Python + 标准库哈希链，无 Docker/外部服务依赖'],
       ['NFR-07','兼容性','现代浏览器（Chrome/Edge）；Windows 本地运行'],
       ['NFR-08','合规','数据集与模型许可合规，可答辩溯源']],
      widths=[0.9,1.2,4.5])

# ============== 5 数据需求 ==============
h1('5. 数据需求')
h2('5.1 数据集')
bullet('来源：主训练集采用公开数据集 TeaLeafAgeQuality（Mendeley Data，DOI 10.17632/7t964jmmy3，CC BY 4.0，4403 张，4 类嫩度 T1-T4），映射 T1→特级/T2→一级/T3→二级/T4→等外；恩施玉露茶为应用品牌，可补充少量自建标注子集；来源与许可写入 data/README。')
bullet('规模目标：训练 ≥ 500 张、验证/测试各 ≥ 100 张（演示规模，可据实际调整）。')
bullet('标注：图像级/框级等级标签；标注工具 LabelImg（仅自建少量样本时）。')
bullet('增强：Albumentations（翻转/调光/加噪）防过拟合。')
h2('5.2 数据实体（逻辑）')
table(['实体','关键字段'],
      [['分级记录','id, 批次号, 图像路径, 等级, 置信度, 模型版本, 时间, 前哈希, 本哈希'],
       ['批次','批次号, 创建时间, 来源, 负责人'],
       ['用户','用户名, 密码哈希, 角色'],
       ['模型版本','版本号, 权重路径, mAP, 训练时间']],
      widths=[1.5,5.0])
h2('5.3 模型与溯源资产')
bullet('模型权重 .pt 文件纳入 Git LFS 或独立备份，打基线 tag。')
bullet('哈希链数据文件随代码版本管理，保证可复现。')

# ============== 6 接口需求 ==============
h1('6. 接口需求')
h2('6.1 后端 API（FastAPI）')
table(['接口','方法','说明'],
      [['/api/grade','POST','上传图像，返回分级结果'],
       ['/api/records','GET','分页查询分级记录（筛选）'],
       ['/api/records/{id}','GET','单条记录详情'],
       ['/api/chain/verify','POST','校验某批次哈希链完整性'],
       ['/api/trace/{batch}','GET','返回批次溯源链'],
       ['/api/stats','GET','看板统计数据'],
       ['/api/auth/login','POST','用户登录']],
      widths=[1.8,0.9,3.8])
h2('6.2 前端界面（Vue）')
bullet('上传页：图像拖拽上传、进度、即时分级结果展示（带框预览）。')
bullet('记录页：分级记录列表/筛选/导出。')
bullet('溯源页：批次号输入 → 溯源链可视化（含完整性标识）。')
bullet('看板页：分级分布、趋势、精度指标图表。')
h2('6.3 外部接口')
bullet('训练：Colab  Notebook 调用本地导出的数据集，训练后回传权重。')
bullet('（无）区块链节点/第三方支付/消息推送等外部依赖 —— 本版不引入。')

# ============== 7 用例 ==============
h1('7. 主要用例')
table(['用例','角色','主流程','预期结果'],
      [['UC-01 批量分级','管理员','导入图像→系统自动分级→查看结果','生成带等级/置信度的记录并上链'],
       ['UC-02 人工校正','管理员','修改某记录等级→保存','校正留痕写入溯源链'],
       ['UC-03 溯源核验','消费者','输入批次号→查看溯源链','显示分级结论与“链完整性：通过”'],
       ['UC-04 篡改检测','管理员','手动改库某记录→点校验','系统报告不一致并定位'],
       ['UC-05 模型迭代','管理员','Colab 训练新权重→更新模型版本','新版本 mAP 记录，旧结果仍可读']],
      widths=[1.3,1.0,2.3,2.0])

# ============== 8 验收标准 ==============
h1('8. 验收标准（M4 端到端）')
bullet('端到端跑通：导入→分级→上链→查询→校验，全流程无人工干预可演示。')
bullet('精度达标：测试集 mAP@0.5 ≥ 0.85（NFR-02）。')
bullet('溯源防篡改：篡改任一记录 100% 被校验检出（FR-04）。')
bullet('性能达标：单张 CPU 推理 ≤ 2s，千条链校验 ≤ 1s（NFR-01）。')
bullet('文档齐全：SRS、设计文档、测试报告、用户手册齐备。')

# ============== 9 待定项 ==============
h1('9. 待定项与假设清单')
table(['待定项','影响','当前占位/默认'],
      [['首选农产品类别','决定数据集与标注体系',SUBJECT],
       ['答辩/中期检查日期','决定甘特日历','答辩 2027-05 中旬（已确认）；中期检查待学校通知'],
       ['数据集具体来源','决定标注与增强策略','主训练集 TeaLeafAgeQuality（Mendeley DOI 10.17632/7t964jmmy3，CC BY 4.0，4403 张，4 类 T1-T4 嫩度分级）；恩施玉露茶为应用品牌；T1→特级/T2→一级/T3→二级/T4→等外'],
       ['学校论文模板/查重阈值','决定文档格式','待用户提供后套用'],
       ['论文字数/章节要求','决定论文结构','按通用本科毕设结构']],
      widths=[1.8,2.6,2.2])
para('说明：首选农产品已于 V1.1 冻结为恩施玉露茶；其余需求条目结构与可追溯性不受影响。', bold=True)

# 页脚页码
section = doc.sections[0]
footer = section.footer
fp = footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run('农产品品质分级与溯源平台 · 软件需求规格说明书 V1.1')
run.font.size = Pt(8); run.font.color.rgb = RGBColor(0x80,0x80,0x80)
# 页码域
p = footer.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run()
fld1 = OxmlElement('w:fldChar'); fld1.set(qn('w:fldCharType'),'begin')
instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'),'preserve'); instr.text='PAGE'
fld2 = OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'),'end')
r._r.append(fld1); r._r.append(instr); r._r.append(fld2)
r.font.size = Pt(8)

out = 'C:/Users/wzd/Desktop/毕业设计/软件需求规格说明书_SRS.docx'
doc.save(out)
print('SRS 已生成:', out)
