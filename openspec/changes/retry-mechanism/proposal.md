# Change: 错误处理重试与可视化进度机制

## Why
目前系统在合同上传处理流程中，用户无法直观了解解析进行到了哪一步（如OCR、向量化等），且遇到错误时只能全量重新上传，导致用户体验不佳且浪费计算资源。用户希望有一个类似“地铁线路图”的直观进度展示，并支持断点重试。

## What Changes
### 1. 后端状态细化与重试
- **状态细化**：在 `UploadStatusManager` 中扩充状态定义，明确记录 `processing` 的子状态：
    - `serializing` (排队中)
    - `parsing_images` (PDF转图片中)
    - `parsing_ocr` (OCR识别中)
    - `vectorizing` (向量化存储中)
    - `metadata_extracting` (元数据提取中)
- **错误记录**：新增对应的失败状态 (`failed_images`, `failed_ocr`, `failed_vector`, `failed_metadata`) 并在 `error` 字段记录详细日志。
- **重试接口**：新增 `POST /upload/retry/{upload_id}` 接口。
    - 智能判断重试起点：例如 `failed_metadata` 仅重提元数据，`failed_ocr` 则重新进行 OCR。
    - **BREAKING**: 之前的通用 `failed` 状态将被细分的状态替代。

### 2. 前端进度可视化 ("地铁线路图")
- **UI组件**：开发一个步骤条组件 (Stepper) 或自定义“地铁图”组件。
    - **节点定义**：上传完成 -> 图片转换 -> OCR识别 -> 向量化 -> 元数据提取 -> 完成。
    - **视觉表现**：
        - **已完成**：绿色/实心圆点，连接线变色。
        - **进行中**：蓝色/呼吸动画圆点。
        - **未开始**：灰色/空心圆点。
        - **失败**：红色/警告图标。
- **集成位置**：
    - 在 `UploadPage` 的文档列表“状态”列，悬停或点击时以 Popover 形式展示详细进度图；或者在表格中直接简化展示（如微型点阵）。
    - 在文档详情弹窗 (`showDetail`) 中顶部显著位置展示完整的“地铁线路图”。

### 3. 前端交互改进
- **重试操作**：
    - 在列表“操作”列及“详情”页，当状态为失败时，显示“重试”按钮。
    - 点击重试后，UI 状态即时更新为 pending 或对应步骤的 processing 状态。
- **错误提示**：
    - 鼠标悬停在失败节点上显示具体错误原因 (Tooltip)。

## Impact
- **Affected specs**: Upload & Parsing Capability
- **Affected code**: 
    - `backend/contractApi.py` (API implementation)
    - `backend/upload_status_manager.py` (State management)
    - `frontend/src/pages/UploadPage.tsx` (UI changes)
    - `frontend/src/components/ProgressStepper.tsx` (New component)
