"""Test utilities for enhanced debugging and verbose logging."""

import sys
import traceback
from typing import Any, List, Optional


def presentIn(res: str, item: str, context: str = "") -> None:
    """
    Assert that an item is present in the result with verbose logging.
    
    Args:
        res: The result string to search in
        item: The item to look for
        context: Optional context description for better error messages
    """
    if item not in res:
        print(f"\n❌ ASSERTION FAILED: '{item}' not found in result", flush=True)
        if context:
            print(f"   Context: {context}", flush=True)
        print(f"   Expected: {repr(item)}", flush=True)
        print(f"   Actual result length: {len(res)} characters", flush=True)
        print(f"   Result preview (first 200 chars):", flush=True)
        print(f"   {repr(res[:200])}", flush=True)
        if len(res) > 200:
            print(f"   ... and {len(res) - 200} more characters", flush=True)
        print(flush=True)
    assert item in res, f"'{item}' not found in result{f' (context: {context})' if context else ''}"


def assert_contains_all(result: str, expected_items: List[str], test_name: str = "") -> None:
    """
    Assert that all expected items are present in the result.
    
    Args:
        result: The result string to check
        expected_items: List of strings that should be present
        test_name: Name of the test for better error reporting
    """
    missing_items = []
    for item in expected_items:
        if item not in result:
            missing_items.append(item)
    
    if missing_items:
        print(f"\n❌ MULTIPLE ASSERTIONS FAILED{f' in {test_name}' if test_name else ''}", flush=True)
        print(f"   Missing {len(missing_items)}/{len(expected_items)} expected items:", flush=True)
        for i, item in enumerate(missing_items, 1):
            print(f"   {i}. {repr(item)}", flush=True)
        print(f"\n   Full result ({len(result)} chars):", flush=True)
        print(f"   {repr(result)}", flush=True)
        print(flush=True)
        
    assert not missing_items, f"{len(missing_items)} items missing from result{f' in {test_name}' if test_name else ''}"


def assert_count(result: str, item: str, expected_count: int, test_name: str = "") -> None:
    """
    Assert that an item appears exactly the expected number of times.
    
    Args:
        result: The result string to check
        item: The item to count
        expected_count: Expected number of occurrences
        test_name: Name of the test for better error reporting
    """
    actual_count = result.count(item)
    if actual_count != expected_count:
        print(f"\n❌ COUNT ASSERTION FAILED{f' in {test_name}' if test_name else ''}", flush=True)
        print(f"   Item: {repr(item)}", flush=True)
        print(f"   Expected count: {expected_count}", flush=True)
        print(f"   Actual count: {actual_count}", flush=True)
        
        # Show all occurrences
        if actual_count > 0:
            print(f"   Found at positions:", flush=True)
            start = 0
            for i in range(actual_count):
                pos = result.find(item, start)
                line_num = result[:pos].count('\n') + 1
                print(f"     {i+1}. Position {pos} (line ~{line_num})", flush=True)
                start = pos + 1
        
        print(f"\n   Full result ({len(result)} chars):", flush=True)
        print(f"   {repr(result)}", flush=True)
        print(flush=True)
    
    assert actual_count == expected_count, f"Expected {expected_count} occurrences of '{item}', found {actual_count}{f' in {test_name}' if test_name else ''}"

def assert_lacking(result: str, item: str, test_name: str = "") -> None:
    """
    Assert that an item is NOT present in the result.
    
    Args:
        result: The result string to check
        item: The item that should not be present
        test_name: Name of the test for better error reporting
    """
    if item in result:
        print(f"\n❌ ASSERTION FAILED{f' in {test_name}' if test_name else ''}", flush=True)
        print(f"   Item '{item}' was found in the result, but it should not be present.", flush=True)
        print(f"   Full result ({len(result)} chars):", flush=True)
        print(f"   {repr(result)}", flush=True)
        print(flush=True)
    
    assert item not in result, f"'{item}' should not be present in result{f' (context: {test_name})' if test_name else ''}"


def log_test_start(test_name: str, source_code: str = "") -> None:
    """
    Log the start of a test with optional source code.
    
    Args:
        test_name: Name of the test
        source_code: Optional source code being tested
    """
    print(f"\n🧪 Starting test: {test_name}", flush=True)
    if source_code:
        print(f"   Source code:", flush=True)
        for i, line in enumerate(source_code.strip().split('\n'), 1):
            print(f"   {i:2d}: {line}", flush=True)
    print(flush=True)


def log_test_result(test_name: str, result: str, show_full: bool = False) -> None:
    """
    Log the result of a transformation or operation.
    
    Args:
        test_name: Name of the test
        result: The result to log
        show_full: Whether to show the full result or just a preview
    """
    print(f"✅ Result for {test_name}:", flush=True)
    if show_full or len(result) <= 300:
        print(f"   Full result ({len(result)} chars):", flush=True)
        for i, line in enumerate(result.split('\n'), 1):
            print(f"   {i:2d}: {line}", flush=True)
    else:
        print(f"   Result preview ({len(result)} chars total):", flush=True)
        preview_lines = result[:300].split('\n')
        for i, line in enumerate(preview_lines, 1):
            print(f"   {i:2d}: {line}", flush=True)
        if len(result) > 300:
            print(f"   ... and {len(result) - 300} more characters", flush=True)
    print(flush=True)


def debug_diff(expected: str, actual: str, context: str = "") -> None:
    """
    Show a detailed diff between expected and actual results.
    
    Args:
        expected: The expected string
        actual: The actual string
        context: Optional context description
    """
    print(f"\n🔍 DIFF ANALYSIS{f' ({context})' if context else ''}", flush=True)
    print(f"   Expected length: {len(expected)}", flush=True)
    print(f"   Actual length: {len(actual)}", flush=True)
    
    if expected == actual:
        print("   ✅ Strings are identical", flush=True)
        return
    
    # Find first difference
    min_len = min(len(expected), len(actual))
    first_diff = None
    for i in range(min_len):
        if expected[i] != actual[i]:
            first_diff = i
            break
    
    if first_diff is not None:
        print(f"   First difference at position {first_diff}:", flush=True)
        print(f"     Expected: {repr(expected[first_diff:first_diff+20])}", flush=True)
        print(f"     Actual:   {repr(actual[first_diff:first_diff+20])}", flush=True)
    
    if len(expected) != len(actual):
        print(f"   Length difference: {len(actual) - len(expected)}", flush=True)
        if len(actual) > len(expected):
            print(f"   Extra in actual: {repr(actual[len(expected):])}", flush=True)
        else:
            print(f"   Missing in actual: {repr(expected[len(actual):])}", flush=True)
    
    print(flush=True)


def safe_assert(condition: bool, message: str, debug_info: Any = None) -> None:
    """
    Assert with enhanced error reporting and optional debug info.
    
    Args:
        condition: The condition to assert
        message: Error message if assertion fails
        debug_info: Optional additional debug information to print
    """
    if not condition:
        print(f"\n❌ ASSERTION FAILED: {message}", flush=True)
        if debug_info is not None:
            print(f"   Debug info: {debug_info}", flush=True)
        print(f"   Stack trace:", flush=True)
        traceback.print_stack(limit=3)
        print(flush=True)
    
    assert condition, message
