# contract-management Specification

## Purpose
TBD - created by archiving change extract-contract-codes. Update Purpose after archive.
## Requirements
### Requirement: Filename Code Extraction
系统 **MUST** 能够从上传的文件名中提取"合同编码"和"CIR编码"，无论这些编码位于文件名的哪个位置。

#### Scenario: 模式 1 - 包含两个编码（带方括号）
- **WHEN** 文件名格式为 `[Code1]-[Code2]Name.pdf`
- **THEN** 如果 Code1 以 "CIR" 开头（不区分大小写），则识别为 CIR编码；否则识别为 合同编码。
- **AND** 如果 Code2 以 "CIR" 开头（不区分大小写），则识别为 CIR编码；否则识别为 合同编码。

#### Scenario: 模式 2 - 仅含合同编码（带方括号）
- **WHEN** 文件名格式为 `[Code]Name.pdf`
- **AND** 提取的 `Code` 不是以 "CIR" 开头（不区分大小写）
- **THEN** 系统将 `Code` 识别为 合同编码，CIR编码为空。

#### Scenario: 模式 3 - 仅含 CIR 编码（带方括号）
- **WHEN** 文件名格式为 `[Code]Name.pdf`
- **AND** 提取的 `Code` 是以 "CIR" 开头（不区分大小写）
- **THEN** 系统将 `Code` 识别为 CIR编码，合同编码为空。

#### Scenario: 模式 4 - 连字符分隔（位置灵活）
- **WHEN** 文件名由多个用连字符分隔的片段组成（例如 `Prefix-Code1-Code2-Name.pdf`）
- **THEN** 系统解析所有片段以识别编码。
- **AND** **第一个**匹配 `^[A-Za-z]\d+$` 正则的片段（排除 CIR 格式）被识别为 合同编码。
- **AND** **第一个**匹配 `^CIR\d+$` 正则的片段（不区分大小写）被识别为 CIR编码。
- **AND** 如果存在多个符合格式的合同编码，忽略后续匹配（视为文件名的一部分）。
- **AND** 如果存在多个符合格式的 CIR 编码，忽略后续匹配。

#### Scenario: 模式 5 - 无编码
- **WHEN** 文件名中不包含任何匹配编码模式的片段
- **THEN** 合同编码和 CIR编码 均为空。

### Requirement: Contract List Columns
The upload list/contract list SHALL display the extracted Contract Code and CIR Code.

#### Scenario: Display Codes
- **WHEN** the user views the contract list
- **THEN** two new columns "合同编码" and "CIR编码" are visible, populating data from the extracted metadata.

### Requirement: 层级式客户分类筛选
系统 **SHALL** 提供层级式客户分类筛选器，在单个筛选行内同时支持一级分类选择和对应二级分类的多选。

#### Scenario: 单一级分类筛选
- **GIVEN** 用户在搜索页面添加"客户分类"筛选器
- **WHEN** 用户在一级分类下拉框中选择一个分类（如"政府"）
- **THEN** 二级分类下拉框变为可用状态
- **AND** 二级分类选项更新为该一级分类下的所有二级分类
- **AND** 二级分类默认未选中任何具体项（表示"全部"）
- **AND** 搜索结果包含该一级分类下所有二级分类的合同

#### Scenario: 二级分类多选
- **GIVEN** 用户已选择一级分类（如"企业"）
- **WHEN** 用户在二级分类下拉框中多选具体分类（如"央企"、"国企"）
- **THEN** 搜索结果仅包含同时满足一级分类"企业"且二级分类为"央企"或"国企"的合同

#### Scenario: 多一级分类筛选
- **GIVEN** 用户已添加一个"客户分类"筛选器并选择了一级分类"政府"
- **WHEN** 用户再次添加"客户分类"筛选器并选择一级分类"企业"
- **THEN** 搜索结果包含一级分类为"政府"或"企业"的合同
- **AND** 各筛选器的二级分类选择独立生效

#### Scenario: 二级分类全选行为
- **GIVEN** 用户选择一级分类"政府"
- **WHEN** 用户未在二级分类下拉框中选择任何具体项
- **THEN** 系统视为选择该一级分类下的全部二级分类
- **AND** API 调用中 `customer_category_level1` 包含 "政府"
- **AND** API 调用中 `customer_category_level2` 不包含该一级分类相关的值（或包含所有二级分类）

#### Scenario: 清除筛选
- **GIVEN** 用户已添加客户分类筛选器并做了选择
- **WHEN** 用户点击筛选行的删除按钮或整体清除
- **THEN** 该筛选条件从搜索查询中移除
- **AND** 搜索结果不再受该筛选条件限制

### Requirement: 批量删除合同
The system SHALL provide a batch delete function to allow users to remove multiple contracts at once.

#### Scenario: 批量删除选中合同
- **GIVEN** 用户在合同列表页面
- **WHEN** 用户勾选多个合同（例如 "A.pdf" 和 "B.pdf"）
- **AND** 用户点击“批量删除”按钮
- **AND** 用户在确认弹窗中点击“确定”
- **THEN** 前端向后端发送批量删除请求
- **AND** 列表刷新，被选中的合同从列表中消失
- **AND** 系统提示删除成功信息

### Requirement: Contract List Responsive Layout
The contract list table SHALL provide a responsive layout that ensures readability on both laptop and desktop screens.

#### Scenario: Laptop Screen Display
- **WHEN** the user views the contract list on a laptop screen (width < 1200px)
- **THEN** the table SHALL enable horizontal scrolling
- **AND** the "合同名称" (Contract Name) column SHALL maintain a minimum width of 200px
- **AND** all column content SHALL remain readable without excessive compression

#### Scenario: Desktop Screen Display
- **WHEN** the user views the contract list on a desktop screen (width >= 1200px)
- **THEN** the table SHALL display all columns without horizontal scrolling if screen space permits
- **AND** the "合同名称" column SHALL expand to fill available space

#### Scenario: Contract Name Wrapping
- **WHEN** a contract name is too long to fit in a single row
- **THEN** the text SHALL wrap naturally to multiple lines
- **AND** each line SHALL display at least 10 characters (not 2-3 characters per line)

### Requirement: 智能搜索多分类解析
智能搜索解析器 **SHALL** 支持从自然语言查询中提取多个客户分类。

#### Scenario: 查询中包含多个分类
- **WHEN** 用户输入类似“查找国有行、股份制银行和城商行的合同”的查询
- **THEN** 系统识别出“国有行”、“股份制银行”和“城商行”为独立的分类
- **AND** API 响应的 `filters` 对象中 `customer_category_level2` 包含列表：`["国有行", "全国股份制银行", "城商行"]`
- **AND** 前端自动在筛选栏中勾选这些值

