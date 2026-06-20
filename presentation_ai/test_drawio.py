import sys, os
sys.path.append('E:/Slide_Generator/presentation_ai')

from services.visual_engine import generate_drawio_diagram

print("Testing Draw.io CLI only...")

test_xml = open('test_input.xml', 'w')
test_xml.write("""<mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="2" value="Cloud" style="rounded=1;" vertex="1" parent="1">
<mxGeometry x="100" y="100" width="200" height="100" as="geometry"/>
</mxCell>
<mxCell id="3" value="Server" style="rounded=1;" vertex="1" parent="1">
<mxGeometry x="400" y="100" width="120" height="80" as="geometry"/>
</mxCell>
<mxCell id="4" style="edgeStyle=orthogonalEdgeStyle;"
edge="1" source="2" target="3" parent="1">
<mxGeometry relative="1" as="geometry"/>
</mxCell>
</root></mxGraphModel>""")
test_xml.close()

xml = open('test_input.xml').read()
# Set max_retries=0 to test rendering directly without LLM complexity retries
svg, png = generate_drawio_diagram(xml, max_retries=0)

print(f"SVG: {svg}")
print(f"PNG: {png}")

if png and os.path.exists(png):
    size = os.path.getsize(png)
    print(f"PNG size: {size} bytes")
    if size > 5000:
        print("[OK] Draw.io CLI WORKS!")
    else:
        print("[WARN] PNG too small - CLI failed silently")
else:
    print("[FAIL] PNG not created - Draw.io CLI FAILED")
