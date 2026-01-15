# dwg_to_dxf_and_pdf.py
import os
import argparse  # For command-line arguments
from pathlib import Path

# local
import support


#  Main function to handle both command-line and VSCode front-end execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DWG -> DXF and DXF -> PDF/PNG")
    parser.add_argument("--directory", help="Path to the directory containing DWG/DXF files")

    parser.add_argument("--layers_only", action="store_true", help="Only list layers from existing DXFs")

    # Output selection
    parser.add_argument("--to_pdf", action="store_true", help="Convert DXF -> PDF")
    parser.add_argument("--to_png", action="store_true", help="Convert DXF -> PNG")

    # PDF backends
    parser.add_argument("--inkscape", action="store_true", help="Use Inkscape for DXF -> PDF")
    parser.add_argument("--aspose", action="store_true", help="Use Aspose for DXF -> PDF")

    # Convenience
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--test_run", action="store_true", help="Only process the first DXF")

    args = parser.parse_args()

    if args.directory:
        input_directory = args.directory
    else:
        input_directory  = support.DWG_FILES
        # input_directory = support.DWG_FILES_TEST
        # defaults when running without CLI flags
        args.to_pdf = True
        args.to_png = True
        args.inkscape = False
        args.ezdxf = True
        args.aspose = True
        args.overwrite = False
        args.test_run = False

    if not os.path.isdir(input_directory):
        raise SystemExit(f"Error: The directory '{input_directory}' does not exist.")

    support.validate_external_tools()

    print(f"Input directory: {input_directory}")
    support.convert_dwg_to_dxf(input_directory, layers_only=args.layers_only, skip_existing=True)

    # DXF -> PDF via LibreCAD
    dxf_root = str(Path(input_directory) / "DXF_Converted")
    pdf_out  = str(Path(input_directory) / "PDF_From_DXF")
    pdf_out_inkscape  = str(Path(input_directory) / "PDF_From_DXF_inkscape")
    img_out  = str(Path(input_directory) / "IMG_From_DXF")
    img_out_inkscape  = str(Path(input_directory) / "IMG_From_DXF_inkscape")
    # If no flags are provided, default to PDF (your current behavior)
    if not (args.to_pdf or args.to_png ):        
        args.to_pdf = True
        args.to_png = True
        
    # support.dxf_to_pdf_librecad(dxf_root, pdf_out)
    # Auto-fit full geometry, add 10px margin, and “zoom out” a bit via 150 DPI
    if args.to_pdf:
        if args.inkscape:
            support.dxf_to_pdf_inkscape(
                dxf_root,
                pdf_out_inkscape,
                area="drawing",   # currently unused but OK
                margin_px=10,
                dpi=150,
                overwrite=args.overwrite,
                test_run=args.test_run,   # or True if you want to test only 1 file
            )
        if args.aspose :
            support.dxf_to_pdf_aspose(
                dxf_root,
                pdf_out,
                page_width=2200.0,
                page_height=1700.0,  # 2200 / 1700 ≈ 1.294
                overwrite=args.overwrite,
                test_run=args.test_run,   # or True if you want to test only 1 file
            )
    if args.to_png:
        if args.aspose :
            support.dxf_to_image_aspose(
                dxf_root,
                img_out,
                fmt="png",
                page_width=2200.0,
                page_height=1700.0,
                overwrite=args.overwrite,
                test_run=args.test_run
            )
        if args.inkscape:
            support.dxf_to_png_inkscape(
                dxf_root,
                img_out_inkscape,
                margin_px=25,
                dpi=200,
                overwrite=args.overwrite,
                test_run=args.test_run,
                timeout_s=60,
            )
        if args.ezdxf:
            # Use the new fast function
            support.dxf_to_png_ezdxf(
                dxf_root,
                img_out + "_ezdxf", # Output to a different folder to compare
                dpi=200,
                overwrite=args.overwrite,
                test_run=args.test_run,
            )