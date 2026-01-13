Below is a complete, professional **README.md** you can place at the root of the project or alongside this script. It explains purpose, architecture, usage, and limitations in a way suitable for internal tooling or open-source sharing.

---

# Smart Python Code Extractor

## Overview

This project provides a **static-analysis–based Python code extraction tool** designed to trace an application from a single entry point and extract only the **relevant, imported source files, functions, classes, and global definitions** into a single consolidated output file.

It is particularly useful for:

* Auditing large Python projects
* Preparing code for LLM ingestion or review
* Generating minimal reproducible subsets of applications
* Understanding dependency trees in monolithic projects

The tool uses Python’s `ast` module to safely analyze source files **without executing them**.

---

## Key Features

* **Entry-point–driven dependency discovery**
* **AST-based import resolution**
* **Selective extraction of used functions/classes**
* **Automatic project tree visualization**
* **Global variable and import preservation**
* **Standard-library and third-party exclusion**
* **Readable, structured output file**
* **Graceful handling of parse errors**

---

## How It Works

The extractor operates in two major phases:

### Phase 1: Discovery

Starting from a specified entry file:

1. Parses all imports (`import` and `from ... import ...`)
2. Resolves imports to local project files
3. Recursively discovers all reachable Python files
4. Applies exclusion patterns
5. Builds and prints a directory tree of discovered files

### Phase 2: Extraction

For each discovered file:

* Extracts:

  * Global imports
  * Global variable assignments
  * Functions and classes explicitly imported
* If the file is imported with `*`, the **entire file** is extracted
* Writes results to a single output file with:

  * Directory tree
  * File metadata
  * Line counts
  * Source code blocks

---

## File Structure (Logical)

```
smart_code_extractor.py   # Main extraction script
smart_extracted_code.txt # Generated output file
README.md                # This documentation
```

---

## Usage

### Requirements

* Python 3.8+
* No external dependencies (standard library only)

### Running the Script

```bash
python smart_code_extractor.py
```

The script is configured via the `extract_used_code()` call in `__main__`.

### Example Configuration

```python
extract_used_code(
    project_dir="/data/flaskapp/ocr2",
    entry_file="/data/flaskapp/ocr2/docker_app.py",
    output_file="smart_extracted_code.txt",
    exclude_patterns=[
        "fine_tuned_model",
        "ocrEnv",
        "__pycache__"
    ]
)
```

---

## Output Format

The generated output file contains:

1. **Summary Header**

   * Total files extracted
   * Project root
2. **Directory Tree**

   * Visual tree of extracted files
