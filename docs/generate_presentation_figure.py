"""
Generate HR Presentation Timeline Visual Graphic
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

output_dir = Path(r"d:\pppppp2\docs\assets")
output_dir.mkdir(parents=True, exist_ok=True)
fig_path = output_dir / "hr_presentation_timeline.png"

# Setup dark aesthetic figure matching ZED VISION UI
fig, ax = plt.subplots(figsize=(12, 6.2), dpi=220)
fig.patch.set_facecolor('#0b0b10')
ax.set_facecolor('#0b0b10')

# Title & Subtitle
ax.text(0.5, 0.94, "ZED VISION: 10-MINUTE HR & TECHNICAL COMMITTEE PRESENTATION ROADMAP",
        color='#ffffff', fontsize=13, weight='bold', ha='center')
ax.text(0.5, 0.89, "Step-by-Step Time-Budgeted Delivery Strategy | Presenter: sasi-04",
        color='#94a3b8', fontsize=10, ha='center')

# Phases definition
phases = [
    {
        "time": "0:00 - 1:30",
        "duration": "1.5 Mins",
        "title": "Phase 1: The Hook & PS-2 Dilemma",
        "desc": "• Introduce yourself & project purpose\n• Explain real-world crowd occlusion dilemma\n• Why standard ByteTrack/DeepSORT fails\n• Enterprise impact: False alarms, bad metrics",
        "color": "#ef4444",
        "badge": "PROBLEM DEFINITION"
    },
    {
        "time": "1:30 - 3:30",
        "duration": "2.0 Mins",
        "title": "Phase 2: Technical Architecture",
        "desc": "• 4-Stage Causal Pipeline (<16ms latency)\n• 8-State Kalman causal motion forecasting\n• Occlusion Intelligence Engine (OIE)\n• Privacy-first design (Zero biometrics/GDPR)",
        "color": "#06b6d4",
        "badge": "SYSTEM DESIGN"
    },
    {
        "time": "3:30 - 6:30",
        "duration": "3.0 Mins",
        "title": "Phase 3: Live Interactive Demo",
        "desc": "• Open Live Studio (Autoplays sequence)\n• Highlight Person #1 & #2 transit gate cross\n• Point out Amber OCCLUDED state recovery\n• Showcase Zero ID Switches preserved",
        "color": "#10b981",
        "badge": "LIVE PROOF (KEY)"
    },
    {
        "time": "6:30 - 8:30",
        "duration": "2.0 Mins",
        "title": "Phase 4: Quantitative Benchmarks",
        "desc": "• Slashed ID switches by -68.2% (182 -> 58)\n• Boosted IDF1 by +38.3% (48.2% -> 66.7%)\n• 65+ FPS real-time causal processing\n• 30/30 automated pytest verification",
        "color": "#f59e0b",
        "badge": "MEASURED RESULTS"
    },
    {
        "time": "8:30 - 10:00",
        "duration": "1.5 Mins",
        "title": "Phase 5: Closing & HR Q&A",
        "desc": "• Summarize technical & business value\n• Connect skills to company vision\n• Confident handling of HR / Tech questions\n• Professional, memorable closing statement",
        "color": "#8b5cf6",
        "badge": "Q&A & CLOSING"
    }
]

# Draw horizontal timeline flow
y_box = 0.42
box_width = 0.175
box_gap = 0.02
start_x = 0.025

for i, p in enumerate(phases):
    x = start_x + i * (box_width + box_gap)
    
    # Outer Card
    rect = patches.FancyBboxPatch(
        (x, 0.12), box_width, 0.68,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=p["color"],
        facecolor='#14141d'
    )
    ax.add_patch(rect)
    
    # Header badge
    ax.text(x + box_width/2, 0.75, p["badge"],
            color=p["color"], fontsize=7.5, weight='bold', ha='center',
            bbox=dict(boxstyle="round,pad=0.2", facecolor='#1e1e2d', edgecolor=p["color"], lw=0.8))
    
    # Time Stamp
    ax.text(x + box_width/2, 0.68, p["time"],
            color='#ffffff', fontsize=11, weight='bold', ha='center')
    ax.text(x + box_width/2, 0.63, f"({p['duration']})",
            color='#94a3b8', fontsize=8.5, ha='center')
    
    # Title
    ax.text(x + 0.01, 0.55, p["title"],
            color='#f8fafc', fontsize=8.5, weight='bold', ha='left')
    
    # Description Bullets
    ax.text(x + 0.008, 0.48, p["desc"],
            color='#cbd5e1', fontsize=7.2, ha='left', va='top', linespacing=1.45)
    
    # Connector Arrow between phases
    if i < len(phases) - 1:
        arrow_x = x + box_width + 0.003
        ax.annotate('', xy=(arrow_x + 0.014, 0.46), xytext=(arrow_x, 0.46),
                    arrowprops=dict(arrowstyle="-|>", color='#64748b', lw=1.5, mutation_scale=10))

# Bottom presentation tip banner
tip_box = patches.FancyBboxPatch(
    (0.025, 0.02), 0.95, 0.07,
    boxstyle="round,pad=0.01,rounding_size=0.015",
    linewidth=1,
    edgecolor='#334155',
    facecolor='#111118'
)
ax.add_patch(tip_box)

ax.text(0.5, 0.055, "PRO-TIP FOR HR INTERVIEWS: Lead with the real-world business impact in Phase 1, SHOW the live demo in Phase 3, and back it with hard numbers (-68% ID switches) in Phase 4.",
        color='#38bdf8', fontsize=8.5, weight='bold', ha='center', va='center')

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.tight_layout()
plt.savefig(fig_path, dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print("HR Presentation timeline graphic saved to:", fig_path)
