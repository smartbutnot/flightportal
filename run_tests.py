#!/usr/bin/env python3
"""
FlightPortal - Master Test Suite
Run all tests without hardware or CircuitPython.
Runs on standard Python on Windows/Mac/Linux.

Usage:
    python run_tests.py
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_parser_tests():
    """Run parser module tests."""
    print_header("PARSER TESTS")
    
    try:
        from test_parser import run_all_tests
        run_all_tests()
        return True
    except Exception as e:
        print(f"✗ Parser tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_tracker_tests():
    """Run tracker module tests."""
    print_header("TRACKER TESTS")
    
    try:
        from test_tracker import run_all_tests
        run_all_tests()
        return True
    except Exception as e:
        print(f"✗ Tracker tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test that all modules can be imported."""
    print_header("MODULE IMPORTS TEST")
    
    modules_to_test = [
        'config',
        'utils',
        'parser',
        'test_fixtures',
        # Note: flight_tracker and display require hardware (board, displayio, etc)
        # These are skipped in this test but work on real hardware
    ]
    
    success = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            success = False
    
    print("\n  Note: flight_tracker, display, and network require CircuitPython hardware")
    print("        These modules are not tested here but work on MatrixPortal devices")
    
    if success:
        print("\n✓ All testable modules import successfully")
    else:
        print("\n✗ Some modules failed to import")
    
    return success


def test_config():
    """Test configuration module."""
    print_header("CONFIGURATION TEST")
    
    try:
        from config import Config
        
        # Check that Config object initialized
        print(f"  ✓ Config initialized")
        print(f"  ✓ Bounds box: {Config.BOUNDS_BOX}")
        print(f"  ✓ FR24 Search URL: {Config.FR24_SEARCH_URL[:50]}...")
        print(f"  ✓ Colors defined: {len(Config.COLORS)} colors")
        print(f"  ✓ Timings defined: {len(Config.TIMINGS)} timing values")
        
        # Test helper methods
        color = Config.get_color('row_one')
        assert color == 0xEE82EE
        print(f"  ✓ get_color() works: row_one = {hex(color)}")
        
        timing = Config.get_timing('query_delay')
        assert timing == 30
        print(f"  ✓ get_timing() works: query_delay = {timing}s")
        
        print("\n✓ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utils():
    """Test utility functions."""
    print_header("UTILS TEST")
    
    try:
        from utils import (
            MemoryBuffer, log_info, log_error, get_free_memory, 
            get_allocated_memory, print_memory_status
        )
        
        # Test logging
        print("  Testing logging functions...")
        log_info("Test info message")
        log_error("Test error message")
        print("  ✓ Logging functions work")
        
        # Test memory status
        print("\n  Testing memory functions...")
        free = get_free_memory()
        alloc = get_allocated_memory()
        print(f"  ✓ Memory info: {free} free, {alloc} allocated")
        
        # Test MemoryBuffer
        print("\n  Testing MemoryBuffer...")
        buffer = MemoryBuffer(256)
        buffer.write(b"Hello World")
        pos = buffer.find(b"World")
        assert pos > 0
        print(f"  ✓ MemoryBuffer works (found at offset {pos})")
        
        print("\n✓ Utils test passed")
        return True
        
    except Exception as e:
        print(f"✗ Utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    tests = [
        ("Module Imports", results['imports']),
        ("Configuration", results['config']),
        ("Utilities", results['utils']),
        ("Parser Functionality", results['parser']),
        ("Tracker Functionality", results['tracker']),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} - {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("  ✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print(f"  ✗✗✗ {total - passed} TEST SUITE(S) FAILED ✗✗✗")
        print("=" * 70)
        return False


def main():
    """Run all tests."""
    start_time = time.time()
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  FlightPortal Test Suite (No Hardware Required)".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"\nRunning on: Python {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    
    # Run tests
    results = {
        'imports': test_imports(),
        'config': test_config(),
        'utils': test_utils(),
        'parser': run_parser_tests(),
        'tracker': run_tracker_tests(),
    }
    
    # Print summary
    elapsed = time.time() - start_time
    all_passed = print_summary(results)
    
    print(f"\nTests completed in {elapsed:.2f} seconds")
    print()
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
