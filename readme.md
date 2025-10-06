# DWG to DXF and PDF

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## Introduction

Small utility to convert DWG files to DXF and then export DXF files to PDF.

This repository contains two main scripts:
- `dwg_to_dxf_and_pdf.py` — command-line entrypoint that runs DWG->DXF conversion
	and then attempts DXF->PDF export.
- `support.py` — conversion helpers (uses Aspose.CAD for DWG->DXF and
	Inkscape/LibreCAD for DXF->PDF).

## Requirements

- Python 3.10 or newer (uses PEP 604 union-types and other 3.10+ annotations)
- The Python dependencies listed in `requirements.txt` (see below)
- One of the external tools for DXF->PDF conversion:
	- Inkscape (recommended)
	- LibreCAD (optional)

Note: `aspose-cad` may require licensing for some features. Check Aspose's
documentation and license policy if you hit limitations.

## Installation

Create and activate a virtual environment, then install Python dependencies:

```powershell
# DWG to DXF and PDF

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## Introduction

Small utility to convert DWG files to DXF and then export DXF files to PDF.

This repository contains two main scripts:
- `dwg_to_dxf_and_pdf.py` — command-line entrypoint that runs DWG->DXF conversion
	and then attempts DXF->PDF export.
- `support.py` — conversion helpers (uses Aspose.CAD for DWG->DXF and
	Inkscape/LibreCAD for DXF->PDF).

## Requirements

- Python 3.10 or newer (uses PEP 604 union-types and other 3.10+ annotations)
- The Python dependencies listed in `requirements.txt` (see below)
- One of the external tools for DXF->PDF conversion:
	- Inkscape (recommended)
	- LibreCAD (optional)

Note: `aspose-cad` may require licensing for some features. Check Aspose's
documentation and license policy if you hit limitations.

## Installation

Create and activate a virtual environment, then install Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you plan to export DXF -> PDF, install Inkscape (or LibreCAD) and ensure
the executable is available on PATH or update the paths in `support.py`.

## External tools

- Inkscape: used by `support.dxf_to_pdf_inkscape`. Install Inkscape and
	either have `inkscape` on your PATH or set `INKSCAPE_EXE` in `support.py`.
- LibreCAD: optional alternative used by `support.dxf_to_pdf_librecad`.
	If using LibreCAD, point `LIBRECAD_EXE` in `support.py` at your install.

Example `support.py` path constants (already present in the file):

```python
LIBRECAD_EXE  = r"C:\path\to\LibreCAD.exe"
INKSCAPE_EXE = r"C:\path\to\inkscape.exe"
```

## Usage

Run the top-level script and point it at a directory containing DWG files.

PowerShell examples:

```powershell
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files

# with spaces in path
python .\dwg_to_dxf_and_pdf.py --directory "C:\Users\You\path with spaces"

# list layers only (does not re-convert DWGs)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --layers_only
```

Behavior summary:
- DWG files (recursively) are searched under `--directory`.
- DWG -> DXF output is written to `(<directory>)/DXF_Converted/`.
- DXF -> PDF output is written to `(<directory>)/PDF_From_DXF/`.
- By default the converter skips DXF files that already exist (idempotent runs).

## Files and main functions

- `dwg_to_dxf_and_pdf.py` — CLI: parses `--directory` and `--layers_only` and
	calls `support.convert_dwg_to_dxf(...)` then `support.dxf_to_pdf_inkscape(...)`.
- `support.py` — contains:
	- `convert_dwg_to_dxf(fdir, layers_only=False, skip_existing=True)`
	- `dxf_to_pdf_inkscape(...)` and `dxf_to_pdf_librecad(...)`
	- helpers for reading DXF layers and saving images

## Dependencies

Install from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Typical `requirements.txt` includes:

- ezdxf
- tqdm
- aspose-cad

If you add or pin dependencies, update the `requirements.txt` accordingly.

## Troubleshooting

- "Directory does not exist": ensure the path you pass to `--directory` is
	correct and accessible.
- Aspose failures / licensing: check Aspose.CAD docs; some features may require
	a license or behave differently under an unlicensed evaluation mode.
- Inkscape export failures: run a single Inkscape export command from
	PowerShell to inspect stdout/stderr, or ensure `inkscape` is on PATH.

Example Inkscape test (PowerShell):

```powershell
& "C:\Program Files\Inkscape\bin\inkscape.exe" "C:\path\to\file.dxf" --export-type=pdf --export-filename="C:\temp\out.pdf"
```

## Contributing

Feel free to open issues or PRs. If you change how external tools are located,
consider adding a small configuration file or environment variables instead of
hard-coding paths into `support.py`.

## GIT - CLONE
----------------------------
``` bash
git clone https://github.com/untucked/DWG_to_DXF_and_PDF.git
```

#### GIT - Upload
----------------------------
``` bash
git init
git add .
git commit -m "Initialize"
git branch -M main
git remote add origin https://github.com/untucked/DWG_to_DXF_and_PDF.git
git push -u origin main
```

## License

This project is provided under the MIT license — see `LICENSE.md` for details.

