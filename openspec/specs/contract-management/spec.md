# contract-management Specification

## Purpose
TBD - created by archiving change extract-contract-codes. Update Purpose after archive.
## Requirements
### Requirement: Filename Code Extraction
The system SHALL extract Contract Code and CIR Code from the uploaded filename based on specific patterns.

#### Scenario: Pattern 1 - Both Codes
- **WHEN** the filename is formatted as `[Code1]-[Code2]Name.pdf`
- **THEN** if Code1 starts with "CIR" (case-insensitive), it is the CIR Code; otherwise, Code1 is the Contract Code.
- **AND** if Code2 starts with "CIR" (case-insensitive), it is the CIR Code; otherwise, Code2 is the Contract Code.

#### Scenario: Pattern 2 - Contract Code Only
- **WHEN** the filename is formatted as `[Code]Name.pdf`
- **AND** the extracted `Code` does NOT start with "CIR" (case-insensitive)
- **THEN** the system extracts ContractCode as `Code` and CIRCode is empty.

#### Scenario: Pattern 3 - CIR Code Only
- **WHEN** the filename is formatted as `[Code]Name.pdf`
- **AND** the extracted `Code` STARTS WITH "CIR" (case-insensitive)
- **THEN** the system extracts CIRCode as `Code` and ContractCode is empty.

#### Scenario: Pattern 4 - No Codes
- **WHEN** the filename generally contains no recognizable code pattern
- **THEN** both ContractCode and CIRCode are empty.

### Requirement: Contract List Columns
The upload list/contract list SHALL display the extracted Contract Code and CIR Code.

#### Scenario: Display Codes
- **WHEN** the user views the contract list
- **THEN** two new columns "合同编码" and "CIR编码" are visible, populating data from the extracted metadata.

