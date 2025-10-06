# support.py
import aspose.cad as cad
from aspose.cad.imageoptions import DxfOptions, CadRasterizationOptions
from aspose.cad import Color  # Correct Color import
import time
from aspose.cad import Image
from aspose.cad.fileformats.cad import CadImage
import ezdxf
import os
from tqdm import tqdm  # Progress bar
import subprocess
import shlex
from pathlib import Path
from tqdm import tqdm
# Context manager = no file locks
from aspose.cad import Image
from aspose.cad.imageoptions import DxfOptions
# ---------------- Helpers ----------------
def _run1(cmd: str, cwd: Path | None = None):
    print(">>", cmd)
    subprocess.run(shlex.split(cmd), check=True, cwd=str(cwd) if cwd else None)
def _run2(args, cwd=None):
    return subprocess.run(args, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True)
# --------------- DWG -> DXF ---------------
def _save_as_dxf(dwg_path: Path, dxf_path: Path, dxf_version: str = "ACAD2013"):
    ver_map = {
        "R12": cad.imageoptions.DxfOutputVersion.R12,
        "ACAD2000": cad.imageoptions.DxfOutputVersion.R2000,
        "ACAD2013": cad.imageoptions.DxfOutputVersion.R2013,
        "ACAD2018": cad.imageoptions.DxfOutputVersion.R2018,
    }
    opts = DxfOptions()
    opts.version = ver_map.get(dxf_version.upper(), cad.imageoptions.DxfOutputVersion.R2013)

    dxf_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    # Context manager ensures file handles are released
    with Image.load(str(dwg_path)) as img:
        img.save(str(dxf_path), opts)
    return time.time() - start

# --- keep your imports ---

def dxf_options(dwg_path, dwg_file, dxf_path, dxf_file,
                start_time, total_files, idx):


    options = DxfOptions()
    options.version = cad.imageoptions.DxfOutputVersion.R12  # stays as you like

    start = time.time()
    with Image.load(dwg_path) as image:
        image.save(dxf_path, options)

    time_taken = time.time() - start_time
    eta = time_taken * (total_files - (idx + 1))
    print(f"\n{dwg_file} converted to {dxf_file} ({time_taken:.2f} sec)")
    print(f"Estimated time remaining: {eta / 60:.2f} minutes")


def print_dxf_file(dxf_file: str | Path, output_txt: bool = True):
    dxf_file = Path(dxf_file)
    if not dxf_file.exists():
        print(f"DXF not found: {dxf_file}")
        return
    doc = ezdxf.readfile(str(dxf_file))
    layer_names = [layer.dxf.name for layer in doc.layers]
    print(f"Layers in {dxf_file.name} ({len(layer_names)}):")
    for i, name in enumerate(layer_names, 1):
        print(f"{i}. {name}")

    if output_txt:
        out_txt = dxf_file.with_suffix("")  # remove .dxf
        out_txt = Path(str(out_txt) + "_layers.txt")
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(f"Total layers: {len(layer_names)}\n")
            for i, name in enumerate(layer_names, 1):
                f.write(f"{i}. {name}\n")
        print(f"Layer list written to {out_txt.name}")

# Function to handle DWG to DXF conversion
def convert_dwg_to_dxf(fdir, layers_only=False, skip_existing=True):
    root = Path(fdir)
    out_dir = root / "DXF_Converted"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Recurse (handles nested drops)
    dwg_files = sorted(root.rglob("*.dwg"))
    print(f"Found {len(dwg_files)} DWG files for conversion (recursive).")

    for i, dwg_path in enumerate(tqdm(dwg_files, desc="Converting DWG to DXF", unit="file")):
        rel = dwg_path.relative_to(root)
        dxf_path = out_dir / rel.with_suffix(".dxf")
        dxf_path.parent.mkdir(parents=True, exist_ok=True)

        if not layers_only:
            if skip_existing and dxf_path.exists():
                print(f"[skip] {dxf_path.name} (already exists)")
            else:
                try:
                    dxf_options(str(dwg_path), dwg_path.name, str(dxf_path), dxf_path.name,
                                time.time(), len(dwg_files), i)
                except Exception as e:
                    print(f"\nError converting {dwg_path.name}: {e}")

        # List layers only if file exists
        if dxf_path.exists():
            try:
                print_dxf_file(str(dxf_path))
            except Exception as e:
                print(f"\nError getting layers from DXF file {dxf_path.name}: {e}")
        else:
            print(f"[miss] DXF not found for {dwg_path.name}")

    print("Batch conversion completed successfully!")

# -------------- DXF -> PDF (LibreCAD) --------------
LIBRECAD_EXE  = r"C:\Users\bradley.eylander\scoop\apps\librecad\current\LibreCAD.exe"
# Quick manual test (PowerShell)
# & "C:\Users\bradley.eylander\scoop\apps\librecad\current\LibreCAD.exe" `
#   -export-pdf "C:\Users\bradley.eylander\Documents\temp\test.pdf" `
#   "C:\Users\bradley.eylander\Documents\Python\dwg_to_pdf\dwg_files\DXF_Converted\civil_example-imperial.dxf"


def dxf_to_pdf_librecad(dxf_root: str, pdf_out: str):
    """
    Batch convert DXF -> PDF using LibreCAD's console tool (dxf2pdf).
    One PDF per DXF. Handles duplicates by prefixing subfolder in filename.
    """
    dxf_root_p = Path(dxf_root)
    pdf_out_p = Path(pdf_out)
    pdf_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PDF export (LibreCAD).")

    for dxf in tqdm(dxfs, desc="DXF -> PDF (LibreCAD)", unit="file"):
        # Build a unique name using subpath pieces (avoid collisions)
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)
        out_pdf = pdf_out_p / f"{stem_unique}.pdf"
        if out_pdf.exists():
            # Skip if already converted (idempotent runs)
            continue

        # Many builds write output into the CWD with input basename.
        # We'll set cwd to the pdf_out folder and then rename if needed.
        cmd = f'"{LIBRECAD_EXE}" dxf2pdf "{dxf}"'
        try:
            _run1(cmd, cwd=pdf_out_p)
        except subprocess.CalledProcessError as e:
            print(f"!! LibreCAD failed on {dxf.name}: {e}")
            continue

        # If LibreCAD created <basename>.pdf, move/rename to our unique target
        default_pdf = pdf_out_p / (dxf.stem + ".pdf")
        if default_pdf.exists() and default_pdf != out_pdf:
            try:
                default_pdf.rename(out_pdf)
            except FileExistsError:
                # Extremely rare: if out_pdf suddenly exists, append a counter
                i = 2
                cand = pdf_out_p / f"{stem_unique} ({i}).pdf"
                while cand.exists():
                    i += 1
                    cand = pdf_out_p / f"{stem_unique} ({i}).pdf"
                default_pdf.rename(cand)


INKSCAPE_EXE = r"C:\Users\bradley.eylander\scoop\shims\inkscape.exe" 

# Quick manual test (PowerShell)
# & "C:\Users\bradley.eylander\scoop\shims\inkscape.exe" `
#   "C:\path\to\DXF_Converted\civil_example-imperial.dxf" `
#   --export-type=pdf `
#   --export-filename="C:\Users\bradley.eylander\Documents\temp\test.pdf"

def dxf_to_pdf_inkscape_simple(dxf_root: str, pdf_out: str,
                        test_run=False):
    dxf_root_p = Path(dxf_root)
    pdf_out_p  = Path(pdf_out)
    pdf_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PDF export (Inkscape).")

    for dxf in tqdm(dxfs, desc="DXF -> PDF (Inkscape)", unit="file"):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)  # avoid name collisions
        target_pdf = pdf_out_p / f"{stem_unique}.pdf"
        if target_pdf.exists():
            continue

        args = [INKSCAPE_EXE, str(dxf), "--export-type=pdf",
                f"--export-filename={str(target_pdf)}"]
        r = _run2(args)
        if r.returncode != 0 or not target_pdf.exists():
            print(f"!! Inkscape failed on {dxf.name}\nSTDERR:\n{r.stderr}\nSTDOUT:\n{r.stdout}")
        if test_run:
            break

def dxf_to_pdf_inkscape(
    dxf_root: str,
    pdf_out: str,
    *,
    area: str = "drawing",         # "drawing" or "page"
    margin_px: int = 10,           # padding around geometry when area="drawing"
    dpi: int | None = 150,         # None to skip, else typical 96/120/150/200
    overwrite: bool = False,
    use_actions_fallback: bool = True,
    test_run: bool = False
):
    """
    Convert DXF -> PDF with Inkscape, auto-fitting content so it doesn't crop.

    area="drawing"  -> export all geometry (recommended)
    area="page"     -> export the page area (if DXF defines one)

    margin_px: adds padding around geometry (area="drawing" only)
    dpi: use higher DPI to effectively see more content in the same page size
    overwrite: if False, skip PDFs that already exist
    use_actions_fallback: if True, try a second pass using --actions to
                          FitCanvasToDrawing if the first export fails
    """
    # Resolve inkscape exe: use your constant if present; else fallback to plain 'inkscape'
    try:
        inkscape = INKSCAPE_EXE  # provided elsewhere in your code
    except NameError:
        inkscape = "inkscape"

    dxf_root_p = Path(dxf_root)
    pdf_out_p  = Path(pdf_out)
    pdf_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PDF export (Inkscape).")
    
    for dxf in tqdm(dxfs, desc="DXF -> PDF (Inkscape)", unit="file"):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)  # avoid name collisions
        target_pdf = pdf_out_p / f"{stem_unique}.pdf"
        if target_pdf.exists() and not overwrite:
            continue

        # if 'NFA100000603581_297_01_fp_ Alphonso' not in stem_unique:
        #     continue

        # --- Primary attempt: --export-area-* flags ---
        args = [inkscape, str(dxf), "--export-type=pdf", f"--export-filename={str(target_pdf)}"]

        if area.lower() == "page":
            args.append("--export-area-page")
        else:
            args.append("--export-area-drawing")
            if margin_px and margin_px > 0:
                args.append(f"--export-margin={int(margin_px)}")

        if dpi is not None:
            args.append(f"--export-dpi={int(dpi)}")

        r = _run2(args)  # your existing runner
        if r.returncode == 0 and target_pdf.exists():
            continue  # success

        print(f"[warn] Primary export failed for {dxf.name}. Code={r.returncode}")
        if r.stderr:
            print(f"STDERR:\n{r.stderr}")
        if r.stdout:
            print(f"STDOUT:\n{r.stdout}")

        # --- Fallback attempt: fit canvas to drawing with actions, then export ---
        if use_actions_fallback:
            # We let actions control export; export-overwrite avoids prompts.
            # Note: we still pass export-filename so output goes where we want it.
            actions = [
                "select-all:all",
                "FitCanvasToSelection",
                "export-overwrite",
                "export-do",
                "FileClose",
            ]
            args2 = [
                inkscape,
                str(dxf),
                "--export-type=pdf",
                f"--export-filename={str(target_pdf)}",
                f"--actions={';'.join(actions)}",
            ]
            # DPI/margin are not used here; the canvas is resized to drawing.
            r2 = _run2(args2)
            if r2.returncode != 0 or not target_pdf.exists():
                print(f"!! Inkscape fallback failed on {dxf.name}\nSTDERR:\n{r2.stderr}\nSTDOUT:\n{r2.stdout}")
        if test_run:
            # only convert 1 file 
            break

if __name__ == "__main__":
    dxf_file = './dwg_files/DXF_Converted/civil_example-imperial.dxf'
    print_dxf_file(dxf_file, layers_only=True)