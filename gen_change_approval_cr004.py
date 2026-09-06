# -*- coding: utf-8 -*-
"""生成 CR-W1-004 变更申请与批复书 docx"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from datetime import datetime

WS = r"C:\Users\wzd\Desktop\毕业设计"
APPLY_OUT = WS + r"\变更申请_CR-W1-004_增加用户认证多页面与低代码配置层.docx"
APPROVE_OUT = WS + r"\变更批复书_CR-W1-004.docx"


def set_font(doc):
    style = doc.styles['Normal']
    style.font.name = 'Microsoft YaHei'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    style.font.size = Pt(10.5)


def add_title(doc, text):
    t = doc.add_heading(text, level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_table_kv(doc, rows):
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Light Grid Accent 1'
    table.rows[0].cells[0].text = '字段'
    table.rows[0].cells[1].text = '内容'
    for k, v in rows:
        row = table.add_row().cells
        row[0].text = k
        row[1].text = v
    doc.add_paragraph()


def build_apply():
    doc = Document()
    set_font(doc)
    add_title(doc, '变更申请单')

    info = [
        ('变更编号', 'CR-W1-004'),
        ('项目名称', '基于计算机视觉的农产品品质分级与溯源平台'),
        ('申请人', 'W4（前端工程师）'),
        ('关联里程碑', 'M3（后端可用）· M4（前端联调）'),
        ('申请日期', '2026-09-05'),
        ('变更类型', '范围扩展 / 功能增强'),
    ]
    add_table_kv(doc, info)

    doc.add_heading('一、变更内容', level=2)
    content = [
        '在前端现有单页检测工作台基础上，扩展为完整的多页面 Web 网站。',
        '新增用户认证模块：注册、登录、登出、当前用户查询、个人中心。',
        '新增页面：首页 / 检测工作台 / 历史记录 / 溯源验证 / 个人中心 / 低代码演示页。',
        '新增后端接口：/api/auth/*、/api/detections、/api/ui/schema，支撑认证、历史记录与低代码配置。',
        '引入内生式低代码配置层（C 方案）：后端维护 ui_schema.json，前端通过 GET /api/ui/schema 动态渲染导航和部分页面；/admin/schema 页提供 JSON 编辑器实时演示“改配置即改页面”。',
    ]
    for c in content:
        doc.add_paragraph(c, style='List Number')

    doc.add_heading('二、变更原因', level=2)
    reasons = [
        '当前设计为单页检测工具，页面过于简单，答辩演示时难以体现完整系统能力。',
        '增加登录注册、历史记录、个人中心后，平台更像完整产品，便于答辩现场讲述“用户体系 + 检测 + 溯源”的闭环故事。',
        '引入低代码配置层可作为论文创新点之一：展示系统不仅完成了业务功能，还具备可配置、可扩展能力。',
        'W1 数据工程与 W2 视觉模型已冻结，本次变更仅影响 W3/W4/W5，风险可控。',
    ]
    for r in reasons:
        doc.add_paragraph(r, style='List Bullet')

    doc.add_heading('三、影响范围分析', level=2)
    impact = [
        ('W1 数据工程', '无影响。数据集、data.yaml、划分脚本均不涉及前端。'),
        ('W2 视觉模型', '无影响。detect() 接口契约②字段不变，仅 detections 表可选增加 user_id 字段用于历史记录关联。'),
        ('W3 后端与溯源', '中等影响。需新增 users 表、认证接口、/api/detections、/api/ui/schema；detections 表扩展 user_id 外键。'),
        ('W4 前端', '较大影响。由单页升级为 Vue Router 多页；新增 SchemaRender 引擎、登录/注册/历史/溯源/个人中心/低代码演示页。'),
        ('W5 测试与集成', '中等影响。需补充认证流程、历史记录隔离、UI Schema、低代码演示页的测试用例。'),
        ('接口契约', '需更新契约③，增加 /api/auth/*、/api/detections、/api/ui/schema。'),
        ('工期', '预计增加 2 天左右，仍在 30 天硬基线内。'),
    ]
    add_table_kv(doc, impact)

    doc.add_heading('四、建议方案', level=2)
    doc.add_paragraph('采用 C 方案：内生式 JSON Schema 配置层。')
    plan = [
        '后端：新增 ui_schema.json 静态配置文件，通过 GET /api/ui/schema 返回 {appName, nav, pages}。',
        '后端：新增 SQLite users 表与 JWT 认证；/api/detections 按当前用户过滤；detect 接口匿名可用但登录后记录 user_id。',
        '前端：使用 Vue Router 实现 /login、/register、/、/detect、/history、/trace、/profile、/admin/schema。',
        '前端：SchemaRender 引擎读取 /api/ui/schema，动态生成导航菜单和页面渲染；/admin/schema 页内置 JSON 编辑器，修改后刷新即可实时更新导航与页面。',
        'W5：增加注册→登录→检测→上链→历史→验证哈希链的端到端测试。',
    ]
    for p in plan:
        doc.add_paragraph(p, style='List Number')

    doc.add_heading('五、工期与风险', level=2)
    doc.add_paragraph('预计增加工作量：W3 +0.5~1 天，W4 +1~1.5 天，W5 +0.5 天，合计约 2 天。')
    doc.add_paragraph('主要风险：')
    for r in [
        'Vue Router 与 SchemaRender 引擎设计不当会导致页面难以维护——需先定 schema 结构再写渲染器。',
        'JWT secret 如使用默认值，答辩时存在被质疑安全性的风险——需在文档中明确“本地演示默认密钥，生产需替换”。',
    ]:
        doc.add_paragraph(r, style='List Bullet')

    doc.add_heading('六、待组长决策项', level=2)
    doc.add_paragraph('1. 是否批准本次范围扩展？')
    doc.add_paragraph('2. 认证方式采用 JWT（无状态）还是 Session（有状态）？建议 JWT。')
    doc.add_paragraph('3. 检测接口是否允许匿名使用？建议允许匿名，但历史记录必须登录后查看。')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p = doc.add_paragraph('申请人签字：_______________')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p = doc.add_paragraph(f'日期：2026-09-05')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(APPLY_OUT)
    print(f"Saved apply: {APPLY_OUT}")


def build_approve():
    doc = Document()
    set_font(doc)
    add_title(doc, '变更批复书')

    info = [
        ('变更编号', 'CR-W1-004'),
        ('项目名称', '基于计算机视觉的农产品品质分级与溯源平台'),
        ('申请人', 'W4（前端工程师）'),
        ('关联里程碑', 'M3（后端可用）· M4（前端联调）'),
        ('申请日期', '2026-09-05'),
        ('批复日期', '2026-09-05'),
        ('批复人', '组长'),
    ]
    add_table_kv(doc, info)

    doc.add_heading('一、变更内容摘要', level=2)
    content = [
        '前端由单页检测工作台扩展为完整多页面网站，新增登录/注册/个人中心/历史记录/低代码演示页。',
        '后端新增用户认证模块（JWT）、/api/detections 历史接口、/api/ui/schema 低代码配置接口。',
        '采用 C 方案：内生式 JSON Schema 配置层，后端维护 ui_schema.json，前端 SchemaRender 引擎动态渲染导航与页面。',
        'W1/W2 工作域不受影响；接口契约②保持不变；接口契约③扩展新增认证/历史/UI Schema 接口。',
    ]
    for c in content:
        doc.add_paragraph(c, style='List Number')

    doc.add_heading('二、批复结论', level=2)
    doc.add_paragraph('同意方案 C：内生式 JSON Schema 配置层 + JWT 认证 + Vue Router 多页面。')
    doc.add_paragraph('附加说明：本次变更申请人字段填写为 W4，实际涉及 W3 后端、W4 前端、W5 测试三个工作域；以文件编号 CR-W1-004 为准，相关提示词与契约已由组长同步更新。')

    doc.add_heading('三、关键决策', level=2)
    doc.add_paragraph('① 认证方式：')
    doc.add_paragraph('采用 JWT（无状态 token）。token 由后端签发，前端存 localStorage，请求时通过 Authorization: Bearer 头部携带。')
    doc.add_paragraph('② 检测接口匿名策略：')
    doc.add_paragraph('允许匿名检测（便于答辩现场快速演示），但历史记录 /api/detections 必须登录后才能查看；登录后的检测记录须关联 user_id。')
    doc.add_paragraph('③ 低代码配置层范围：')
    doc.add_paragraph('第一阶段仅用于导航生成和部分页面渲染（如历史列表、溯源验证表单）。检测工作台 /detect 因涉及图像上传与可视化，仍用专用页面实现，不由 schema 完全驱动。/admin/schema 页提供 JSON 编辑器用于答辩演示。')
    doc.add_paragraph('④ W1/W2 边界：')
    doc.add_paragraph('W1 数据工程、W2 视觉模型不受影响；接口契约② detect() 字段保持不变。')

    doc.add_heading('四、生效范围与后续动作', level=2)
    actions = [
        '组长已同步更新接口契约③、W3/W4/W5 提示词、派工指导手册，新文件已覆盖旧版。',
        'W3 在 M3 实现中补充 users 表、JWT 认证、/api/detections、/api/ui/schema，并更新数据库说明文档。',
        'W4 在 M4 实现 Vue Router 多页面、SchemaRender 引擎、登录/注册/历史/溯源/个人中心/低代码演示页。',
        'W5 补充认证流程、历史记录隔离、UI Schema、低代码演示的测试用例与端到端脚本。',
        '本次变更预计增加 2 天工作量，组长已在里程碑跟踪中预留缓冲；若实际超支，由责任方提前上报。',
    ]
    for a in actions:
        doc.add_paragraph(a, style='List Number')

    doc.add_heading('五、风险与约束', level=2)
    risks = [
        'JWT secret 默认仅用于本地演示，生产环境必须替换；W3 须在 README/文档中醒目标注。',
        'SchemaRender 引擎需在开发早期定好 schema 结构，避免后期 W3/W4 对字段理解不一致。',
        '历史记录按用户过滤必须在后端实现，禁止前端仅做展示层过滤，防止数据越权。',
        '低代码演示页 /admin/schema 允许修改本地内存中的 schema 并重新渲染，但不要直接写后端 ui_schema.json 文件，避免并发/持久化风险。',
    ]
    for r in risks:
        doc.add_paragraph(r, style='List Bullet')

    doc.add_heading('六、M3/M4 验收口径补充', level=2)
    checks = [
        'M3 后端：/api/auth/register、/api/auth/login、/api/auth/me、/api/auth/logout 可正常返回；/api/detections 按用户过滤；/api/ui/schema 返回有效 JSON。',
        'M4 前端：所有路由页面可正常访问；未登录访问 /history 自动跳转 /login；登录后 token 自动附加到后续请求。',
        'M4 前端：/admin/schema 页修改 schema 后，导航和部分页面能实时更新。',
        'M5 集成：注册→登录→检测→上链→历史→验证哈希链 全链路可一键跑通。',
    ]
    for c in checks:
        doc.add_paragraph(c, style='List Number')

    doc.add_paragraph()
    p = doc.add_paragraph('批复人签字：_______________')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p = doc.add_paragraph('日期：2026-09-05')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(APPROVE_OUT)
    print(f"Saved approve: {APPROVE_OUT}")


if __name__ == '__main__':
    build_apply()
    build_approve()
