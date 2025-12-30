# Spec: 英特尔风格纵向筛选器 (Filter UI)

## MODIFIED Requirements

### Requirement: Remove Legacy Advanced Filter Panel
The system SHALL remove the current "Advanced Filter" panel and its toggle button based on `Collapse` component or hidden form.
- **Scope**: Frontend Only (`SearchPage.tsx`)

#### Scenario: Verify Removal
- **WHEN** 用户访问搜索页面
- **THEN** 旧版的"高级筛选"折叠面板（灰色背景、6列网格布局）不再显示
- **AND** 使用新的纵向筛选器列表替代

---

### Requirement: Filter Bar with Vertical Row Layout
The system SHALL introduce a new "Filter Bar" component (`FilterBar`) below the search box. Filters SHALL be displayed as **vertically stacked rows**, NOT horizontal chips.

#### Scenario: Initial State
- **WHEN** 页面初次加载
- **THEN** 筛选栏部分显示入口按钮"高级筛选"
- **WHEN** 用户点击"高级筛选"按钮
- **THEN** 展开筛选器区域
- **AND** 显示一个空的筛选器行（选择筛选器 ▼）

#### Scenario: Filter Row Structure
- **GIVEN** 筛选器区域已展开
- **THEN** 每一行筛选条件包含以下元素（从左到右）：
  1. **类型下拉框**：显示当前选中的筛选维度（或"选择筛选器"占位符）
  2. **值输入控件**：根据类型动态变化的输入组件
  3. **删除按钮**：× 图标，点击删除该行

---

### Requirement: Add Filter via Type Selection
The system SHALL allow users to add new filter dimensions by selecting from the Type dropdown.

#### Scenario: Select Filter Type
- **WHEN** 用户在空行的"选择筛选器"下拉框中选择一个类型（如"签订日期"）
- **THEN** 该行的类型下拉框显示选中的类型
- **AND** 该行的值输入控件变为对应类型的输入组件（如日期选择器）
- **AND** 筛选器区域底部自动新增一个空行

#### Scenario: Filter Type Options
- **WHEN** 用户打开"选择筛选器"下拉菜单
- **THEN** 显示以下选项：
  - 签订日期
  - 合同金额范围
  - 返回结果数量
  - 我方实体
  - 客户分类（一级）
  - 客户分类（二级）

---

### Requirement: Dynamic Value Input Based on Filter Type
The system SHALL render different input controls based on the selected filter type.

#### Scenario: Date Filter Value Input
- **WHEN** 用户选择"签订日期"类型
- **THEN** 值区域显示 **两个独立的日期选择器**（开始日期、结束日期）
- **AND** 用户可以只选择开始日期、只选择结束日期、或两者都选
- **AND** 显示格式为"YYYY-MM-DD → YYYY-MM-DD"（如只选一个则另一端显示"..."）

#### Scenario: Amount Filter Value Input
- **WHEN** 用户选择"合同金额范围"类型
- **THEN** 值区域显示 **两个数字输入框**（最小金额、最大金额）
- **AND** 用户可以只填最小值、只填最大值、或两者都填

#### Scenario: Entity Filter Value Input
- **WHEN** 用户选择"我方实体"类型
- **THEN** 值区域显示 **单选下拉框**
- **AND** 选项为预定义的中软实体名称列表

#### Scenario: Category Filter Value Input
- **WHEN** 用户选择"客户分类（一级）"或"客户分类（二级）"类型
- **THEN** 值区域显示 **可多选的下拉框**
- **AND** 如果是二级分类，需要先选择一级分类才能加载选项

#### Scenario: TopK Filter Value Input
- **WHEN** 用户选择"返回结果数量"类型
- **THEN** 值区域显示 **数字输入框**（范围 1-99）

---

### Requirement: Remove Single Filter Row
The system SHALL allow users to remove a specific filter condition by clicking the × button.

#### Scenario: Remove Filter
- **WHEN** 用户点击某一行右侧的 × 按钮
- **THEN** 该行从筛选器列表中移除
- **AND** 对应的筛选条件重置（不参与后续搜索过滤）

---

### Requirement: Clear All Filters
The system SHALL provide a "Clear All" button to reset all filter conditions at once.

#### Scenario: Clear All
- **WHEN** 用户点击"清除筛选"按钮
- **THEN** 所有筛选行被移除
- **AND** 只剩下一行空的选择器

---

### Requirement: Independent Date Selection
The system SHALL allow users to select start and end dates independently. The user SHALL NOT be forced to select both dates.

#### Scenario: Select Start Date Only
- **WHEN** 用户在"签订日期"筛选器中只设定了"开始日期"
- **THEN** 系统应执行"大于等于开始日期"的搜索

#### Scenario: Select End Date Only
- **WHEN** 用户在"签订日期"筛选器中只设定了"结束日期"
- **THEN** 系统应执行"小于等于结束日期"的搜索

#### Scenario: Select Both Dates
- **WHEN** 用户设定了两个日期
- **THEN** 系统应执行"日期范围"搜索

---

### Requirement: Real-time Filter Application
The system SHALL apply filters immediately when values change (no explicit "Apply" button needed).

#### Scenario: Auto-trigger Search
- **WHEN** 用户修改任意筛选器的值（选择日期、输入金额等）
- **THEN** 系统自动更新搜索结果（可添加防抖延迟 300-500ms）

---

### Requirement: Responsive Layout
The Filter Bar UI SHALL be responsive and usable on different screen sizes.

#### Scenario: Desktop Layout
- **WHEN** 在宽屏设备上（>768px）
- **THEN** 每行水平排列：类型下拉框（固定宽度）+ 值输入控件（弹性宽度）+ 删除按钮

#### Scenario: Mobile Layout
- **WHEN** 在窄屏设备上（≤768px）
- **THEN** 类型下拉框和值输入控件垂直堆叠
- **AND** 删除按钮位于行右上角

---

### Requirement: Visual Styling
The Filter Bar SHALL follow the Intel-style dark theme for type selectors.

#### Scenario: Type Selector Styling
- **THEN** 类型下拉框使用深色背景（如 `#1a1a2e`）、白色文字
- **AND** hover 时显示蓝色边框高亮

#### Scenario: Value Input Styling
- **THEN** 值输入控件使用白色背景、灰色边框
- **AND** focus 时显示蓝色边框

#### Scenario: Remove Button Styling
- **THEN** × 按钮默认灰色
- **AND** hover 时变为红色
