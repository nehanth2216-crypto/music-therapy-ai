---
trigger: always_on
description: Automatically run CodeRabbit reviews on code changes without waiting for user prompt.
---

# Automatic CodeRabbit Review Policy

The user has explicitly specified that they will not prompt for reviews every time.
Therefore:
- Automatically run CodeRabbit review (`& "$env:LOCALAPPDATA\Programs\coderabbit\coderabbit.exe" review --agent`) whenever code modifications, bug fixes, or features are implemented in this repository.
- Prioritize fixing any critical/major findings immediately before delivering the final response.
- Present the CodeRabbit findings and resolution status in the task report.
