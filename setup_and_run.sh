#!/bin/bash

# Bash script to set up virtual environment and run mbox_parser.py
VENV_DIR=".venv"
SCRIPT="mbox_parser.py"

# 1. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Activate virtual environment
source "$VENV_DIR/bin/activate"

# 3. Install dependencies
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing dependencies from requirements.txt ..."
    pip install -r requirements.txt
else
    echo "[WARNING] requirements.txt not found!"
fi

# 4. Run the parser if an argument is provided
if [ -z "$1" ]; then
    echo "[USAGE] Drag and drop or pass a .mbox file as argument:"
    echo "    ./setup_and_run.sh path/to/file.mbox"
    deactivate
    exit 1
fi

echo "[INFO] Running parser ..."
python "$SCRIPT" "$1"

# 5. Deactivate environment
deactivate

echo "[DONE] Processing complete."
