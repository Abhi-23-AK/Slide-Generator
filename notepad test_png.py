import sys, os
sys.path.append('E:/Slide_Generator/presentation_ai')
from services.visual_engine import generate_drawio_diagram

xml = open('E:/Slide_Generator/presentation_ai/test_input.xml').read()
svg, png = generate_drawio_diagram(xml, topic='test')

print('SVG:', svg)
print('PNG:', png)

if svg and os.path.exists(svg):
    print('SVG size:', os.path.getsize(svg), 'bytes')
else:
    print('SVG missing!')

if png and os.path.exists(png):
    print('PNG size:', os.path.getsize(png), 'bytes')
    print('SUCCESS - PNG works!')
else:
    print('PNG MISSING - CLI failed!')