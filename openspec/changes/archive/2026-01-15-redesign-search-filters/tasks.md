# Tasks: 英特尔风格筛选器重构

## Phase 1: 组件基础架构

- [x] **Task 1.1: 创建 FilterBar 组件**
  - **文件**: `frontend/src/components/FilterBar.tsx`
  - **内容**:
    - 创建 `FilterBar` 组件，管理筛选行列表状态
    - 实现 `FilterRowState` 数据结构
    - 导出 `onFiltersChange` 回调，供父组件订阅筛选变化
  - **验证**: 组件可正常渲染，TypeScript 无类型错误 ✓

- [x] **Task 1.2: 创建 FilterRow 组件**
  - **文件**: `frontend/src/components/FilterRow.tsx`
  - **内容**:
    - 创建单行筛选器组件
    - 包含类型选择下拉框、值输入区域、删除按钮
    - Props: `id`, `type`, `value`, `onTypeChange`, `onValueChange`, `onRemove`
  - **验证**: 组件可正常渲染，布局为水平三列 ✓

- [x] **Task 1.3: 实现筛选类型选择下拉框**
  - **文件**: `FilterRow.tsx` 内
  - **内容**:
    - 使用 Ant Design `Select` 组件
    - 选项: 签订日期、合同金额范围、返回结果数量、我方实体、客户分类一级、客户分类二级
    - 深色背景样式（`#1a1a2e`）
  - **验证**: 下拉框可正常展开和选择 ✓

---

## Phase 2: 动态值输入控件

- [x] **Task 2.1: 实现日期筛选值输入**
  - **组件**: `frontend/src/components/filters/DateFilterInput.tsx`
  - **内容**:
    - 两个独立的 `DatePicker` 组件（开始日期、结束日期）
    - 支持只选择单个日期
    - 显示格式: "YYYY-MM-DD → YYYY-MM-DD" 或 "YYYY-MM-DD → ..."
  - **验证**: 可独立选择开始/结束日期 ✓

- [x] **Task 2.2: 实现金额筛选值输入**
  - **组件**: `frontend/src/components/filters/AmountFilterInput.tsx`
  - **内容**:
    - 两个 `InputNumber` 组件（最小金额、最大金额）
    - 支持只填写单个金额
    - 千分位格式化显示
  - **验证**: 可输入金额范围 ✓

- [x] **Task 2.3: 实现实体筛选值输入**
  - **组件**: `frontend/src/components/filters/EntityFilterInput.tsx`
  - **内容**:
    - `Select` 单选下拉框
    - 数据源: `CHINASOFT_ENTITY_NAMES` 常量
  - **验证**: 可选择实体 ✓

- [x] **Task 2.4: 实现分类筛选值输入**
  - **组件**: `frontend/src/components/filters/CategoryFilterInput.tsx`
  - **内容**:
    - `Select` 多选下拉框
    - 一级分类直接加载
    - 二级分类需要依赖一级分类选择后加载
  - **验证**: 可多选分类，二级分类联动正确 ✓

- [x] **Task 2.5: 实现结果数量筛选值输入**
  - **组件**: `frontend/src/components/filters/TopKFilterInput.tsx`
  - **内容**:
    - `InputNumber` 组件，范围 1-99
  - **验证**: 可输入数字 ✓

---

## Phase 3: 集成到搜索页面

- [x] **Task 3.1: 重构 SearchPage 引入 FilterBar**
  - **文件**: `frontend/src/pages/SearchPage.tsx`
  - **内容**:
    - 移除旧版"高级筛选"折叠面板代码
    - 引入 `FilterBar` 组件
    - 将 `FilterBar` 的输出转换为 `SearchFilters` API 参数
  - **验证**: 旧版筛选不再显示，新版筛选可用 ✓

- [x] **Task 3.2: 实现筛选行动态增减**
  - **内容**:
    - 选择类型后自动添加新空行
    - 点击 × 删除指定行
    - 始终保持底部有一个空行
  - **验证**: 可添加多个筛选条件，可删除任意条件 ✓

- [x] **Task 3.3: 实现清除全部功能**
  - **内容**:
    - 添加"清除筛选"按钮
    - 点击后清空所有筛选行，只保留一个空行
  - **验证**: 一键清除所有筛选 ✓

---

## Phase 4: 样式与响应式

- [x] **Task 4.1: 应用英特尔风格样式**
  - **文件**: `frontend/src/components/FilterBar.css`
  - **内容**:
    - 类型下拉框: 深色背景 `#1a1a2e`，白色文字
    - 值输入: 白色背景，灰色边框
    - 删除按钮: 灰色，hover 变红
    - 行间距 8px，列间距 12px
  - **验证**: 视觉效果符合设计稿 ✓

- [x] **Task 4.2: 实现响应式布局**
  - **内容**:
    - Desktop (>768px): 水平排列
    - Mobile (≤768px): 类型和值垂直堆叠
  - **验证**: 在不同屏幕宽度下布局正确 ✓

---

## Phase 5: 测试与验收

- [x] **Task 5.1: 功能测试**
  - 添加/删除筛选条件 ✓
  - 各类型筛选值输入正确 ✓
  - 搜索结果根据筛选条件过滤 ✓

- [x] **Task 5.2: 边界条件测试**
  - 只选择开始日期 / 只选择结束日期 ✓
  - 只填写最小金额 / 只填写最大金额 ✓
  - 二级分类在一级分类未选时禁用 ✓

---


---

## Phase 6: AI 集成与优化 (新增)

- [x] **Task 6.1: FilterBar 支持外部筛选注入**
  - **文件**: `frontend/src/components/FilterBar.tsx`
  - **内容**:
    - 添加 `externalFilters` prop 或 `useImperativeHandle` 方法
    - 实现将外部 `SearchFilters` 对象转换为 `FilterRowState` 的逻辑
    - 标记这些转换为 `isAiGenerated: true`
  - **验证**: 通过 props 注入外部筛选条件并正确转换为 FilterRowState ✓

- [x] **Task 6.2: 搜索页 Smart Search 联动**
  - **文件**: `frontend/src/pages/SearchPage.tsx`
  - **内容**:
    - 在 `handleSmartSearch` 中，不仅触发搜索，还将解析结果传递给 `FilterBar`
    - 确保 `FilterBar` UI 更新以反映 AI 解析出的条件
  - **验证**: 智能搜索后 FilterBar 自动显示 AI 解析的筛选条件 ✓

- [x] **Task 6.3: 实现 AI 筛选器视觉区分**
  - **文件**: `frontend/src/components/FilterRow.tsx`, `FilterBar.css`
  - **内容**:
    - 在 `FilterRow` 中接收 `isAiGenerated` 属性
    - 添加 CSS 样式：紫色边框/光晕效果 (`border: 2px solid #a78bfa`)
    - 确保视觉上与手动添加的行有明显区分
  - **验证**: AI 生成的筛选行显示紫色边框和 "✨ AI" 标签 ✓

- [x] **Task 6.4: 处理 AI 筛选器的用户交互**
  - **文件**: `frontend/src/components/FilterBar.tsx`
  - **内容**:
    - 当用户修改 AI 生成的行时，自动移除 `isAiGenerated` 标记（变为普通行）
    - 确保交互逻辑自然流畅
  - **验证**: 用户编辑 AI 行后，紫色样式消失变为普通行 ✓


完成日期: 2026-01-14

### 创建的文件
1. `frontend/src/components/FilterBar.tsx` - 主筛选器栏组件
2. `frontend/src/components/FilterRow.tsx` - 单行筛选器组件
3. `frontend/src/components/FilterBar.css` - Intel风格样式
4. `frontend/src/components/filters/DateFilterInput.tsx` - 日期筛选输入
5. `frontend/src/components/filters/AmountFilterInput.tsx` - 金额筛选输入
6. `frontend/src/components/filters/EntityFilterInput.tsx` - 实体筛选输入
7. `frontend/src/components/filters/CategoryFilterInput.tsx` - 分类筛选输入
8. `frontend/src/components/filters/TopKFilterInput.tsx` - 结果数量输入

### 修改的文件
1. `frontend/src/pages/SearchPage.tsx` - 移除旧版筛选，集成新FilterBar
2. `frontend/src/services/api.ts` - 添加 `topK` 到 `SearchFilters` 接口

### 构建验证
- TypeScript 编译通过 ✓
- Vite 构建成功 ✓
