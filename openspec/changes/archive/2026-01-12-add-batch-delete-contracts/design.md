# 批量删除设计文档

## 架构设计

### 前端设计
1.  **交互变更**：
    *   在 `UploadPage` 的 `Table` 组件中开启 `rowSelection`。
    *   绑定 `selectedRowKeys` 状态以追踪选中的合同。
    *   在表格上方（或工具栏区域）新增一个“批量删除”按钮。
    *   该按钮仅在 `selectedRowKeys.length > 0` 时可用（或高亮显示）。
    *   点击按钮后弹出 `Popconfirm` 或 `Modal` 确认框，提示“确定删除选中的 N 个合同吗？”。

2.  **API 调用**：
    *   在 `frontend/src/services/api.ts` 中新增 `batchDeleteDocuments(filenames: string[])` 方法。
    *   调用后端新增的 POST `/document/delete/batch` 接口。

3.  **状态反馈**：
    *   删除过程中显示 loading 状态。
    *   删除完成后，根据返回结果显示成功/失败的消息（例如：“成功删除 5 个，失败 0 个”）。
    *   刷新合同列表并清空选中状态。

### 后端设计
1.  **API 接口**：
    *   新增 `POST /document/delete/batch`。
    *   请求体：`{ filenames: List[str] }`。
    *   权限：`require_admin`。

2.  **处理逻辑**：
    *   接收文件名列表。
    *   遍历列表，复用现有的 `es_deleter.delete_by_filename` 逻辑。
    *   同步清理 `UploadStatusManager` 中的状态记录。
    *   收集每个文件的删除结果（成功/失败）。

3.  **响应格式**：
    *   返回包含成功列表、失败列表及统计信息的 JSON 响应。

## 接口定义

### Request
```http
POST /document/delete/batch
Content-Type: application/json
Authorization: Bearer ...

{
  "filenames": ["contract1.pdf", "contract2.pdf"]
}
```

### Response
```json
{
  "code": 200,
  "message": "批量删除完成",
  "data": {
    "success": ["contract1.pdf"],
    "failed": [
      {
        "filename": "contract2.pdf",
        "error": "File not found"
      }
    ],
    "total": 2,
    "success_count": 1,
    "failed_count": 1
  }
}
```
