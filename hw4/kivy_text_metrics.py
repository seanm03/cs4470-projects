import freetype
import uharfbuzz as hb


# Scales text attributes according to the proportional difference between computed text_width and actual texture_width
def scale_attribs(attribs, text_width, texture_width):
    new_attribs = []
    sx = texture_width / text_width
    # print(f"text_width: {text_width} texture_width: {texture_width} sx: {sx}")

    for attrib in attribs:
        rect_x, rect_y, rect_w, rect_h, glyph_ascent, glyph_descent, x_advance = attrib
        new_attrib = rect_x * sx, rect_y, rect_w * sx, rect_h, glyph_ascent, glyph_descent, x_advance * sx
        new_attribs.append(new_attrib)

    return new_attribs


class TextMetrics:
    def __init__(self, font_path, font_size):
        self.font_path = ""
        self.font_size = 0
        self.face = None
        self.hb_blob = None
        self.hb_face = None
        self.hb_font = None
        self.set_font(font_path, font_size)

    # Configure the font that will be measured.
    def set_font(self, font_path, font_size):
        self.font_path = font_path
        self.font_size = font_size

        # Configure freetype
        self.face = freetype.Face(self.font_path)
        self.face.set_char_size(self.font_size * 64)

        # Load the font face buffer for HarfBuzz
        self.hb_blob = hb.Blob.from_file_path(font_path)
        self.hb_face = hb.Face(self.hb_blob)
        self.hb_font = hb.Font(self.hb_face)
        self.hb_font.scale = (self.font_size * 64, self.font_size * 64)

    # Find the extents of the text for the specified font and size.
    #
    # Parameters:
    # text: The string to be measured
    # output_texture_size: The size of the texture that Kivy/SDL2 has already generated (e.g. for a Label)
    #
    # Return: A tuple of: glyph_attribs, ascender, descender
    # glyph_attribs is a list of tuples of: rect_x, rect_y, rect_w, rect_h, glyph_ascent, glyph_descent, x_advance
    # Those attribs specify bounding box of the glyph, ascent and descent (relative to baseline), and advance to the
    # next glyph.
    # The ascender, and descender specify the full ascent/descent for the font and can be used to determine the
    # baseline.
    def get_text_extents(self, text, output_texture_size):
        # Extract needed face.size.* values from freetype
        ascender = self.face.size.ascender / 64.0
        descender = self.face.size.descender / 64.0

        # Set up harfbuzz for typesetting
        hb_buffer = hb.Buffer()
        hb_buffer.add_str(text)
        hb_buffer.guess_segment_properties()

        # In my testing, it does appear that Kivy/SDL2 has both kerning and ligatures enabled.
        # So let's make sure the measurements are based on those options enabled.
        enable_kerning = True
        enable_ligatures = True

        features = {
            'kern': enable_kerning,  # Kerning
            'liga': enable_ligatures,  # Standard Ligatures
        }

        # The actual harfbuzz typesetting
        hb.shape(self.hb_font, hb_buffer, features)

        glyph_info = hb_buffer.glyph_infos
        glyph_positions = hb_buffer.glyph_positions

        hb_glyph_attribs = []
        hb_x_cursor = 0

        # Iterate through harfbuzz's typesetting output so we can build each glyph's bounding box
        for info, pos in zip(glyph_info, glyph_positions):

            gid = info.codepoint

            # Useful for debugging. Glyph may be a compound ligature of multiple adjacent character in original string
            # glyph_name = self.hb_font.glyph_to_string(gid)

            # There seems to be a bug in harfbuzz and the pos offsets per glyph are always zero.
            # So we will use the measurements from freetype instead.
            # hb_x_offset = pos.x_offset / 64
            # hb_y_offset = pos.y_offset / 64

            hb_x_advance = pos.x_advance / 64

            # print("Glyph Name:", glyph_name)
            # print(f"hb_x_offset: {hb_x_offset}, hb_y_offset: {hb_y_offset}, x_advance: {hb_x_advance}")

            # We use freetype to lookup information about each glyph
            self.face.load_glyph(gid)
            bitmap = self.face.glyph.bitmap

            # Some freetype glyph metrics
            glyph_ascent = self.face.glyph.metrics.horiBearingY / 64
            glyph_descent = (self.face.glyph.metrics.height - self.face.glyph.metrics.horiBearingY) / 64
            x_offset = self.face.glyph.metrics.horiBearingX / 64
            y_offset = self.face.glyph.metrics.horiBearingY / 64

            # Harfbuzz's hb_x_offset and hb_y_offset are always zero for some reason.
            # So we'll use the base freetype offsets, which seem to work.
            hb_rect_x = hb_x_cursor + x_offset
            hb_rect_y = y_offset - bitmap.rows
            hb_rect_w = bitmap.width  # This probably works as well: self.face.glyph.metrics.width / 64.0
            hb_rect_h = bitmap.rows  # This probably works as well: self.face.glyph.metrics.height / 64.0

            # Save the info for the current glyph
            hb_glyph_attribs.append((hb_rect_x, hb_rect_y, hb_rect_w, hb_rect_h,
                                    glyph_ascent, glyph_descent, hb_x_advance))

            # Advance to the next glyph position
            hb_x_cursor += hb_x_advance

        # print(f"total width via harfbuzz: {hb_x_cursor}")

        # harfbuzz's horizontal advances do not generally sum to Kivy/SDL2's texture width
        # So let's just proportionally scale the advances to the correct width.
        # Everything appears to align once this method is applied.
        hb_glyph_attribs = scale_attribs(hb_glyph_attribs, hb_x_cursor, output_texture_size[0])
        return hb_glyph_attribs, ascender, descender
