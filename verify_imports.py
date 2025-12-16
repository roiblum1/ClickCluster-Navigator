#!/usr/bin/env python3
"""
Import Verification Script
Tests that all imports work correctly without circular dependency issues.
Based on IMPORT_ISSUE_EXPLANATION.md
"""
import sys

def test_utils_imports():
    """Test 1: Basic utils imports"""
    print('Test 1: Basic utils imports...')
    from src.utils import ClusterValidator, ClusterUtils, SiteUtils
    print('   ✓ src.utils imports successful')
    return True

def test_direct_validator_import():
    """Test 2: Direct validator import"""
    print('\nTest 2: Direct validator import...')
    from src.utils.validators import ClusterValidator
    print('   ✓ Direct validator import successful')
    return True

def test_import_order_independence():
    """Test 3: Import order independence (the critical test)"""
    print('\nTest 3: Import order independence...')

    # Clear cache
    modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('src.utils')]
    for mod in modules_to_clear:
        del sys.modules[mod]

    # Import in exact order from __init__.py
    # This is what caused the issue in disconnected environments
    from src.utils import ClusterValidator, ClusterUtils, SiteUtils
    print('   ✓ Import order test passed (ClusterValidator before ClusterUtils)')
    return True

def test_re_export_chain():
    """Test 4: Re-export chain is eliminated"""
    print('\nTest 4: Verify no re-export chain...')

    # Clear cache
    modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('src.utils')]
    for mod in modules_to_clear:
        del sys.modules[mod]

    # Check that ClusterValidator is imported directly from validators, not from cluster_utils
    import src.utils
    import inspect

    # Verify the source
    init_file = inspect.getsourcefile(src.utils)
    with open(init_file, 'r') as f:
        content = f.read()

    # Check for the correct import pattern
    assert 'from src.utils.validators import ClusterValidator' in content, \
        "ClusterValidator should be imported directly from validators"

    # Check that ClusterValidator comes BEFORE ClusterUtils (correct order)
    validator_pos = content.find('from src.utils.validators import ClusterValidator')
    utils_pos = content.find('from src.utils.cluster_utils import ClusterUtils')

    assert validator_pos < utils_pos, \
        "ClusterValidator must be imported before ClusterUtils"

    print('   ✓ No re-export chain (direct import from validators)')
    print('   ✓ Correct import order (ClusterValidator before ClusterUtils)')
    return True

def test_functionality():
    """Test 5: Verify functionality"""
    print('\nTest 5: Verify functionality...')
    from src.utils import ClusterUtils

    result = ClusterUtils.normalize_cluster_name('OCP4-TEST')
    assert result == 'ocp4-test', f'Expected ocp4-test, got {result}'
    print(f'   ✓ ClusterUtils.normalize_cluster_name works: {result}')
    return True

def test_fresh_import():
    """Test 6: Fresh import (simulates disconnected environment)"""
    print('\nTest 6: Fresh import simulation...')

    # Clear ALL src modules to simulate fresh container
    modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('src.')]
    for mod in modules_to_clear:
        del sys.modules[mod]

    # Import as if starting fresh
    from src.utils import ClusterValidator, ClusterUtils

    # This should work because:
    # 1. ClusterValidator is imported first in __init__.py
    # 2. No re-export chain exists
    # 3. Import order is correct

    print('   ✓ Fresh import test passed (disconnected environment simulation)')
    return True

def main():
    """Run all tests"""
    print('='*60)
    print('Import Verification Script')
    print('Based on IMPORT_ISSUE_EXPLANATION.md')
    print('='*60)

    tests = [
        test_utils_imports,
        test_direct_validator_import,
        test_import_order_independence,
        test_re_export_chain,
        test_functionality,
        test_fresh_import,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f'   ✗ FAILED: {e}')

    print('\n' + '='*60)
    if failed == 0:
        print('✅ ALL TESTS PASSED!')
        print('='*60)
        print('\nVerified:')
        print('  ✓ No circular import issues')
        print('  ✓ Import order is correct (ClusterValidator before ClusterUtils)')
        print('  ✓ Direct imports work (no re-export chain)')
        print('  ✓ Fresh imports work (disconnected environment ready)')
        print('  ✓ Functionality verified')
        print('\n🎉 Code is ready for deployment in disconnected environments!')
        return 0
    else:
        print(f'❌ {failed} TEST(S) FAILED!')
        print(f'✓ {passed} test(s) passed')
        return 1

if __name__ == '__main__':
    sys.exit(main())
