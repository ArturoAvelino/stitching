#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Draw vertical and horizontal lines near image borders and save copies."
        )
    )
    parser.add_argument("--image-path", help="Full path to a single input image.")
    parser.add_argument(
        "--image-batch-dir",
        help="Directory containing images to process in batch.",
    )
    parser.add_argument(
        "--image-filename-pattern",
        default="*.jpg",
        help="Filename pattern for batch mode. Default: *.jpg",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where output images will be saved.",
    )

    parser.add_argument(
        "--line-color",
        default="red",
        help="Color of the border line and filename text (e.g., 'red' or '#FF0000').",
    )
    parser.add_argument(
        "--color-lines-left",
        help="Color for vertical lines drawn from the left side.",
    )
    parser.add_argument(
        "--color-lines-right",
        help="Color for vertical lines drawn from the right side.",
    )
    parser.add_argument(
        "--color-lines-top",
        help="Color for horizontal lines drawn from the top side.",
    )
    parser.add_argument(
        "--color-lines-bottom",
        help="Color for horizontal lines drawn from the bottom side.",
    )
    parser.add_argument(
        "--line-width",
        type=int,
        default=1,
        help="Line width in pixels.",
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=5,
        help="Step size in pixels between lines.",
    )
    parser.add_argument(
        "--range-start",
        type=int,
        default=0,
        help="Start of the range (in pixels) from each border.",
    )
    parser.add_argument(
        "--range-end",
        type=int,
        default=0,
        help="End of the range (in pixels) from each border.",
    )
    parser.add_argument(
        "--horizontal",
        action="store_true",
        help="Draw horizontal lines within the specified range.",
    )
    parser.add_argument(
        "--vertical",
        action="store_true",
        help="Draw vertical lines within the specified range.",
    )
    parser.add_argument(
        "--draw-border-line",
        action="store_true",
        help="Draw a line along the image frame (all borders).",
    )
    parser.add_argument(
        "--write-filename",
        action="store_true",
        help="Write the image filename at the center of the image.",
    )
    parser.add_argument(
        "--font-path",
        help="Optional path to a .ttf font file for filename rendering.",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        help="Font size in pixels (default: image_height/20).",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.image_path and not args.image_batch_dir:
        raise SystemExit("Provide --image-path or --image-batch-dir.")
    if args.image_path and args.image_batch_dir:
        raise SystemExit("Provide only one of --image-path or --image-batch-dir.")
    if args.line_width <= 0:
        raise SystemExit("--line-width must be > 0.")
    if args.step_size <= 0:
        raise SystemExit("--step-size must be > 0.")
    if args.range_start < 0 or args.range_end < 0:
        raise SystemExit("--range-start and --range-end must be >= 0.")
    if args.range_end < args.range_start:
        raise SystemExit("--range-end must be >= --range-start.")
    if not args.horizontal and not args.vertical and not args.draw_border_line:
        raise SystemExit(
            "Nothing to draw. Set --horizontal and/or --vertical and/or --draw-border-line."
        )


def iter_image_paths(args: argparse.Namespace) -> Iterable[Path]:
    if args.image_path:
        return [Path(args.image_path)]
    batch_dir = Path(args.image_batch_dir)
    pattern = args.image_filename_pattern
    return sorted(batch_dir.glob(pattern))


def load_font(font_path: Optional[str], font_size: int) -> ImageFont.ImageFont:
    if font_path:
        return ImageFont.truetype(font_path, font_size)
    # DejaVuSans is commonly bundled with Pillow
    try:
        return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except OSError:
        return ImageFont.load_default(size=font_size)


def draw_lines(
    image: Image.Image,
    color_lines_left: str,
    color_lines_right: str,
    color_lines_top: str,
    color_lines_bottom: str,
    line_width: int,
    step_size: int,
    range_start: int,
    range_end: int,
    draw_horizontal: bool,
    draw_vertical: bool,
    draw_border_line: bool,
    border_color: str,
) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size

    if draw_border_line:
        draw.rectangle([0, 0, width - 1, height - 1], outline=border_color, width=line_width)

    offsets = range(range_start, range_end + 1, step_size)

    if draw_vertical:
        for offset in offsets:
            x_left = offset
            x_right = (width - 1) - offset
            if 0 <= x_left < width:
                draw.line(
                    [(x_left, 0), (x_left, height - 1)],
                    fill=color_lines_left,
                    width=line_width,
                )
            if 0 <= x_right < width:
                draw.line(
                    [(x_right, 0), (x_right, height - 1)],
                    fill=color_lines_right,
                    width=line_width,
                )

    if draw_horizontal:
        for offset in offsets:
            y_top = offset
            y_bottom = (height - 1) - offset
            if 0 <= y_top < height:
                draw.line(
                    [(0, y_top), (width - 1, y_top)],
                    fill=color_lines_top,
                    width=line_width,
                )
            if 0 <= y_bottom < height:
                draw.line(
                    [(0, y_bottom), (width - 1, y_bottom)],
                    fill=color_lines_bottom,
                    width=line_width,
                )


def draw_filename(
    image: Image.Image,
    filename: str,
    font_path: Optional[str],
    font_size: Optional[int],
    text_color: str,
) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    size = font_size if font_size else max(10, height // 20)
    font = load_font(font_path, size)
    text = filename

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    y = (height - text_h) // 2
    draw.text((x, y), text, fill=text_color, font=font)


def process_image(
    path: Path,
    args: argparse.Namespace,
    output_dir: Path,
    color_lines_left: str,
    color_lines_right: str,
    color_lines_top: str,
    color_lines_bottom: str,
) -> None:
    with Image.open(path) as img:
        img = img.convert("RGB")
        draw_lines(
            img,
            color_lines_left=color_lines_left,
            color_lines_right=color_lines_right,
            color_lines_top=color_lines_top,
            color_lines_bottom=color_lines_bottom,
            line_width=args.line_width,
            step_size=args.step_size,
            range_start=args.range_start,
            range_end=args.range_end,
            draw_horizontal=args.horizontal,
            draw_vertical=args.vertical,
            draw_border_line=args.draw_border_line,
            border_color=args.line_color,
        )
        if args.write_filename:
            draw_filename(img, path.name, args.font_path, args.font_size, args.line_color)

        output_path = output_dir / path.name
        img.save(output_path)
