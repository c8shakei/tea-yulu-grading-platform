"""
W1 数据集划分
==============
将 all/{images,labels} 按 7:2:1 分层划分为 train/val/test，固定随机种子保证可复现。
同时生成 YOLO 格式 data.yaml。
"""

import os
import random
import shutil
from pathlib import Path
from collections import defaultdict
import yaml

# ---------------------------------------------------------------------------
# 可配置项
# ---------------------------------------------------------------------------
SEED = 42
SPLIT_RATIOS = {"train": 0.7, "val": 0.2, "test": 0.1}

DATASET_ROOT = Path("D:/BISHE_DATA/datasets/tea_yulu")
ALL_IMAGES = DATASET_ROOT / "all" / "images"
ALL_LABELS = DATASET_ROOT / "all" / "labels"

NAMES = ["特级", "一级", "二级", "等外"]
# ---------------------------------------------------------------------------


def read_class_id(label_path: Path) -> int:
    """读取标注文件中第一个 bbox 的 class_id。"""
    text = label_path.read_text(encoding="utf-8").strip()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if parts:
            return int(float(parts[0]))
    raise ValueError(f"空标注文件: {label_path}")


def collect_samples():
    """收集所有成对样本，按 class_id 分组。"""
    samples_by_class = defaultdict(list)
    for img_path in sorted(ALL_IMAGES.iterdir()):
        stem = img_path.stem
        lbl_path = ALL_LABELS / f"{stem}.txt"
        if not lbl_path.exists():
            print(f"[跳过] 无标注: {img_path.name}")
            continue
        try:
            cls = read_class_id(lbl_path)
        except Exception as e:
            print(f"[跳过] {e}")
            continue
        samples_by_class[cls].append(stem)
    return samples_by_class


def stratified_split(samples_by_class: dict, ratios: dict, seed: int):
    """对每个类别分别按比例随机划分。"""
    random.seed(seed)
    splits = defaultdict(list)
    split_stats = defaultdict(lambda: defaultdict(int))

    for cls, stems in sorted(samples_by_class.items()):
        stems = stems.copy()
        random.shuffle(stems)
        n = len(stems)
        n_train = int(round(n * ratios["train"]))
        n_val = int(round(n * ratios["val"]))
        # 避免舍入导致为空
        if n_train == 0 and n > 0:
            n_train = 1
        if n_val == 0 and n > 1:
            n_val = 1
        # 保证三个集合不越界
        n_train = min(n_train, n - 2)
        n_val = min(n_val, n - n_train - 1)

        train_stems = stems[:n_train]
        val_stems = stems[n_train : n_train + n_val]
        test_stems = stems[n_train + n_val :]

        for split_name, split_stems in [("train", train_stems), ("val", val_stems), ("test", test_stems)]:
            for stem in split_stems:
                splits[split_name].append((stem, cls))
                split_stats[split_name][cls] += 1

    return dict(splits), split_stats


def copy_samples(splits: dict):
    """将样本复制到对应 split 目录。"""
    for split_name, items in splits.items():
        img_out = DATASET_ROOT / split_name / "images"
        lbl_out = DATASET_ROOT / split_name / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for stem, _ in items:
            src_img = ALL_IMAGES / f"{stem}.jpg"
            if not src_img.exists():
                src_img = ALL_IMAGES / f"{stem}.jpeg"
            if not src_img.exists():
                src_img = ALL_IMAGES / f"{stem}.png"
            if not src_img.exists():
                # 查找任意扩展名
                candidates = list(ALL_IMAGES.glob(f"{stem}.*"))
                if not candidates:
                    raise FileNotFoundError(f"找不到图像: {stem}")
                src_img = candidates[0]

            src_lbl = ALL_LABELS / f"{stem}.txt"
            shutil.copy2(src_img, img_out / src_img.name)
            shutil.copy2(src_lbl, lbl_out / f"{stem}.txt")

        print(f"[{split_name}] 已复制 {len(items)} 个样本")


def write_data_yaml():
    """
    按接口契约①生成 data.yaml，path 必须使用相对路径（禁止盘符绝对路径）。
    生成两份：
      1) scripts/data.yaml —— 项目内主文件，path 指向 ../datasets/tea_yulu
      2) D:/BISHE_DATA/datasets/tea_yulu/data.yaml —— 数据集便携副本，path 为 .
    """
    # 1. 项目内主文件（供本地 / Colab 从仓库根目录运行时使用 data=scripts/data.yaml）
    repo_root = Path(__file__).resolve().parent.parent
    project_yaml = repo_root / "scripts" / "data.yaml"
    project_yaml.parent.mkdir(parents=True, exist_ok=True)
    data_project = {
        "path": "../datasets/tea_yulu",
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": 4,
        "names": NAMES,
    }
    with open(project_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(data_project, f, sort_keys=False, allow_unicode=True)
    print(f"data.yaml 已生成: {project_yaml}")

    # 2. 数据集目录内的便携副本（path 为 .，上传到哪都能用）
    dataset_yaml = DATASET_ROOT / "data.yaml"
    data_dataset = {
        "path": ".",
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": 4,
        "names": NAMES,
    }
    with open(dataset_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(data_dataset, f, sort_keys=False, allow_unicode=True)
    print(f"data.yaml 便携副本已生成: {dataset_yaml}")


def write_manifest(splits: dict, split_stats: dict):
    """生成逐样本划分清单（split_manifest.csv）与汇总统计（split_summary.csv）。"""
    # 逐样本清单：一行一个原始样本，可审计、可复现
    detail = ["filename,split,class_id,class_name"]
    for split_name in ["train", "val", "test"]:
        for stem, cls in sorted(splits.get(split_name, [])):
            detail.append(f"{stem},{split_name},{cls},{NAMES[cls]}")
    out_path = DATASET_ROOT / "split_manifest.csv"
    out_path.write_text("\n".join(detail) + "\n", encoding="utf-8")
    print(f"逐样本划分清单已生成: {out_path} ({len(detail) - 1} 行)")

    # 汇总统计：split x class 数量
    lines = ["split,class_id,class_name,count"]
    for split_name in ["train", "val", "test"]:
        stats = split_stats.get(split_name, {})
        for cls in sorted(stats.keys()):
            lines.append(f"{split_name},{cls},{NAMES[cls]},{stats[cls]}")
    sum_path = DATASET_ROOT / "split_summary.csv"
    sum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"汇总统计已生成: {sum_path}")


def main():
    if not ALL_IMAGES.exists() or not ALL_LABELS.exists():
        raise FileNotFoundError(
            f"请先运行 w1_extract_prepare.py 生成 {ALL_IMAGES} 与 {ALL_LABELS}"
        )

    samples_by_class = collect_samples()
    print("=" * 50)
    print("原始类别分布:")
    for cls in sorted(samples_by_class.keys()):
        print(f"  {cls}={NAMES[cls]}: {len(samples_by_class[cls])}")

    splits, split_stats = stratified_split(samples_by_class, SPLIT_RATIOS, SEED)

    print("=" * 50)
    print("划分后分布:")
    for split_name in ["train", "val", "test"]:
        stats = split_stats.get(split_name, {})
        total = sum(stats.values())
        print(f"  {split_name}: 总计 {total}")
        for cls in sorted(stats.keys()):
            print(f"    {cls}={NAMES[cls]}: {stats[cls]}")

    copy_samples(splits)
    write_data_yaml()
    write_manifest(splits, split_stats)

    print("=" * 50)
    print("数据集划分完成")


if __name__ == "__main__":
    main()
