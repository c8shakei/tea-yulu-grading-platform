"""
Colab 训练脚本：YOLOv8 检测模型（恩施玉露茶等级检测）
=====================================================
运行环境：Google Colab GPU (T4 / A100)
作物/任务：恩施玉露茶品质等级检测
类别映射：T1特级(0)、T2一级(1)、T3二级(2)、T4等外(3)

使用方式：
1. 上传本文件到 Colab /content 目录
2. 执行：%run train_detect.py
3. 训练完成后，best_detect.pt 会自动同步到 Google Drive
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# 冻结约束（修改需走变更申请）
# ---------------------------------------------------------------------------
SEED = 42
PROJECT_NAME = "tea_yulu_detect"
# 骨干规模通过环境变量 YOLO_MODEL_SIZE 切换：yolov8n（默认）或 yolov8s
MODEL_SIZE = os.environ.get("YOLO_MODEL_SIZE", "yolov8n")
EXPERIMENT_NAME = MODEL_SIZE    # 本地目录 runs/detect/tea_yulu_detect/<size>，与 n 基线隔离
EPOCHS = 100
IMG_SIZE = 640
# batch 按规模自适应：yolov8s 参数量≈3.5×，T4 15GB 下降为 8 防 OOM；可用 YOLO_BATCH 覆盖
BATCH_SIZE = int(os.environ.get("YOLO_BATCH", 8 if MODEL_SIZE == "yolov8s" else 16))
PATIENCE = 20
OPTIMIZER = "AdamW"
LR0 = 1e-3
LRF = 1e-2

# 运行平台可移植：WORK_DIR 控制本地工作根目录；SYNC_TARGET 覆盖产物落地（设了就不挂 Drive）；DATA_ROOT 直接指定数据集根
WORK_DIR = Path(os.environ.get("WORK_DIR", "/content"))
SYNC_TARGET = os.environ.get("SYNC_TARGET")
DATA_ROOT = os.environ.get("DATA_ROOT")

COLAB_DATASET_DIR = WORK_DIR / "datasets" / "tea_yulu"
DRIVE_SAVE_DIR = Path("/content/drive/MyDrive/BISHE/models")
DRIVE_DATASET_DIR = Path("/content/drive/MyDrive/BISHE_DATA/datasets/tea_yulu")
DRIVE_ZIP_PATH = Path("/content/drive/MyDrive/tea_yulu_dataset.zip")
LOCAL_ZIP_PATH = WORK_DIR / "tea_yulu_dataset.zip"

CLASS_NAMES = ["特级", "一级", "二级", "等外"]


def set_seed(seed: int = SEED) -> None:
    """固定所有可固定随机种子，保证实验可复现。"""
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
    """挂载 Google Drive，用于读取上传的数据集和保存训练结果。"""
    try:
        from google.colab import drive
    except ImportError:
        raise RuntimeError("未在 Colab 环境运行，无法挂载 Google Drive")
    drive.mount("/content/drive", force_remount=False)
    return Path("/content/drive/MyDrive")


def prepare_from_drive(drive_base: Optional[Path] = None) -> Path:
    r"""
    方案 A：从 Google Drive 拷贝已上传的数据集到 Colab 本地。
    要求：将本地 D:\BISHE_DATA\datasets\tea_yulu 整体上传到
          Google Drive 的 /MyDrive/BISHE_DATA/datasets/tea_yulu
    """
    if drive_base is None:
        drive_base = mount_google_drive()
    src = drive_base / "BISHE_DATA" / "datasets" / "tea_yulu"
    if not src.exists():
        raise FileNotFoundError(
            f"Google Drive 数据集不存在：{src}\n"
            "请先将本地 D:\\BISHE_DATA\\datasets\\tea_yulu 上传到 Drive 对应路径。"
        )
    if COLAB_DATASET_DIR.exists():
        shutil.rmtree(COLAB_DATASET_DIR)
    shutil.copytree(src, COLAB_DATASET_DIR)
    log(f"方案 A 完成：已拷贝数据集 {src} -> {COLAB_DATASET_DIR}")
    return COLAB_DATASET_DIR


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
                # 目录名含反斜杠：创建新目录并移动内容，然后删除旧目录
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

    # 兼容 Windows 反斜杠路径
    _normalize_backslash_paths(extract_to)

    # 标准结构：/content/datasets/tea_yulu/data.yaml
    if COLAB_DATASET_DIR.exists() and (COLAB_DATASET_DIR / "data.yaml").exists():
        return COLAB_DATASET_DIR

    # 兼容：没有顶层 tea_yulu/，文件直接铺在 extract_to 下
    if (extract_to / "data.yaml").exists():
        return _flatten_to_tea_yulu(extract_to)

    # 兼容：顶层只有一个目录且里面有 data.yaml
    extracted_dirs = [p for p in extract_to.iterdir() if p.is_dir()]
    if len(extracted_dirs) == 1 and (extracted_dirs[0] / "data.yaml").exists():
        extracted_dirs[0].rename(COLAB_DATASET_DIR)
        return COLAB_DATASET_DIR

    raise FileNotFoundError(
        f"解压后未找到有效数据集。期望 {COLAB_DATASET_DIR}/data.yaml，"
        f"请检查 zip 顶层结构。"
    )


def prepare_from_drive_zip(drive_base: Optional[Path] = None) -> Path:
    """方案 B：从 Google Drive 根目录的 tea_yulu_dataset.zip 解压。"""
    if drive_base is None:
        drive_base = mount_google_drive()
    zip_path = drive_base / "tea_yulu_dataset.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Google Drive 根目录数据集 zip 不存在：{zip_path}")
    return extract_zip(zip_path, Path("/content/datasets"))


def ensure_dataset() -> Path:
    """
    数据集准备优先级：
    1. 已解压目录（跳过，支持断点重跑）
    2. Drive 根目录 tea_yulu_dataset.zip
    3. Drive /MyDrive/BISHE_DATA/datasets/tea_yulu 目录拷贝
    4. /content/tea_yulu_dataset.zip 本地 zip
    """
    # 平台可移植：若设置了 DATA_ROOT，直接作为数据集根（Kaggle 输入数据集解压到本地后指向此目录）
    if DATA_ROOT:
        root = Path(DATA_ROOT)
        if (root / "data.yaml").exists():
            log(f"使用 DATA_ROOT 指定数据集：{root}")
            return root
        log(f"DATA_ROOT 下未找到 data.yaml：{root}")

    if COLAB_DATASET_DIR.exists() and (COLAB_DATASET_DIR / "data.yaml").exists():
        log(f"本地数据集已存在：{COLAB_DATASET_DIR}")
        return COLAB_DATASET_DIR

    # 方案 A：Drive 根目录 zip
    try:
        return prepare_from_drive_zip()
    except Exception as exc:
        log(f"方案 A（Drive 根目录 zip）失败：{exc}")

    # 方案 B：Drive 数据集目录
    try:
        return prepare_from_drive()
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


def save_hyper_params(save_dir: Path) -> Path:
    """保存训练超参，供论文和 W3 后端溯源使用。"""
    hyper = {
        "model": f"{MODEL_SIZE}.pt",
        "task": "detect",
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
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "degrees": 0.0,
        "translate": 0.1,
        "scale": 0.5,
        "shear": 0.0,
        "perspective": 0.0,
        "flipud": 0.0,
        "fliplr": 0.5,
        "mosaic": 1.0,
        "mixup": 0.0,
        "copy_paste": 0.0,
        "class_names": CLASS_NAMES,
        "class_map": {"特级": 0, "一级": 1, "二级": 2, "等外": 3},
        "created_at": datetime.now().isoformat(),
    }
    hp_path = save_dir / "hyper_params.json"
    hp_path.write_text(json.dumps(hyper, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"超参已保存：{hp_path}")
    return hp_path


def resolve_data_yaml(data_yaml: Path) -> Path:
    """
    把 data.yaml 中的 path 字段改为数据集目录的绝对路径，
    避免 Ultralytics 在当前工作目录解析相对路径导致找不到图片。
    """
    with data_yaml.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["path"] = str(data_yaml.parent.resolve())

    # 写出到可写目录（Colab/Kaggle 的 input 可能为只读），避免写入失败
    out_dir = WORK_DIR / "datasets" / "tea_yulu"
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = out_dir / "data_colab.yaml"
    with resolved.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
    log(f"已生成专用 data.yaml：{resolved}")
    return resolved


def plot_training_curves(results_csv: Path, save_dir: Path) -> None:
    """读取 Ultralytics results.csv 绘制并保存训练曲线。"""
    import pandas as pd

    if not results_csv.exists():
        log(f"未找到 results.csv：{results_csv}")
        return

    df = pd.read_csv(results_csv)
    epochs = df["epoch"].values
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # box_loss
    for split in ["train/box_loss", "val/box_loss"]:
        if split in df.columns:
            axes[0, 0].plot(epochs, df[split].values, label=split)
    axes[0, 0].set_title("Box Loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].legend()

    # cls_loss
    for split in ["train/cls_loss", "val/cls_loss"]:
        if split in df.columns:
            axes[0, 1].plot(epochs, df[split].values, label=split)
    axes[0, 1].set_title("Cls Loss")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].legend()

    # mAP
    if "metrics/mAP50(B)" in df.columns:
        axes[1, 0].plot(epochs, df["metrics/mAP50(B)"].values, label="mAP50")
    if "metrics/mAP50-95(B)" in df.columns:
        axes[1, 0].plot(epochs, df["metrics/mAP50-95(B)"].values, label="mAP50-95")
    axes[1, 0].set_title("mAP")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].legend()

    # precision / recall
    if "metrics/precision(B)" in df.columns:
        axes[1, 1].plot(epochs, df["metrics/precision(B)"].values, label="Precision")
    if "metrics/recall(B)" in df.columns:
        axes[1, 1].plot(epochs, df["metrics/recall(B)"].values, label="Recall")
    axes[1, 1].set_title("Precision / Recall")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].legend()

    plt.tight_layout()
    curve_path = save_dir / "training_curves.png"
    plt.savefig(curve_path, dpi=300)
    log(f"训练曲线已保存：{curve_path}")


def main() -> int:
    set_seed(SEED)
    log(f"PyTorch 版本：{torch.__version__}；CUDA 可用：{torch.cuda.is_available()}")

    # 1. 准备数据集
    dataset_dir = ensure_dataset()
    data_yaml = dataset_dir / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml 不存在：{data_yaml}")
    log(f"使用 data.yaml：{data_yaml}")
    data_yaml = resolve_data_yaml(data_yaml)

    # 2. 创建保存目录（与 Ultralytics 实际保存路径一致：project/name）
    exp_dir = Path(PROJECT_NAME) / EXPERIMENT_NAME
    exp_dir.mkdir(parents=True, exist_ok=True)
    save_hyper_params(exp_dir)

    # 3. 训练检测模型
    log(f"开始训练 {MODEL_SIZE} 检测模型...")
    model = YOLO(f"{MODEL_SIZE}.pt")
    results = model.train(
        data=str(data_yaml),
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
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0,
    )
    log(f"训练完成，结果目录：{exp_dir}")

    # 4. 在测试集上评估
    best_pt = exp_dir / "weights" / "best.pt"
    if not best_pt.exists():
        raise FileNotFoundError(f"训练未生成 best.pt：{best_pt}")

    val_model = YOLO(str(best_pt))
    metrics = val_model.val(data=str(resolve_data_yaml(dataset_dir / "data.yaml")), split="test")
    eval_dict = {
        "mAP50-95": float(metrics.box.map),
        "mAP50": float(metrics.box.map50),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "created_at": datetime.now().isoformat(),
    }
    eval_path = exp_dir / "test_metrics.json"
    eval_path.write_text(json.dumps(eval_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"测试集指标：{eval_dict}")

    # 5. 绘制训练曲线
    results_csv = exp_dir / "results.csv"
    plot_training_curves(results_csv, exp_dir)

    # 6. 同步产物（文件名带 size 后缀，避免覆盖 yolov8n 基线）
    suffix = MODEL_SIZE  # "yolov8n" 或 "yolov8s"
    if SYNC_TARGET:
        target = Path(SYNC_TARGET)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_pt, target / f"best_detect_{suffix}.pt")
        for base in ["hyper_params.json", "test_metrics.json", "training_curves.png", "results.csv"]:
            src = exp_dir / base
            if src.exists():
                stem, ext = os.path.splitext(base)
                shutil.copy(src, target / f"{stem}_{suffix}{ext}")
        log(f"检测训练产物已同步到 SYNC_TARGET：{target}")
    else:
        drive_base = mount_google_drive()
        DRIVE_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_pt, DRIVE_SAVE_DIR / f"best_detect_{suffix}.pt")
        for base in ["hyper_params.json", "test_metrics.json", "training_curves.png", "results.csv"]:
            src = exp_dir / base
            if src.exists():
                stem, ext = os.path.splitext(base)
                shutil.copy(src, DRIVE_SAVE_DIR / f"{stem}_{suffix}{ext}")
        log(f"检测训练产物已同步到 Drive：{DRIVE_SAVE_DIR}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"训练脚本异常：{e}")
        raise
