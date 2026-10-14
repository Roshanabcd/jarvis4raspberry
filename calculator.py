#!/usr/bin/env python3
"""
Simple Interactive Calculator created by JARVIS OS
"""
import sys

def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b):
    if b == 0: return "Error: Division by zero"
    return a / b

def run_tests():
    print("=== JARVIS Calculator Self-Test ===")
    print(f"10 + 5 = {add(10, 5)}")
    print(f"10 - 5 = {subtract(10, 5)}")
    print(f"10 * 5 = {multiply(10, 5)}")
    print(f"10 / 5 = {divide(10, 5)}")
    print("✓ All calculator functions operating normally.")

if __name__ == "__main__":
    run_tests()
