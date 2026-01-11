## MODIFIED Requirements
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
