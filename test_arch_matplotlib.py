import sys, os
sys.path.append('E:/Slide_Generator/presentation_ai')
from services.visual_engine import _render_arch_matplotlib

xml = open('E:/Slide_Generator/presentation_ai/test_input.xml').read()
png = _render_arch_matplotlib(xml)

print('PNG:', png)

if png and os.path.exists(png):
    print('PNG size:', os.path.getsize(png), 'bytes')
    print('SUCCESS - Matplotlib architecture renderer works!')
else:
    print('PNG MISSING - Matplotlib renderer failed!')
