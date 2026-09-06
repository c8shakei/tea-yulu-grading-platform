import subprocess, os, shutil, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ---------- 探测工具版本/路径 ----------
def run(cmd):
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
    except Exception as e:
        return f"探测失败: {e}"

def find_path(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    return "未找到"

def modver(name):
    try:
        import importlib
        m = importlib.import_module(name)
        return getattr(m, "__version__", "已安装")
    except Exception:
        return "未安装/安装中"

rows = []

# 项目管理/文档
rows.append(["WorkBuddy（AI 编程代理）", "本项目全程由 AI 代理写代码，你只下指令+验收", "必需", "已具备", "当前会话", "桌面应用", "本机已装", "即当前使用的 AI 工具"])
rows.append(["项目根目录", "所有代码/文档/数据集存放位置", "必需", "已具备", "-", "C:/Users/wzd/Desktop/毕业设计", "无需安装", "毕业设计主文件夹"])

# Python
py_m = "C:/Users/wzd/.workbuddy/binaries/python/versions/3.13.12/python.exe"
py_s = "C:/Users/wzd/AppData/Local/Microsoft/WindowsApps/python.exe"
rows.append(["Python（托管 3.13）", "运行 python-docx / 数据处理 / 文档生成脚本", "必需", "已安装", run(f'"{py_m}" --version'), py_m, "已装", "WorkBuddy 自带托管运行时"])
rows.append(["Python（系统 3.11）", "备用；部分训练脚本兼容 3.11", "可选", "已安装", run(f'"{py_s}" --version'), py_s, "已装", "系统自带"])
rows.append(["Python 虚拟环境 venv", "隔离项目依赖（python-docx/openpyxl 已装）", "必需", "已具备", "-", "C:/Users/wzd/.workbuddy/binaries/python/envs/default", "已创建", "pip 装包均在此环境"])

# Node / 前端
node_m = "C:/Users/wzd/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
rows.append(["Node.js（托管 22）", "Vue 前端开发运行时", "必需", "已安装", run(f'"{node_m}" --version'), node_m, "已装", "Vue 项目构建依赖"])
rows.append(["npm", "安装前端依赖包", "必需", "已安装", run("npm --version"), "随 Node 自带", "已装", ""])

# Git
rows.append(["Git", "代码版本管理、打基线 tag", "必需", "已安装", run("git --version"), find_path(["C:/Users/wzd/.workbuddy/binaries/PortableGit/versions/1.2.0/bin/git.exe", "C:/Program Files/Git/bin/git.exe"]), "已装", ""])

# Go（链码）—— 已改用哈希链，Go 不再必需
go_exe = "C:/Users/wzd/go/bin/go.exe"
go_ver = run(f'"{go_exe}" version') if os.path.exists(go_exe) else "未安装/下载中"
go_status = "已安装" if os.path.exists(go_exe) else "安装中"
rows.append(["Go", "原定写 Fabric 链码；改用哈希链后不再必需", "可选", go_status, go_ver, go_exe, "便携包解压至 C:/Users/wzd/go", "溯源层已改为哈希链，Go 暂不需要，保留无害"])

# 深度学习训练栈（本地为 CPU 版；GPU 训练走 Colab）
torch_ver = modver("torch")
torchvision_ver = modver("torchvision")
ultra_ver = modver("ultralytics")
opencv_ver = modver("cv2")
alb_ver = modver("albumentations")
rows.append(["PyTorch", "YOLOv8 底层框架（当前为 CPU 版）", "必需", "已安装", torch_ver, "venv 内", "pip install torch", "本机网络无法下载 CUDA 版轮子，本地为 CPU 推理/轻量训练；GPU 训练走 Colab"])
rows.append(["torchvision", "图像变换/数据预处理", "必需", "已安装", torchvision_ver, "venv 内", "随 torch 安装", ""])
rows.append(["Ultralytics YOLOv8", "目标检测/分级模型训练与推理", "必需", "已安装", ultra_ver, "venv 内", "pip install ultralytics", ""])
rows.append(["OpenCV / Albumentations", "图像读取与数据增强（数据工程）", "必需", "已安装", f"cv2 {opencv_ver} / albu {alb_ver}", "venv 内", "pip install opencv-python-headless albumentations", ""])
rows.append(["哈希链溯源模块", "用 hashlib 实现不可篡改溯源，替代 Fabric", "必需", "待开发", "-", "Python 标准库", "无需安装", "去除 Docker/Fabric 依赖，环境零风险，30天工期最稳"])

# Docker（已不再需要）
rows.append(["Docker Desktop", "原定运行 Fabric；改用哈希链后不再需要", "不再需要", "已弃用", "未安装", "-", "无需安装", "溯源层已改为哈希链，去除 Docker 依赖"])
rows.append(["Docker Compose", "原定编排 Fabric 网络；已不再需要", "不再需要", "已弃用", "未安装", "-", "无需安装", ""])

# VS Code
vscode = find_path(["C:/Users/wzd/AppData/Local/Programs/Microsoft VS Code/Code.exe"])
rows.append(["VS Code", "代码编辑器（可选，AI 代理也可直接改）", "可选", "已安装" if vscode != "未找到" else "缺失", "present" if vscode != "未找到" else "-", vscode, "已装", ""])

# CUDA / GPU
cuda_ver = run("nvidia-smi --version")
rows.append(["NVIDIA 显卡驱动", "本机独显驱动（存在，但 CUDA 版 torch 受网络限制无法安装）", "可选", "已具备", cuda_ver, "系统驱动", "已装", "有独显；奈何本地无法装 CUDA 版 torch，GPU 训练改用 Colab"])
rows.append(["CUDA 版 PyTorch", "本地 GPU 训练加速（当前网络不可达，暂用 CPU 版）", "可选", "网络受限", "不可用", "需官方 cu124 轮子", "本机到 download.pytorch.org 仅 ~12 B/s", "已验证：官方源被掐速、国内镜像无 cu124 cp313 轮子；故本地用 CPU torch，GPU 训练走 Colab"])

# 云端
rows.append(["Google Colab（云端）", "免费 GPU 训练 YOLOv8（GPU 训练实际走这里）", "必需", "云端可用", "-", "https://colab.research.google.com", "浏览器登录即可", "本地 GPU 受限后的实际 GPU 训练方式"])
rows.append(["GitHub / Gitee", "远程代码仓库", "必需", "需账号", "-", "https://github.com", "注册账号", "用于代码备份与协作"])

# 文档库
rows.append(["python-docx", "生成 Word 文档（开题/章程等）", "必需", "已安装", "1.2.0", "venv 内", "pip install python-docx", ""])
rows.append(["openpyxl", "生成 Excel（本配置清单）", "必需", "已安装", "3.1.5", "venv 内", "pip install openpyxl", ""])

# ---------- 写 Excel ----------
wb = Workbook()
ws = wb.active
ws.title = "环境配置清单"

headers = ["序号", "工具 / 组件", "在本项目中的用途", "是否必需", "状态", "版本", "安装 / 可执行路径", "安装命令或获取方式", "备注 / 注意事项"]
ws.append(headers)

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(bold=True, color="FFFFFF", size=11)
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

for c in range(1, len(headers)+1):
    cell = ws.cell(row=1, column=c)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
    cell.border = border

status_fill = {
    "已安装": "C6EFCE", "已具备": "C6EFCE", "已装": "C6EFCE", "云端可用": "C6EFCE",
    "缺失-需手动": "FFC7CE", "待配置": "FFEB9C", "安装中": "FFEB9C", "需账号": "FFEB9C",
    "网络受限": "FFEB9C",
}
for i, r in enumerate(rows, start=1):
    ws.append([i] + r)
    excel_row = i + 1
    for c in range(1, len(headers)+1):
        cell = ws.cell(row=excel_row, column=c)
        cell.border = border
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    st = r[3]
    if st in status_fill:
        ws.cell(row=excel_row, column=5).fill = PatternFill("solid", fgColor=status_fill[st])

widths = [6, 22, 34, 10, 14, 16, 40, 30, 34]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[chr(64+i) if i<=26 else "A"].width = w
ws.freeze_panes = "A2"

# 第二页：技术栈调整说明
ws2 = wb.create_sheet("技术栈调整说明")
ws2.append(["决策点", "原方案", "新方案", "影响 / 说明"])
for c in range(1,5):
    cell = ws2.cell(row=1, column=c); cell.fill = header_fill; cell.font = header_font; cell.border = border
notes = [
    ["溯源层", "Hyperledger Fabric + Docker + Go 链码", "Python 哈希链（hashlib 不可篡改日志）", "去除 Docker/WSL2/管理员/重启依赖，环境零风险；创新点“分级-溯源一体化存证”仍成立；Go 不再必需"],
    ["训练方式", "Colab 免费 GPU（云端）", "本地 NVIDIA GPU 训练（PyTorch CUDA）", "实测：本机到 PyTorch 官方源被掐至 ~12 B/s、国内镜像无 cu124 cp313 轮子，CUDA 版 torch 无法安装；故本地用 CPU torch 跑推理/轻量训练，GPU 训练回退 Colab（仍有免费 GPU）"],
    ["Docker", "必需", "已弃用", "当前沙箱 wsl 被安全策略拦截，无法静默安装；改用哈希链后彻底无需"],
    ["Go", "链码必需", "可选/暂不需要", "已安装无害；后续若想升级为真实 Fabric 再启用"],
    ["工期影响", "Docker 安装+WSL2 可能卡 1-2 天", "无此风险", "30 天基线更稳，P1 阶段不再被环境阻塞"],
]
for s in notes:
    ws2.append(s)
    for c in range(1,5):
        ws2.cell(row=ws2.max_row, column=c).border = border
        ws2.cell(row=ws2.max_row, column=c).alignment = Alignment(vertical="center", wrap_text=True)
ws2.column_dimensions["A"].width = 12
ws2.column_dimensions["B"].width = 34
ws2.column_dimensions["C"].width = 34
ws2.column_dimensions["D"].width = 52
ws2.freeze_panes = "A2"

out = "C:/Users/wzd/Desktop/毕业设计/环境配置清单.xlsx"
wb.save(out)
print("Excel 已生成:", out)
print("共", len(rows), "项工具配置 + Docker 手动步骤页")
print("Go 状态:", go_status, "| 版本:", go_ver)
