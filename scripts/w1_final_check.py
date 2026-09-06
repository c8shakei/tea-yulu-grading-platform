"""W1 交付物终检脚本：存在性 / junction / 契约符合性 / 配对 / 标注合法性 / 清单行数。"""
from pathlib import Path
import collections
import csv
import yaml

ROOT = Path("C:/Users/wzd/Desktop/毕业设计")
DS = ROOT / "datasets" / "tea_yulu"


def ok(b):
    return "PASS" if b else "FAIL"


print("========== W1 终检 ==========")

# 1. 交付物存在性
checks = {
    "data.yaml(项目根)": ROOT / "data.yaml",
    "数据说明.md": ROOT / "数据说明.md",
    ".gitignore": ROOT / ".gitignore",
    "scripts/w1_download_dataset.py": ROOT / "scripts/w1_download_dataset.py",
    "scripts/w1_extract_prepare.py": ROOT / "scripts/w1_extract_prepare.py",
    "scripts/w1_split_dataset.py": ROOT / "scripts/w1_split_dataset.py",
    "scripts/w1_augment.py": ROOT / "scripts/w1_augment.py",
    "scripts/setup_data_link.bat": ROOT / "scripts/setup_data_link.bat",
    "datasets/tea_yulu/data.yaml(便携)": DS / "data.yaml",
    "split_manifest.csv": DS / "split_manifest.csv",
    "split_summary.csv": DS / "split_summary.csv",
    "class_distribution.csv": DS / "class_distribution.csv",
}
all_pass = True
for k, p in checks.items():
    all_pass &= p.exists()
    print(f"[{ok(p.exists())}] {k}")

# 2. junction 可用性
j = DS / "train" / "images"
print(f"[{ok(j.exists())}] junction 可达: {j.resolve()}")

# 3. data.yaml 契约符合性
d = yaml.safe_load(open(ROOT / "data.yaml", encoding="utf-8"))
contract = d["nc"] == 4 and d["names"] == ["特级", "一级", "二级", "等外"] and d["path"] == "datasets/tea_yulu"
print(f"[{ok(contract)}] data.yaml 契约1 (nc=4, names, path=datasets/tea_yulu)")
d2 = yaml.safe_load(open(DS / "data.yaml", encoding="utf-8"))
portable = d2["path"] == "." and "D:" not in str(d2)
print(f"[{ok(portable)}] 便携 data.yaml 无盘符绝对路径 (path=.)")

# 4. 数据规模与配对
total = 0
for split in ["train", "val", "test"]:
    imgs = {p.stem for p in (DS / split / "images").glob("*")}
    lbls = {p.stem for p in (DS / split / "labels").glob("*.txt")}
    pair_ok = imgs == lbls
    total += len(imgs)
    print(f"[{ok(pair_ok)}] {split}: 图像 {len(imgs)} = 标注 {len(lbls)}")
print(f"       总样本(含增强): {total}")

# 5. 标注合法性 + 类别分布
dist = collections.Counter()
bad = 0
empty_files = 0
for split in ["train", "val", "test"]:
    for lp in (DS / split / "labels").glob("*.txt"):
        txt = lp.read_text(encoding="utf-8").strip()
        if not txt:
            empty_files += 1
            continue
        for line in txt.splitlines():
            p = line.split()
            if len(p) != 5:
                bad += 1
                continue
            cid = int(float(p[0]))
            vals = [float(x) for x in p[1:]]
            if cid not in (0, 1, 2, 3) or not all(0 <= v <= 1 for v in vals):
                bad += 1
            dist[cid] += 1
print(f"[{ok(bad == 0)}] 标注合法性: 异常行 {bad}, 空标注文件 {empty_files}")
print(f"       bbox 类别分布(全量): {dict(sorted(dist.items()))}")

# 6. manifest 行数
rows = list(csv.reader(open(DS / "split_manifest.csv", encoding="utf-8")))
print(f"[{ok(len(rows) - 1 == 2195)}] split_manifest 原始样本行数: {len(rows) - 1} (期望 2195)")

print("========== 终检结束 ==========")
