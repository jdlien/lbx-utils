#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script to check the available APIs in the installed uharfbuzz version.
"""

import sys
import os
import inspect

try:
    import uharfbuzz as hb
    print(f"uharfbuzz version: {getattr(hb, '__version__', 'Unknown')}")

    print("\nAvailable modules and functions in uharfbuzz:")
    for name in dir(hb):
        if not name.startswith("__"):
            obj = getattr(hb, name)
            if inspect.isclass(obj):
                print(f"\nClass: {name}")
                for method_name in dir(obj):
                    if not method_name.startswith("__"):
                        method = getattr(obj, method_name)
                        if inspect.isfunction(method) or inspect.ismethod(method):
                            print(f"  Method: {method_name}")
                        elif not callable(method):
                            print(f"  Attribute: {method_name}")
            elif inspect.isfunction(obj):
                print(f"Function: {name}")
            else:
                print(f"Other: {name}")

    # Try to create objects and check their APIs
    print("\nTesting object creation and APIs:")

    # Test creating a blob
    try:
        test_data = b"Hello, World!"
        print("\nCreating Blob:")

        # Try different ways to create a blob
        methods = [
            lambda: hb.Blob(test_data),
            lambda: hb.Blob.from_bytes(test_data),
            lambda: hb.Blob.with_bytes(test_data)
        ]

        blob = None
        for method in methods:
            try:
                blob = method()
                print(f"  Success with {method.__code__.co_consts[0]}")
                break
            except Exception as e:
                print(f"  Failed with {method.__code__.co_consts[0]}: {str(e)}")

        if blob:
            print("  Blob created successfully")
            print(f"  Blob attributes: {[attr for attr in dir(blob) if not attr.startswith('__')]}")
        else:
            print("  Could not create Blob with any method")
    except Exception as e:
        print(f"  Error testing Blob: {str(e)}")

    # Test creating a buffer
    try:
        print("\nCreating Buffer:")

        # Try different ways to create a buffer
        methods = [
            lambda: hb.Buffer(),
            lambda: hb.Buffer.create()
        ]

        buf = None
        for method in methods:
            try:
                buf = method()
                print(f"  Success with {method.__code__.co_consts[0]}")
                break
            except Exception as e:
                print(f"  Failed with {method.__code__.co_consts[0]}: {str(e)}")

        if buf:
            print("  Buffer created successfully")
            print(f"  Buffer attributes: {[attr for attr in dir(buf) if not attr.startswith('__')]}")

            # Try adding text
            test_text = "Hello"
            buf.add_str(test_text)
            print(f"  Added text: '{test_text}'")

            # Check if we can access the content
            try:
                print(f"  Buffer length: {len(buf)}")
            except Exception as e:
                print(f"  Error getting buffer length with len(): {str(e)}")

            try:
                print(f"  Buffer length attribute: {buf.length}")
            except Exception as e:
                print(f"  Error getting buffer length attribute: {str(e)}")
        else:
            print("  Could not create Buffer with any method")
    except Exception as e:
        print(f"  Error testing Buffer: {str(e)}")

except ImportError:
    print("uharfbuzz module not found. Please install with: pip install uharfbuzz")

if __name__ == "__main__":
    print("Test complete")