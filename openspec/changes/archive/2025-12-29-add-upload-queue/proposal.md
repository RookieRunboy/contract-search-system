# Change: 新增上传任务队列与并发控制

## Why
当前系统在高并发上传场景下（如同时上传几百个 PDF 文件）存在以下问题：
1. **资源争抢**：所有上传的文件会同时开始处理，竞争 CPU、内存、GPU 资源
2. **VLM API 瓶颈**：视觉模型（qwen3vl）调用有并发限制，大量并行请求可能导致失败
3. **内存压力**：PDF 转图片阶段每页需要几十 MB 内存，并发过多会导致内存不足
4. **内存泄漏**：当前 PDF 处理后，PIL Image 对象未显式释放，导致待机内存持续增长（观察到 ~3GB）
5. **系统不稳定**：上述问题叠加可能导致服务崩溃或响应超时

需要引入任务队列、并发控制和内存回收机制，确保系统在高负载下依然稳定运行。

## What Changes
- **后端**：
  - 使用 `asyncio.Semaphore` 限制同时处理的上传任务数量（默认 4 个）
  - 新增配置项 `UPLOAD_MAX_CONCURRENT` 控制最大并发处理数
  - **新增内存监控机制**：使用 `psutil` 监控系统可用内存
  - **内存保护策略**：当可用内存低于阈值（默认 512MB）时，暂停启动新的处理任务
  - **修复内存泄漏**：
    - 在 `pdfToText.py` 的 `process_contract` 中显式调用 `image.close()` 释放 PIL Image
    - 每个 PDF 处理完成后调用 `gc.collect()` 强制垃圾回收
    - 清理大对象引用，确保内存及时归还给操作系统
  - 优化 `UploadStatusManager`，支持按状态过滤和优先级排序
  - 新增队列状态查询 API `GET /upload/queue-status` 显示当前队列情况和内存状态
- **前端**：
  - 上传页面增加队列状态展示（待处理数量、正在处理数量、内存使用情况）
  - 优化上传状态显示，增加"排队中"状态提示
  - 当内存不足时显示警告提示

## Impact
- Affected specs: `upload-queue`（新增）
- Affected code:
  - `backend/contractApi.py` - 添加 Semaphore 并发控制、内存监控，新增队列状态接口
  - `backend/pdfToText.py` - 修复 PIL Image 内存泄漏，添加显式 close() 和 gc.collect()
  - `backend/upload_status_manager.py` - 新增队列查询方法
  - `backend/requirements.txt` - 新增 `psutil` 依赖
  - `frontend/src/pages/UploadPage.tsx` - 展示队列状态和内存信息

## Design Decisions
1. **选择 Semaphore 而非消息队列**：改动最小，利用现有的 asyncio 异步机制，无需引入 Redis/Celery 等额外依赖
2. **文件上传与处理解耦**：上传接口快速返回，处理在后台排队执行，用户体验不受影响
3. **可配置并发数**：通过环境变量 `UPLOAD_MAX_CONCURRENT` 配置，可根据服务器资源调整（默认值 4，适合 16GB 内存 + 8核 CPU 服务器）
4. **内存保护优先于吞吐量**：宁可处理慢一点，也不能让系统 OOM 崩溃。当可用内存低于阈值时，暂停处理直到内存恢复
5. **使用 psutil 监控**：轻量级跨平台库，可准确获取系统内存状态
6. **主动内存回收**：每个任务处理完成后主动调用 `gc.collect()`，避免 Python 延迟回收导致的内存堆积

