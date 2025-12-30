# Tasks: 新增上传任务队列与并发控制

## 1. 后端实现

### 1.1 依赖与配置
- [x] 1.1.1 在 `backend/requirements.txt` 添加 `psutil` 依赖
- [x] 1.1.2 读取环境变量 `UPLOAD_MAX_CONCURRENT` 配置最大并发数（默认 4）
- [x] 1.1.3 读取环境变量 `UPLOAD_MIN_MEMORY_MB` 配置最小可用内存阈值（默认 512 MB）

### 1.2 并发控制
- [x] 1.2.1 在 `contractApi.py` 中创建全局 `asyncio.Semaphore` 实例
- [x] 1.2.2 修改 `_process_uploaded_file` 函数，使用 `async with PROCESSING_SEMAPHORE` 包装处理逻辑

### 1.3 内存监控
- [x] 1.3.1 新增 `get_memory_status()` 函数，使用 psutil 获取系统内存信息
  - 返回：total_mb, available_mb, percent_used, is_low（是否低于阈值）
- [x] 1.3.2 在 `_process_uploaded_file` 中添加内存检查
  - 如果可用内存低于阈值，等待并重试（每 5 秒检查一次，最多等待 5 分钟）
- [x] 1.3.3 添加日志输出，记录内存不足时的等待情况

### 1.4 内存回收（修复内存泄漏）
- [x] 1.4.1 修改 `pdfToText.py` 的 `process_contract` 方法：
  - 每页处理完成后调用 `image.close()` 释放 PIL Image 对象
  - 处理完所有页面后清理 `images` 列表引用
- [x] 1.4.2 在 `_process_uploaded_file` 处理完成后调用 `gc.collect()` 强制垃圾回收
- [x] 1.4.3 定期检查并清理长时间未使用的缓存对象
  - 每 5 分钟自动执行 `gc.collect()`
  - 通过 FastAPI startup/shutdown 事件管理后台任务

### 1.5 队列状态管理
- [x] 1.5.1 在 `UploadStatusManager` 新增 `count_by_status()` 方法，统计各状态的任务数量
- [x] 1.5.2 在 `UploadStatusManager` 新增 `list_pending_uploads(limit)` 方法，获取待处理任务列表

### 1.6 API 接口
- [x] 1.6.1 新增 `GET /upload/queue-status` 接口，返回队列状态和内存信息
  - 返回字段：pending_count, processing_count, max_concurrent, memory_available_mb, memory_percent_used, memory_is_low

## 2. 前端实现

### 2.1 类型定义
- [x] 2.1.1 在 `frontend/src/types/index.ts` 新增 `UploadQueueStatus` 类型（包含内存信息字段）

### 2.2 API 服务
- [x] 2.2.1 在 `frontend/src/services/` 新增获取队列状态的 API 调用函数

### 2.3 UI 组件
- [x] 2.3.1 在 `UploadPage.tsx` 添加队列状态展示区域
- [x] 2.3.2 显示内容：待处理数量、正在处理数量、内存使用百分比
- [x] 2.3.3 当有任务排队时显示友好提示（如"您的文件已加入队列，将按顺序处理"）
- [x] 2.3.4 当内存不足（memory_is_low=true）时显示警告提示

## 3. 配置与文档

### 3.1 环境变量
- [x] 3.1.1 在 `backend/.env.example` 添加配置示例：
  - `UPLOAD_MAX_CONCURRENT=4`
  - `UPLOAD_MIN_MEMORY_MB=512`
