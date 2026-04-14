# Image Border Line Drawer

A command-line Python tool that copies images and draws configurable vertical and horizontal lines near the borders. It can also draw a full border frame and optionally write the filename centered on the image.

The script is designed for large photos (for example 6000 x 4000 JPGs around 6.5 MB) but works with any image size supported by Pillow.

## Features
- Draw vertical lines from the left and right borders using a pixel range and step size.
- Draw horizontal lines from the top and bottom borders using a pixel range and step size.
- Optional border frame around the full image.
- Optional centered filename text.
- Batch processing by directory and filename pattern.

## Requirements
- Python 3.8+
- Pillow

Install dependencies:
```bash
python -m pip install pillow
```

## Usage
The script is located at:
```bash
python /Users/aavelino/PycharmProjects/stitching/src/draw_lines_in_images.py [options]
```

You must provide either a single image path (`--image-path`) or a batch directory (`--image-batch-dir`). The output directory is required.

### Single image
```bash
python /Users/aavelino/PycharmProjects/stitching/src/draw_lines_in_images.py \
  --image-path /full/path/to/image.jpg \
  --output-dir /full/path/to/output \
  --vertical --horizontal \
  --line-color "white" \
  --line-width 1 \
  --step-size 5 \
  --range-start 400 \
  --range-end 450 \
  --draw-border-line \
  --write-filename
```

### Batch processing
```bash
python /Users/aavelino/PycharmProjects/stitching/src/draw_lines_in_images.py \
  --image-batch-dir /full/path/to/images \
  --image-filename-pattern "*.jpg" \
  --output-dir /full/path/to/output \
  --vertical --horizontal \
  --line-color "white" \
  --line-width 1 \
  --step-size 5 \
  --range-start 400 \
  --range-end 450
```

### Per-side line colors
```bash
python /Users/aavelino/PycharmProjects/stitching/src/draw_lines_in_images.py \
  --image-path /full/path/to/image.jpg \
  --output-dir /full/path/to/output \
  --vertical --horizontal \
  --color-lines-left "#FF0000" \
  --color-lines-right "#00FF00" \
  --color-lines-top "#0000FF" \
  --color-lines-bottom "#FFA500" \
  --line-width 2 \
  --step-size 5 \
  --range-start 50 \
  --range-end 150
```

## How line placement works
For vertical lines, the script counts pixels from both the left and right image borders:
- From the left border, it draws the first line at `range-start` pixels, then every `step-size` pixels up to `range-end`.
- From the right border, it does the same but counting from right to left.

For horizontal lines, the logic is the same but starting from the top and bottom borders.

Example: with `--step-size 5 --range-start 400 --range-end 450`, the script draws lines at 400, 405, 410, ... , 450 pixels from each border.

## Parameters

### Input selection
- `--image-path`: Full path to a single image file.
- `--image-batch-dir`: Path to a directory of images to process.
- `--image-filename-pattern`: Pattern for batch processing (default `*.jpg`).

### Output
- `--output-dir` (required): Directory where output images are saved. The output filename matches the input filename.

### Line styling and layout
- `--line-color`: Color name (e.g., `red`) or hex (e.g., `#FF0000`). Default: `red`.
- `--color-lines-left`: Color for vertical lines drawn from the left side. Default: `--line-color`.
- `--color-lines-right`: Color for vertical lines drawn from the right side. Default: `--line-color`.
- `--color-lines-top`: Color for horizontal lines drawn from the top side. Default: `--line-color`.
- `--color-lines-bottom`: Color for horizontal lines drawn from the bottom side. Default: `--line-color`.
- `--line-width`: Line width in pixels. Default: `1`.
- `--step-size`: Step size in pixels between lines. Default: `5`.
- `--range-start`: Start of the drawing range in pixels from each border. Default: `0`.
- `--range-end`: End of the drawing range in pixels from each border. Default: `0`.
- `--horizontal`: If set, draw horizontal lines within the range.
- `--vertical`: If set, draw vertical lines within the range.
- `--draw-border-line`: If set, draw a full border frame around the image.

### Text options
- `--write-filename`: If set, write the image filename at the center of the image.
- `--font-path`: Optional path to a `.ttf` font file.
- `--font-size`: Optional font size in pixels. Default is `image_height / 20` (minimum 10).

## Output
The script writes a copy of each input image to `--output-dir` with the same filename. The image is saved in RGB mode using Pillow’s default settings for the output format inferred by the file extension.

## Error handling and constraints
- You must provide exactly one of `--image-path` or `--image-batch-dir`.
- `--line-width` and `--step-size` must be greater than 0.
- `--range-start` and `--range-end` must be non-negative and `range-end >= range-start`.
- At least one of `--horizontal`, `--vertical`, or `--draw-border-line` must be set.

## Notes
- If you want text color different from line color, ask to add a separate text color flag.
- If your environment does not have `DejaVuSans.ttf`, the script falls back to Pillow’s default font.
