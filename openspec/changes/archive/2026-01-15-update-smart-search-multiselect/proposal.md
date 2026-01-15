# 变更: 更新智能搜索支持多选分类

## 为什么 (Why)
目前的智能搜索仅支持选择单一客户分类。用户经常需要同时搜索多个分类（例如“国有银行 和 股份制银行”）。当前的限制迫使系统将其泛化为更广泛的父级分类或仅依赖关键词，降低了搜索精度。

## 变更内容 (What Changes)
- **后端 (`smart_query_parser.py`)**: 
    - 更新 LLM 提示词 (Prompt)，要求 `customer_category_level1` 和 `customer_category_level2` 返回字符串列表，而不是单个字符串/null。
    - 更新解析逻辑以处理 JSON 数组验证。
- **前端 (`api.ts`, `SearchPage.tsx`)**:
    - 更新 `SmartParseResult` 接口以支持 `string[]` 类型的分类字段。
    - 更新 `convertSmartFilters` 逻辑，将数组直接映射到 `SearchFilters`。

## 影响 (Impact)
- **受影响的 Spec**: `search`
- **受影响的代码**: 
    - `backend/smart_query_parser.py`
    - `frontend/src/services/api.ts`
    - `frontend/src/pages/SearchPage.tsx`
