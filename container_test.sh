#!/bin/bash
# Container Import Diagnostic Script
# Run this inside the container to diagnose import issues

echo "=================================================="
echo "Container Import Diagnostic Script"
echo "=================================================="
echo ""

echo "1. Environment Check"
echo "-------------------"
echo "PYTHONPATH: ${PYTHONPATH:-NOT SET}"
echo "Working Directory: $(pwd)"
echo "Python Version: $(python --version)"
echo ""

echo "2. Directory Structure"
echo "---------------------"
ls -la /app/
echo ""
echo "src/ contents:"
ls -la /app/src/ 2>/dev/null || echo "src/ not found!"
echo ""

echo "3. PYTHONPATH Test"
echo "------------------"
if [ -z "$PYTHONPATH" ]; then
    echo "❌ PYTHONPATH is NOT set!"
    echo "Setting PYTHONPATH=/app..."
    export PYTHONPATH=/app
else
    echo "✓ PYTHONPATH is set to: $PYTHONPATH"
fi
echo ""

echo "4. Python Module Path"
echo "--------------------"
python -c "import sys; print('sys.path:'); [print(f'  {p}') for p in sys.path]"
echo ""

echo "5. Import Test - src.utils"
echo "--------------------------"
python -c "
try:
    from src.utils import ClusterValidator, ClusterUtils, SiteUtils
    print('✅ SUCCESS: Imported from src.utils')
    print('   - ClusterValidator:', ClusterValidator)
    print('   - ClusterUtils:', ClusterUtils)
    print('   - SiteUtils:', SiteUtils)
except ImportError as e:
    print('❌ FAILED: Import error')
    print(f'   Error: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

echo "6. Import Test - src.main"
echo "-------------------------"
python -c "
try:
    from src.main import app
    print('✅ SUCCESS: Imported FastAPI app')
    print('   - App:', app)
except ImportError as e:
    print('❌ FAILED: Import error')
    print(f'   Error: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

echo "7. Try Running Application"
echo "--------------------------"
echo "If all tests above passed, try running:"
echo "  uvicorn src.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "If tests failed, export PYTHONPATH and try again:"
echo "  export PYTHONPATH=/app"
echo "  uvicorn src.main:app --host 0.0.0.0 --port 8000"
echo ""

echo "=================================================="
echo "Diagnostic Complete"
echo "=================================================="
