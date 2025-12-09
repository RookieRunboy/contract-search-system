# Change Proposal: Windows stop script and service configs

## Summary
- Add a Windows stop script to terminate the FastAPI backend started by `start_windows.ps1`, optionally stopping the Docker Elasticsearch container.
- Provide Windows service manager examples (NSSM/WinSW) for guarding the backend process in production.

## Motivation
- Current Windows one-click start lacks a paired stop helper and guidance for process supervision, increasing operational friction.

## Scope
- Scripts/docs only; no behavioral change to Linux/macOS tooling.

## Out of Scope
- No changes to existing Linux `start.sh`/`stop.sh`.
- No new packaging or installers.
