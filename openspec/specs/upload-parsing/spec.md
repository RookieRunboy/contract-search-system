# upload-parsing Specification

## Purpose
TBD - created by archiving change retry-mechanism. Update Purpose after archive.
## Requirements
### Requirement: Granular Parsing Status
The system SHALL classify the document processing into granular stages: Uploaded, Parsing Images, Parsing OCR, Vectorizing, and Extracting Metadata, and record specific failure states for each stage.

#### Scenario: Successful Processing Flow
- **WHEN** a user uploads a PDF
- **THEN** the status transitions sequentially: 'Pending' -> 'Parsing Images' -> 'Parsing OCR' -> 'Vectorizing' -> 'Extracting Metadata' -> 'Completed'

#### Scenario: Failure State Recording
- **WHEN** the OCR process fails
- **THEN** the system records the status as 'failed_ocr' and saves the specific error message

### Requirement: Visual Progress Tracking
The system SHALL provide a visual "subway map" style indicator showing the status of each processing stage, accessible from the document list or details.

#### Scenario: Visual Indication of Progress
- **WHEN** a document is in 'Parsing OCR' stage
- **THEN** the 'Upload' and 'Parsing Images' nodes are marked as completed (green)
- **AND** the 'Parsing OCR' node is marked as in-progress (blue/animating)
- **AND** subsequent nodes are marked as pending (gray)

#### Scenario: Visual Indication of Failure
- **WHEN** a document is in 'failed_ocr' stage
- **THEN** the 'Parsing OCR' node is marked as failed (red)
- **AND** a tooltip on the failed node displays the error message

### Requirement: Retry Mechanism
The system SHALL allow users to retry processing for failed documents, intelligently resuming from the appropriate stage based on the failure type.

#### Scenario: Retry from Metadata Extraction
- **WHEN** a document fails with status 'failed_metadata'
- **AND** the user clicks 'Retry'
- **THEN** the system skips OCR and Vectorization steps
- **AND** immediately attempts to extract metadata again using existing text

#### Scenario: Retry from OCR
- **WHEN** a document fails with status 'failed_ocr'
- **AND** the user clicks 'Retry'
- **THEN** the system restarts the process from the OCR stage (or earlier if necessary)

