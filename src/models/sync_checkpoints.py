"""
sync_checkpoints.py — Colab 训练产物抢救/同步脚本
=================================================

用途
----
当 train_detect.py / train_cls.py 在「训练已完成、但收尾（val/sync）步骤崩溃」
导致 best.pt 与指标 JSON 没有同步到 Google Drive 时，用本脚本不重训、直接
从 /content/runs/ 下已存在的权重抢救并同步。

背景（2026-09-04 实战）
----------------------
当天两个训练脚本的 exp_dir 路径写错（写成 PROJECT_NAME/EXPERIMENT_NAME，
而 Ultralytics 实际把权重存到 runs/detect/... 与 runs/classify/...），于是
main() 在训练后找不到 best.pt → 抛 FileNotFoundError，best.pt / 指标 / 曲线
全部没同步到 Drive。权重其实都在 Colab 磁盘上，本脚本用于就地抢救。

规模切换（2026-09-05 增强）
---------------------------
通过环境变量 YOLO_MODEL_SIZE 选择要抢救的规模：
- 不设置 / "yolov8n"  → 抢救检测 yolov8n + 分类 yolov8n-cls（默认）
- "yolov8s"            → 抢救检测 yolov8s + 分类 yolov8s-cls
Drive 文件名带 size 后缀（best_detect_yolov8s.pt / val_metrics_yolov8s-cls.json ...），
与 train_detect.py / train_cls.py 完全一致，不会互相覆盖。

前置条件（重要）
---------------
- Colab 会话**未断开**（/content/runs/ 下的权重还在）。
- 已在 Colab 中挂载 Drive：from google.colab import drive; drive.mount('/content/drive')
- 已安装 ultralytics、pandas、matplotlib、pyyaml。

用法（在 Colab 单元格中 %run 或直接粘贴运行）
--------------------------------------------
    %env YOLO_MODEL_SIZE=yolov8s      # 可选，默认 yolov8n
    %run sync_checkpoints.py
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import yaml
import matplotlib.pyplot as plt
import pandas as pd
from ultralytics import YOLO

# ---- 规模切换（与 train_detect.py / train_cls.py 共用同一变量） ----
DET_SIZE = os.environ.get("YOLO_MODEL_SIZE", "yolov8n")   # yolov8n / yolov8s
CLS_SIZE = f"{DET_SIZE}-cls"                                # yolov8n-cls / yolov8s-cls

# ---- 路径配置（与 train_detect.py / train_cls.py 保持一致，平台可移植） ----
WORK_DIR = Path(os.environ.get("WORK_DIR", "/content"))
SYNC_TARGET = os.environ.get("SYNC_TARGET")
DATA_ROOT = os.environ.get("DATA_ROOT")

DRIVE_SAVE = Path("/content/drive/MyDrive/BISHE/models")
DETECT_DATA = (Path(DATA_ROOT) / "data.yaml") if DATA_ROOT else (WORK_DIR / "datasets" / "tea_yulu" / "data.yaml")
DETECT_RUN = WORK_DIR / "tea_yulu_detect" / DET_SIZE
CLS_DATA = WORK_DIR / "datasets" / "tea_yulu_cls"
CLS_RUN = WORK_DIR / "tea_yulu_cls" / CLS_SIZE

# 产物落地目录：设了 SYNC_TARGET 用本地目录，否则回写 Drive
SAVE_DIR = Path(SYNC_TARGET) if SYNC_TARGET else DRIVE_SAVE


def resolve_data_yaml(src: Path) -> Path:
    """把 data.yaml 的 path 改写为数据集目录绝对路径，规避 Ultralytics 把
    `path: .` 解析为当前工作目录的旧坑。写出到可写目录（Kaggle input 只读）。"""
    cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
    cfg["path"] = str(src.parent)
    out_dir = WORK_DIR / "datasets" / "tea_yulu"
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = out_dir / "data_colab.yaml"
    resolved.write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(f"[data] 已生成绝对路径版 data.yaml: {resolved}")
    return resolved


def _sync_files(run_dir: Path, suffix: str, drive_files: list[str]) -> None:
    """把 run_dir 下的产物以 `<stem>_<suffix><ext>` 命名同步到 Drive。"""
    for base in drive_files:
        s = run_dir / base
        if s.exists():
            stem, ext = os.path.splitext(base)
            shutil.copy(s, SAVE_DIR / f"{stem}_{suffix}{ext}")


def sync_detect() -> dict:
    """重算检测模型 test 指标、生成曲线、同步到 Drive。返回指标 dict。"""
    resolved = resolve_data_yaml(DETECT_DATA)
    det_model = YOLO(str(DETECT_RUN / "weights" / "best.pt"))
    det_m = det_model.val(data=str(resolved), split="test")

    test_metrics = {
        "mAP50-95": float(det_m.box.map),
        "mAP50": float(det_m.box.map50),
        "precision": float(det_m.box.mp),
        "recall": float(det_m.box.mr),
        "created_at": datetime.now().isoformat(),
    }
    (DETECT_RUN / "test_metrics.json").write_text(
        json.dumps(test_metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[detect] test 指标: {test_metrics}")

    # 训练曲线
    df = pd.read_csv(DETECT_RUN / "results.csv")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for s in ["train/box_loss", "val/box_loss"]:
        if s in df:
            axes[0, 0].plot(df["epoch"], df[s], label=s)
    axes[0, 0].set_title("Box Loss")
    axes[0, 0].legend()
    for s in ["train/cls_loss", "val/cls_loss"]:
        if s in df:
            axes[0, 1].plot(df["epoch"], df[s], label=s)
    axes[0, 1].set_title("Cls Loss")
    axes[0, 1].legend()
    if "metrics/mAP50(B)" in df:
        axes[1, 0].plot(df["epoch"], df["metrics/mAP50(B)"], label="mAP50")
    if "metrics/mAP50-95(B)" in df:
        axes[1, 0].plot(df["epoch"], df["metrics/mAP50-95(B)"], label="mAP50-95")
    axes[1, 0].set_title("mAP")
    axes[1, 0].legend()
    if "metrics/precision(B)" in df:
        axes[1, 1].plot(df["epoch"], df["metrics/precision(B)"], label="Precision")
    if "metrics/recall(B)" in df:
        axes[1, 1].plot(df["epoch"], df["metrics/recall(B)"], label="Recall")
    axes[1, 1].set_title("Precision/Recall")
    axes[1, 1].legend()
    plt.tight_layout()
    fig.savefig(DETECT_RUN / "training_curves.png", dpi=300)
    plt.close(fig)

    shutil.copy(DETECT_RUN / "weights" / "best.pt", SAVE_DIR / f"best_detect_{DET_SIZE}.pt")
    _sync_files(DETECT_RUN, DET_SIZE, ["hyper_params.json", "test_metrics.json", "training_curves.png", "results.csv"])
    return test_metrics


def sync_cls() -> dict:
    """重算分类模型 val 指标、同步到 Drive。返回指标 dict。"""
    cls_model = YOLO(str(CLS_RUN / "weights" / "best.pt"))
    cls_m = cls_model.val(data=str(CLS_DATA))
    val_metrics = {
        "top1_accuracy": float(cls_m.top1),
        "top5_accuracy": float(cls_m.top5),
        "created_at": datetime.now().isoformat(),
    }
    (CLS_RUN / "val_metrics.json").write_text(
        json.dumps(val_metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[cls] val 指标: {val_metrics}")

    shutil.copy(CLS_RUN / "weights" / "best.pt", SAVE_DIR / f"best_cls_{CLS_SIZE}.pt")
    _sync_files(CLS_RUN, CLS_SIZE, ["hyper_params_cls.json", "val_metrics.json", "results.csv"])
    return val_metrics


def main() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    if not DETECT_RUN.exists():
        missing.append(f"检测={DETECT_RUN}")
    if not CLS_RUN.exists():
        missing.append(f"分类={CLS_RUN}")

    # 检测和分类允许部分完成：缺哪个就跳过哪个
    if DETECT_RUN.exists():
        sync_detect()
    else:
        print(f"[warn] 跳过检测同步，目录不存在：{DETECT_RUN}")

    if CLS_RUN.exists():
        sync_cls()
    else:
        print(f"[warn] 跳过分类同步，目录不存在：{CLS_RUN}")

    if missing:
        print(f"[warn] 以下目录缺失（属于正常情况，如果对应模型尚未训练）：{', '.join(missing)}")

    print("==== 同步完成 ====")
    print([p.name for p in SAVE_DIR.iterdir()])


if __name__ == "__main__":
    main()
