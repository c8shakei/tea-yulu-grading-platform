"""
W1 数据集解压与预处理
======================
从 TeaLeafAgeQuality zip 中提取带 YOLO 标注的子集，映射类别，统一命名，
输出到 all/{images,labels}，供后续划分使用。

类别映射（与接口契约严格一致）:
    T1 / 特级 -> 0
    T2 / 一级 -> 1
    T3 / 二级 -> 2
    T4 / 等外 -> 3
"""

import os
import re
import shutil
import zipfile
from pathlib import Path
from collections import Counter, defaultdict
import logging

# ---------------------------------------------------------------------------
# 可配置项
# ---------------------------------------------------------------------------
ZIP_PATH = Path("D:/BISHE_DATA/raw/TeaLeafAgeQuality.zip")
OUT_ROOT = Path("D:/BISHE_DATA/datasets/tea_yulu")
ALL_DIR = OUT_ROOT / "all"
IMAGES_DIR = ALL_DIR / "images"
LABELS_DIR = ALL_DIR / "labels"

CLASS_MAP = {
    "T1": 0,
    "T2": 1,
    "T3": 2,
    "T4": 3,
    "特级": 0,
    "一级": 1,
    "二级": 2,
    "等外": 3,
}

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)


def is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMG_EXTS


def is_label(name: str) -> bool:
    return Path(name).suffix.lower() == ".txt"


def normalize_basename(name: str) -> str:
    """去掉扩展名，并把文件名中的特殊字符转成下划线。

    注意：保留 Roboflow 哈希后缀（_jpg.rf.<hash>），因为不同子集可能
    共享同一时间戳原名，去掉哈希会导致合并时互相覆盖。
    """
    stem = Path(name).stem
    stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem


def infer_class_from_path(path_parts: list[str]) -> int | None:
    """根据文件路径中的目录名推断类别。"""
    for part in reversed(path_parts):
        upper = part.upper()
        if upper in CLASS_MAP:
            return CLASS_MAP[upper]
        # 尝试提取 T1/T2/T3/T4 子串
        m = re.search(r"T[1-4]", upper)
        if m:
            return CLASS_MAP[m.group(0)]
    return None


def read_yolo_class(label_text: str) -> int | None:
    """读取 YOLO txt 第一行的 class_id。"""
    for line in label_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            return int(float(parts[0]))
        except ValueError:
            continue
    return None


def collect_zip_entries(zip_path: Path):
    """扫描 zip，按目录聚合图像与标注文件。"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        entries = zf.namelist()

    dirs = defaultdict(lambda: {"images": [], "labels": []})
    for e in entries:
        if e.endswith("/"):
            continue
        p = Path(e)
        parent = str(p.parent).replace("\\", "/")
        name = p.name
        if is_image(name):
            dirs[parent]["images"].append(e)
        elif is_label(name):
            dirs[parent]["labels"].append(e)
    return dirs


# 数据集实际结构（2026-09-04 实测）：
#   TeaLeafAgeQuality(Annotated)/{train,valid,test}/{images,labels}   <- 选用（2208 对）
#   TeaLeafAgeQuality(Annotated and Augmented)/...                    <- 弃用（W1 自行增强）
#   TeaLeafAgeQuality(Raw Data)/Category X/...                        <- 无标注，弃用
# 标签 class_id 与 Raw 类别一一对应：0=A(1-2天), 1=B(2-4天), 2=C(4-7天), 3=D(7天+)
# 映射为契约类别：0=特级, 1=一级, 2=二级, 3=等外（id 不变，仅命名映射）
ANNOTATED_PREFIX = "TeaLeafAgeQuality(Annotated)/"


def select_annotated_subset(dirs: dict) -> list[tuple[str, dict]]:
    """
    选择 Annotated（非 Augmented）分支下的所有 images/labels 配对目录
    （train / valid / test 三个子目录），合并后统一重划分。
    """
    # images 与 labels 是同级的兄弟目录（.../train/images 与 .../train/labels），
    # 需要按 split 根目录（.../train）聚合。
    groups = defaultdict(lambda: {"images": [], "labels": []})
    for dname, files in dirs.items():
        norm = dname.replace("\\", "/")
        if ANNOTATED_PREFIX not in norm or "Augmented" in norm:
            continue
        if norm.endswith("/images"):
            groups[norm[: -len("/images")]]["images"].extend(files["images"])
        elif norm.endswith("/labels"):
            groups[norm[: -len("/labels")]]["labels"].extend(files["labels"])

    selected = []
    for root, files in sorted(groups.items()):
        imgs, lbls = files["images"], files["labels"]
        if not imgs or not lbls:
            continue
        img_stems = {normalize_basename(n) for n in imgs}
        lbl_stems = {normalize_basename(n) for n in lbls}
        matched = len(img_stems & lbl_stems)
        if matched < 10:
            continue
        selected.append((root, files))
        logging.info(f"纳入目录: {root} (图像 {len(imgs)}, 标注 {len(lbls)}, 配对 {matched})")

    if not selected:
        raise RuntimeError("未在 zip 中找到 Annotated 标注目录")
    return selected


def process_subset(zf: zipfile.ZipFile, dname: str, files: dict, out_images: Path, out_labels: Path):
    """解压并处理选中的子集，输出到 all/{images,labels}。"""
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels.mkdir(parents=True, exist_ok=True)

    imgs = files["images"]
    lbls = files["labels"]

    # 建立 basename -> full path 映射
    img_by_stem = {normalize_basename(n): n for n in imgs}
    lbl_by_stem = {normalize_basename(n): n for n in lbls}

    stats = Counter()
    skipped = []
    written = 0

    for stem in sorted(set(img_by_stem.keys()) & set(lbl_by_stem.keys())):
        img_zip_path = img_by_stem[stem]
        lbl_zip_path = lbl_by_stem[stem]

        # 读取标注，确定 class_id
        label_text = zf.read(lbl_zip_path).decode("utf-8", errors="ignore")
        label_class = read_yolo_class(label_text)
        path_class = infer_class_from_path(Path(img_zip_path).parts)

        if path_class is not None and label_class is not None and path_class != label_class:
            skipped.append((img_zip_path, f"路径类别 {path_class} 与标注类别 {label_class} 冲突"))
            continue

        final_class = path_class if path_class is not None else label_class
        if final_class is None:
            skipped.append((img_zip_path, "无法推断类别"))
            continue

        # 重写标注文件：把所有 bbox 的 class_id 统一为 final_class
        new_lines = []
        for line in label_text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                skipped.append((img_zip_path, f"YOLO 行格式异常: {line}"))
                break
            try:
                cls, xc, yc, w, h = parts
                new_lines.append(f"{final_class} {xc} {yc} {w} {h}")
            except ValueError:
                skipped.append((img_zip_path, f"YOLO 行解析失败: {line}"))
                break
        else:
            # 没有 break，写入文件
            ext = Path(img_zip_path).suffix.lower()
            out_name = f"{stem}{ext}"
            out_img_path = out_images / out_name
            out_lbl_path = out_labels / f"{stem}.txt"

            with zf.open(img_zip_path) as src, open(out_img_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            out_lbl_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

            stats[final_class] += 1
            written += 1

    logging.info(f"成功写入 {written} 对图像/标注")
    logging.info(f"类别分布: {dict(sorted(stats.items()))}")
    if skipped:
        logging.warning(f"跳过 {len(skipped)} 个样本，前 5 个原因:")
        for path, reason in skipped[:5]:
            logging.warning(f"  {path}: {reason}")

    return written, stats, skipped


def main():
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"zip 文件不存在: {ZIP_PATH}")

    logging.info(f"正在扫描 zip: {ZIP_PATH}")
    dirs = collect_zip_entries(ZIP_PATH)
    logging.info(f"发现 {len(dirs)} 个非空目录")

    selected = select_annotated_subset(dirs)

    total_written = 0
    total_stats = Counter()
    total_skipped = []
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        for dname, files in selected:
            written, stats, skipped = process_subset(zf, dname, files, IMAGES_DIR, LABELS_DIR)
            total_written += written
            total_stats.update(stats)
            total_skipped.extend(skipped)
    stats = total_stats

    logging.info(f"合计写入 {total_written} 对图像/标注")
    logging.info(f"合计类别分布: {dict(sorted(total_stats.items()))}")

    # 写入类别名映射供参考
    names = ["特级", "一级", "二级", "等外"]
    summary_lines = ["class_id,name,count"]
    for cid in sorted(stats.keys()):
        summary_lines.append(f"{cid},{names[cid]},{stats[cid]}")
    (ALL_DIR / "class_distribution.csv").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    logging.info(f"预处理完成，输出目录: {ALL_DIR}")


if __name__ == "__main__":
    main()
