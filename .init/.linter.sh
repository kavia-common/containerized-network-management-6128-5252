#!/bin/bash
cd /home/kavia/workspace/code-generation/containerized-network-management-6128-5252/BackendApplication
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

