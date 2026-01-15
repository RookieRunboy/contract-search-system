# 任务清单

## 1. 后端实现

- [x] 1.1 修改 `pdfToText.py`：将 `pdf_to_images` 改为分批加载方式
  - 使用 `convert_from_path(first_page, last_page)` 分批转换
  - 每批次默认 5 页，通过 `PDF_BATCH_SIZE` 环境变量可配置
  - 每批完成后立即释放内存

- [x] 1.2 重构 `process_contract` 方法：实现分批 + 并发
  - 引入 `ThreadPoolExecutor`
  - 实现 `process_batch_concurrently` 辅助方法
  - 外层遍历批次，内层多线程并发调用 OCR
  - 确保进度回调准确（批量更新或单页更新）
  - 每批处理完后主动 GC

- [x] 1.3 更新 `.env.example`：添加 `PDF_BATCH_SIZE` 和 `OCR_CONCURRENCY` 配置说明

## 2. 测试验证

- [x] 2.1 功能测试：上传多页 PDF，验证解析结果与优化前一致
- [x] 2.2 内存测试：使用 `psutil` 或系统工具监测单任务内存峰值
- [x] 2.3 并发测试：同时上传 5-10 个合同，验证实际并发数 > 1

## 3. 文档更新

- [ ] 3.1 更新规范：归档后同步 `upload-parsing` spec

