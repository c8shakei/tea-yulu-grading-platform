"""
Colab 训练脚本：YOLOv8 分类对照模型（恩施玉露茶等级分类）
============================================================
运行环境：Google Colab GPU
作物/任务：恩施玉露茶品质等级分类（论文对照实验）
类别映射：T1特级(0)、T2一级(1)、T3二级(2)、T4等外(3)

说明：
- 本脚本首先将检测格式数据集（YOLO txt）转换为分类目录结构；
- 然后训练 yolov8n-cls 作为与检测模型的对照实验；
- 最终 best_cls.pt 同步到 Google Drive。
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# 冻结约束
# ---------------------------------------------------------------------------
SEED = 42
PROJECT_NAME = "tea_yulu_cls"
# 骨干规模与检测脚本共用环境变量 YOLO_MODEL_SIZE：yolov8n / yolov8s（分类对应 -cls 后缀）
_DET_SIZE = os.environ.get("YOLO_MODEL_SIZE", "yolov8n")
MODEL_SIZE = f"{_DET_SIZE}-cls"   # yolov8n-cls / yolov8s-cls
EXPERIMENT_NAME = MODEL_SIZE
EPOCHS = 100
IMG_SIZE = 224                  # 分类模型输入尺寸
# 分类 batch 较大；yolov8s-cls 显存上升，自动降为 32，可用 YOLO_BATCH 覆盖
BATCH_SIZE = int(os.environ.get("YOLO_BATCH", 32 if _DET_SIZE == "yolov8s" else 64))
PATIENCE = 20
OPTIMIZER = "AdamW"
LR0 = 1e-3
LRF = 1e-2

# 运行平台可移植
WORK_DIR = Path(os.environ.get("WORK_DIR", "/content"))
SYNC_TARGET = os.environ.get("SYNC_TARGET")
DATA_ROOT = os.environ.get("DATA_ROOT")

COLAB_DATASET_DIR = WORK_DIR / "datasets" / "tea_yulu"
COLAB_CLS_DIR = WORK_DIR / "datasets" / "tea_yulu_cls"
DRIVE_SAVE_DIR = Path("/content/drive/MyDrive/BISHE/models")
LOCAL_ZIP_PATH = WORK_DIR / "tea_yulu_dataset.zip"

CLASS_NAMES = ["特级", "一级", "二级", "等外"]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ["PYTHONHASHSEED"] = str(seed)


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def mount_google_drive() -> Path:
    try:
        from google.colab import drive
    except ImportError:
        raise RuntimeError("未在 Colab 环境运行，无法挂载 Google Drive")
    drive.mount("/content/drive", force_remount=False)
    return Path("/content/drive/MyDrive")


def _normalize_backslash_paths(root: Path) -> None:
    """把 zip 中反斜杠路径名重建为正常目录结构（Windows 压缩工具常见）。"""
    for item in list(root.rglob("*")):
        if item == root or not item.exists():
            continue
        if "\\" in item.name:
            rel = item.relative_to(root)
            new_rel = Path(str(rel).replace("\\", "/"))
            new_path = root / new_rel
            if item.is_dir():
                new_path.mkdir(parents=True, exist_ok=True)
                for child in list(item.iterdir()):
                    target = new_path / child.name
                    if target.exists():
                        shutil.rmtree(target) if target.is_dir() else target.unlink()
                    shutil.move(str(child), str(target))
                item.rmdir()
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if new_path.exists():
                    new_path.unlink()
                shutil.move(str(item), str(new_path))


def _flatten_to_tea_yulu(root: Path) -> Path:
    """如果 zip 没有顶层 tea_yulu/，把文件整理进 /content/datasets/tea_yulu。"""
    if COLAB_DATASET_DIR.exists():
        shutil.rmtree(COLAB_DATASET_DIR)
    COLAB_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for item in list(root.iterdir()):
        if item.resolve() == COLAB_DATASET_DIR.resolve():
            continue
        target = COLAB_DATASET_DIR / item.name
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        shutil.move(str(item), str(target))
    log(f"已整理数据集目录：{root} -> {COLAB_DATASET_DIR}")
    return COLAB_DATASET_DIR


def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """解压数据集 zip，并确保最终得到 /content/datasets/tea_yulu。"""
    extract_to.mkdir(parents=True, exist_ok=True)
    if COLAB_DATASET_DIR.exists():
        shutil.rmtree(COLAB_DATASET_DIR)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    log(f"已解压 {zip_path} -> {extract_to}")

    _normalize_backslash_paths(extract_to)

    if COLAB_DATASET_DIR.exists() and (COLAB_DATASET_DIR / "data.yaml").exists():
        return COLAB_DATASET_DIR

    if (extract_to / "data.yaml").exists():
        return _flatten_to_tea_yulu(extract_to)

    extracted_dirs = [p for p in extract_to.iterdir() if p.is_dir()]
    if len(extracted_dirs) == 1 and (extracted_dirs[0] / "data.yaml").exists():
        extracted_dirs[0].rename(COLAB_DATASET_DIR)
        return COLAB_DATASET_DIR

    raise FileNotFoundError(
        f"解压后未找到有效数据集。期望 {COLAB_DATASET_DIR}/data.yaml，"
        f"请检查 zip 顶层结构。"
    )


def ensure_detect_dataset() -> Path:
    """
    复用检测数据集，优先级：
    1. 已解压目录
    2. Drive 根目录 tea_yulu_dataset.zip
    3. Drive /MyDrive/BISHE_DATA/datasets/tea_yulu 目录
    4. /content/tea_yulu_dataset.zip 本地 zip
    """
    # 平台可移植：DATA_ROOT 直接作为数据集根（Kaggle）
    if DATA_ROOT:
        root = Path(DATA_ROOT)
        if (root / "data.yaml").exists():
            log(f"使用 DATA_ROOT 指定数据集：{root}")
            return root
        log(f"DATA_ROOT 下未找到 data.yaml：{root}")

    if COLAB_DATASET_DIR.exists() and (COLAB_DATASET_DIR / "data.yaml").exists():
        log(f"检测数据集已存在：{COLAB_DATASET_DIR}")
        return COLAB_DATASET_DIR

    # 方案 A：Drive 根目录 zip
    try:
        drive_base = mount_google_drive()
        zip_path = drive_base / "tea_yulu_dataset.zip"
        if zip_path.exists():
            return extract_zip(zip_path, WORK_DIR / "datasets")
    except Exception as exc:
        log(f"方案 A（Drive 根目录 zip）失败：{exc}")

    # 方案 B：Drive 数据集目录
    try:
        drive_base = mount_google_drive()
        src = drive_base / "BISHE_DATA" / "datasets" / "tea_yulu"
        if src.exists():
            if COLAB_DATASET_DIR.exists():
                shutil.rmtree(COLAB_DATASET_DIR)
            shutil.copytree(src, COLAB_DATASET_DIR)
            log(f"已拷贝检测数据集：{src} -> {COLAB_DATASET_DIR}")
            return COLAB_DATASET_DIR
    except Exception as exc:
        log(f"方案 B（Drive 数据集目录）失败：{exc}")

    # 方案 C：本地上传 zip
    if LOCAL_ZIP_PATH.exists():
        return extract_zip(LOCAL_ZIP_PATH, WORK_DIR / "datasets")

    raise FileNotFoundError(
        "未找到可用数据集。请按以下方式之一准备：\n"
        "1. 上传 tea_yulu_dataset.zip 到 Google Drive 根目录（推荐）\n"
        "2. 上传 D:\\BISHE_DATA\\datasets\\tea_yulu 到 Drive /MyDrive/BISHE_DATA/datasets/tea_yulu\n"
        "3. 在 Colab 中上传 zip 到 /content/tea_yulu_dataset.zip"
    )


def read_label(label_path: Path) -> Optional[int]:
    """读取 YOLO 标注文件，返回首个框的 class_id。"""
    if not label_path.exists():
        return None
    with label_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                return int(float(parts[0]))
            except ValueError:
                continue
    return None


def build_cls_dataset(src_dir: Path, dst_dir: Path) -> dict:
    """
    将检测格式数据集转换为分类目录结构。
    源结构：src_dir/{train,val,test}/images 和 labels
    目标结构：dst_dir/{train,val}/{class_name}/image.jpg
    """
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    stats = {"train": 0, "val": 0, "test": 0}
    for split in ["train", "val", "test"]:
        img_dir = src_dir / split / "images"
        lbl_dir = src_dir / split / "labels"
        if not img_dir.exists():
            log(f"警告：{img_dir} 不存在，跳过")
            continue

        for img_path in sorted(img_dir.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                continue
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            cls_id = read_label(lbl_path)
            if cls_id is None or cls_id < 0 or cls_id >= len(CLASS_NAMES):
                log(f"警告：{img_path.name} 无有效标注，跳过")
                continue

            cls_name = CLASS_NAMES[cls_id]
            target_dir = dst_dir / split / cls_name
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / img_path.name

            # 使用 PIL 复制并校验图片可读性
            with Image.open(img_path) as im:
                im.copy().save(target_path)
            stats[split] += 1

    log(f"分类数据集构建完成：{stats}")
    return stats


def save_hyper_params(save_dir: Path) -> Path:
    hyper = {
        "model": f"{MODEL_SIZE}.pt",
        "task": "classify",
        "seed": SEED,
        "epochs": EPOCHS,
        "imgsz": IMG_SIZE,
        "batch": BATCH_SIZE,
        "device": "0",
        "optimizer": OPTIMIZER,
        "lr0": LR0,
        "lrf": LRF,
        "patience": PATIENCE,
        "augment": True,
        "class_names": CLASS_NAMES,
        "class_map": {"特级": 0, "一级": 1, "二级": 2, "等外": 3},
        "created_at": datetime.now().isoformat(),
    }
    hp_path = save_dir / "hyper_params_cls.json"
    hp_path.write_text(json.dumps(hyper, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"分类模型超参已保存：{hp_path}")
    return hp_path


def main() -> int:
    set_seed(SEED)
    log(f"PyTorch 版本：{torch.__version__}；CUDA 可用：{torch.cuda.is_available()}")

    # 1. 准备检测数据集并转换为分类格式
    src_dir = ensure_detect_dataset()
    stats = build_cls_dataset(src_dir, COLAB_CLS_DIR)
    if stats["train"] == 0:
        raise RuntimeError("分类训练集为空，请检查数据集")

    # 2. 创建保存目录（与 Ultralytics 实际保存路径一致：project/name）
    exp_dir = Path(PROJECT_NAME) / EXPERIMENT_NAME
    exp_dir.mkdir(parents=True, exist_ok=True)
    save_hyper_params(exp_dir)

    # 3. 训练分类模型
    log(f"开始训练 {MODEL_SIZE} 分类模型...")
    model = YOLO(f"{MODEL_SIZE}.pt")
    results = model.train(
        data=str(COLAB_CLS_DIR),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=0,
        project=PROJECT_NAME,
        name=EXPERIMENT_NAME,
        exist_ok=True,
        seed=SEED,
        patience=PATIENCE,
        optimizer=OPTIMIZER,
        lr0=LR0,
        lrf=LRF,
        augment=True,
    )
    log(f"分类训练完成，结果目录：{exp_dir}")

    # 4. 评估（使用 val 集）
    best_pt = exp_dir / "weights" / "best.pt"
    if not best_pt.exists():
        raise FileNotFoundError(f"训练未生成 best.pt：{best_pt}")

    val_model = YOLO(str(best_pt))
    metrics = val_model.val(data=str(COLAB_CLS_DIR))

    # 分类指标：Ultralytics 返回 top1 / top5 准确率
    eval_dict = {
        "top1_accuracy": float(metrics.top1),
        "top5_accuracy": float(metrics.top5),
        "created_at": datetime.now().isoformat(),
    }
    eval_path = exp_dir / "val_metrics.json"
    eval_path.write_text(json.dumps(eval_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"分类验证指标：{eval_dict}")

    # 5. 同步产物（文件名带 size 后缀，避免覆盖 yolov8n-cls 基线）
    suffix = MODEL_SIZE  # "yolov8n-cls" 或 "yolov8s-cls"
    if SYNC_TARGET:
        target = Path(SYNC_TARGET)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_pt, target / f"best_cls_{suffix}.pt")
        for base in ["hyper_params_cls.json", "val_metrics.json", "results.csv"]:
            src = exp_dir / base
            if src.exists():
                stem, ext = os.path.splitext(base)
                shutil.copy(src, target / f"{stem}_{suffix}{ext}")
        log(f"分类训练产物已同步到 SYNC_TARGET：{target}")
    else:
        drive_base = mount_google_drive()
        DRIVE_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_pt, DRIVE_SAVE_DIR / f"best_cls_{suffix}.pt")
        for base in ["hyper_params_cls.json", "val_metrics.json", "results.csv"]:
            src = exp_dir / base
            if src.exists():
                stem, ext = os.path.splitext(base)
                shutil.copy(src, DRIVE_SAVE_DIR / f"{stem}_{suffix}{ext}")
        log(f"分类训练产物已同步到 Drive：{DRIVE_SAVE_DIR}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"分类训练脚本异常：{e}")
        raise
