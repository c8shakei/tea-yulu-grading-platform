"""一次性修复：从现有 train/val/test 目录重建逐样本 split_manifest.csv 与 split_summary.csv。

排除 _aug1/_aug2 增强文件，仅统计原始样本；类别取自标注文件首行 class_id。
"""
from pathlib import Path
from collections import defaultdict

DS = Path("D:/BISHE_DATA/datasets/tea_yulu")
NAMES = ["特级", "一级", "二级", "等外"]

detail = ["filename,split,class_id,class_name"]
summary_stats = defaultdict(lambda: defaultdict(int))

for split in ["train", "val", "test"]:
    stems = sorted(
        p.stem for p in (DS / split / "images").glob("*") if "_aug" not in p.stem
    )
    for stem in stems:
        lbl = (DS / split / "labels" / f"{stem}.txt").read_text(encoding="utf-8").strip()
        cls = int(float(lbl.split()[0]))
        detail.append(f"{stem},{split},{cls},{NAMES[cls]}")
        summary_stats[split][cls] += 1

(DS / "split_manifest.csv").write_text("\n".join(detail) + "\n", encoding="utf-8")

lines = ["split,class_id,class_name,count"]
for split in ["train", "val", "test"]:
    for cls in sorted(summary_stats[split].keys()):
        lines.append(f"{split},{cls},{NAMES[cls]},{summary_stats[split][cls]}")
(DS / "split_summary.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"split_manifest.csv: {len(detail) - 1} 行（期望 2195）")
print("split_summary.csv:")
print("\n".join(lines))
