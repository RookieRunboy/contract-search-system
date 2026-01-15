## ADDED Requirements

### Requirement: Batched PDF Image Loading
系统 SHALL 将 PDF 页面分批转换为图片进行 OCR，而非一次性加载全部页面，以降低内存峰值。

配置项：
- 环境变量名：`PDF_BATCH_SIZE`
- 类型：正整数
- 默认值：5
- 有效范围：1 - 20

#### Scenario: 分批加载生效
- **GIVEN** `PDF_BATCH_SIZE=5`（默认值）
- **WHEN** 系统处理一个 20 页的 PDF 文件
- **THEN** 系统分 4 批（每批 5 页）进行图片转换和 OCR
- **AND** 每批处理完成后释放该批次的图片内存
- **AND** 任意时刻内存中最多只有 5 页的图片数据

#### Scenario: 自定义批次大小
- **GIVEN** 环境变量 `PDF_BATCH_SIZE=10`
- **WHEN** 系统启动
- **THEN** 系统按每批 10 页进行处理

#### Scenario: 无效配置回退默认值
- **GIVEN** 环境变量 `PDF_BATCH_SIZE` 设置为非法值（如负数、0 或超过 20）
- **WHEN** 系统启动
- **THEN** 系统使用默认值 5 并打印警告日志

#### Scenario: 批次之间主动垃圾回收
- **WHEN** 一个批次的所有页面处理完成
- **THEN** 系统调用 `gc.collect()` 强制回收该批次的内存
- **AND** 在处理下一批次前确保内存已释放

### Requirement: Concurrent OCR Processing
系统 SHALL 在每个处理批次内部并发调用 OCR 接口，以提升单任务处理速度。

配置项：
- 环境变量名：`OCR_CONCURRENCY`
- 类型：正整数
- 默认值：3

#### Scenario: 页面级并发生效
- **GIVEN** `OCR_CONCURRENCY=3`
- **AND** 当前批次有 5 张待识别图片
- **WHEN** 系统开始处理该批次
- **THEN** 系统同时发起 3 个 OCR API 请求
- **AND** 随着请求返回，后续请求自动填补空位，保持 3 个并发

#### Scenario: 错误独立处理
- **WHEN** 某个页面的并发 OCR 请求失败
- **THEN** 该页面的错误被单独捕获和记录
- **AND** 不影响同批次其他页面的正常识别
