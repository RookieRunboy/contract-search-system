# 技术设计：PDF 分批解析

## Context
当前 `pdfToText.py` 的 `pdf_to_images` 方法一次性调用 `convert_from_path()` 加载全部页面图片到内存，导致内存占用与 PDF 页数成正比。在内存保护机制下，这使得系统只能串行处理 PDF。

## Goals / Non-Goals
### Goals
- 将单任务内存峰值降低 90%（从 ~1.5GB 降至 ~150MB）
- 使系统在 8GB 内存服务器上能够真正并发处理 3-5 个任务
- 将单任务 OCR 处理速度提升 60% 以上

### Non-Goals
- 不调整向量化或元数据提取流程
- 不优化 PDF 渲染 DPI（保持 220）

## Decisions

### Decision 1: 使用 `first_page` / `last_page` 参数分批加载
**理由**：`pdf2image.convert_from_path()` 原生支持此参数，无需引入新依赖。修改最小，风险可控。

**代码示例**：
```python
BATCH_SIZE = int(os.getenv("PDF_BATCH_SIZE", "5"))

def pdf_to_images_batched(pdf_path: Path, dpi: int = 220):
    """分批生成 PDF 页面图片。"""
    from pdf2image import pdfinfo_from_path
    info = pdfinfo_from_path(str(pdf_path), poppler_path=self.poppler_path)
    total_pages = info["Pages"]
    
    for start_page in range(1, total_pages + 1, BATCH_SIZE):
        end_page = min(start_page + BATCH_SIZE - 1, total_pages)
        images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=start_page,
            last_page=end_page,
            # ... other params
        )
        yield from images
        # images 列表出 yield 后自动失去引用，可被 GC
```

### Decision 2: 批次大小默认为 5，可配置
**理由**：
- 5 页约 150MB（220 DPI），在大多数服务器上可接受
- 过小（如 1）会增加 Poppler 调用开销
- 过大（如 20）失去内存优化意义

**配置**：`PDF_BATCH_SIZE`，范围 1-20，默认 5。

### Decision 3: 使用 `ThreadPoolExecutor` 实现 OCR 并发
**理由**：OCR 是 IO 密集型操作（等待 HTTP 响应），适合使用多线程。`process_contract` 将改为双层并发结构：
- 外层：系统级并发（多进程/协程处理不同文件）
- 内层：页面级并发（多线程处理同一文件的不同页面）

**代码模式**：
```python
def process_batch(self, images_batch, start_page_idx):
    results = [None] * len(images_batch)
    with ThreadPoolExecutor(max_workers=OCR_CONCURRENCY) as executor:
        futures = {
            executor.submit(self.extract_text_from_image, img, start_page_idx + i): i
            for i, img in enumerate(images_batch)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = f"ERROR: {e}"
    return results
```

### Decision 4: 放弃 generator 全改造（暂时）
**理由**：当前 `process_contract` 方法对 `images` 列表有 `len()` 调用依赖（用于进度计算）。改为 generator 需同时重构进度跟踪逻辑。作为 MVP，先采用"分批 + 主动清理"方式，future work 可考虑 generator。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Poppler 多次调用增加约 5% 总耗时 | 可接受，内存节省优先 |
| generator 部分 yield 失败回滚复杂 | MVP 采用分批而非 generator |

## Migration Plan
无数据迁移。代码部署后立即生效。

## Open Questions
- 是否需要支持"禁用分批"的 escape hatch（如 `PDF_BATCH_SIZE=0` 表示一次性加载）？暂定不需要。
