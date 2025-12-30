# 任务列表：上传列表 UI 改进

- [x] 创建 `ClickToCopy` 组件（可在 `UploadPage.tsx` 内部定义或新建文件），用于新的“点击即复制”交互。 <!-- id: 0 -->
- [x] 修改 `UploadPage.tsx` 中的表格列配置 (`columns`)： <!-- id: 1 -->
    - [x] **合同名称列**：移除 `ellipsis` 和 `maxWidth`，允许自动换行显示完整名称。
    - [x] **合同编码列**：应用 `ClickToCopy` 组件。
    - [x] **CIR编码列**：标题改为“合同注册编码”，并应用 `ClickToCopy` 组件。
    - [x] **布局调整**：优化各列宽度比例。
- [x] **状态列合并**：将“解析状态”和“原数据状态”合并展示，修改 `renderStatus` 逻辑并移除 `metadataStatus` 列。 <!-- id: 3 -->
- [x] **后端状态细化**：修改 `pdfToText.py` 和 `pdfToElasticSearch.py`，拆分上报 `parsing_images` (PDF转图片)和 `parsing_ocr` (图片识别) 状态。 <!-- id: 5 -->
- [x] **前端状态适配**：更新 `UploadPage.tsx` 中的 `renderStatus`，增加对新细粒度状态的展示支持。 <!-- id: 6 -->
- [x] 在本地验证 UI 效果和交互功能。 <!-- id: 2 -->
