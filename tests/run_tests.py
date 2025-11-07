"""Test runner for core ETL pipeline functionality tests."""

import os
import sys
import importlib.util

def run_all_tests():
    """Run all core functionality test files."""
    print("ETL PIPELINE CORE FUNCTIONALITY TESTS")
    print("="*60)
    
    tests_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
    
    print(f"Tests directory: {tests_dir}")
    print(f"Found {len(test_files)} core test files\n")
    
    results = {}
    
    for test_file in sorted(test_files):
        test_name = test_file[:-3]  # Remove .py extension
        print(f"Running {test_name}...")
        print("-" * 40)
        
        try:
            # Load and run the test module
            test_path = os.path.join(tests_dir, test_file)
            spec = importlib.util.spec_from_file_location(test_name, test_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            results[test_name] = "PASSED"
            
        except Exception as e:
            results[test_name] = f"FAILED: {e}"
        
        print("\n")
    
    # Summary
    print("="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        print(f"{test_name:<25}: {result}")
    
    # Overall result
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed successfully!")
        return True
    else:
        print("WARNING: Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    # Run core functional tests only
    success = run_all_tests()
    
    print("\nCore functionality test suite completed!")