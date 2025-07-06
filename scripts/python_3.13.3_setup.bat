#!/bin/bash
# Translation Cost Calculator - Python 3.13.3 Setup

echo "🐍 Setting up Translation Cost Calculator for Python 3.13.3"
echo "================================================================"

# Check Python version
python --version

# Install core dependencies for Python 3.13
echo "📦 Installing Python 3.13 compatible packages..."

# Install PySide6 latest (supports Python 3.13)
pip install PySide6>=6.8.1

# Install data processing libraries
pip install pandas>=2.1.0
pip install openpyxl>=3.1.0

# Install PDF generation
pip install reportlab>=4.0.0

# Install utilities
pip install python-dateutil>=2.8.0
pip install charset-normalizer>=3.0.0

# Optional development tools
pip install pytest>=7.0.0
pip install black>=23.0.0

echo "✅ Installation complete!"
echo ""
echo "🧪 Testing imports..."

# Test critical imports
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import PySide6
    print(f'✅ PySide6 {PySide6.__version__}')
except ImportError as e:
    print(f'❌ PySide6: {e}')

try:
    import sqlite3
    print(f'✅ sqlite3 {sqlite3.sqlite_version} (built-in)')
except ImportError as e:
    print(f'❌ sqlite3: {e}')

try:
    import pandas as pd
    print(f'✅ pandas {pd.__version__}')
except ImportError as e:
    print(f'❌ pandas: {e}')

try:
    import decimal, dataclasses, pathlib, typing
    print('✅ Built-in modules: decimal, dataclasses, pathlib, typing')
except ImportError as e:
    print(f'❌ Built-in modules: {e}')
"

echo ""
echo "🚀 Ready to run Translation Cost Calculator!"
echo "Next steps:"
echo "1. Rename .txt files to .csv"
echo "2. python startup_verification.py"
echo "3. python main.py"