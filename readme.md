# DWG → DXF → PDF/PNG (Batch Converter)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

A small utility to:

1. Convert **DWG → DXF** using **Aspose.CAD**
2. Export **DXF → PDF** using **Aspose.CAD** and/or **Inkscape**
3. Export **DXF → PNG/JPG** using **Aspose.CAD**

The tool is designed for **batch, recursive** conversion of nested folders, and writes outputs into predictable subfolders.

---

## Repository layout

- `dwg_to_dxf_and_pdf.py` — CLI entrypoint (DWG→DXF and DXF→PDF/PNG)
- `support.py` — conversion helpers and external-tool wrappers

---

## Requirements

### Python
- Python **3.10+** (uses PEP 604 union types and 3.10+ annotations)
- Dependencies listed in `requirements.txt`

### External tools (optional)
- **Inkscape** (optional but recommended for DXF→PDF in many cases)
- **LibreCAD** (optional alternative for DXF→PDF)

### Licensing note (Aspose.CAD)
Aspose.CAD may run in evaluation mode without a license. If you hit limits or watermarks, review Aspose licensing terms and apply a license as appropriate.

---

## Installation

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you plan to export DXF → PDF via Inkscape or LibreCAD, install the tool and configure its path (see below).

---

## Configuration (config.yaml)

External tool paths are configured via `config.yaml` in the project root.

Example:

```yaml
paths:
  inkscape_exe: "C:/Users/you/scoop/shims/inkscape.exe"
  librecad_exe: "C:/Users/you/scoop/apps/librecad/current/LibreCAD.exe"

---

## Usage

Run the CLI and pass a directory containing DWG files (and/or pre-generated DXF files).

### Basic examples (PowerShell)

```powershell
# Convert using defaults (depends on your default behavior in the script)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files

# Paths with spaces
python .\dwg_to_dxf_and_pdf.py --directory "C:\Users\You\path with spaces"

# List layers from DXFs (via ezdxf) without re-converting DWGs (if you enable that flow)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --layers_only
```

### Output selection flags

```powershell
# Export PDFs (DXF -> PDF)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_pdf

# Export PNGs (DXF -> PNG)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_png

# Export both
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_pdf --to_png
```

### PDF backend selection

```powershell
# PDF via Aspose
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_pdf --aspose

# PDF via Inkscape
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_pdf --inkscape

# Run both (two PDFs per DXF, typically suffixed)
python .\dwg_to_dxf_and_pdf.py --directory .\dwg_files --to_pdf --aspose --inkscape
```

> Note: Ensure your script defines these flags in `argparse` (`--to_pdf`, `--to_png`, `--aspose`, `--inkscape`) before use.

---

## Output folders

Given an input directory `ROOT`:

- DWG → DXF outputs are written to:
  - `ROOT\DXF_Converted\`

- DXF → PDF outputs are written to:
  - `ROOT\PDF_From_DXF\`

- DXF → PNG/JPG outputs are written to:
  - `ROOT\IMG_From_DXF\`

To avoid filename collisions when converting nested folders, outputs use a **unique stem** built from the relative path, for example:

```
subfolder_plan1_fileA.dxf  ->  subfolder_plan1_fileA_aspose.pdf
```

---

## Key functions (support.py)

### DWG → DXF
- `convert_dwg_to_dxf(fdir, layers_only=False, skip_existing=True)`

### DXF → PDF
- `dxf_to_pdf_aspose(dxf_root, pdf_out, page_width=..., page_height=..., ...)`
- `dxf_to_pdf_inkscape(dxf_root, pdf_out, area="drawing"|"page", margin_px=..., dpi=..., ...)`
- `dxf_to_pdf_librecad(dxf_root, pdf_out)`

### DXF → Image (PNG/JPG)
- `dxf_to_image_aspose(dxf_root, img_out, fmt="png"|"jpg", page_width=..., page_height=..., ...)`

---

## Notes on scaling and framing

### Aspose (PDF/PNG/JPG)
Aspose output framing is primarily controlled via:

- `CadRasterizationOptions.page_width`
- `CadRasterizationOptions.page_height`

These values mainly determine the **page aspect ratio** and how the geometry is fit into that page. They are not always a literal “physical size” in inches; printing behavior depends on the PDF viewer/printer settings.

### Inkscape
Inkscape’s DXF import/export behavior can vary by drawing. `--export-area-drawing` is often closest to “fit drawing,” but some DXFs may still crop due to stray entities or unusual extents.

---

## Layers (DXF)

Layer listing is supported via **ezdxf**:

- `print_dxf_file(dxf_file, output_txt=True)`

### Important limitation (Aspose layer filtering)
The Aspose.CAD Python binding used here does **not** expose layer enumeration/filtering APIs in a consistent way (e.g., `CadImage`, `.layers`). As a result:

- You can **list layers** with `ezdxf`
- You should **remove unwanted entities/layers** by preprocessing DXF with `ezdxf` (if needed)
- Do not assume Aspose PDF/PNG rendering can selectively disable layers

If you want, add a preprocessing step:
1. Read DXF with `ezdxf`
2. Delete entities on specific layers (e.g., `"0"` or `"O"`)
3. Save a “clean” DXF, then render it

---

## Troubleshooting

### “Import ... could not be resolved from source” (Pylance)
Aspose.CAD has incomplete type stubs. Pylance may show import warnings even when runtime imports work.

If it bothers you, use guarded imports for some Aspose options:

```python
try:
    from aspose.cad.imageoptions import PngOptions, JpegOptions
except Exception:
    PngOptions = None
    JpegOptions = None
```

### Inkscape failures
Run a single export command manually to see stdout/stderr:

```powershell
& "C:\Program Files\Inkscape\bin\inkscape.exe" "C:\path\to\file.dxf" --export-type=pdf --export-filename="C:\temp\out.pdf"
```

### Aspose evaluation / licensing issues
If you see evaluation behavior, consult Aspose licensing and apply a license if required.

---

## Git helpers

### Clone
```bash
git clone https://github.com/untucked/DWG_to_DXF_and_PDF.git
```

### Initial push
```bash
git init
git add .
git commit -m "Initialize"
git branch -M main
git remote add origin https://github.com/untucked/DWG_to_DXF_and_PDF.git
git push -u origin main
```

---

## License

MIT — see `LICENSE.md`.
