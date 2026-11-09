# Virtual Environment Enforcement

1. Activate the venv before any CLI command:
   - Windows: `venv\Scripts\activate` (Git Bash, the Claude Code shell: `source venv/Scripts/activate`)
   - Linux/Mac: `source venv/bin/activate`
2. If the venv is missing or broken, recreate it immediately:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. STOP all work if the venv cannot be activated.
4. Never `pip install` without a venv active.
