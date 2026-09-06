# -*- coding: utf-8 -*-
"""一键校验 W1 数据集数量"""
from pathlib import Path

base = Path(r"C:\Users\wzd\Desktop\毕业设计\datasets\tea_yulu")
train = len(list((base / "train" / "images").glob("*")))
val   = len(list((base / "val"   / "images").glob("*")))
test  = len(list((base / "test"  / "images").glob("*")))
total = train + val + test

print("=== 数据集数量校验 ===")
print(f"train: {train}  (预期 4611)")
print(f"val:   {val}    (预期 439)")
print(f"test:  {test}   (预期 219)")
print(f"total: {total}  (预期 5269)")

if train == 4611 and val == 439 and test == 219:
    print("[PASS] 数据集数量校验通过")
else:
    print("[WARN] 数量与预期不符，请检查 W1 输出")
