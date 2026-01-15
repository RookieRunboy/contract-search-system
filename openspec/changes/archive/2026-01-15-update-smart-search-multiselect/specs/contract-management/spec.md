## ADDED Requirements

### Requirement: 智能搜索多分类解析
智能搜索解析器 **SHALL** 支持从自然语言查询中提取多个客户分类。

#### Scenario: 查询中包含多个分类
- **WHEN** 用户输入类似“查找国有行、股份制银行和城商行的合同”的查询
- **THEN** 系统识别出“国有行”、“股份制银行”和“城商行”为独立的分类
- **AND** API 响应的 `filters` 对象中 `customer_category_level2` 包含列表：`["国有行", "全国股份制银行", "城商行"]`
- **AND** 前端自动在筛选栏中勾选这些值
