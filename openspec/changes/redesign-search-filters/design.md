# Design: 英特尔风格纵向筛选器列表架构

## User Interface

### 1. 筛选器行 (Filter Row)
每个激活的筛选条件显示为一行，水平排列以下元素：

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────┐    ┌──────────────────────────┐                      │
│  │ 选择筛选器    ▼ │    │ 选择值              ▼ │       ✕              │
│  └──────────────────┘    └──────────────────────────┘                      │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────────────┐                      │
│  │ 签订日期      ▼ │    │ 2023-01-01 → 2023-12-31 │       ✕              │
│  └──────────────────┘    └──────────────────────────┘                      │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────────────┐                      │
│  │ 我方实体      ▼ │    │ 中软国际科技服务有限公司 │       ✕              │
│  └──────────────────┘    └──────────────────────────┘                      │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────────────┐                      │
│  │ 选择筛选器    ▼ │    │                       ▼ │                      │
│  └──────────────────┘    └──────────────────────────┘                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2. 筛选器类型下拉框 (Filter Type Selector)
第一个下拉框，用于选择筛选的维度。

- **外观**：深色背景（如 `#1a1a2e`），白色文字，宽度固定（约 180px）
- **提示文字**：未选中时显示"选择筛选器"
- **选项**：
  - 签订日期
  - 合同金额范围
  - 我方实体
  - 客户分类（一级）
  - 客户分类（二级）
  - 返回结果数量

### 3. 筛选器值输入控件 (Filter Value Input)
第二个下拉框/输入控件，根据所选类型动态变化。

| 筛选类型       | 值输入控件                                       |
| -------------- | ------------------------------------------------ |
| 签订日期       | 两个独立的 DatePicker（开始日期、结束日期）       |
| 合同金额范围   | 两个 InputNumber（最小金额、最大金额）            |
| 我方实体       | Select 单选下拉框                                |
| 客户分类（一级）| Select 下拉框（支持多选）                        |
| 客户分类（二级）| Select 下拉框（支持多选，依赖一级分类）          |
| 返回结果数量   | InputNumber（1-99）                              |

- **外观**：白色背景，深色边框，宽度弹性扩展

### 4. 删除按钮 (Remove Button)
每行右侧的 × 图标按钮。

- **外观**：`×` 符号，hover 时变为红色
- **交互**：点击删除该行筛选条件

### 5. 空行 (Empty Row)
底部始终保留一行空的筛选器选择器，方便用户添加新条件。

- **初始状态**：Type 下拉框显示"选择筛选器"，Value 下拉框禁用
- **选择类型后**：Type 锁定，Value 下拉框激活

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                          搜索框                                     │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ ▼ 高级筛选                                                          │
├─────────────────────────────────────────────────────────────────────┤
│  (Row 1) [Type Selector ▼] [Value Input          ▼]  ✕             │
│  (Row 2) [Type Selector ▼] [Value Input          ▼]  ✕             │
│  ...                                                                │
│  (Empty Row) [选择筛选器 ▼] [                    ▼]                 │
├─────────────────────────────────────────────────────────────────────┤
│                                              [清除筛选]             │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Model

### Filter Row State
每一行筛选器的状态：

```typescript
type FilterType = 'date' | 'amount' | 'entity' | 'categoryL1' | 'categoryL2' | 'topK';

interface FilterRowState {
  id: string;                    // 唯一标识（uuid）
  type: FilterType | null;       // 筛选类型，null 表示未选择
  value: FilterValue;            // 筛选值
  isAiGenerated?: boolean;       // 是否为AI生成的筛选条件
}

type FilterValue =
  | { dateStart?: string; dateEnd?: string }    // 日期范围
  | { min?: number; max?: number }              // 金额范围
  | string                                      // 单选值
  | string[]                                    // 多选值
  | number;                                     // 数字值
```

### Filter Bar State
整个筛选器栏的状态：

```typescript
interface FilterBarState {
  rows: FilterRowState[];        // 所有筛选行
}
```

## Component Structure

```
SearchPage.tsx
└── FilterBar.tsx (新组件)
    ├── FilterRow.tsx (每一行)
    │   ├── FilterTypeSelector (类型下拉框)
    │   ├── FilterValueInput (值输入控件 - 根据类型动态渲染)
    │   └── RemoveButton (删除按钮)
    └── ClearAllButton (清除全部按钮)
```

## Styling Guidelines

### Color Palette
- **Row Background**: `rgba(255, 255, 255, 0.6)` (Semi-transparent white) with `backdrop-filter: blur(8px)`
- **Type Selector**:
    - Background: `#ffffff` (White)
    - Border: `1px solid rgba(102, 126, 234, 0.2)`
    - Text: `#1f2937` (Dark Gray)
- **Value Input**:
    - Background: `#ffffff` (White)
    - Border: `1px solid rgba(102, 126, 234, 0.2)`
- **Remove Button**: `#9ca3af` (Gray), hover `#ef4444` (Red)
- **Active Accents**: `#667eea` (Primary Purple/Blue) for focus states and borders
- **AI Generated Highlight**:
    - Border: `2px solid #a78bfa` (Light Purple) or Gradient Border
    - Box Shadow: `0 0 8px rgba(167, 139, 250, 0.4)`


### Spacing
- **Row Gap**: `8px`
- **Column Gap (between Type and Value)**: `12px`
- **Padding**: `12px 16px`

### Responsive Behavior
- **Desktop**: Type selector 180px, Value input 弹性扩展
- **Mobile**: Type selector 和 Value input 各占 100%，垂直堆叠
