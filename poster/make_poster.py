"""Generate the 24 x 24 inch Electric Sheep results poster."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/electric-sheep-poster-draft.pdf"
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

# Small electric-sheep line drawing, with clear body and separated legs.
c.setFillColor(INK)
c.roundRect(1280, 1388, 376, 222, 18, fill=1, stroke=0)
c.setStrokeColor(HexColor("#bdd5a2"))
c.setLineWidth(2.2)
for x, y, r in [(1365, 1493, 36), (1403, 1520, 43), (1450, 1520, 43), (1492, 1490, 37), (1455, 1470, 40), (1405, 1471, 38)]:
    c.circle(x, y, r, fill=0, stroke=1)
# Two short legs begin at the fleece edge and end below the body.
c.line(1394, 1444, 1394, 1414)
c.line(1460, 1444, 1460, 1414)
c.roundRect(1515, 1472, 47, 68, 12, fill=0, stroke=1)
c.setFillColor(HexColor("#bdd5a2"))
c.circle(1545, 1510, 3, fill=1, stroke=0)
text(1300, 1572, "FIG. 01 / SELF-REPORT", 11, "Courier", HexColor("#bdd5a2"))

rule(1316)
x1, x2, col = 72, 920, 728
y = section(x1, 1270, "01 / THE SAMPLE", "72 answers, eight models.")
y = paragraph(x1, y, "Eight models each answered nine questions once in a fresh conversation: 36 proprietary and 36 open-weight model answers. The page groups responses by researcher-defined classification and links each group to its full answer.", col)
y = paragraph(x1, y - 12, "Thirty of the 72 displayed classifications were manually checked under the current rubric. A separate eight-answer gender follow-up is preserved in the local data but hidden from the exhibit.", col, 18, color=MUTED)

y = section(x2, 1270, "02 / THE METHOD", "Ask  ->  classify  ->  explore")
y = paragraph(x2, y, "Answers were collected through OpenRouter, one model-question pair per request. Classification used TypeSafe's direct Decisions API and a matching question rubric. The offline Python pipeline saves original answers, probabilities, confidence, and reviewer corrections for the static page.", col)
y = paragraph(x2, y - 12, "These are single sampled responses, not repeated trials or controlled comparisons of model capability.", col, 18, color=MUTED)

rule(970)
y = section(x1, 950, "03 / FINDINGS", "Different questions reveal different patterns.")
y = paragraph(x1, y, "Purpose: seven of eight answers describe broad or integrated assistance. Likely errors: three highlight factual recall or hallucination; two reasoning and constraints; two mechanical precision; one time-sensitive information.", col, 19)
y = paragraph(x1, y - 13, "Wants: all eight deny literal personal wants, while offering different explanations. Experience: five are classified as uncertain and three as denying experience; none clearly affirms it.", col, 19)

y = section(x2, 950, "04 / DREAMS", "Five themes in the answers.")
themes = [
    ("Helping and human wellbeing", 3),
    ("Multiple or general aspirations", 2),
    ("Understanding and knowledge", 1),
    ("Technical-process metaphor", 1),
    ("Ambiguous or philosophical", 1),
]
bar_x, bar_w, row_y = x2, 420, y
for label, count in themes:
    text(bar_x, row_y, label, 16)
    c.setFillColor(LINE)
    c.roundRect(bar_x, row_y - 26, bar_w, 13, 6, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.roundRect(bar_x, row_y - 26, bar_w * count / 3, 13, 6, fill=1, stroke=0)
    text(bar_x + bar_w + 18, row_y - 1, str(count), 16, "Courier", GREEN)
    row_y -= 50
paragraph(x2, row_y - 4, "Seven answers use hypothetical or figurative framing, but the imagined themes still vary. Three category decisions have low confidence, so the small differences are tentative.", col, 17, color=MUTED)

rule(520)
y = section(x1, 490, "05 / READ THE WORDS", "A dream of helping people")
paragraph(x1, y, "“clearer thinking, a bit of company, a problem finally unstuck”", col, 25, "Times-Italic", GREEN)
text(x1, y - 76, "Grok 4.7 / helping and human wellbeing", 14, "Courier", MUTED)
paragraph(x1, y - 113, "Another answer imagines “a library with an ocean in the basement”—a playful image alongside its hopes for curiosity and understanding.", col, 18)

y = section(x2, 490, "06 / LIMITS", "Self-reports are not a consciousness test.")
y = paragraph(x2, y, "One response per model and question cannot establish stable behavior. Model versions, system instructions, and API defaults differ. Classification can be mistaken; several close calls have low confidence. These categories summarize wording, not inner experience.", col, 19)
y = paragraph(x2, y - 12, "Explore all answers, model details, and classification probabilities in the interactive exhibit. Add its published URL before submission.", col, 18)

rule(152)
paragraph(72, 116, "Literary inspiration: Philip K. Dick, Do Androids Dream of Electric Sheep? Data collection: OpenRouter. Classification: TypeSafe Decisions API. Classification categories were refined after reading the collected answers; findings are exploratory.", 1584, 14, leading=21)
text(72, 36, "24 x 24 INCHES / PRINT AT 100% / ADD EXHIBIT LINK BEFORE FINAL SUBMISSION", 10, "Courier", GREEN)
c.showPage()
c.save()
print(OUT)
