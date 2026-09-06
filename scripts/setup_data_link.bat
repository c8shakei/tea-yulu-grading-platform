@echo off
chcp 65001 >nul
:: W1 数据集 junction 一键建链脚本
:: 将项目内的 datasets/tea_yulu 映射到 D 盘实际数据目录

set "SRC=D:\BISHE_DATA\datasets\tea_yulu"
set "LINK=C:\Users\wzd\Desktop\毕业设计\datasets\tea_yulu"
set "LINK_PARENT=C:\Users\wzd\Desktop\毕业设计\datasets"

echo ========================================
echo 创建数据集 junction
echo 实际数据目录: %SRC%
echo 项目映射路径: %LINK%
echo ========================================

:: 1. 检查实际数据目录是否存在
if not exist "%SRC%" (
    echo [错误] 实际数据目录不存在: %SRC%
    echo 请先运行 w1_extract_prepare.py 与 w1_split_dataset.py 生成数据集。
    pause
    exit /b 1
)

:: 2. 确保父目录存在
if not exist "%LINK_PARENT%" (
    mkdir "%LINK_PARENT%"
    echo [信息] 创建父目录: %LINK_PARENT%
)

:: 3. 如果 link 已存在，先删除（可能是旧 junction 或目录）
if exist "%LINK%" (
    echo [信息] 已存在 %LINK%，正在移除旧映射...
    rmdir /S /Q "%LINK%"
    if exist "%LINK%" (
        echo [错误] 无法移除旧映射，请手动检查权限。
        pause
        exit /b 1
    )
)

:: 4. 创建 junction
mklink /J "%LINK%" "%SRC%"
if errorlevel 1 (
    echo [错误] junction 创建失败。
    pause
    exit /b 1
)

echo [成功] junction 已创建。

:: 5. 校验：检查关键文件/目录是否可达
echo [校验] 检查数据目录内容...
if exist "%LINK%\data.yaml" (
    echo [通过] data.yaml 可达
) else (
    echo [警告] 未找到 %LINK%\data.yaml
)

if exist "%LINK%\train\images" (
    echo [通过] train/images 可达
) else (
    echo [警告] 未找到 %LINK%\train\images
)

if exist "%LINK%\val\images" (
    echo [通过] val/images 可达
) else (
    echo [警告] 未找到 %LINK%\val\images
)

if exist "%LINK%\test\images" (
    echo [通过] test/images 可达
) else (
    echo [警告] 未找到 %LINK%\test\images
)

echo ========================================
echo 完成。可按任意键退出。
pause
