"""
W1 训练集数据增强
==================
仅对 train 集做 Albumentations 几何/光度增强，严格保持标签语义：
- 几何变换会同步更新 bbox 坐标
- 不改变 class_id
- 不增强 val/test

输出：在 train/images、train/labels 中追加增强后的样本。
"""

import os
import random
from pathlib import Path

import cv2
import albumentations as A
from albumentations.core.composition import BboxParams

# ---------------------------------------------------------------------------
# 可配置项
# ---------------------------------------------------------------------------
SEED = 42
AUG_FACTOR = 2              # 每张训练样本生成 2 张增强图（可改）
DATASET_ROOT = Path("D:/BISHE_DATA/datasets/tea_yulu")
NAMES = ["特级", "一级", "二级", "等外"]

# Albumentations 增强管线（仅几何/光度，不改标签语义）
TRANSFORM = A.Compose(
    [
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.RandomRotate90(p=0.3),
        A.ShiftScaleRotate(
            shift_limit=0.05, scale_limit=0.1, rotate_limit=15, p=0.4
        ),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.HueSaturationValue(
            hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=20, p=0.3
        ),
        A.GaussNoise(var_limit=(5.0, 20.0), p=0.2),
        A.GaussianBlur(blur_limit=(3, 5), p=0.2),
    ],
    bbox_params=BboxParams(
        format="yolo",
        label_fields=["class_ids"],
        min_visibility=0.3,
    ),
)
# ---------------------------------------------------------------------------

random.seed(SEED)


def read_yolo_label(label_path: Path):
    """读取 YOLO 标注，返回 (class_ids, bboxes)。"""
    class_ids = []
    bboxes = []
    text = label_path.read_text(encoding="utf-8").strip()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        cls, xc, yc, w, h = parts
        class_ids.append(int(float(cls)))
        bboxes.append([float(xc), float(yc), float(w), float(h)])
    return class_ids, bboxes


def write_yolo_label(label_path: Path, class_ids: list, bboxes: list):
    lines = []
    for cls, box in zip(class_ids, bboxes):
        xc, yc, w, h = box
        lines.append(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
    label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def augment_sample(image_path: Path, label_path: Path, out_index: int):
    """对单个样本做一次增强并写入。"""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    class_ids, bboxes = read_yolo_label(label_path)
    if not bboxes:
        return False

    transformed = TRANSFORM(image=img, bboxes=bboxes, class_ids=class_ids)
    aug_img = transformed["image"]
    aug_bboxes = transformed["bboxes"]
    aug_class_ids = transformed["class_ids"]

    if not aug_bboxes:
        return False

    stem = image_path.stem
    ext = image_path.suffix
    new_name = f"{stem}_aug{out_index}"

    out_img_path = image_path.parent / f"{new_name}{ext}"
    out_lbl_path = label_path.parent / f"{new_name}.txt"

    aug_img_bgr = cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out_img_path), aug_img_bgr)
    write_yolo_label(out_lbl_path, aug_class_ids, aug_bboxes)
    return True


def main():
    train_img_dir = DATASET_ROOT / "train" / "images"
    train_lbl_dir = DATASET_ROOT / "train" / "labels"

    if not train_img_dir.exists():
        raise FileNotFoundError(
            f"请先运行 w1_split_dataset.py 生成 {train_img_dir}"
        )

    image_paths = sorted(train_img_dir.iterdir())
    original_count = len(image_paths)
    generated = 0
    skipped = 0

    for img_path in image_paths:
        # 只处理原始图像，跳过已生成的增强图
        if "_aug" in img_path.stem:
            continue
        lbl_path = train_lbl_dir / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            skipped += 1
            continue

        for i in range(1, AUG_FACTOR + 1):
            try:
                if augment_sample(img_path, lbl_path, i):
                    generated += 1
            except Exception as e:
                print(f"[跳过] {img_path.name}: {e}")
                skipped += 1

    print("=" * 50)
    print(f"原始训练样本: {original_count}")
    print(f"新增增强样本: {generated}")
    print(f"跳过/失败: {skipped}")
    print(f"增强后训练集总量: {original_count + generated}")
    print("=" * 50)


if __name__ == "__main__":
    main()
