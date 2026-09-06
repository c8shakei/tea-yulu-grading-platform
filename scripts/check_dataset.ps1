# 一键校验 W1 数据集数量
# encoding: utf-8
$base = "C:\Users\wzd\Desktop\毕业设计\datasets\tea_yulu"
$train = (Get-ChildItem "$base\train\images" -File).Count
$val   = (Get-ChildItem "$base\val\images" -File).Count
$test  = (Get-ChildItem "$base\test\images" -File).Count
$total = $train + $val + $test

Write-Host "=== Dataset Count Check ==="
Write-Host "train: $train  (expected 4611)"
Write-Host "val:   $val    (expected 439)"
Write-Host "test:  $test   (expected 219)"
Write-Host "total: $total  (expected 5269)"

if (($train -eq 4611) -and ($val -eq 439) -and ($test -eq 219)) {
    Write-Host "[PASS] count OK" -ForegroundColor Green
} else {
    Write-Host "[WARN] count mismatch, check W1 output" -ForegroundColor Yellow
}
