#!/bin/bash

echo "==== 1. GIT STATUS ===="
git status
echo
echo "==== 2. GIT LOG (last commit) ===="
git log -1
echo
echo "==== 3. GIT DIFF (uncommitted changes) ===="
git diff
echo
echo "==== 4. GIT BRANCH ===="
git branch
echo

echo "==== 5. PYTHON VERSION ===="
python3 --version
echo
echo "==== 6. PIP FREEZE ===="
pip freeze
echo

echo "==== 7. ENVIRONMENT VARIABLES (.env) ===="
if [ -f .env ]; then
    sed 's/.*key.*/[REDACTED]/I' .env
else
    echo ".env file not found in current directory."
fi
echo

echo "==== 8. APP LOG (last 100 lines) ===="
if [ -f app_output.log ]; then
    tail -n 100 app_output.log
else
    echo "app_output.log not found."
fi
echo

echo "==== 9. TOOL REGISTRATION (Python) ===="
python3 -c "from backend.tools.registry import get_tools; print('Registered tools:', [t['function']['name'] for t in get_tools()])"
echo

echo "==== 10. OS AND SHELL ===="
uname -a
echo "Default shell: $SHELL"
echo

echo "==== 11. USER CONFIG (~/.smartscreen_config.json) ===="
if [ -f ~/.smartscreen_config.json ]; then
    sed 's/.*key.*/[REDACTED]/I' ~/.smartscreen_config.json
else
    echo "~/.smartscreen_config.json not found."
fi
echo

echo "==== 12. CHECK FOR LOCAL FRONTEND/LOGIC/CONFIG FILES ===="
find frontend/logic/ -type f -name "*.py" -exec ls -lh {} \;
echo

echo "==== 13. CHECK FOR LOCAL BACKEND/TOOLS/CONFIG FILES ===="
find backend/tools/ -type f -name "*.py" -exec ls -lh {} \;
echo

echo "==== DONE ===="