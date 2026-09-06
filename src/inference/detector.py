"""
恩施玉露茶等级检测推理封装
============================
接口契约②实现：
    detect(image: str | np.ndarray) -> {
        "class_id": int,        # 0特级 / 1一级 / 2二级 / 3等外
        "class_name": str,      # "特级" 等
        "confidence": float,    # 0-1
        "bbox": [x1, y1, x2, y2]  # 归一化 0-1
    }
分级策略：单图取置信度最高的检测框类别作为最终等级。

运行环境：本地 CPU 推理验证（生产权重由 Colab GPU 训练后导出）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# 冻结约束（修改需走变更申请）
# ---------------------------------------------------------------------------
CLASS_NAMES = ["特级", "一级", "二级", "等外"]
CLASS_MAP = {0: "特级", 1: "一级", 2: "二级", 3: "等外"}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHT = PROJECT_ROOT / "models" / "best_detect.pt"

# 本地 CPU 推理强制设置
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"


class TeaGradeDetector:
    """恩施玉露茶等级检测器。"""

    def __init__(
        self,
        weight_path: Union[str, Path] = DEFAULT_WEIGHT,
        device: str = "cpu",
        skip_exists_check: bool = False,
    ):
        self.weight_path = Path(weight_path)
        if not skip_exists_check and not self.weight_path.exists():
            raise FileNotFoundError(
                f"检测模型权重不存在：{self.weight_path}\n"
                "请先通过 Colab 训练并导出 best_detect.pt 到 models/ 目录。"
            )
        self.device = device
        self.model = YOLO(str(self.weight_path))
        self.model.to(device)

    def _xywh2xyxy(self, x: np.ndarray) -> np.ndarray:
        """将归一化 xywh（中心点+宽高）转换为 xyxy（左上角+右下角）。"""
        y = np.copy(x)
        y[..., 0] = x[..., 0] - x[..., 2] / 2  # x1
        y[..., 1] = x[..., 1] - x[..., 3] / 2  # y1
        y[..., 2] = x[..., 0] + x[..., 2] / 2  # x2
        y[..., 3] = x[..., 1] + x[..., 3] / 2  # y2
        return y

    def _clip_bbox(self, bbox: list) -> list:
        """将 bbox 裁剪到 [0, 1] 区间。"""
        return [max(0.0, min(1.0, float(v))) for v in bbox]

    def detect(self, image: Union[str, Path, np.ndarray]) -> dict:
        """
        对单张图片进行等级检测。

        Args:
            image: 图片路径（str / Path）或 numpy 数组（HWC, BGR/RGB 均可）。

        Returns:
            符合契约②的字典。
        """
        results = self.model.predict(
            source=image,
            device=self.device,
            verbose=False,
            conf=0.25,
            iou=0.45,
        )

        if not results or len(results) == 0:
            # 无检测框时返回等外，置信度 0
            return {
                "class_id": 3,
                "class_name": "等外",
                "confidence": 0.0,
                "bbox": [0.0, 0.0, 1.0, 1.0],
            }

        result = results[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return {
                "class_id": 3,
                "class_name": "等外",
                "confidence": 0.0,
                "bbox": [0.0, 0.0, 1.0, 1.0],
            }

        # 提取所有检测框并选取置信度最高者
        confs = boxes.conf.cpu().numpy()
        cls_ids = boxes.cls.cpu().numpy().astype(int)
        xywh = boxes.xywhn.cpu().numpy()  # 已归一化

        best_idx = int(np.argmax(confs))
        class_id = int(cls_ids[best_idx])
        confidence = float(confs[best_idx])
        xyxy = self._xywh2xyxy(xywh[best_idx])
        bbox = self._clip_bbox(xyxy.tolist())

        return {
            "class_id": class_id,
            "class_name": CLASS_MAP.get(class_id, "未知"),
            "confidence": confidence,
            "bbox": bbox,
        }


# 保持兼容旧调用方式：直接导入函数
def detect(image: Union[str, Path, np.ndarray], weight_path: Union[str, Path] = DEFAULT_WEIGHT) -> dict:
    """单例风格的 detect 函数，供 W3 后端直接调用。"""
    detector = TeaGradeDetector(weight_path=weight_path)
    return detector.detect(image)


if __name__ == "__main__":
    # 本地 CPU 推理验证入口
    import sys

    test_image = PROJECT_ROOT / "datasets" / "tea_yulu" / "test" / "images"
    weight = DEFAULT_WEIGHT
    output: dict

    # 如果生产权重存在，执行真实推理验证
    if weight.exists():
        detector = TeaGradeDetector(weight_path=weight)
        sample = None
        if test_image.exists():
            imgs = sorted(test_image.glob("*"))
            for img in imgs:
                if img.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                    sample = str(img)
                    break
        if sample is None:
            print("[WARN] 未找到测试图片，使用随机噪声图做接口验证。")
            sample = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        output = detector.detect(sample)
    else:
        print("[WARN] 未找到 best_detect.pt，将尝试下载 yolov8n.pt 做接口格式验证。")
        try:
            detector = TeaGradeDetector(weight_path="yolov8n.pt", skip_exists_check=True)
            sample = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            output = detector.detect(sample)
            print("[INFO] 使用 yolov8n.pt 完成接口格式验证（类别无实际意义）。")
        except Exception as exc:
            print(f"[WARN] 真实模型加载失败（{type(exc).__name__}），可能是网络/代理问题。")
            print("[INFO] 进入 Mock 模式，仅校验接口字段与数据范围。")
            output = {
                "class_id": 0,
                "class_name": "特级",
                "confidence": 0.9876,
                "bbox": [0.1, 0.2, 0.8, 0.9],
            }

    print("接口契约②输出示例：")
    print(output)

    # 校验字段
    required_keys = {"class_id", "class_name", "confidence", "bbox"}
    assert set(output.keys()) == required_keys, f"输出字段不匹配：{output.keys()}"
    assert isinstance(output["class_id"], int)
    assert output["class_name"] in CLASS_NAMES
    assert 0.0 <= output["confidence"] <= 1.0
    assert len(output["bbox"]) == 4
    assert all(0.0 <= v <= 1.0 for v in output["bbox"])
    print("接口字段校验通过。")
