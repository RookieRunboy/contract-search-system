# 文件重复检测 - 任务清单

## 状态: PROPOSED

---

## Task 1: 后端 - 实现重复检测核心函数

**状态**: [ ] 未开始

### 描述
在 `contractApi.py` 中实现文件重复检测的核心逻辑。

### 子任务
- [ ] 1.1 新增 `_compute_file_hash(content: bytes) -> str` 函数
  - 使用 SHA256 算法
  - 返回格式: `sha256:xxxx...`
- [ ] 1.2 新增 `_check_filename_exists(filename: str) -> Optional[str]` 函数
  - 检查 `uploaded_contracts` 目录是否有同名文件
  - 返回已存在的文件路径或 None
- [ ] 1.3 新增 `_check_content_hash_exists(file_hash: str) -> Optional[str]` 函数
  - 查询 ES 中是否存在相同哈希值的文档
  - 返回匹配的合同名或 None
- [ ] 1.4 新增 `_check_file_duplicates(filename: str, content: bytes) -> Dict` 主函数
  - 依次调用文件名检测和内容哈希检测
  - 返回结构化的检测结果

### 验证标准
```python
# 测试用例
result = _check_file_duplicates("test.pdf", b"content")
assert "is_duplicate" in result
assert "duplicate_type" in result
assert "existing_file" in result
```

---

## Task 2: 后端 - 修改上传流程集成检测

**状态**: [ ] 未开始

### 描述
在 `upload_document()` 函数中集成重复检测逻辑。

### 子任务
- [ ] 2.1 在读取文件内容后，调用 `_check_file_duplicates()`
- [ ] 2.2 检测到重复时，将文件添加到 `rejected_files` 列表
- [ ] 2.3 返回结果中包含 `rejected` 字段，包含被拒绝的文件及原因
- [ ] 2.4 修改返回消息格式，显示通过/重复/失败数量

### 返回格式示例
```json
{
  "code": 200,
  "message": "已加入解析队列 2 个文件，跳过 1 个重复文件",
  "data": {
    "success": [...],
    "failed": [...],
    "rejected": [
      {
        "pdf_name": "重复文件.pdf",
        "reason": "content_duplicate",
        "existing_file": "原文件.pdf"
      }
    ]
  }
}
```

---

## Task 3: 后端 - 存储文件哈希到 ES

**状态**: [ ] 未开始

### 描述
在文件处理成功后，将内容哈希存储到 Elasticsearch。

### 子任务
- [ ] 3.1 修改 `pdfToElasticSearch.py` 中的文档结构
  - 在 `document_metadata` 中添加 `file_hash` 字段
- [ ] 3.2 在 `_process_uploaded_file()` 处理完成后更新哈希值
- [ ] 3.3 确保只在第一页文档中存储哈希值（避免重复）

### 字段位置
```json
{
  "contractName": "xxx",
  "document_metadata": {
    "file_hash": "sha256:abc123...",
    ...其他元数据
  }
}
```

---

## Task 4: 后端 - 历史数据哈希回填脚本

**状态**: [ ] 未开始

### 描述
创建一次性脚本，为已上传的历史文件计算并存储哈希值。

### 子任务
- [ ] 4.1 创建 `tools/backfill_file_hashes.py` 脚本
- [ ] 4.2 遍历 `uploaded_contracts` 目录中的所有 PDF 文件
- [ ] 4.3 计算每个文件的 SHA256 哈希
- [ ] 4.4 更新对应 ES 文档的 `document_metadata.file_hash` 字段
- [ ] 4.5 输出处理进度和统计信息

---

## Task 5: 前端 - 显示重复检测结果

**状态**: [ ] 未开始

### 描述
在上传页面显示重复检测的结果，并提供操作选项。

### 子任务
- [ ] 5.1 修改 `UploadPage.tsx` 解析 API 返回的 `rejected` 字段
- [ ] 5.2 在上传结果中用不同颜色/图标标识：
  - ✅ 成功加入队列
  - ⚠️ 文件名重复
  - ❌ 内容重复
- [ ] 5.3 显示重复原因和原始文件名
- [ ] 5.4 添加 "了解更多" 提示，说明为什么被跳过

### UI 组件
```tsx
// 重复文件提示卡片
<DuplicateFileCard
  fileName="重复文件.pdf"
  reason="content_duplicate"
  existingFile="原文件.pdf"
/>
```

---

## Task 6: 同批次内部重复检测

**状态**: [ ] 未开始

### 描述
检测同一批次上传中是否有重复文件。

### 子任务
- [ ] 6.1 在处理批量文件前，先进行批次内部去重
- [ ] 6.2 检测同批次中是否有：
  - 相同文件名
  - 相同内容（哈希相同）
- [ ] 6.3 保留第一个文件，后续重复文件添加到 `rejected` 列表
- [ ] 6.4 设置重复类型为 `batch_duplicate`

---

## 依赖关系

```
Task 1 (核心函数)
    ↓
Task 2 (集成到上传) ← Task 6 (批次内检测)
    ↓
Task 3 (存储哈希)
    ↓
Task 4 (历史回填) ← Task 5 (前端显示)
```

---

## 完成标准

- [ ] 上传同名文件时，返回重复提示并跳过
- [ ] 上传相同内容（不同文件名）时，返回重复提示并跳过
- [ ] 同批次内重复文件被正确识别
- [ ] 前端正确显示重复原因
- [ ] 历史文件的哈希值已回填完成
