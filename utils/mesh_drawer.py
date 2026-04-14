import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional


class MeshDrawer:
    """
    A class for drawing a mesh of thin horizontal and vertical lines on images.

    The mesh starts from the center of the image and extends to the borders.
    Includes optional scale bar and subscale markings.
    """

    def __init__(
            self,
            line_color: str = "gray",
            pixels_per_mm: float = 476.0,
            line_distance_mm: float = 1.0,
            line_width: int = 1,
            scale_size_mm: float = 1.0,
            scale_position: str = "bottom_right",
            subscale_distance_mm: float = 0.2,
            image_size: Tuple[int, int] = (1000, 667),
            draw_scale: bool = False,
            draw_subscales: bool = False
    ):
        """
        Initialize the MeshDrawer.

        Args:
            line_color: Color of the mesh lines (default: "gray")
            pixels_per_mm: Conversion factor from mm to pixels (default: 476)
            line_distance_mm: Distance between mesh lines in mm (default: 1.0)
            line_width: Width of the mesh lines in pixels (default: 1)
            scale_size_mm: Size of the scale bar in mm (default: 1.0)
            scale_position: Position of scale bar ("top_left", "top_right",
                          "bottom_left", "bottom_right") (default: "bottom_right")
            subscale_distance_mm: Distance between subscale marks in mm (default: 0.2)
            image_size: Default image size (width, height) in pixels (default: (1000, 667))
            draw_scale: Whether to draw the scale bar (default: False)
            draw_subscales: Whether to draw subscale marks (default: False)
        """
        self.line_color = line_color
        self.pixels_per_mm = pixels_per_mm
        self.line_distance_mm = line_distance_mm
        self.line_width = max(1, line_width)  # Ensure minimum width of 1
        self.scale_size_mm = scale_size_mm
        self.scale_position = scale_position
        self.subscale_distance_mm = subscale_distance_mm
        self.default_image_size = image_size
        self.draw_scale = draw_scale
        self.draw_subscales = draw_subscales

        # Calculate pixel distances
        self.line_distance_px = int(self.line_distance_mm * self.pixels_per_mm)
        self.scale_size_px = int(self.scale_size_mm * self.pixels_per_mm)
        self.subscale_distance_px = int(
            self.subscale_distance_mm * self.pixels_per_mm)


    def draw_mesh_on_image(self,
                           input_image: Image.Image
                           ) -> Image.Image:
        """
        Draw mesh lines on an existing image.

        Args:
            input_image: PIL Image to draw mesh on

        Returns:
            PIL Image with mesh overlay
        """

        # Create a copy of the input image
        output_image = input_image.copy()
        draw = ImageDraw.Draw(output_image)

        width, height = output_image.size
        center_x, center_y = width // 2, height // 2

        # Draw vertical lines
        self._draw_vertical_lines(draw, center_x, height)

        # Draw horizontal lines
        self._draw_horizontal_lines(draw, center_y, width)

        # Draw subscales if enabled
        if self.draw_subscales:
            self._draw_subscales(draw, center_x, center_y, width, height)

        # Draw scale bar if enabled
        if self.draw_scale:
            self._draw_scale_bar(draw, width, height)

        return output_image


    def create_mesh_image(self,
                          image_size: Optional[Tuple[int, int]] = None,
                          background_color: str = "white") -> Image.Image:
        """
        Create a new image with just the mesh (no input image).

        Args:
            image_size: Size of the image (width, height). If None, uses default.
            background_color: Background color of the image (default: "white")

        Returns:
            PIL Image with mesh
        """
        if image_size is None:
            image_size = self.default_image_size

        # Create a blank image
        image = Image.new("RGB", image_size, background_color)

        # Draw mesh on the blank image
        return self.draw_mesh_on_image(image)


    def _draw_vertical_lines(self, draw: ImageDraw.Draw, center_x: int,
                             height: int):
        """Draw vertical lines starting from center extending to borders."""
        # Draw center line
        draw.line([(center_x, 0), (center_x, height)], fill=self.line_color,
                  width=self.line_width)

        # Draw lines to the right
        x = center_x + self.line_distance_px
        while x < draw.im.size[0]:  # width
            draw.line([(x, 0), (x, height)], fill=self.line_color,
                      width=self.line_width)
            x += self.line_distance_px

        # Draw lines to the left
        x = center_x - self.line_distance_px
        while x > 0:
            draw.line([(x, 0), (x, height)], fill=self.line_color,
                      width=self.line_width)
            x -= self.line_distance_px

    def _draw_horizontal_lines(self, draw: ImageDraw.Draw, center_y: int,
                               width: int):
        """Draw horizontal lines starting from center extending to borders."""
        # Draw center line
        draw.line([(0, center_y), (width, center_y)], fill=self.line_color,
                  width=self.line_width)

        # Draw lines downward
        y = center_y + self.line_distance_px
        while y < draw.im.size[1]:  # height
            draw.line([(0, y), (width, y)], fill=self.line_color,
                      width=self.line_width)
            y += self.line_distance_px

        # Draw lines upward
        y = center_y - self.line_distance_px
        while y > 0:
            draw.line([(0, y), (width, y)], fill=self.line_color,
                      width=self.line_width)
            y -= self.line_distance_px

    def _draw_subscales(self, draw: ImageDraw.Draw, center_x: int,
                        center_y: int,
                        width: int, height: int):
        """Draw small perpendicular lines for subscales."""
        subscale_length = 10  # Length of the small perpendicular lines in pixels

        # Draw vertical subscale marks on horizontal lines
        y = center_y
        while y <= height:
            x = center_x
            while x <= width:
                if x != center_x or y != center_y:  # Skip center intersection
                    # Draw small vertical line
                    draw.line([(x, y - subscale_length // 2),
                               (x, y + subscale_length // 2)],
                              fill=self.line_color, width=self.line_width)
                x += self.subscale_distance_px

            x = center_x - self.subscale_distance_px
            while x >= 0:
                # Draw small vertical line
                draw.line([(x, y - subscale_length // 2),
                           (x, y + subscale_length // 2)],
                          fill=self.line_color, width=self.line_width)
                x -= self.subscale_distance_px

            y += self.line_distance_px

        # Draw for lines above center
        y = center_y - self.line_distance_px
        while y >= 0:
            x = center_x
            while x <= width:
                # Draw small vertical line
                draw.line([(x, y - subscale_length // 2),
                           (x, y + subscale_length // 2)],
                          fill=self.line_color, width=self.line_width)
                x += self.subscale_distance_px

            x = center_x - self.subscale_distance_px
            while x >= 0:
                # Draw small vertical line
                draw.line([(x, y - subscale_length // 2),
                           (x, y + subscale_length // 2)],
                          fill=self.line_color, width=self.line_width)
                x -= self.subscale_distance_px

            y -= self.line_distance_px

        # Draw horizontal subscale marks on vertical lines
        x = center_x
        while x <= width:
            y = center_y
            while y <= height:
                if x != center_x or y != center_y:  # Skip center intersection
                    # Draw small horizontal line
                    draw.line([(x - subscale_length // 2, y),
                               (x + subscale_length // 2, y)],
                              fill=self.line_color, width=self.line_width)
                y += self.subscale_distance_px

            y = center_y - self.subscale_distance_px
            while y >= 0:
                # Draw small horizontal line
                draw.line([(x - subscale_length // 2, y),
                           (x + subscale_length // 2, y)],
                          fill=self.line_color, width=self.line_width)
                y -= self.subscale_distance_px

            x += self.line_distance_px

        # Draw for lines to the left of center
        x = center_x - self.line_distance_px
        while x >= 0:
            y = center_y
            while y <= height:
                # Draw small horizontal line
                draw.line([(x - subscale_length // 2, y),
                           (x + subscale_length // 2, y)],
                          fill=self.line_color, width=self.line_width)
                y += self.subscale_distance_px

            y = center_y - self.subscale_distance_px
            while y >= 0:
                # Draw small horizontal line
                draw.line([(x - subscale_length // 2, y),
                           (x + subscale_length // 2, y)],
                          fill=self.line_color, width=self.line_width)
                y -= self.subscale_distance_px

            x -= self.line_distance_px

    def _draw_scale_bar(self, draw: ImageDraw.Draw, width: int, height: int):
        """Draw scale bar with text at the specified position."""
        margin = 20
        scale_thickness = 3
        text_offset = 10

        # Determine position
        if self.scale_position == "top_left":
            start_x = margin
            start_y = margin
            text_x = start_x
            text_y = start_y + scale_thickness + text_offset
        elif self.scale_position == "top_right":
            start_x = width - margin - self.scale_size_px
            start_y = margin
            text_x = start_x
            text_y = start_y + scale_thickness + text_offset
        elif self.scale_position == "bottom_left":
            start_x = margin
            start_y = height - margin - scale_thickness - text_offset - 20
            text_x = start_x
            text_y = start_y + scale_thickness + text_offset
        else:  # bottom_right
            start_x = width - margin - self.scale_size_px
            start_y = height - margin - scale_thickness - text_offset - 20
            text_x = start_x
            text_y = start_y + scale_thickness + text_offset

        # Draw scale bar
        draw.rectangle([start_x, start_y,
                        start_x + self.scale_size_px,
                        start_y + scale_thickness],
                       fill=self.line_color)

        # Draw text
        scale_text = f"{self.scale_size_mm} mm"
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            # Fallback to basic drawing without font
            font = None

        draw.text((text_x, text_y), scale_text, fill=self.line_color, font=font)


# ######################################################################
# # Example usage and test functions
#
# # Basic usage - mesh on blank image
# mesh_drawer = MeshDrawer()
# mesh_image = mesh_drawer.create_mesh_image()
# mesh_image.save("output.png")
#
# # Advanced usage with all features
# mesh_drawer = MeshDrawer(
#     line_color="blue",
#     pixels_per_mm=400,
#     line_distance_mm=1.5,
#     draw_scale=True,
#     scale_position="top_left",
#     scale_size_mm=2.0,
#     draw_subscales=True,
#     subscale_distance_mm=0.1
# )
#
# # Apply to existing image
# existing_image = Image.open("my_image.jpg")
# result = mesh_drawer.draw_mesh_on_image(existing_image)
# result.save("image_with_mesh.jpg")
#
# # --------------------------------------------
#
# # Example usage with different line widths
# def example_usage():
#     """Example showing how to use the MeshDrawer class with different line widths."""
#
#     # Example 1: Thin lines (default)
#     mesh_drawer_thin = MeshDrawer(
#         line_color="gray",
#         line_width=1,
#         pixels_per_mm=476,
#         line_distance_mm=1.0,
#         draw_scale=True,
#         scale_position="bottom_right"
#     )
#
#     # Example 2: Thick lines
#     mesh_drawer_thick = MeshDrawer(
#         line_color="red",
#         line_width=5,
#         pixels_per_mm=476,
#         line_distance_mm=1.0,
#         draw_scale=True,
#         scale_position="top_left"
#     )
#
#     # Create mesh images with different line widths
#     thin_mesh = mesh_drawer_thin.create_mesh_image()
#     thick_mesh = mesh_drawer_thick.create_mesh_image()
#
#     thin_mesh.save("thin_mesh.png")
#     thick_mesh.save("thick_mesh.png")
#
#     print("Examples created with different line widths!")
#
#
# def example_usage():
#     """Example showing how to use the MeshDrawer class."""
#
#     # Example 1: Create a mesh on a blank image
#     print("Creating mesh on blank image...")
#     mesh_drawer = MeshDrawer(
#         line_color="gray",
#         pixels_per_mm=476,
#         line_distance_mm=1.0,
#         draw_scale=True,
#         scale_position="bottom_right",
#         draw_subscales=True,
#         subscale_distance_mm=0.2
#     )
#
#     mesh_image = mesh_drawer.create_mesh_image()
#     mesh_image.save("mesh_example.png")
#     print("Saved mesh_example.png")
#
#     # Example 2: Load an existing image and add mesh
#     try:
#         # Create a sample image for demonstration
#         sample_image = Image.new("RGB", (800, 600), "lightblue")
#
#         print("Adding mesh to existing image...")
#         mesh_drawer_2 = MeshDrawer(
#             line_color="red",
#             pixels_per_mm=300,  # Different conversion factor
#             line_distance_mm=2.0,  # Larger grid
#             draw_scale=True,
#             scale_position="top_left",
#             scale_size_mm=5.0  # 5mm scale bar
#         )
#
#         image_with_mesh = mesh_drawer_2.draw_mesh_on_image(sample_image)
#         image_with_mesh.save("image_with_mesh.png")
#         print("Saved image_with_mesh.png")
#
#     except Exception as e:
#         print(f"Error in example 2: {e}")
#
#     print("Examples completed!")



# --------------------------------------------
