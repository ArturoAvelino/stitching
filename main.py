#!/usr/bin/env python3
from pathlib import Path

from src.draw_lines_in_images import (
    iter_image_paths,
    parse_args,
    process_image,
    validate_args,
)


def main() -> None:
    args = parse_args()
    validate_args(args)

    color_lines_left = args.color_lines_left or args.line_color
    color_lines_right = args.color_lines_right or args.line_color
    color_lines_top = args.color_lines_top or args.line_color
    color_lines_bottom = args.color_lines_bottom or args.line_color

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = list(iter_image_paths(args))
    if not paths:
        raise SystemExit("No images found with the given input.")

    for path in paths:
        process_image(
            path,
            args,
            output_dir,
            color_lines_left,
            color_lines_right,
            color_lines_top,
            color_lines_bottom,
        )


if __name__ == "__main__":
    main()
