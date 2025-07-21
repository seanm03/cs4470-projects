# Other Sources:
- ShrinkWrapLabel class borrowed from positionable_label_text_demo.py
- Fonts, kivy_text_metrics, and helper_functions grabbed from class resource github repo.
# Issues:
- The first word after loading a text file is at the bottom left corner; is fixed when played.
- Marked letter isn't fully centered, is noticeably apparent when dealing with really long words.
- Changing font size before loading a text file breaks baseline & focus lines
# Other Build Reqs:
- bbcode, freetype-py, uharfbuzz
