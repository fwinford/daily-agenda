#!/usr/bin/env python3
"""
Simple setup test
"""

import sys
import os

def main():
    print("* Daily Agenda Setup Test")
    print("Python version:", sys.version)
    print("Current directory:", os.getcwd())
    print("+ Script is working!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
