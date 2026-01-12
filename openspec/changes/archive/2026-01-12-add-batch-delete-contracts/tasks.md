# 任务列表

## 后端开发
- [x] 在 `backend/contractApi.py` 中定义请求体模型 `BatchDeleteRequest` (包含 `filenames: List[str]`)。 <!-- id: backend-model -->
- [x] 在 `backend/contractApi.py` 中实现 `POST /document/delete/batch` 接口，复用 `delete_by_filename` 逻辑并处理批量结果。 <!-- id: backend-api -->
- [x] 验证后端接口是否能正确删除 ES 索引、本地文件和状态记录。 <!-- id: backend-test -->

## 前端开发
- [x] 在 `frontend/src/services/api.ts` 中添加 `batchDeleteDocuments` 函数。 <!-- id: frontend-api -->
- [x] 修改 `frontend/src/pages/UploadPage.tsx`，添加 `selectedRowKeys` 状态和 `rowSelection` 配置。 <!-- id: frontend-selection -->
- [x] 在 `UploadPage.tsx` 顶部工具栏添加“批量删除”按钮，并实现点击处理逻辑（确认弹窗、调用 API、错误处理）。 <!-- id: frontend-ui -->
- [x] 优化 UI 细节：选中项统计显示、删除时的 Loading 状态、删除后的列表刷新。 <!-- id: frontend-polish -->
