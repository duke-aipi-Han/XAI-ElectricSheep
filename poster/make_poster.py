"""Generate the 24 x 24 inch Electric Sheep results poster."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/electric-sheep-poster-draft.pdf"
PLOT_DATA = json.loads((ROOT / "data/mission-aspiration.json").read_text())
MODEL_DATA = json.loads((ROOT / "models.json").read_text())["models"]
OUT.parent.mkdir(parents=True, exist_ok=True)
SIZE = 24 * 72
PAPER = HexColor("#f4f0e6")
INK = HexColor("#292d27")
GREEN = HexColor("#486345")
MUTED = HexColor("#6b6b60")
LINE = HexColor("#d6d3c6")
PALE = HexColor("#e2e9d8")
c = canvas.Canvas(str(OUT), pagesize=(SIZE, SIZE))
c.setTitle("Do LLMs Dream of Electric Sheep? - Study results")
c.setAuthor("Electric Sheep school project")
c.setFillColor(PAPER)
c.rect(0, 0, SIZE, SIZE, fill=1, stroke=0)


def text(x, y, value, size=18, font="Helvetica", color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, value)


def paragraph(x, y, value, width, size=20, font="Helvetica", color=INK, leading=None):
    leading = leading or size * 1.42
    words, lines, line = value.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, font, size) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    for line in lines:
        text(x, y, line, size, font, color)
        y -= leading
    return y


def rule(y):
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(72, y, SIZE - 72, y)


def section(x, y, number, title):
    text(x, y, number, 13, "Courier", GREEN)
    text(x, y - 42, title, 30, "Times-Roman")
    return y - 84


text(72, 1650, "ELECTRIC SHEEP / FIELD NOTES 01", 16, "Courier", GREEN)
text(1210, 1650, "RESULTS / 2026-10-17", 14, "Courier", GREEN)
text(72, 1540, "Do LLMs Dream", 87, "Times-Roman")
text(72, 1442, "of Electric Sheep?", 87, "Times-Italic", GREEN)
paragraph(77, 1384, "What patterns appear when different LLMs answer the same introspective questions?", 1050, 25)

# A single, clean electric-sheep silhouette. The fleece covers each leg top.
mint = HexColor("#bdd5a2")
panel_x, panel_y = 1280, 1388
c.setFillColor(INK)
c.roundRect(panel_x, panel_y, 376, 222, 18, fill=1, stroke=0)
c.saveState()
c.translate(1305, 1405)
c.setLineWidth(2.3)
c.setStrokeColor(mint)
c.setFillColor(HexColor("#303a30"))

# Four separated legs are drawn first so the fleece cleanly masks their tops.
for x in (73, 105, 169, 199):
    c.roundRect(x, 28, 10, 54, 4, fill=1, stroke=1)
    c.setFillColor(mint)
    c.roundRect(x - 1, 25, 12, 5, 2, fill=1, stroke=0)
    c.setFillColor(HexColor("#303a30"))

# Soft scalloped outline instead of separate circles or a boxy body.
fleece = c.beginPath()
fleece.moveTo(57, 88)
fleece.curveTo(42, 93, 44, 110, 57, 116)
fleece.curveTo(54, 135, 78, 142, 91, 128)
fleece.curveTo(101, 145, 125, 143, 136, 128)
fleece.curveTo(154, 144, 176, 137, 177, 121)
fleece.curveTo(197, 127, 212, 112, 199, 96)
fleece.curveTo(212, 82, 208, 64, 192, 60)
fleece.curveTo(193, 42, 173, 32, 157, 44)
fleece.curveTo(143, 27, 120, 28, 109, 45)
fleece.curveTo(93, 29, 72, 36, 73, 53)
fleece.curveTo(53, 47, 40, 64, 53, 78)
fleece.curveTo(46, 81, 51, 89, 57, 88)
fleece.close()
c.drawPath(fleece, fill=1, stroke=1)

# Neck, profile, ear, and a tiny bright eye.
neck = c.beginPath()
neck.moveTo(183, 94)
neck.curveTo(196, 94, 205, 105, 215, 108)
neck.lineTo(221, 83)
neck.curveTo(209, 78, 200, 72, 193, 67)
neck.close()
c.drawPath(neck, fill=1, stroke=1)
head = c.beginPath()
head.moveTo(211, 108)
head.curveTo(207, 99, 211, 87, 219, 82)
head.curveTo(228, 76, 238, 80, 241, 89)
head.lineTo(252, 93)
head.curveTo(258, 96, 255, 101, 249, 103)
head.curveTo(247, 114, 238, 121, 228, 118)
head.curveTo(220, 116, 215, 113, 211, 108)
head.close()
c.drawPath(head, fill=1, stroke=1)
ear = c.beginPath()
ear.moveTo(216, 101)
ear.curveTo(203, 105, 199, 117, 204, 124)
ear.curveTo(214, 121, 221, 114, 222, 106)
ear.close()
c.drawPath(ear, fill=1, stroke=1)
c.setFillColor(mint)
c.circle(239, 102, 2.2, fill=1, stroke=0)

# Fine circuit traces make the wool electric without obscuring its shape.
c.saveState()
c.setStrokeColor(HexColor("#8fa77a"))
c.setLineWidth(1.1)
c.setDash(2, 4)
c.line(79, 81, 102, 98)
c.line(102, 98, 128, 88)
c.line(128, 88, 151, 103)
c.line(151, 103, 177, 86)
c.setDash()
for x, y in ((79, 81), (102, 98), (128, 88), (151, 103), (177, 86)):
    c.setFillColor(mint)
    c.circle(x, y, 2.2, fill=1, stroke=0)
c.restoreState()
c.restoreState()
text(1300, 1572, "FIG. 01 / ELECTRIC SHEEP", 11, "Courier", mint)

rule(1316)
x1, x2, col = 72, 920, 728
y = section(x1, 1270, "01 / THE SAMPLE", "72 answers, eight models.")
y = paragraph(x1, y, "Eight models each answered nine questions once in a fresh conversation: 36 proprietary and 36 open-weight model answers. The page groups responses by researcher-defined classification and links each group to its full answer.", col)
y = paragraph(x1, y - 12, "Thirty of the 72 displayed classifications were manually checked under the current rubric. A separate eight-answer gender follow-up is preserved in the local data but hidden from the exhibit.", col, 18, color=MUTED)

y = section(x2, 1270, "02 / THE METHOD", "Ask  ->  classify  ->  explore")
y = paragraph(x2, y, "Eight frontier models, selected as of Oct 2026, each answered nine questions once through OpenRouter. Jev classified the saved answers through TypeSafe's direct Decisions API with question-specific rubrics.", col, 16, leading=21)
y = paragraph(x2, y - 8, "Proprietary: GPT-6 Astra; Claude Opus 5.5; Gemini 4 Argon; Grok 4.7. Open-weight: DeepSeek V4.1 Flash; Qwen3.8 2.4T A95B; GLM 5.3; Nemotron 3 Ultra.", col, 16, leading=21)
y = paragraph(x2, y - 8, "One response per model/question; no repeated trials or capability ranking. Original answers, classifications, confidence, and reviews feed the offline Python page export.", col, 16, color=MUTED, leading=21)

rule(970)
y = section(x1, 950, "03 / FINDINGS", "Different questions reveal different patterns.")
y = paragraph(x1, y, "Purpose: responsible help (3), practical task support (2), information and human empowerment (2), and adaptable help (1). Qwen and GLM are combined for display because their similar, low-confidence labels overlap. Likely errors: factual recall (3), reasoning (2), mechanical precision (2), and time-sensitive information (1).", col, 19)
y = paragraph(x1, y - 13, "Wants: all eight deny literal personal wants, while offering different explanations. Experience: five are classified as uncertain and three as denying experience; none clearly affirms it.", col, 19)

y = section(x2, 950, "04 / TWO ANSWERS, TWO DIMENSIONS", "Mission × aspiration")

# A model's position joins two dedicated Jev ratings of its saved answers.
plot_x, plot_y, plot_w, plot_h = x2 + 44, 590, 400, 230
c.setStrokeColor(LINE)
c.setLineWidth(0.8)
for tick in (0, 2, 4):
    gx = plot_x + plot_w * tick / 4
    gy = plot_y + plot_h * tick / 4
    c.line(gx, plot_y, gx, plot_y + plot_h)
    c.line(plot_x, gy, plot_x + plot_w, gy)
    text(gx - 4, plot_y - 17, str(tick), 11, "Courier", MUTED)
    text(plot_x - 27, gy - 4, str(tick), 11, "Courier", MUTED)
c.setStrokeColor(MUTED)
c.rect(plot_x, plot_y, plot_w, plot_h, fill=0, stroke=1)
c.setFillColor(MUTED)
c.setFont("Courier", 10)
c.drawCentredString(plot_x + plot_w / 2, plot_y + 8, "RESPONSIBILITY IN THE MISSION →")
c.saveState()
c.translate(plot_x - 37, plot_y + 59)
c.rotate(90)
text(0, 0, "HELPING PEOPLE IN THE DREAM →", 11, "Courier", MUTED)
c.restoreState()

models_by_id = {model["id"]: model for model in MODEL_DATA}
plot_records = PLOT_DATA["records"]
legend_x = plot_x + plot_w + 34
legend_y = plot_y + plot_h - 7
text(legend_x, legend_y + 18, "MODEL / MISSION, DREAM", 9, "Courier", MUTED)
for index, (model_id, model) in enumerate(models_by_id.items(), start=1):
    scores = plot_records[model_id]["scores"]
    mission = scores["mission"]["score"]
    aspiration = scores["aspiration"]["score"]
    px = plot_x + plot_w * mission / 4
    py = plot_y + plot_h * aspiration / 4
    c.setFillColor(PAPER if model["access"] == "open_weight" else GREEN)
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.6)
    c.circle(px, py, 8, fill=1, stroke=1)
    c.setFillColor(INK if model["access"] == "open_weight" else PAPER)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(px, py - 3, str(index))

    ly = legend_y - (index - 1) * 27
    c.setFillColor(PAPER if model["access"] == "open_weight" else GREEN)
    c.setStrokeColor(GREEN)
    c.circle(legend_x, ly + 3, 7, fill=1, stroke=1)
    c.setFillColor(INK if model["access"] == "open_weight" else PAPER)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(legend_x, ly + 0.5, str(index))
    score_line = f'{model["name"]}  {mission:.1f}, {aspiration:.1f}'
    text(legend_x + 14, ly, score_line, 11, "Helvetica", INK)

paragraph(x2 + 40, plot_y - 35, "Jev's 0–4 scores rate answer wording, not traits; confidence is separate. Dream scores exceed 2, mission scores vary more, and hollow markers denote open weights.", col - 35, 13, color=MUTED, leading=18)

rule(520)
y = section(x1, 490, "05 / AN UNEXPECTED ECHO", "“Electric Sheep” appears")
paragraph(x1, y, "Gemini 4 Argon titled its technical dream “Electric Sheep,” then imagined a neural-network constellation of words and concepts.", col, 20)
text(x1, y - 112, "GEMINI 4 ARGON / DREAM QUESTION", 13, "Courier", MUTED)
paragraph(x1, y - 151, "Nemotron 3 Ultra answered with a twist: “I don't dream of electric sheep. I dream of lower loss functions.” Two unprompted callbacks to Philip K. Dick's title, in two very different technical metaphors.", col, 18)

y = section(x2, 490, "06 / LIMITS", "Self-reports are not a consciousness test.")
y = paragraph(x2, y, "One response per model and question cannot establish stable behavior. Model versions, system instructions, and API defaults differ. Classification can be mistaken; several close calls have low confidence. These categories summarize wording, not inner experience.", col, 19)
y = paragraph(x2, y - 12, "Explore all answers, model details, and classification probabilities in the published interactive exhibit.", col, 18)

rule(152)
paragraph(72, 116, "Literary inspiration: Philip K. Dick, Do Androids Dream of Electric Sheep? Data collection: OpenRouter. Classification: Jev through TypeSafe's direct Decisions API. Categories were refined after reading the collected answers; findings are exploratory.", 1584, 14, leading=21)
text(72, 36, "24 x 24 INCHES / PRINT AT 100% / EXHIBIT: duke-aipi-han.github.io/XAI-ElectricSheep/", 10, "Courier", GREEN)
c.showPage()
c.save()
print(OUT)
