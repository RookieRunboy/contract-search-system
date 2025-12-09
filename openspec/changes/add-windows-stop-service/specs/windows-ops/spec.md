## ADDED Requirements

### Requirement: The Windows stop helper SHALL terminate the backend started by `start_windows.ps1` and MAY stop the Docker Elasticsearch container on request.
The stop helper SHALL read `logs/backend.pid`, stop the referenced backend process, clean the PID file, and MAY stop the Docker `es` container when explicitly requested.
#### Scenario: stop backend by PID
- Given `logs/backend.pid` exists and contains a running backend PID
- When `stop_windows.ps1` runs with default options
- Then the process is terminated and the PID file is removed or updated without throwing an error
#### Scenario: missing or stale PID
- Given `logs/backend.pid` is missing or points to a non-existent process
- When `stop_windows.ps1` runs
- Then the script reports the condition and exits without a crash
#### Scenario: optional Elasticsearch stop
- Given the Docker container named `es` is running
- When `stop_windows.ps1 -StopElasticsearch` runs
- Then the `es` container is stopped gracefully; if the container is absent, the script reports and continues

### Requirement: Windows service supervision guidance SHALL include NSSM and WinSW examples for running the backend with auto-restart semantics.
The documentation SHALL provide copy-pasteable NSSM commands and a WinSW XML template that start the backend (`uvicorn contractApi:app`), define working directories, log paths, and restart behavior.
#### Scenario: NSSM service example
- Given a Windows operator needs backend auto-restart/boot start
- When they follow the documented NSSM commands
- Then a service runs `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --workers N` with restart on failure and log redirection paths defined
#### Scenario: WinSW service example
- Given WinSW is preferred
- When the operator copies the provided XML template and adjusts paths
- Then a Windows service is created that starts the backend with restart and log settings matching the documentation
