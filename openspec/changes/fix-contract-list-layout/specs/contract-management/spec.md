## ADDED Requirements

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
