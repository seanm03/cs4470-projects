# Keypresses:
- jump back: left arrow key
- jump forward: right arrow key
- increase WPM: up arrow key
- decrease WPM: down arrow key
- increase font size: =/+ key
- decrease font size: - key
- pause/play: spacebar

# Gestures:
- jump back: < arrow, drawn from top to bottom
- jump forward: > arrow, drawn from top to bottom
- increase WPM: ^ arrow, drawn from left to right
- decrease WPM: down arrow, drawn from left to right
- increase font size: + cross, drawn starting from top to bottom and then left-to-right in one unbroken motion
- decrease font size: straight horizontal line, drawn from left to right
- pause/play: circle, drawn starting from the top going counterclockwise

# Other Sources:
- ShrinkWrapLabel class borrowed from positionable_label_text_demo.py
- Fonts, kivy_text_metrics, and helper_functions grabbed from class resource github repo.
- Gesture code and Keyboard event code grabbed from provided files for this assignment.

# Issues (unchanged from HW3):
- The first word after loading a text file is at the bottom left corner; is fixed when played.
- Marked letter isn't fully centered, is noticeably apparent when dealing with really long words.
- Changing font size before loading a text file breaks baseline & focus lines

# Other Build Reqs:
- bbcode, freetype-py, uharfbuzz
