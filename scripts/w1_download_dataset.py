"""
W1 数据集下载器
================
从 Mendeley Data (DOI: 10.17632/7t964jmmy3) 并行下载 TeaLeafAgeQuality 全量 zip。
特性：
- 8 路并发分片
- 断点续传
- 每片独立重定向（S3 预签名 URL 5 分钟过期）
- 进度日志输出到 stdout 与 .log 文件
"""

import os
import sys
import time
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# 可配置项
# ---------------------------------------------------------------------------
DATASET_DOI = "10.17632/7t964jmmy3"
DATASET_VERSION = "1"
MENDELEY_ZIP_URL = f"https://data.mendeley.com/public-api/zip/{DATASET_DOI.split('/')[-1]}/download/{DATASET_VERSION}"

# 默认保存路径（D 盘，避免 C 盘空间不足）
DEFAULT_OUT_DIR = Path("D:/BISHE_DATA/raw")
DEFAULT_OUT_FILE = DEFAULT_OUT_DIR / "TeaLeafAgeQuality.zip"

CHUNK_SIZE = 50 * 1024 * 1024   # 50 MB / 片
MAX_WORKERS = 8                  # 并发数
MAX_RETRIES = 3                  # 每片重试次数
RETRY_DELAY = 5                  # 重试间隔（秒）
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 120
# ---------------------------------------------------------------------------


def setup_logging(log_path: Path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def resolve_total_size(url: str) -> int:
    """通过 GET Range 请求获取 S3 最终文件大小。"""
    # 注意：Mendeley 重定向到为 GET 签名的 S3 预签名 URL，HEAD 会 403，因此用 Range GET。
    with requests.get(
        url,
        headers={"Range": "bytes=0-0"},
        allow_redirects=True,
        stream=True,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    ) as resp:
        resp.raise_for_status()
        # 消费掉这一字节，避免连接泄漏
        _ = resp.content
        # 优先读取 Content-Range: bytes 0-0/<total>
        rng = resp.headers.get("Content-Range")
        if rng and "/" in rng:
            return int(rng.split("/")[-1])
        length = resp.headers.get("Content-Length")
        if length:
            return int(length)
    raise RuntimeError("无法获取文件总大小，无法分片下载")


def download_chunk(chunk_idx: int, start: int, end: int, url: str, out_path: Path) -> dict:
    """下载单个分片；支持重试、断点续传。"""
    chunk_file = out_path.with_suffix(f".part{chunk_idx:04d}")
    existing = chunk_file.stat().st_size if chunk_file.exists() else 0

    # 若已完整下载则跳过
    expected = end - start + 1
    if existing >= expected:
        return {"idx": chunk_idx, "status": "skipped", "bytes": existing}

    # 断点续传：调整起始位置
    actual_start = start + existing
    headers = {"Range": f"bytes={actual_start}-{end}"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(
                url,
                headers=headers,
                stream=True,
                allow_redirects=True,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            ) as r:
                r.raise_for_status()
                mode = "ab" if existing else "wb"
                downloaded = existing
                with open(chunk_file, mode) as f:
                    for block in r.iter_content(chunk_size=256 * 1024):
                        if block:
                            f.write(block)
                            downloaded += len(block)
                return {"idx": chunk_idx, "status": "ok", "bytes": downloaded, "attempt": attempt}
        except Exception as e:
            logging.warning(f"分片 {chunk_idx} 第 {attempt} 次尝试失败: {e}")
            if attempt == MAX_RETRIES:
                return {"idx": chunk_idx, "status": "failed", "error": str(e)}
            time.sleep(RETRY_DELAY)


def assemble_chunks(out_path: Path, chunks: list[Path]):
    """按顺序合并分片文件。"""
    # 文件名格式: <stem>.part0000，按数字序合并
    def part_index(p: Path) -> int:
        suffix = p.suffix  # ".part0000"
        return int(suffix.replace(".part", ""))
    chunks.sort(key=part_index)
    with open(out_path, "wb") as out:
        for part in chunks:
            with open(part, "rb") as src:
                while True:
                    buf = src.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    out.write(buf)
    logging.info(f"合并完成: {out_path} ({out_path.stat().st_size / 1e9:.2f} GB)")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".download.log")
    setup_logging(log_path)

    logging.info(f"Mendeley zip URL: {MENDELEY_ZIP_URL}")
    logging.info(f"输出文件: {out_path}")

    # 1. 解析总大小
    logging.info("正在获取文件总大小...")
    total_size = resolve_total_size(MENDELEY_ZIP_URL)
    logging.info(f"总大小: {total_size / 1e9:.3f} GB ({total_size} bytes)")

    # 2. 生成分片任务
    chunks = []
    start = 0
    while start < total_size:
        end = min(start + CHUNK_SIZE - 1, total_size - 1)
        chunks.append((len(chunks), start, end))
        start = end + 1
    logging.info(f"分片数: {len(chunks)}，每片约 {CHUNK_SIZE / 1e6:.0f} MB，并发 {MAX_WORKERS}")

    # 3. 并行下载
    completed = 0
    failed = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(download_chunk, idx, s, e, MENDELEY_ZIP_URL, out_path): idx
            for idx, s, e in chunks
        }
        for fut in as_completed(futures):
            res = fut.result()
            completed += 1
            if res["status"] == "failed":
                failed.append(res)
                logging.error(f"[{completed}/{len(chunks)}] 分片 {res['idx']} 失败: {res.get('error')}")
            else:
                logging.info(
                    f"[{completed}/{len(chunks)}] 分片 {res['idx']} {res['status']} "
                    f"({res['bytes'] / 1e6:.1f} MB)"
                )

    if failed:
        logging.error(f"有 {len(failed)} 个分片下载失败，请检查网络后重跑脚本（支持续传）")
        sys.exit(1)

    # 4. 合并
    # 注意：part 文件名为 <stem>.partXXXX（如 TeaLeafAgeQuality.part0000）
    part_files = sorted(out_path.parent.glob(f"{out_path.stem}.part*"))
    logging.info(f"合并 {len(part_files)} 个分片...")
    assemble_chunks(out_path, part_files)

    # 5. 校验大小
    actual_size = out_path.stat().st_size
    if actual_size != total_size:
        logging.error(f"文件大小不匹配: 期望 {total_size}, 实际 {actual_size}")
        sys.exit(1)

    # 6. 清理分片
    for p in part_files:
        p.unlink()
    logging.info("分片已清理")

    # 7. 计算 SHA256（耗时较长，仅记录）
    logging.info("正在计算 SHA256...")
    sha = compute_sha256(out_path)
    logging.info(f"SHA256: {sha}")
    (out_path.with_suffix(".sha256")).write_text(f"{sha}  {out_path.name}\n", encoding="utf-8")

    logging.info("下载完成")


if __name__ == "__main__":
    main()
