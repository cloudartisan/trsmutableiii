#!/usr/bin/env python3
"""
Run tests for TRS-80 Model III projects.
Handles test discovery and mocking of CircuitPython modules.
"""
import os
import sys
import unittest

# Mock CircuitPython modules
def mock_module(name):
    """Create a mock module"""
    class MockModule:
        def __getattr__(self, attr):
            return MockModule()
        def __call__(self, *args, **kwargs):
            return MockModule()
    
    module = type(sys)(name)
    module.__dict__.update({
        '__file__': None,
        '__name__': name,
        '__package__': name.split('.')[0],
        '__path__': [],
        '__loader__': None,
        '__spec__': None,
    })
    
    for attr_name in dir(MockModule()):
        if not attr_name.startswith('__'):
            setattr(module, attr_name, getattr(MockModule(), attr_name))
    
    return module

# Mock hardware modules before they can be imported
cp_modules = [
    "board", "displayio", "terminalio", "adafruit_display_text", 
    "adafruit_st7789", "adafruit_display_text.label"
]

for module_name in cp_modules:
    if module_name not in sys.modules:
        sys.modules[module_name] = mock_module(module_name)

if __name__ == "__main__":
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Set up the test runner
    test_loader = unittest.TestLoader()
    
    # Determine what tests to run
    if len(sys.argv) > 1:
        # Run specific test file(s) if provided
        test_names = sys.argv[1:]
        tests = test_loader.loadTestsFromNames(test_names)
    else:
        # Default to running wargames tests
        tests = test_loader.discover('wargames', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(tests)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())