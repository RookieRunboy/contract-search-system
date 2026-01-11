# 变更：改进文件名编码提取逻辑

## Why
用户反馈，当文件名包含较多连字符或编码不在文件开头时，合同编码和 CIR 编码无法完整提取。当前的逻辑限制为仅检查文件名的前两个片段，导致对于复杂命名规则的文件提取失败。

## What Changes
- 更新 `backend/contractApi.py` 和 `backend/update_existing_codes.py` 中的文件名为解析逻辑。
- 移除对于连字符分隔文件名仅检查前 2 个片段的限制；改为扫描所有片段。
- 确保提取逻辑在找到所有部分（或扫描完所有部分）后才停止，允许编码位于文件名的任意位置。
- 更新说明文档 `specs/contract-management/spec.md`，正式包含连字符分隔模式以及灵活位置提取的需求。

## Impact (影响)
- 涉及规格: `contract-management`
- 涉及代码:
  - `backend/contractApi.py`
  - `backend/update_existing_codes.py`
