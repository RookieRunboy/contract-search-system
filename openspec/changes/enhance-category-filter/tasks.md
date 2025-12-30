# 增强客户分类筛选器 - 任务清单

## 依赖关系
- 无外部依赖
- 任务 1-3 可并行执行
- 任务 4 依赖任务 1-3 完成

---

## 任务列表

### 任务 1: 创建层级式客户分类选择组件
**文件**: `frontend/src/components/filters/HierarchicalCategoryFilter.tsx`

**描述**:
创建新的 `HierarchicalCategoryFilter` 组件，在单行内结合一级分类单选下拉框和二级分类多选下拉框。

**验收标准**:
- [x] 组件接收 `categoryHierarchy` prop（一级到二级的映射）
- [x] 组件输出包含 `level1` (string) 和 `level2` (string[]) 的值对象
- [x] 一级下拉框为单选，选择后更新二级下拉框选项
- [x] 二级下拉框支持多选
- [x] 二级下拉框在一级选择后默认显示"全部"占位文本
- [x] 未选一级时，二级下拉框禁用
- [x] 支持清除操作

**估时**: 2 小时

---

### 任务 2: 定义新的筛选器类型结构
**文件**: `frontend/src/components/FilterBar.tsx`

**描述**:
更新 FilterBar 类型定义，将 `categoryL1` 和 `categoryL2` 替换为统一的 `category` 类型。

**具体改动**:
1. 修改 `FilterType` 类型，移除 `categoryL1` 和 `categoryL2`，新增 `category`
2. 新增 `CategoryFilterValue` 接口：
   ```typescript
   interface CategoryFilterValue {
     level1?: string;
     level2?: string[];
   }
   ```
3. 更新 `FilterValue` 联合类型包含 `CategoryFilterValue`
4. 修改 `convertToFilters` 函数以正确处理新的 `category` 类型值

**验收标准**:
- [x] 类型编译无错误
- [x] `category` 类型允许多行（不在 usedTypes 中排除）
- [x] 多行 `category` 的值能正确合并为 API 参数

**估时**: 1.5 小时

---

### 任务 3: 更新 FilterRow 组件
**文件**: `frontend/src/components/FilterRow.tsx`

**描述**:
更新 FilterRow 组件以支持新的 `category` 筛选器类型。

**具体改动**:
1. 更新 `FILTER_TYPE_OPTIONS`，将两个客户分类选项合并为一个"客户分类"
2. 在 `renderValueInput` 中新增 `category` case，渲染 `HierarchicalCategoryFilter`
3. 移除 `level2Options` 和 `level2Disabled` props（不再需要外部传递）

**验收标准**:
- [x] 筛选器类型下拉框显示"客户分类"选项
- [x] 选择"客户分类"后显示层级选择组件
- [x] 可添加多个"客户分类"筛选行

**估时**: 1 小时

---

### 任务 4: 集成与验证
**文件**: 多个

**描述**:
集成所有组件，进行功能验证。

**验证步骤**:
1. 启动开发环境：`npm run dev --prefix frontend`
2. 访问搜索页面
3. 测试以下场景：
   - 添加一个客户分类筛选器，选择一级分类，验证二级选项更新
   - 在二级分类中多选几个选项
   - 添加第二个客户分类筛选器，选择不同一级分类
   - 执行搜索，验证筛选结果正确
   - 验证清除筛选功能

**验收标准**:
- [x] 无控制台错误
- [x] 多个一级分类筛选正确合并
- [x] 二级分类多选正确传递给 API
- [x] UI 交互流畅无明显延迟

**估时**: 1 小时

---

## 总估时
约 **5.5 小时**
