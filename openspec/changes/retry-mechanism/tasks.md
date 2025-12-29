# 任务列表：错误处理和重试机制

- [x] **状态定义更新**： <!-- id: 0 -->
    - [x] 在 `UploadStatusManager` (后端) 定义细粒度状态：`processing` (拆分为 `parsing_images`, `parsing_ocr`, `vectorizing`, `metadata_extracting`) 和 `failed` 对应子状态。
    - [x] 在前端 `types/index.ts` 或 `UploadPage.tsx` 更新状态类型定义。

- [x] **后端逻辑优化**： <!-- id: 1 -->
    - [x] 修改 `pdfToElasticSearch.py`，细化进度状态上报，并在捕获异常时根据阶段抛出不同类型的错误。
    - [x] 修改 `contractApi.py` 中的 `_process_uploaded_file`，确保状态流转正确写入 ES，并正确记录错误信息。

- [x] **实现重试接口**： <!-- id: 2 -->
    - [x] 在 `contractApi.py` 中实现 `POST /upload/retry/{upload_id}`。
    - [x] 实现智能重试逻辑：
        - 若是 `failed_metadata`，仅重新触发元数据提取。
        - 若是其他失败，检查文件是否存在，存在则重置状态为 `pending` 并重新处理。

- [x] **前端组件开发 ("地铁图")**： <!-- id: 3 -->
    - [x] 创建 `src/components/ProgressStepper.tsx` 组件。
    - [x] 实现类似地铁站点的可视化效果：
        - 定义步骤：上传 -> 转图片 -> OCR -> 向量化 -> 元数据。
        - 样式：完成(绿点实线)、进行中(蓝点呼吸)、未开始(灰点虚线)、失败(红点)。

- [x] **前端页面集成**： <!-- id: 4 -->
    - [x] 在 `UploadPage.tsx` 的详情弹窗中引入 `ProgressStepper`，展示完整进度。
    - [x] 在文档列表“状态”列，悬停状态标签时通过 Popover 展示 `ProgressStepper` (或简化版)。
    - [x] 实现“重试”按钮逻辑：调用重试接口并刷新列表。
    - [x] 错误展示优化：失败节点或状态标签 Tooltip 显示后端传回的具体 `error` 信息。

- [x] **测试验证**： <!-- id: 5 -->
    - [x] 验证正常流程下“地铁图”各节点的点亮顺序。
    - [x] 验证 OCR 失败和元数据失败场景下，重试功能是否按预期仅重跑必要步骤。
