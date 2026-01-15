# support.py
import aspose.cad as cad
import time
from aspose.cad import Image
import ezdxf
from tqdm import tqdm  # Progress bar
import subprocess
import shlex
from pathlib import Path
# Context manager = no file locks
from aspose.cad import Image
from aspose.cad.imageoptions import (
    DxfOptions,
    CadRasterizationOptions,
    PdfOptions,
    PngOptions,
    JpegOptions,
)
from configparser import ConfigParser
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import LayoutProperties
import matplotlib.pyplot as plt

def load_ini(path: str | Path = "config.ini") -> ConfigParser:
    cfg = ConfigParser()
    cfg.read(path)
    return cfg

_cfg = load_ini()

INKSCAPE_EXE = _cfg.get("paths", "INKSCAPE_EXE", fallback="inkscape")
LIBRECAD_EXE = _cfg.get("paths", "LIBRECAD_EXE", fallback=None)

DWG_FILES = _cfg.get("input_dirs", "DWG_FILES", fallback=None)
DWG_FILES_TEST = _cfg.get("input_dirs", "DWG_FILES_TEST", fallback=None)

def validate_external_tools():
    for name, exe in {
        "Inkscape": INKSCAPE_EXE,
        "LibreCAD": LIBRECAD_EXE,
    }.items():
        if exe and not Path(exe).exists():
            print(f"WARNING: {name} executable not found: {exe}")

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
                continue
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
# Quick manual test (PowerShell)
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
    dpi: int | None = 150,         # None to skip
    overwrite: bool = False,
    use_actions_fallback: bool = True,
    test_run: bool = False,
    add_filename: str | None = None,
):
    """
    Convert DXF -> PDF with Inkscape.

    Primary path: --export-area-drawing or --export-area-page.
    Fallback: use actions (select-all + FitCanvasToDrawing) if primary fails.

    add_filename: if provided, appended to the stem before ".pdf"
                  e.g., "_inkscape" → "filename_inkscape.pdf".
    """

    try:
        inkscape = INKSCAPE_EXE  # defined elsewhere in your code
    except NameError:
        inkscape = "inkscape"

    dxf_root_p = Path(dxf_root)
    pdf_out_p  = Path(pdf_out)
    pdf_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PDF export (Inkscape).")

    for idx, dxf in enumerate(tqdm(dxfs, desc="DXF -> PDF (Inkscape)", unit="file")):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)
        if add_filename:
            stem_unique = f"{stem_unique}{add_filename}"
        target_pdf = pdf_out_p / f"{stem_unique}.pdf"

        if target_pdf.exists() and not overwrite:
            continue

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

        r = _run2(args)
        if r.returncode == 0 and target_pdf.exists():
            if test_run and idx == 0:
                break
            continue  # success

        print(f"[warn] Primary export failed for {dxf.name}. Code={r.returncode}")
        if r.stderr:
            print(f"STDERR:\n{r.stderr}")
        if r.stdout:
            print(f"STDOUT:\n{r.stdout}")

        # --- Fallback attempt: fit canvas to drawing with actions, then export ---
        if use_actions_fallback:
            actions = [
                "select-all:all",
                "FitCanvasToDrawing",
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
            r2 = _run2(args2)
            if r2.returncode != 0 or not target_pdf.exists():
                print(f"!! Inkscape fallback failed on {dxf.name}")
                if r2.stderr:
                    print(f"STDERR:\n{r2.stderr}")
                if r2.stdout:
                    print(f"STDOUT:\n{r2.stdout}")

        if test_run and idx == 0:
            break

def dxf_to_pdf_aspose(
    dxf_root: str,
    pdf_out: str,
    *,
    page_width: float = 2200.0,
    page_height: float = 1700.0,   # ~11:8.5 landscape aspect ratio
    overwrite: bool = False,
    test_run: bool = False,
    add_filename: str | None = None,
    # kept for future compatibility, but NOT used in this Aspose version:
    exclude_layers: set[str] | None = None,
):
    """
    Convert DXF -> PDF using Aspose.CAD.

    - Page shape: Letter-style landscape (11:8.5 aspect ratio).
    - exclude_layers: names like {"0", "O"} you would *like* to drop.
      Actual filtering only works if this Aspose.CAD build exposes
      `image.layers`. Otherwise we emit a warning and render all layers.
    """

    dxf_root_p = Path(dxf_root)
    pdf_out_p  = Path(pdf_out)
    pdf_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PDF export (Aspose).")

    # Normalize exclude list once
    if exclude_layers:
        exclude_layers_lower = {name.strip().lower() for name in exclude_layers}
    else:
        exclude_layers_lower = set()

    for idx, dxf in enumerate(tqdm(dxfs, desc="DXF -> PDF (Aspose)", unit="file")):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)
        if add_filename:
            stem_unique = f"{stem_unique}{add_filename}"
        target_pdf = pdf_out_p / f"{stem_unique}.pdf"

        if target_pdf.exists() and not overwrite:
            continue

        print(f"Converting {dxf} -> {target_pdf}")

        # Aspose.CAD in your environment: use Image.load, no .layers available
        with cad.Image.load(str(dxf)) as image:
            raster_opts = CadRasterizationOptions()
            raster_opts.page_width  = float(page_width)
            raster_opts.page_height = float(page_height)
            raster_opts.no_scaling = False
            raster_opts.background_color = cad.Color.white

            # ---------- CONDITIONAL LAYER FILTERING ----------
            if exclude_layers_lower:
                # Only works if this Aspose build exposes `layers`
                if hasattr(image, "layers"):
                    # This branch will *not* run on your current build,
                    # but will start working automatically if you upgrade.
                    for layer in image.layers:
                        name = (getattr(layer, "layer_name", "") or "").strip()
                        if name.lower() not in exclude_layers_lower:
                            raster_opts.layers.add(name)
                else:
                    # Current situation: this is what will execute now.
                    print(
                        "WARNING: exclude_layers requested, but this Aspose.CAD "
                        "version does not expose 'image.layers'. "
                        "Rendering all layers."
                    )
            # If exclude_layers is empty, we just render all layers by default.
            # -------------------------------------------------

            pdf_opts = PdfOptions()
            pdf_opts.vector_rasterization_options = raster_opts

            image.save(str(target_pdf), pdf_opts)

        if test_run:
            break

def dxf_to_image_aspose(
    dxf_root: str,
    img_out: str,
    *,
    fmt: str = "png",               # "png" or "jpg" / "jpeg"
    page_width: float = 2200.0,     # controls framing similarly to your PDF
    page_height: float = 1700.0,
    raster_width_px: int | None = None,   # optional explicit raster size
    raster_height_px: int | None = None,
    jpeg_quality: int = 90,         # only applies to JPEG
    overwrite: bool = False,
    test_run: bool = False,
    add_filename: str | None = None,
):
    """
    Convert DXF -> PNG/JPG using Aspose.CAD.

    - page_width/page_height: sets the "paper" aspect/frame (same as your PDF approach)
    - raster_width_px/raster_height_px: optional explicit pixel dimensions (if supported)
    - fmt: "png" or "jpg"/"jpeg"
    - add_filename: suffix appended to output filename stem (e.g., "_png")
    """

    fmt_norm = fmt.strip().lower()
    if fmt_norm in ("jpg", "jpeg"):
        out_ext = "jpg"
    elif fmt_norm == "png":
        out_ext = "png"
    else:
        raise ValueError("fmt must be 'png' or 'jpg'/'jpeg'")

    dxf_root_p = Path(dxf_root)
    img_out_p  = Path(img_out)
    img_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for image export (Aspose -> {out_ext.upper()}).")

    for idx, dxf in enumerate(tqdm(dxfs, desc=f"DXF -> {out_ext.upper()} (Aspose)", unit="file")):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)
        if add_filename:
            stem_unique = f"{stem_unique}{add_filename}"
        target_img = img_out_p / f"{stem_unique}.{out_ext}"

        if target_img.exists() and not overwrite:
            continue

        with cad.Image.load(str(dxf)) as image:
            raster_opts = CadRasterizationOptions()
            raster_opts.page_width  = float(page_width)
            raster_opts.page_height = float(page_height)
            raster_opts.no_scaling = False
            raster_opts.background_color = cad.Color.white

            # Optional explicit pixel sizing (only if your Aspose build supports it)
            if raster_width_px is not None and hasattr(raster_opts, "rasterization_width"):
                raster_opts.rasterization_width = int(raster_width_px)
            if raster_height_px is not None and hasattr(raster_opts, "rasterization_height"):
                raster_opts.rasterization_height = int(raster_height_px)

            if out_ext == "png":
                opts = PngOptions()
                opts.vector_rasterization_options = raster_opts
                image.save(str(target_img), opts)
            else:
                opts = JpegOptions()
                opts.vector_rasterization_options = raster_opts
                # quality property name varies; guard it
                if hasattr(opts, "quality"):
                    opts.quality = int(jpeg_quality)
                image.save(str(target_img), opts)

        if test_run:
            break

from pathlib import Path
from tqdm import tqdm
import subprocess

def dxf_to_png_inkscape(
    dxf_root: str,
    img_out: str,
    *,
    dpi: int = 200,
    margin_px: int = 10,
    overwrite: bool = False,
    test_run: bool = False,
    add_filename: str | None = None,
    timeout_s: int = 60,  # <-- prevents “hang forever”
):
    """
    Convert DXF -> PNG using Inkscape (single-pass).

    Notes:
    - Uses --export-area-drawing to capture the drawing extents.
    - Adds optional --export-margin.
    - Uses a timeout so problematic DXFs don’t stall the whole batch.
    """
    inkscape = INKSCAPE_EXE if "INKSCAPE_EXE" in globals() else "inkscape"

    dxf_root_p = Path(dxf_root)
    img_out_p  = Path(img_out)
    img_out_p.mkdir(parents=True, exist_ok=True)

    dxfs = sorted(dxf_root_p.rglob("*.dxf"))
    print(f"Found {len(dxfs)} DXF files for PNG export (Inkscape single-pass).")

    for idx, dxf in enumerate(tqdm(dxfs, desc="DXF -> PNG (Inkscape)", unit="file")):
        rel = dxf.relative_to(dxf_root_p)
        stem_unique = "_".join(rel.with_suffix("").parts)
        if add_filename:
            stem_unique = f"{stem_unique}{add_filename}"

        target_png = img_out_p / f"{stem_unique}.png"
        if target_png.exists() and not overwrite:
            continue

        args = [
            inkscape,
            str(dxf),
            "--export-type=png",
            f"--export-filename={str(target_png)}",
            "--export-area-drawing",
            f"--export-dpi={int(dpi)}",
        ]

        if margin_px and margin_px > 0:
            args.append(f"--export-margin={int(margin_px)}")

        try:
            r = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            print(f"!! TIMEOUT ({timeout_s}s): {dxf.name} (skipping)")
            continue

        if r.returncode != 0 or not target_png.exists():
            print(f"!! Inkscape DXF->PNG failed on {dxf.name} (code={r.returncode})")
            if r.stderr:
                print(f"STDERR:\n{r.stderr}")
            if r.stdout:
                print(f"STDOUT:\n{r.stdout}")
            # Make sure we don't leave a corrupt file behind
            try:
                target_png.unlink(missing_ok=True)
            except Exception:
                pass
            continue

        if test_run:
            break


def dxf_to_png_ezdxf(
    dxf_root: str,
    img_out: str,
    *,
    dpi: int = 200,
    overwrite: bool = False,
    test_run: bool = False,
):
    dxf_root_p = Path(dxf_root)
    img_out_p = Path(img_out)
    img_out_p.mkdir(parents=True, exist_ok=True)
    dxfs = sorted(dxf_root_p.rglob("*.dxf"))    
    for dxf in tqdm(dxfs, desc="DXF -> PNG (ezdxf Fast)", unit="file"):
        target_png = img_out_p / f"{'_'.join(dxf.relative_to(dxf_root_p).with_suffix('').parts)}.png"
        if target_png.exists() and not overwrite:
            continue
        try:
            doc = ezdxf.readfile(dxf)
            msp = doc.modelspace()
            # --- FIX 1: Missing Layers ---
            # Force all layers to be visible and unfrozen
            for layer in doc.layers:
                layer.on()
                layer.thaw()
            # --- FIX 2: Color Mapping & Background ---
            # LayoutProperties tells ezdxf to swap 'Color 7' to black 
            # because the background is white.
            ctx = RenderContext(doc)
            layout_props = LayoutProperties.from_layout(msp)
            layout_props.set_colors(bg="#FFFFFF") # Sets logical white background
            fig = plt.figure(frameon=True)
            fig.patch.set_facecolor("white")
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_facecolor("white")
            ax.set_axis_off()
            out = MatplotlibBackend(ax)            
            # finalize=True is critical for bounding box calculation
            Frontend(ctx, out).draw_layout(msp, finalize=True, layout_properties=layout_props)
            # --- FIX 3: Clipping ---
            # bbox_inches='tight' works better when the layout_properties are set
            fig.savefig(target_png, dpi=dpi, bbox_inches='tight', pad_inches=0.1, facecolor=fig.get_facecolor())
            plt.close(fig)
        except Exception as e:
            print(f"!! Failed {dxf.name}: {e}")
            continue
        if test_run: break

if __name__ == "__main__":
    dxf_folder = './dwg_files/DXF_Converted'
    dxf_file = './dwg_files/DXF_Converted/civil_example-imperial.dxf'
    print_dxf_file(dxf_file)

    dxf_to_pdf_aspose(
        dxf_root=dxf_folder,
        pdf_out=dxf_folder,
        page_width=2200.0,
        page_height=1700.0,  # 2200 / 1700 ≈ 1.294, “Letter-style” landscape
        overwrite=True,
        test_run=True,
        add_filename='_clean',
        exclude_layers={"0", "O"},   # currently ignored (no layer API)
    )

    # dxf_to_pdf_inkscape(
    #     dxf_folder,
    #     dxf_folder,
    #     area="drawing",
    #     margin_px=10,
    #     dpi=150,
    #     overwrite=True,
    #     use_actions_fallback=True,
    #     add_filename='inkspace'
    # )