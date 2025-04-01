<!-- @format -->

# LBX Text Editor Test Suite

This test suite validates the functionality of the `lbx_text_edit.py` tool, which is used to manipulate text in Brother P-touch LBX label files.

## Test Coverage

The test suite covers the following operations:

1. **Delete First String Item**: Removes the first string item from a text object
2. **Merge String Items**: Combines all string items into a single item
3. **Remove First Newline**: Removes the first newline character from text
4. **Replace All Newlines**: Replaces all newline characters with spaces
5. **Replace Text with Regex**: Converts "4 x 4" to "4×4" using regex
6. **Add String Item with Comic Sans**: Adds a new string item with a different font
7. **Combined Operations**: Performs multiple operations in sequence

Each test creates a modified LBX file in the `test_output` directory.

## Running the Tests

### Prerequisites

To run the test suite, you need the following:

- Python 3.6 or later
- The original `lbx_text_edit.py` file in the same directory
- The test output directory will be created automatically

### Method 1: Using the run_tests.py Script (Recommended)

The easiest way to run the tests is to use the provided `run_tests.py` script:

```bash
python run_tests.py
```

This will run all tests, display detailed results, and automatically extract the label.xml files from each test output LBX file for easier analysis.

### Method 2: Running the Test Suite Directly

You can also run the test suite directly:

```bash
python test_lbx_text_edit.py
```

Note: This method will not automatically extract the label.xml files.

### Method 3: Using Python's unittest Module

For more control over which tests to run:

```bash
python -m unittest test_lbx_text_edit.py
```

To run a specific test:

```bash
python -m unittest test_lbx_text_edit.LBXTextEditTests.test_1_delete_first_string_item
```

Note: These methods will not automatically extract the label.xml files.

## Test Output

All test output files are saved in the `test_output` directory:

### LBX Files

Each test creates an LBX file named according to the test that created it:

- `test1_delete_first_item.lbx`
- `test2_merge_all_items.lbx`
- `test3_remove_first_newline.lbx`
- `test4_replace_all_newlines.lbx`
- `test5_replace_x_with_multiplication.lbx`
- `test6_add_comic_sans.lbx`
- `test7_combined_operations.lbx`

### Extracted XML Files

When using the `run_tests.py` script, the label.xml files are automatically extracted to the `test_output/xml` directory with the same base names:

- `test1_delete_first_item.xml`
- `test2_merge_all_items.xml`
- `test3_remove_first_newline.xml`
- `test4_replace_all_newlines.xml`
- `test5_replace_x_with_multiplication.xml`
- `test6_add_comic_sans.xml`
- `test7_combined_operations.xml`

This makes it easier to inspect the changes made by each test without having to manually extract the files.

## Manual Extraction

If you need to manually extract the label.xml from an LBX file, you can use the `lbx_text_edit.py` tool:

```bash
python lbx_text_edit.py extract test_output/test5_replace_x_with_multiplication.lbx -o output_dir
```

## Troubleshooting

If you encounter import errors, make sure that:

1. The `lbx_text_edit.py` file is in the same directory as the test files
2. You have the necessary permissions to read and write files
3. The `example-labels/30182.lbx` file exists and is accessible

## Adding New Tests

To add new tests, simply add new test methods to the `LBXTextEditTests` class in `test_lbx_text_edit.py`. Make sure to follow the naming convention `test_X_description` where X is a number and description indicates what the test does.

## Setup and Configuration

The test suite assumes:

1. The `lbx_text_edit.py` file is in the same directory as the test files
