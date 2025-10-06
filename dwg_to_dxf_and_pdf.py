# dwg_to_dxf_and_pdf.py
import aspose.cad as cad
from aspose.cad.imageoptions import DxfOptions, CadRasterizationOptions
from aspose.cad import Color  # Correct Color import
import os
import time
from tqdm import tqdm  # Progress bar
import argparse  # For command-line arguments
from pathlib import Path

# local
import support


#  Main function to handle both command-line and VSCode front-end execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DWG -> DXF and then DXF -> PDF (LibreCAD)")
    parser.add_argument("--directory", help="Path to the directory containing DWG files")
    parser.add_argument("--layers_only", action="store_true", help="Only list layers from existing DXFs")
    args = parser.parse_args()

    if args.directory:
        input_directory = args.directory
    else:
        input_directory = r'./dwg_files'

    if not os.path.isdir(input_directory):
        raise SystemExit(f"Error: The directory '{input_directory}' does not exist.")

    print(f"Input directory: {input_directory}")
    support.convert_dwg_to_dxf(input_directory, layers_only=args.layers_only, skip_existing=True)

    # DXF -> PDF via LibreCAD
    dxf_root = str(Path(input_directory) / "DXF_Converted")
    pdf_out  = str(Path(input_directory) / "PDF_From_DXF")
    # support.dxf_to_pdf_librecad(dxf_root, pdf_out)
    # Auto-fit full geometry, add 10px margin, and “zoom out” a bit via 150 DPI
    support.dxf_to_pdf_inkscape(
        dxf_root,
        pdf_out,
        area="drawing",
        margin_px=10,
        dpi=150,
        overwrite=False,
        use_actions_fallback=True,
    )