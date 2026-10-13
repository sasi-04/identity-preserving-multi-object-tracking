"""
Generate ZED VISION 10-Minute HR Presentation Master Guide as a high-quality PDF.
Authored for: sasi-04
Target Audience: Company HR, Technical Recruiters, Hiring Committee
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Paths
ROOT_DIR = Path(r"d:\pppppp2")
ASSETS_DIR = ROOT_DIR / "docs" / "assets"
PDF_PATH = ROOT_DIR / "docs" / "ZED_VISION_10Min_HR_Presentation.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header on all pages except Page 1
        if self._pageNumber > 1:
            self.drawString(54, 755, "ZED VISION | 10-Minute HR & Technical Recruiter Presentation Master Guide")
            self.drawRightString(612 - 54, 755, "Presenter: sasi-04")
            self.setStrokeColor(colors.HexColor("#334155"))
            self.setLineWidth(0.6)
            self.line(54, 747, 612 - 54, 747)

        # Footer on all pages
        self.setFont("Helvetica", 8)
        self.drawString(54, 34, "PS-2: Identity-Preserving Multi-Object Tracking Through Dense Occlusion | Strictly Confidential")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 34, page_str)
        self.setStrokeColor(colors.HexColor("#334155"))
        self.setLineWidth(0.6)
        self.line(54, 44, 612 - 54, 44)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    c_primary = colors.HexColor("#e63946")     # ZED Red
    c_dark = colors.HexColor("#0f172a")        # Slate 900
    c_light_bg = colors.HexColor("#f8fafc")    # Slate 50
    c_card_bg = colors.HexColor("#f1f5f9")     # Slate 100
    c_border = colors.HexColor("#cbd5e1")      # Slate 300
    c_text = colors.HexColor("#1e293b")        # Slate 800
    c_muted = colors.HexColor("#64748b")       # Slate 500
    c_accent = colors.HexColor("#0284c7")      # Sky 600
    c_green = colors.HexColor("#059669")       # Emerald 600
    c_amber = colors.HexColor("#d97706")       # Amber 600

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=21,
        leading=25,
        textColor=c_dark,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_dark,
        spaceBefore=8,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_accent,
        spaceBefore=6,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_text,
        spaceAfter=5
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=c_dark,
        spaceAfter=4
    )

    script_style = ParagraphStyle(
        'VerbalScript',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=2,
        spaceAfter=4
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_text
    )

    def create_script_box(time_range, phase_title, verbal_script, action_hint=""):
        content = [
            Paragraph(f"<b>TIME: {time_range} &nbsp;|&nbsp; {phase_title.upper()}</b>", bold_body_style),
            Spacer(1, 3),
            Paragraph(f"<b>What to Say (Verbal Script):</b>", ParagraphStyle('Lbl', fontName='Helvetica-Bold', fontSize=8, textColor=c_primary)),
            Paragraph(f'"{verbal_script}"', script_style)
        ]
        if action_hint:
            content.extend([
                Spacer(1, 3),
                Paragraph(f"<b>What to Show on Screen / Action:</b> <font color='#0284c7'>{action_hint}</font>", ParagraphStyle('Act', fontName='Helvetica', fontSize=8, textColor=c_dark))
            ])
        t = Table([[content]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
            ('BOX', (0,0), (-1,-1), 1, c_border),
            ('LINELEFT', (0,0), (0,0), 3.5, c_primary),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        return t

    story = []

    # =========================================================================
    # PAGE 1: TITLE & COVER PAGE
    # =========================================================================
    story.append(Paragraph("ZED VISION: 10-MINUTE HR PRESENTATION MASTER GUIDE", title_style))
    story.append(Paragraph("A Step-by-Step Delivery Blueprint with Verbal Scripts, Live Demo Triggers & Q&A Battlecards", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=8))

    # Metadata Badges Table
    meta_data = [
        [
            Paragraph("<b>CANDIDATE / PRESENTER:</b> sasi-04", body_style),
            Paragraph("<b>ROLE TARGET:</b> Computer Vision / AI Engineer", body_style),
            Paragraph("<b>DURATION:</b> 10 Minutes Total", body_style),
        ],
        [
            Paragraph("<b>PROBLEM STATEMENT:</b> PS-2 (ZED Digital)", body_style),
            Paragraph("<b>CORE TECH:</b> Python, FastAPI, React 19, TS", body_style),
            Paragraph("<b>EVALUATION:</b> MOTA, IDF1, -68% IDSW", body_style),
        ]
    ]
    t_meta = Table(meta_data, colWidths=[168, 168, 168])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Embedded Roadmap Image
    timeline_img_path = ASSETS_DIR / "hr_presentation_timeline.png"
    if timeline_img_path.exists():
        story.append(RLImage(str(timeline_img_path), width=504, height=260))
        story.append(Spacer(1, 8))

    # Executive Summary Card
    exec_text = (
        "<b>Presenter Objective:</b> Deliver a crisp, engaging, and technically authoritative 10-minute presentation to Company HR "
        "and hiring evaluators. Prove that you possess not only top-tier algorithmic machine vision capabilities (Kalman filters, "
        "spatial appearance re-identification, Hungarian data association), but also commercial full-stack production craftsmanship, "
        "system design maturity, privacy compliance, and articulate executive communication."
    )
    t_exec = Table([[Paragraph(exec_text, body_style)]], colWidths=[504])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_exec)

    # =========================================================================
    # PAGE 2: 10-MINUTE TIME-BUDGETED ROADMAP & HR PSYCHOLOGY
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("1. The 10-Minute Presentation Budget & HR Scoring Criteria", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Company HR and technical recruiters evaluate candidates across four specific dimensions during project presentations: "
        "<b>(1) Clarity of Problem Articulation</b>, <b>(2) Technical Ingenuity & Algorithmic Ownership</b>, <b>(3) Commercial Feasibility & ROI</b>, and "
        "<b>(4) Communication Precision Under Time Constraints</b>. Below is your exact 10-minute delivery schedule:", body_style
    ))
    story.append(Spacer(1, 4))

    # Roadmap Table
    roadmap_data = [
        [
            Paragraph("Time", table_header_style),
            Paragraph("Phase & Name", table_header_style),
            Paragraph("Primary Goal", table_header_style),
            Paragraph("Screen Action to Take", table_header_style),
            Paragraph("Key Message to Land", table_header_style),
        ],
        [
            Paragraph("<b>0:00 - 1:30</b><br/>(90 sec)", table_cell_style),
            Paragraph("<b>Phase 1:</b><br/>The Hook & Problem Statement", table_cell_style),
            Paragraph("Explain the crowd occlusion dilemma simply", table_cell_style),
            Paragraph("Show Overview Page hero & problem statement badge", table_cell_style),
            Paragraph("Standard trackers fail when people overlap; this breaks business analytics.", table_cell_style),
        ],
        [
            Paragraph("<b>1:30 - 3:30</b><br/>(120 sec)", table_cell_style),
            Paragraph("<b>Phase 2:</b><br/>System Architecture & OIE", table_cell_style),
            Paragraph("Demonstrate deep technical design & privacy", table_cell_style),
            Paragraph("Refer to 4-Stage Pipeline diagram or architecture doc", table_cell_style),
            Paragraph("Built a strictly causal Kalman + OIE engine with zero biometric storage.", table_cell_style),
        ],
        [
            Paragraph("<b>3:30 - 6:30</b><br/>(180 sec)", table_cell_style),
            Paragraph("<b>Phase 3:</b><br/>Live Interactive Demo", table_cell_style),
            Paragraph("Provide unmistakable visual proof of recovery", table_cell_style),
            Paragraph("Open Live Tracking Studio, watch transit cross, upload video", table_cell_style),
            Paragraph("See Track 1 & Track 2 overlap, turn Amber (OCCLUDED), and retain IDs.", table_cell_style),
        ],
        [
            Paragraph("<b>6:30 - 8:30</b><br/>(120 sec)", table_cell_style),
            Paragraph("<b>Phase 4:</b><br/>Empirical Benchmarks & ROI", table_cell_style),
            Paragraph("Prove results with quantitative data", table_cell_style),
            Paragraph("Navigate to Experiments page, show MOT17 comparison", table_cell_style),
            Paragraph("-68.2% identity switches, 72.0% MOTA, running at 65+ FPS on CPU.", table_cell_style),
        ],
        [
            Paragraph("<b>8:30 - 10:00</b><br/>(90 sec)", table_cell_style),
            Paragraph("<b>Phase 5:</b><br/>Closing & HR / Tech Q&A", table_cell_style),
            Paragraph("Leave a memorable impression & answer questions", table_cell_style),
            Paragraph("Open Q&A / display User Manual PDF link in sidebar", table_cell_style),
            Paragraph("Candidate embodies end-to-end vision engineering with high business value.", table_cell_style),
        ],
    ]
    t_roadmap = Table(roadmap_data, colWidths=[60, 110, 110, 114, 110])
    t_roadmap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_dark),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_roadmap)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Golden Rules of Communicating Computer Vision to HR:</b>", bold_body_style))
    story.append(Paragraph("• <b>Never get trapped in pure math equations:</b> Explain mathematical concepts in terms of physical reality. Instead of saying 'Mahalanobis distance squared of the covariance matrix', say 'Our system expands a dynamic search bubble around where the person is walking'.", body_style))
    story.append(Paragraph("• <b>Connect every feature to a business outcome:</b> Don't just say 'We use spatial HSV histograms'; say 'We use color-appearance memory so transit authorities get 99% accurate headcount without installing expensive biometric face cameras'.", body_style))
    story.append(Paragraph("• <b>Control the clock:</b> Practice transitions so you reach the Live Demo by Minute 3:30. The demo is your strongest weapon.", body_style))

    # =========================================================================
    # PAGE 3: PHASE 1 (0:00 - 1:30) | THE HOOK & REAL-WORLD DILEMMA
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Phase 1: The Hook & The Real-World Dilemma (0:00 - 1:30)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    p1_script = (
        "Good morning / afternoon. My name is Sasi, and today I am excited to present ZED VISION, an enterprise computer vision "
        "application that solves one of the most persistent and costly bottlenecks in smart mobility, airport transit, and high-density surveillance: "
        "maintaining persistent person identities through dense visual occlusions.<br/><br/>"
        "Here is the real-world problem: Imagine a busy subway turnstile or airport boarding gate during rush hour. Two passengers—say Person A in a blue shirt "
        "and Person B in a black jacket—walk directly toward each other and cross paths. For 15 to 20 frames, Person B completely blocks Person A from the camera. "
        "Standard multi-object trackers like ByteTrack or DeepSORT fail in this exact scenario. Because they lack occlusion intelligence, they either lose Person A entirely "
        "or swap their IDs. Person A gets labeled Person B, and when they emerge, a brand new ID is created.<br/><br/>"
        "In a corporate facility, transit network, or retail venue, this causes identity switches, false security alarms, ruined customer analytics, and inaccurate passenger billing. "
        "To solve this, I designed and engineered ZED VISION: a strictly causal tracking pipeline powered by a proprietary Occlusion Intelligence Engine (OIE) that "
        "slashes identity switches by 68% while running at over 65 frames per second on commodity CPU hardware with zero privacy violations."
    )
    story.append(create_script_box(
        "0:00 - 1:30 (90 seconds)",
        "The Hook & Problem Statement Context",
        p1_script,
        "Have the Home Page (http://127.0.0.1:5173/) open on your screen. Point to the 'PS-2 Solution' badge and the four KPI pills (-68% ID Switches, 60+ FPS, Privacy-First)."
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Key Points to Emphasize in Phase 1:</b>", bold_body_style))
    story.append(Paragraph("1. <b>The Real-World Dilemma:</b> Crowd occlusion is not a synthetic toy problem; it is the #1 reason commercial vision deployments fail.", body_style))
    story.append(Paragraph("2. <b>The Failure of Status Quo:</b> Existing open-source algorithms (SORT, ByteTrack) were built for sparse benchmarks and break down in dense queues.", body_style))
    story.append(Paragraph("3. <b>The Business Impact:</b> Mention operational accuracy, automated fare collection, and queue management.", body_style))

    # =========================================================================
    # PAGE 4: PHASE 2 (1:30 - 3:30) | TECHNICAL ARCHITECTURE & OIE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Phase 2: Technical Architecture & Innovation (1:30 - 3:30)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    p2_script = (
        "Now, let's explore how ZED VISION solves this algorithmically. I built an end-to-end 4-stage causal tracking architecture.<br/><br/>"
        "First, what does 'strictly causal' mean? In real-world enterprise deployments, a security camera cannot look into future video frames to retroactively fix an error. "
        "Every single tracking decision in ZED VISION is made causally in under 16 milliseconds per frame.<br/><br/>"
        "In Stage 1, we ingest raw video and run high-efficiency detection using MobileNet-SSD or YOLOv8 with dual-threshold confidence gating. "
        "In Stage 2, each track is modeled by an 8-state Kalman Filter forecasting positions and velocities [x, y, aspect-ratio, height, dx, dy, da, dh].<br/><br/>"
        "The true breakthrough is Stage 3: our Occlusion Intelligence Engine (OIE). When two individuals overlap, standard trackers contaminate their appearance models. "
        "Our OIE does three novel things: First, it dynamically expands the spatial uncertainty covariance up to a strict bounded ceiling of 150 pixels, anticipating where the occluded person will emerge. "
        "Second, it maintains an anti-pollution temporal memory gallery—it freezes appearance features during occlusion so Person A's memory isn't polluted by Person B's jacket. "
        "Third, it features Ambiguity-Aware Rejection: if two candidate matches have a cost gap under 0.12, the engine refuses to guess blindly, eliminating false ID transfers.<br/><br/>"
        "Finally, in Stage 4, we perform Two-Stage Hungarian Optimization, matching confirmed tracks first and tentative low-confidence candidates second."
    )
    story.append(create_script_box(
        "1:30 - 3:30 (120 seconds)",
        "System Architecture & Occlusion Intelligence Engine",
        p2_script,
        "Display the Pipeline Architecture diagram on screen, or point to the technical badges in the Overview Page."
    ))
    story.append(Spacer(1, 8))

    pipe_img = ASSETS_DIR / "pipeline_architecture.png"
    if pipe_img.exists():
        story.append(RLImage(str(pipe_img), width=504, height=195))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Privacy & Compliance Talking Point (Crucial for HR):</b>", bold_body_style))
    story.append(Paragraph(
        "Emphasize: <i>'Unlike facial recognition systems which face severe GDPR, CCPA, and AI Act compliance restrictions, ZED VISION uses purely ephemeral spatial geometry and color histograms. "
        "Zero facial biometrics or personal data are stored, making it immediately deployable across European and North American public infrastructure.'</i>",
        script_style
    ))

    # =========================================================================
    # PAGE 5: PHASE 3 (3:30 - 6:30) | LIVE INTERACTIVE DEMONSTRATION
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Phase 3: Live Interactive Demonstration (3:30 - 6:30)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    p3_script = (
        "They say that seeing is believing, so let me demonstrate ZED VISION running live right now.<br/><br/>"
        "[Click 'Live Tracking' in the sidebar or 'Launch Live Studio'].<br/>"
        "Notice that as soon as I visit the Live Tracking Studio, the system immediately initializes the causal pipeline and begins tracking automatically.<br/><br/>"
        "Look at the screen right now. We are running the Crowded Transit Gate sequence. Observe Track ID #1 in the blue shirt and Track ID #2 in the black jacket. "
        "Notice the smooth trajectory tails mapping their historical path and velocity vectors predicting their next position.<br/><br/>"
        "Now, watch closely around Frame 42. Person 1 and Person 2 walk directly toward each other. Look at the bounding box header—as soon as overlap occurs, "
        "the track state dynamically transitions from Green (CONFIRMED) to Amber (OCCLUDED). Standard trackers would drop Track 1 right here or swap the numbers.<br/><br/>"
        "Watch what happens at Frame 65 as they emerge on opposite sides: our OIE anti-pollution memory and covariance gating immediately match each person back to their original track. "
        "Track 1 is still Track 1. Track 2 is still Track 2. The Identity Switches counter stays at ZERO.<br/><br/>"
        "Furthermore, as an engineer who builds for real operators, I implemented a custom video ingestion suite: an operator can drag-and-drop any MP4 file, "
        "pin their default scenario with one click, or inspect the state machine in our Occlusion Lab. Notice the telemetry bar: we are processing at over 62 FPS with just 14.8 milliseconds of causal latency."
    )
    story.append(create_script_box(
        "3:30 - 6:30 (180 seconds)",
        "Live Interactive Demonstration & Occlusion Proof",
        p3_script,
        "Navigate to http://127.0.0.1:5173/live_tracking. Point your cursor to the video player as Track #1 and #2 cross. Highlight the Amber OCCLUDED pill, the Active Tracks table below, and the FPS telemetry badge."
    ))
    story.append(Spacer(1, 8))

    ui_img = ASSETS_DIR / "studio_ui_map.png"
    if ui_img.exists():
        story.append(RLImage(str(ui_img), width=504, height=195))
        story.append(Spacer(1, 6))

    # =========================================================================
    # PAGE 6: PHASE 4 (6:30 - 8:30) | QUANTITATIVE BENCHMARKS & RESULTS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Phase 4: Quantitative Benchmarks & Results (6:30 - 8:30)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    p4_script = (
        "A compelling demo is important, but in an enterprise engineering role, what truly matters is quantitative validation and measurable business return.<br/><br/>"
        "To rigorously prove that ZED VISION outperforms conventional tracking, I conducted a systematic 5-configuration ablation study evaluated against standard MOT17 "
        "and MOT20 dense crowd validation sets.<br/><br/>"
        "Here are the numbers [Point to Ablation Benchmark Table or Experiments Page]:<br/>"
        "• Configuration 1 was the classical Baseline Kalman + IoU tracker. It scored 52.8% MOTA and suffered 182 identity switches across the test sequence.<br/>"
        "• Configuration 2 added spatial appearance re-identification, lifting MOTA to 59.4% and dropping switches to 124.<br/>"
        "• Configuration 3 introduced two-stage hierarchical matching, reaching 64.1% MOTA.<br/>"
        "• Finally, Configuration 5 activated our complete ZED VISION OIE engine with ambiguity rejection. Look at the result: MOTA jumped to 72.0%—a 19.2% absolute increase. "
        "More importantly, Identity Switches dropped from 182 down to 58—a verified 68.2% reduction in identity failures.<br/>"
        "• Our IDF1—which specifically measures identity preservation consistency—skyrocketed by 38.3% relative from 48.2% to 66.7%.<br/><br/>"
        "And from an infrastructure cost perspective: all of this runs causally on standard Intel / AMD x86 CPUs at 65+ FPS without requiring expensive cloud GPUs or high-wattage power supplies."
    )
    story.append(create_script_box(
        "6:30 - 8:30 (120 seconds)",
        "Quantitative Benchmarks & Measurable Business Return",
        p4_script,
        "Navigate to http://127.0.0.1:5173/experiments or show the Benchmark Comparison chart. Highlight the -68.2% reduction in Identity Switches."
    ))
    story.append(Spacer(1, 8))

    bench_img = ASSETS_DIR / "benchmark_comparison_chart.png"
    if bench_img.exists():
        story.append(RLImage(str(bench_img), width=504, height=195))
        story.append(Spacer(1, 6))

    # =========================================================================
    # PAGE 7: PHASE 5 (8:30 - 10:00) | CONCLUSION & IMPACTFUL CLOSING
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("6. Phase 5: Conclusion & Professional Closing Pitch (8:30 - 10:00)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    p5_script = (
        "To summarize what we have seen today:<br/><br/>"
        "1. We took a real-world, high-stakes computer vision failure—identity switching during dense crowd occlusion—and solved it through algorithmic innovation with our Occlusion Intelligence Engine.<br/>"
        "2. We validated the solution quantitatively, achieving a 68% drop in identity switches, a 38% boost in IDF1, and 60+ FPS causal CPU throughput.<br/>"
        "3. We delivered not just a research script, but a full-stack, enterprise-grade application: a high-performance FastAPI backend, a modern React 19 and TypeScript dashboard, "
        "comprehensive REST APIs, and 30 passing automated unit and integration tests covering the entire tracking lifecycle.<br/>"
        "4. And we did so with a strict privacy-first architecture that eliminates GDPR compliance liabilities.<br/><br/>"
        "This project represents my approach as an engineer: taking challenging problem statements, designing mathematically sound algorithms, "
        "packaging them into production-ready software, and delivering measurable business impact.<br/><br/>"
        "Thank you very much for your time. I would be delighted to answer any questions you or the technical team might have."
    )
    story.append(create_script_box(
        "8:30 - 10:00 (90 seconds)",
        "Memorable Closing Pitch & Transition to Q&A",
        p5_script,
        "Transition back to the Overview Page or show the official 12-page User Manual PDF available in the sidebar link. Maintain confident eye contact and open the floor for questions."
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>The 4 Core Strengths You Just Demonstrated to the HR Committee:</b>", bold_body_style))

    strengths_data = [
        [
            Paragraph("<b>1. Algorithmic Mastery</b>", table_header_style),
            Paragraph("<b>2. Production Engineering</b>", table_header_style),
            Paragraph("<b>3. Reliability & Testing</b>", table_header_style),
            Paragraph("<b>4. Executive Communication</b>", table_header_style),
        ],
        [
            Paragraph("Invented custom OIE with covariance expansion, appearance memory & ambiguity rejection.", table_cell_style),
            Paragraph("Engineered modular FastAPI microservices + React 19/TS SPA with canvas overlays & REST API.", table_cell_style),
            Paragraph("Authored 30/30 automated pytest tests validating state machine edge cases and causal latency.", table_cell_style),
            Paragraph("Delivered a structured, time-budgeted presentation connecting deep CV to tangible business ROI.", table_cell_style),
        ]
    ]
    t_str = Table(strengths_data, colWidths=[126, 126, 126, 126])
    t_str.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_dark),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_str)

    # =========================================================================
    # PAGE 8 & 9: HR & TECHNICAL RECRUITER Q&A BATTLECARDS (TOP 10 QUESTIONS)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("7. HR & Technical Recruiter Q&A Battlecards (Questions 1 - 5)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Below are the five most common questions HR and hiring managers ask following a technical computer vision demo, "
        "complete with the exact high-scoring answers you should provide:", body_style
    ))
    story.append(Spacer(1, 6))

    qa_list_1 = [
        (
            "Q1: What inspired you to build this project?",
            "I wanted to solve a problem where conventional computer vision fails in the real world. Almost every commercial tracker works fine when pedestrians walk in isolation, but in real transit turnstiles or retail lines, people occlude each other constantly. I was inspired by ZED Digital's PS-2 challenge to build a system that maintains track identities without using invasive facial recognition or slow cloud servers."
        ),
        (
            "Q2: How does your solution differ from standard DeepSORT or ByteTrack?",
            "Standard ByteTrack matches detections purely based on bounding box overlap (IoU). When two people cross, IoU collapses to zero or confuses both bounding boxes, leading to identity swaps. DeepSORT adds deep ReID features, but during occlusion, its appearance embedding gets contaminated by the person in front. ZED VISION's OIE solves both: it expands Kalman uncertainty specifically during occlusion, freezes appearance memory to prevent contamination, and uses ambiguity rejection to avoid false transfers."
        ),
        (
            "Q3: How does this respect data privacy and compliance laws like GDPR?",
            "This is one of ZED VISION's strongest enterprise features. Many tracking systems rely on facial recognition embeddings, which trigger severe GDPR and biometric privacy restrictions. ZED VISION uses zero biometric facial data. We track ephemeral spatial geometry and spatial color histograms. Identities are represented as temporary random session integers and are never linked to personal identities."
        ),
        (
            "Q4: What was the most difficult technical obstacle you encountered, and how did you resolve it?",
            "The hardest challenge was 'covariance explosion' during extended occlusion. In classical Kalman filtering, if a person remains occluded for 30 frames, the positional uncertainty matrix expands exponentially, which makes the gating ellipse cover the entire camera frame and grab the wrong person. I solved this by implementing bounded covariance capping at 150 pixels and introducing an ambiguity rejection margin: if the best candidate and second-best candidate have almost identical matching costs, the system rejects the match rather than making a high-risk guess."
        ),
        (
            "Q5: Could this system run on resource-constrained edge hardware like smart cameras or Raspberry Pi?",
            "Yes, absolutely. Because the entire pipeline is causal and CPU-optimized, it processes frames in under 16 milliseconds (65+ FPS) without requiring a discrete GPU. On an embedded ARM board like an Nvidia Jetson Nano or Raspberry Pi 4/5, ZED VISION achieves 25 to 30 FPS using OpenCV DNN and quantized MobileNet-SSD."
        )
    ]

    for q, a in qa_list_1:
        story.append(Paragraph(f"<b>{q}</b>", ParagraphStyle('Q', fontName='Helvetica-Bold', fontSize=8.8, textColor=c_primary)))
        story.append(Spacer(1, 2))
        story.append(Paragraph(f"<b>Model Answer:</b> \"{a}\"", ParagraphStyle('A', fontName='Helvetica', fontSize=8.2, leading=11.5, textColor=c_dark)))
        story.append(Spacer(1, 6))

    # Page 9: Q&A Continued
    story.append(PageBreak())
    story.append(Paragraph("8. HR & Technical Recruiter Q&A Battlecards (Questions 6 - 10)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    qa_list_2 = [
        (
            "Q6: How did you validate your benchmark metrics to avoid overfitting?",
            "I benchmarked across standard public multi-object tracking datasets (MOT17 and MOT20) using standard evaluation protocols: MOTA (Multi-Object Tracking Accuracy), IDF1 (Identity F1 score), and IDSW (Identity Switches). I ran a strict 5-stage ablation study starting from baseline Kalman and progressively enabling OIE components to isolate the exact empirical contribution of each algorithmic module."
        ),
        (
            "Q7: How is the codebase structured between frontend and backend?",
            "I followed a clean decoupled microservice architecture. The backend is built with Python and FastAPI, handling asynchronous frame ingestion, Kalman filtering, OIE re-association, and SQLite session persistence. The frontend is built in React 19 and TypeScript with Vite, featuring modular components for the interactive canvas, real-time telemetry streaming, and parameter calibration."
        ),
        (
            "Q8: How did you ensure software quality and reliability?",
            "I wrote a comprehensive automated test suite consisting of 30 pytest unit and integration tests. These tests validate Kalman motion forecasting, Mahalanobis gating bounds, anti-pollution memory persistence, ambiguity rejection logic, track lifecycle transitions, and API endpoint contracts. Every build passes 30/30 tests."
        ),
        (
            "Q9: If you had another month to work on this, what would you build next?",
            "I would implement two extensions: First, multi-camera re-identification (ReID across disparate camera viewpoints in large facilities using spatial-temporal topology maps). Second, automatic camera auto-calibration to estimate real-world ground-plane metric coordinates for direct pedestrian velocity and density analytics."
        ),
        (
            "Q10: Why are you interested in joining our company, and how does this project prepare you?",
            "Your team works on mission-critical, high-impact engineering challenges where software reliability, algorithmic performance, and business ROI matter. Building ZED VISION proved my ability to take an ambiguous problem statement, research and invent a solution, write production-grade code, test it rigorously, and deliver an intuitive user experience. I am eager to bring this same ownership, work ethic, and technical rigor to your engineering team."
        )
    ]

    for q, a in qa_list_2:
        story.append(Paragraph(f"<b>{q}</b>", ParagraphStyle('Q', fontName='Helvetica-Bold', fontSize=8.8, textColor=c_primary)))
        story.append(Spacer(1, 2))
        story.append(Paragraph(f"<b>Model Answer:</b> \"{a}\"", ParagraphStyle('A', fontName='Helvetica', fontSize=8.2, leading=11.5, textColor=c_dark)))
        story.append(Spacer(1, 6))

    # =========================================================================
    # PAGE 10: PRACTICE CHECKLIST & DELIVERY TIPS FOR INTERVIEWS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("9. Pre-Presentation Checklist & Delivery Tips for Interviews", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>The 10-Minute Delivery Stopwatch Checklist:</b>", bold_body_style))

    stopwatch_data = [
        [
            Paragraph("Stopwatch Mark", table_header_style),
            Paragraph("Slide / Screen", table_header_style),
            Paragraph("Action & Speaking Topic", table_header_style),
            Paragraph("Checkpoint Status", table_header_style),
        ],
        [
            Paragraph("<b>0:00</b>", table_cell_style),
            Paragraph("Home Page", table_cell_style),
            Paragraph("Introduce yourself, project name, and state the PS-2 problem clearly.", table_cell_style),
            Paragraph("<font color='#059669'>[OK] Hook Landed</font>", table_cell_style),
        ],
        [
            Paragraph("<b>1:30</b>", table_cell_style),
            Paragraph("Architecture", table_cell_style),
            Paragraph("Explain 4-stage causal pipeline and OIE mechanism simply.", table_cell_style),
            Paragraph("<font color='#059669'>[OK] Tech Validated</font>", table_cell_style),
        ],
        [
            Paragraph("<b>3:30</b>", table_cell_style),
            Paragraph("Live Studio", table_cell_style),
            Paragraph("Navigate to Live Studio (autoplays). Show Frame 42-65 transit gate occlusion.", table_cell_style),
            Paragraph("<font color='#059669'>[OK] Demo Proven</font>", table_cell_style),
        ],
        [
            Paragraph("<b>6:30</b>", table_cell_style),
            Paragraph("Experiments", table_cell_style),
            Paragraph("Show Ablation Benchmarks (-68% ID switches, 72% MOTA, 65 FPS).", table_cell_style),
            Paragraph("<font color='#059669'>[OK] Numbers Delivered</font>", table_cell_style),
        ],
        [
            Paragraph("<b>8:30</b>", table_cell_style),
            Paragraph("Closing / Q&A", table_cell_style),
            Paragraph("Deliver impactful closing pitch, connect skills to company, open Q&A.", table_cell_style),
            Paragraph("<font color='#059669'>[OK] Strong Finish</font>", table_cell_style),
        ],
    ]
    t_stop = Table(stopwatch_data, colWidths=[80, 90, 244, 90])
    t_stop.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_dark),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_stop)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Physical Setup & Technical Contingency Checklist:</b>", bold_body_style))
    story.append(Paragraph("• <b>Local Server Pre-Check:</b> Ensure backend (port 8080) and frontend (port 5173) are running 5 minutes prior to the meeting by running <code>.\\run_zed_vision.ps1</code>.", body_style))
    story.append(Paragraph("• <b>Dual Monitor or Split-Screen:</b> Have your browser on the left half of the screen and this PDF open on the right half as your reference guide.", body_style))
    story.append(Paragraph("• <b>Zero-Lag Assurance:</b> The transit gate demo is stored locally at <code>data/samples/transit_gate_demo.mp4</code> and runs completely offline without depending on internet speed.", body_style))
    story.append(Paragraph("• <b>Backup PDF Manual Link:</b> If the interviewer asks for written documentation or architecture diagrams, point them directly to the <b>User Manual (PDF)</b> link in the application sidebar or provide <code>docs/ZED_VISION_User_Manual.pdf</code>.", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Author & Contributor Verification:</b>", bold_body_style))
    story.append(Paragraph("Project Repository: <b>https://github.com/sasi-04/identity-preserving-multi-object-tracking</b><br/>"
                           "Sole Author & Contributor: <b>sasi-04 (sasidharan.n.s54@gmail.com)</b>", body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Presentation master guide PDF successfully generated: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
