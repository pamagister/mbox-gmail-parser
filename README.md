[![Run Python Tests](https://github.com/pamagister/mbox-gmail-parser/actions/workflows/python-tests.yml/badge.svg)](https://github.com/maxmustermann/mbox-parser/actions/workflows/python-tests.yml)

# MBOX Parser

A Python script for parsing and structured export of `.mbox` files.
Supports output in text or CSV format with optional on/off email fields.
Useful for analyzing, archiving or further processing e-mail correspondence.

## 🔽 Download installer

- [⬇️ Download for Windows](https://github.com/pamagister/mbox-gmail-parser/releases/latest/download/MboxParserGUI.exe)
- [⬇️ Download for macOS](https://github.com/pamagister/mbox-gmail-parser/releases/latest/download/MboxParserGUI-macOS.zip)


## Run from source code

Setup & execution

### 1. prepare the repository

```bash
# Create virtual environment (optional, recommended)
python -m venv env
source env/bin/activate  # Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

````


### 2. Execute script

```bash
python mbox_parser.py [OPTIONS] path/to/file.mbox
```

---

## ⚙️ CLI-Optionen

| Option              | Typ        | Description                                                               | Default value  |
| ------------------- |------------|---------------------------------------------------------------------------|----------------|
| `--from`            | `ON/OFF`   | Outputs the sender address                                                | `ON`           |
| `--to`              | `ON/OFF`   | Outputs the recipient address                                             | `ON`           |
| `--date`            | `ON/OFF`   | Outputs the shipping date                                                 | `ON`           |
| `--subject`         | `ON/OFF`   | Outputs the subject                                                       | `ON`           |
| `--format`          | `txt/csv`  | Defines the output format (text file or CSV file)                         | `txt`          |
| `--max_days`        | Number     | Maximum number of days per output file (e.g. '7' for weekly splits)       | `inf`          |
| `path/to/file.mbox` | File       | Path to the MBOX file to be processed                                     | *required* |

---

## 💡 Examples

In the example, the following is assumed: `example.mbox` in the current directory

### 1. standard version (all fields, text format)

```bash
python mbox_parser.py example.mbox
```

### 2. sender & subject only, in CSV format

```bash
python mbox_parser.py --to OFF --date OFF --format csv example.mbox
```

### 3. grouping of issues by week (7 days per file)

```bash
python mbox_parser.py --max_days 7 example.mbox
```

### 4. complete control (subject only, CSV, grouped daily)

```bash
python mbox_parser.py --from OFF --to OFF --date OFF --format csv --max_days 1 example.mbox
```

---

## 📁 Output

* **Text mode (`--format txt`)**: Contains structured text blocks with fields and e-mail content.
* **CSV Mode (`--format csv`)**: CSV file with one line per mail. Fields correspond to the activated CLI options.

The output files are numbered automatically:

```bash
example_001.txt
example_002.txt
...
```

---

## 🔚 Exiting the virtual environment

```bash
deactivate
```

Certainly! Here's an additional chapter you can include in your `README.md` file under the title:

---

## 🖱️ Usage by Drag-and-Drop

You can also run the parser conveniently by dragging and dropping `.mbox` files onto the provided startup scripts. This is especially useful for non-technical users or quick one-off processing.

---

### 🪟 Windows (`.bat` file)

#### File: `run_mbox_parser.bat` or `setup_and_run.bat`

**Steps:**

1. Make sure `mbox_parser.py`, `requirements.txt`, and the `.bat` file are in the same directory.
2. Drag a `.mbox` file and drop it onto the `.bat` file (e.g. `example.mbox`).
3. The script will:

   * create a virtual environment (if not already present),
   * install all dependencies,
   * run the parser with default options.

> 💡 Output files will be created in the same directory, with names like `example_001.txt` or `example_001.csv`.

---

### 🐧 Linux/macOS (`.sh` file)

#### File: `setup_and_run.sh`

**Steps:**

1. Place `setup_and_run.sh`, `mbox_parser.py`, and `requirements.txt` in the same directory.

2. Make the script executable:

   ```bash
   chmod +x setup_and_run.sh
   ```

3. Open a terminal.

4. Drag your `.mbox` file into the terminal window — it will paste the full path.

5. Complete the command like this:

   ```bash
   ./setup_and_run.sh /full/path/to/example.mbox
   ```

6. The script will:

   * create and activate a `.venv` if needed,
   * install requirements,
   * and run the parser on the file.

---

### 📝 Notes

* The `.venv` directory will be reused across runs.
* You can modify the batch or shell script to hard-code specific parser options (like `--format csv`), if desired.

Let me know if you’d like a version that includes GUI elements (e.g., file picker dialogs).



## References

- [Installing packages using pip and virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
- A tutorial on working with [Virtual Environments and Packages](https://docs.python.org/3/tutorial/venv.html)
- [A Guide to Python’s Virtual Environments](https://towardsdatascience.com/virtual-environments-104c62d48c54)
- [Email Address and MIME Parsing](https://github.com/mailgun/flanker)
- [Signature Stripping Solution](https://github.com/mailgun/talon)
- [MBOX Parsing Example: Mining the Social](https://www.oreilly.com/library/view/mining-the-social/9781449368180/ch06.html)
- [Gmail MBOX Parser](https://github.com/alejandro-g-m/Gmail-MBOX-email-parser)
- [Mail Parser Package](https://pypi.org/project/mail-parser/)
