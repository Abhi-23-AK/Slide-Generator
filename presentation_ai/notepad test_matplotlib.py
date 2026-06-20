import sys
sys.path.append('E:/Slide_Generator/presentation_ai')

# Test matplotlib arch rendering directly
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 1000)
ax.set_ylim(-700, 0)
ax.axis('off')
fig.patch.set_facecolor('#F0F4F8')

# Cloud container
ax.add_patch(FancyBboxPatch((20,-680), 960, 660,
    boxstyle="round,pad=3", facecolor='#dae8fc',
    edgecolor='#6c8ebf', linewidth=2,
    linestyle='--', alpha=0.4))
ax.text(500,-350,'☁ Cloud Platform',
    ha='center',va='center',fontsize=16,
    fontweight='bold',color='#1A1A2E')

# Zone 1
ax.add_patch(FancyBboxPatch((40,-620), 420, 560,
    boxstyle="round,pad=3", facecolor='#fff2cc',
    edgecolor='#d6b656', linewidth=1.5, alpha=0.6))
ax.text(250,-340,'Zone 1',
    ha='center',va='center',fontsize=12,
    fontweight='bold',color='#333')

# Nodes
boxes = [
    (80,-200,160,70,'#0075db','#fff','Load Balancer'),
    (80,-320,160,70,'#dae8fc','#1A1A2E','Web Server'),
    (80,-440,160,70,'#dae8fc','#1A1A2E','App Server'),
    (80,-560,160,70,'#d5e8d4','#1A1A2E','Database'),
    (550,-200,160,70,'#ff8000','#fff','API Gateway'),
    (550,-320,160,70,'#dae8fc','#1A1A2E','Cache Redis'),
    (550,-440,160,70,'#f8cecc','#1A1A2E','Security'),
    (800,-300,120,60,'#f5f5f5','#1A1A2E','Internet'),
    (800,-420,120,60,'#f5f5f5','#1A1A2E','User'),
]

for x,y,w,h,fill,fc,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,
        boxstyle="round,pad=3",
        facecolor=fill, edgecolor='#666',
        linewidth=1.5, alpha=0.9, zorder=2))
    ax.text(x+w/2, y+h/2, label,
        ha='center', va='center',
        fontsize=9, fontweight='bold',
        color=fc, zorder=3)

# Arrows
arrows = [
    (860,-270,710,-165),  # Internet→LB
    (860,-390,860,-330),  # User→Internet
    (160,-165,160,-250),  # LB→Web
    (160,-320,160,-370),  # Web→App
    (160,-440,160,-490),  # App→DB
    (240,-285,550,-235),  # Web→API
    (240,-355,550,-355),  # App→Cache
]
for sx,sy,tx,ty in arrows:
    ax.annotate('', xy=(tx,ty), xytext=(sx,sy),
        arrowprops=dict(arrowstyle='-|>',
        color='#0075DB', lw=2, mutation_scale=15,
        connectionstyle='arc3,rad=0.05'), zorder=5)

ax.set_title('Cloud Architecture Diagram',
    fontsize=16, fontweight='bold', 
    color='#1A1A2E', pad=15)

out = 'E:/Slide_Generator/presentation_ai/test_arch_output.png'
plt.tight_layout()
plt.savefig(out, dpi=150, bbox_inches='tight',
            facecolor='#F0F4F8')
plt.close()

if os.path.exists(out):
    print(f'SUCCESS! PNG: {out}')
    print(f'Size: {os.path.getsize(out)} bytes')
else:
    print('FAILED!')