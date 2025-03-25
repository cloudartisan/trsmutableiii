#!/usr/bin/env python3
"""
Universal simulator for TRS-80 Model III programs.
This allows running any CircuitPython program in a simulated environment.
"""
import os
import sys
import argparse

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the simulator
from simulator.program_runner import run_program

def main():
    """Run the simulator with the specified program."""
    parser = argparse.ArgumentParser(description='Run a TRS-80 Model III program in the simulator')
    parser.add_argument('program', nargs='?', default='wargames',
                        help='Name of the program directory to run (default: wargames)')
    args = parser.parse_args()
    
    # Get the full path to the program directory
    program_path = os.path.join(project_root, args.program)
    
    # Check if the program directory exists
    if not os.path.isdir(program_path):
        print(f"Error: Program directory '{args.program}' not found")
        print("Available programs:")
        for item in os.listdir(project_root):
            if os.path.isdir(os.path.join(project_root, item)) and \
               os.path.exists(os.path.join(project_root, item, 'code.py')):
                print(f"  - {item}")
        return 1
    
    # Run the program
    print(f"Starting simulator for: {args.program}")
    success = run_program(program_path)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())