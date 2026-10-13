# Automated CodeRabbit Reviews

Whenever you write, modify, or refactor code in this workspace:
1. **Automatic Review**: Do NOT wait for the user to ask for a code review. Run a CodeRabbit review automatically after completing code changes using:
   ```powershell
   & "$env:LOCALAPPDATA\Programs\coderabbit\coderabbit.exe" review --agent
   ```
2. **Autonomous Fix & Verification**:
   - Inspect findings emitted by the review.
   - Address any critical or major issues, bug risks, or security vulnerabilities within the scope of changes.
   - Re-verify if needed (respecting review limits, at most 2-3 reviews per change set).
3. **Report Results**:
   - Provide a clear summary of the CodeRabbit review outcome (issues found, fixes applied, or clean status) with every code change deliverable.
