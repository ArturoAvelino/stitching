"""
Image stitching (Zigzag Pattern)

What it does:
- Reads a text file containing image file paths (one path per line).
- Arranges the images into a grid with the specified number of rows/cols.
- Stitches each row horizontally with a configurable overlap.
- Stitches the rows vertically with a configurable overlap.
- Alternates row direction (right-to-left then left-to-right), producing
  a zigzag scanline pattern commonly used in tiled captures.

Inputs:
- filename_list_path (positional CLI arg): Path to a text file that lists
  image paths, one per line. The number of lines must equal rows * cols.
- --rows: Number of rows in the grid (default: 13).
- --cols: Number of columns in the grid (default: 8).
- --h-overlap: Horizontal overlap between adjacent images in a row (pixels).
- --v-overlap: Vertical overlap between adjacent stitched rows (pixels).
- --output: Output filename. The extension is used to infer the format unless
  --format is provided.
- --format: Optional output format (jpg, jpeg, png, tif, tiff). If provided,
  the output filename extension is normalized to match the format.
- --force-bigtiff: Always write BigTIFF when output format is TIFF.

Output:
- A single stitched image file written to the path provided by --output.

Typical usage:
python tools/image_stitching_zigzag_pattern.py /path/to/images_to_stitch.txt \
  --rows 12 --cols 8 --h-overlap 372 --v-overlap 422 \
  --output /path/to/stitched.tiff --format tiff

Notes:
- All source images should have identical dimensions for best results.
- Overlap values must be less than the image width/height to avoid negative
  dimensions.
"""

from PIL import Image
import struct
import argparse
import math
from pathlib import Path
import sys

def read_image_filenames(filename):
    """Read image filenames from a text file."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f.readlines()]

def _load_first_image_size(image_paths):
    with Image.open(image_paths[0]) as img:
        return img.size, img.mode


def _compute_layout(rows, cols, tile_w, tile_h, h_overlap, v_overlap):
    if h_overlap >= tile_w or v_overlap >= tile_h:
        raise ValueError("Overlap values must be smaller than tile dimensions.")
    row_width = cols * tile_w - (cols - 1) * h_overlap
    total_height = rows * tile_h - (rows - 1) * v_overlap
    return row_width, total_height

def _normalize_output_path(output_path, output_format):
    out_path = Path(output_path)
    ext = out_path.suffix.lower().lstrip(".")
    if output_format is None:
        # Infer format from the file extension when not explicitly provided.
        if ext in {"tif", "tiff"}:
            return str(out_path), "TIFF"
        if ext in {"jpg", "jpeg"}:
            return str(out_path), "JPEG"
        if ext == "png":
            return str(out_path), "PNG"
        return str(out_path), None

    fmt = output_format.strip().lower()
    if fmt in {"tif", "tiff"}:
        fmt = "tiff"
    elif fmt in {"jpg", "jpeg"}:
        fmt = "jpeg"
    elif fmt == "png":
        fmt = "png"
    else:
        raise ValueError("Unsupported format. Use one of: jpg, jpeg, png, tif, tiff.")

    if ext != fmt:
        out_path = out_path.with_suffix(f".{fmt}")
    return str(out_path), fmt.upper()


def _estimate_uncompressed_size_bytes(image):
    width, height = image.size
    mode = image.mode
    try:
        info = Image.getmodeinfo(mode)
        if getattr(info, "bits", None):
            bpp = math.ceil(info.bits / 8)
        else:
            raise ValueError("Missing bits info")
    except Exception:
        if mode == "RGB":
            bpp = 3
        elif mode == "RGBA":
            bpp = 4
        elif mode == "L":
            bpp = 1
        elif mode == "LA":
            bpp = 2
        elif mode in {"I;16", "I;16B", "I;16L", "I;16N"}:
            bpp = 2
        elif mode in {"I", "F"}:
            bpp = 4
        else:
            bpp = len(image.getbands())
    return width * height * bpp


def _should_use_bigtiff(image):
    # Be conservative: BigTIFF is required when offsets exceed 32-bit.
    # Use >= to avoid edge cases right at the 4 GiB boundary.
    return _estimate_uncompressed_size_bytes(image) >= (2**32)

def _pillow_libtiff_available():
    try:
        from PIL import features
        return features.check("libtiff")
    except Exception:
        return False

def _tifffile_available():
    try:
        import tifffile  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False

def _save_tiff_with_tifffile(final_result, normalized_output_path, bigtiff):
    """
    Save TIFF via tifffile (supports BigTIFF). Uses deflate compression when possible.
    """
    import numpy as np
    import tifffile

    arr = np.asarray(final_result)
    compression = "deflate"
    kwargs = {
        "bigtiff": bigtiff,
        "compression": compression,
    }
    if final_result.mode in {"RGB", "RGBA"}:
        kwargs["photometric"] = "rgb"

    try:
        tifffile.imwrite(normalized_output_path, arr, **kwargs)
        return normalized_output_path
    except Exception:
        # Retry without compression in case compression backend is unavailable.
        tifffile.imwrite(normalized_output_path, arr, bigtiff=bigtiff)
        return normalized_output_path

def _save_with_pillow(final_result, normalized_output_path, pil_format, save_kwargs):
    if pil_format:
        final_result.save(normalized_output_path, format=pil_format, **save_kwargs)
    else:
        final_result.save(normalized_output_path, **save_kwargs)
    return normalized_output_path


def stitch_images(filename_list_path, rows=13, cols=8, h_overlap=300, v_overlap=400, output_path='stitched_image.jpg', output_format=None, force_bigtiff=False):
    """
    Stitch multiple images in a zigzag pattern with specified overlaps.
    """
    # Read image filenames
    filenames = read_image_filenames(filename_list_path)
    
    if len(filenames) != rows * cols:
        raise ValueError(f"Expected {rows * cols} images, but got {len(filenames)}")
    
    # Reshape filenames into a 2D array without numpy
    image_grid = [filenames[r * cols:(r + 1) * cols] for r in range(rows)]

    # Compute final canvas once, then paste tiles directly (no intermediate merges)
    (tile_w, tile_h), mode = _load_first_image_size(image_grid[0])
    final_width, final_height = _compute_layout(rows, cols, tile_w, tile_h, h_overlap, v_overlap)
    final_result = Image.new(mode, (final_width, final_height))

    for row_idx, row_images in enumerate(image_grid):
        left_to_right = (row_idx % 2 == 1)
        if left_to_right:
            ordered_paths = row_images
        else:
            ordered_paths = list(reversed(row_images))

        y = row_idx * (tile_h - v_overlap)
        for col_idx, img_path in enumerate(ordered_paths):
            x = col_idx * (tile_w - h_overlap)
            with Image.open(img_path) as img:
                if img.size != (tile_w, tile_h):
                    raise ValueError("All source images must have identical dimensions.")
                if img.mode != mode:
                    img = img.convert(mode)
                final_result.paste(img, (x, y))
    
    # Save the final result
    normalized_output_path, pil_format = _normalize_output_path(output_path, output_format)
    save_kwargs = {}
    if pil_format == "TIFF":
        # TIFF classic uses 32-bit offsets; switch to BigTIFF for very large images.
        if force_bigtiff or _should_use_bigtiff(final_result):
            save_kwargs["bigtiff"] = True

    if pil_format == "TIFF":
        needs_bigtiff = save_kwargs.get("bigtiff", False)
        if needs_bigtiff and _tifffile_available():
            _save_tiff_with_tifffile(final_result, normalized_output_path, bigtiff=True)
            return final_result

        # Try Pillow first (with compression to reduce size) when possible.
        if needs_bigtiff and not _pillow_libtiff_available():
            raise RuntimeError(
                "This Pillow build cannot write BigTIFF and tifffile is not available. "
                "Install tifffile (and numpy) or use a Pillow build with libtiff to write BigTIFF."
            )

        save_kwargs.setdefault("compression", "tiff_deflate")
        try:
            _save_with_pillow(final_result, normalized_output_path, pil_format, save_kwargs)
        except struct.error:
            # Retry BigTIFF if classic TIFF overflows 32-bit offsets.
            if not save_kwargs.get("bigtiff"):
                save_kwargs["bigtiff"] = True
                _save_with_pillow(final_result, normalized_output_path, pil_format, save_kwargs)
            else:
                raise
    else:
        _save_with_pillow(final_result, normalized_output_path, pil_format, save_kwargs)
    return final_result

def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Stitch multiple images in a zigzag pattern with specified overlaps."
    )
    parser.add_argument("filename_list_path", help="Path to text file with one image path per line.")
    parser.add_argument("--rows", type=int, default=13, help="Number of rows in the image grid.")
    parser.add_argument("--cols", type=int, default=8, help="Number of columns in the image grid.")
    parser.add_argument("--h-overlap", type=int, default=300, help="Horizontal overlap in pixels.")
    parser.add_argument("--v-overlap", type=int, default=400, help="Vertical overlap in pixels.")
    parser.add_argument("--output", default="stitched_image.jpg", help="Output filename (extension optional).")
    parser.add_argument(
        "--format",
        choices=["jpg", "jpeg", "png", "tif", "tiff"],
        help="Optional output format. Use 'tif' or 'tiff' for TIFF output.",
    )
    parser.add_argument(
        "--force-bigtiff",
        action="store_true",
        help="Always write BigTIFF when output format is TIFF.",
    )
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.force_bigtiff:
        if args.format and args.format.lower() not in {"tif", "tiff"}:
            parser.error("--force-bigtiff requires --format tif or tiff.")
        if not args.format:
            output_ext = Path(args.output).suffix.lower()
            if output_ext not in {".tif", ".tiff"}:
                parser.error("--force-bigtiff requires TIFF output (use --format tif/tiff or a .tif/.tiff filename).")

    stitch_images(
        args.filename_list_path,
        rows=args.rows,
        cols=args.cols,
        h_overlap=args.h_overlap,
        v_overlap=args.v_overlap,
        output_path=args.output,
        output_format=args.format,
        force_bigtiff=args.force_bigtiff,
    )


if __name__ == "__main__":
    main()
