# Design Notes

- Keep parity with the Windows start helper: read the PID emitted by `start_windows.ps1`, stop that process, and optionally stop the `es` Docker container to avoid orphaned services.
- Avoid Linux/macOS impact by keeping new scripts/docs Windows-only and self-contained.
- Service supervision examples rely on existing tooling (NSSM/WinSW) rather than introducing new dependencies or code changes.
