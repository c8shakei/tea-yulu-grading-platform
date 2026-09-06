# 一键打包数据集到 D 盘根目录
$source = "D:\BISHE_DATA\datasets\tea_yulu"
$out    = "D:\BISHE_DATA\tea_yulu_dataset.zip"

if (Test-Path $out) {
    Remove-Item $out -Force
}

Write-Host "开始打包..." -ForegroundColor Cyan
Write-Host "源目录: $source"
Write-Host "输出:   $out"

Compress-Archive -Path $source -DestinationPath $out -Force

if (Test-Path $out) {
    $sizeMB = [math]::Round((Get-Item $out).Length / 1MB, 2)
    Write-Host "打包完成: $out (大小: $sizeMB MB)" -ForegroundColor Green
} else {
    Write-Host "打包失败" -ForegroundColor Red
}
