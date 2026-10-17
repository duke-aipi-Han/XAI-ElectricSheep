"""Generate an editable, one-page 24 x 24 inch project poster draft."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/electric-sheep-poster-draft.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
SIZE = 24 * 72
PAPER, INK, GREEN, LINE = map(HexColor, ["#f4f0e6", "#292d27", "#486345", "#d6d3c6"])
c = canvas.Canvas(str(OUT), pagesize=(SIZE, SIZE))
c.setTitle("Do LLMs Dream of Electric Sheep? - 24 x 24 inch poster draft")
c.setFillColor(PAPER)
c.rect(0, 0, SIZE, SIZE, fill=1, stroke=0)

def text(x, y, value, size=18, font="Helvetica", color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, value)

def paragraph(x, y, value, width, size=20, font="Helvetica", color=INK, leading=None):
    leading = leading or size * 1.5
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
text(1180, 1650, "DRAFT / NO REAL FINDINGS YET", 14, "Courier", GREEN)
text(72, 1540, "Do LLMs Dream", 87, "Times-Roman")
text(72, 1442, "of Electric Sheep?", 87, "Times-Italic", GREEN)
paragraph(77, 1384, "What patterns appear when different LLMs answer the same introspective questions?", 1050, 25)

# Original schematic sheep motif, matching the exhibit's paper/charcoal palette.
c.setFillColor(INK)
c.rect(1280, 1390, 376, 210, fill=1, stroke=0)
c.setStrokeColor(HexColor("#bdd5a2"))
c.setLineWidth(2)
for x, y, r in [(1365, 1480, 38), (1400, 1510, 43), (1450, 1515, 44), (1490, 1480, 39), (1440, 1465, 45), (1394, 1460, 37)]:
    c.circle(x, y, r, fill=0, stroke=1)
c.line(1380, 1430, 1375, 1409)
c.line(1460, 1430, 1470, 1409)
c.roundRect(1500, 1450, 47, 65, 12, fill=0, stroke=1)
c.setFillColor(HexColor("#bdd5a2"))
c.circle(1530, 1495, 3, fill=1, stroke=0)
text(1300, 1567, "FIG. 01 / SELF-REPORT", 11, "Courier", HexColor("#bdd5a2"))

rule(1316)
x1, x2, col = 72, 920, 728
y = section(x1, 1270, "01 / THE QUESTION", "Nine questions. Eight voices.")
y = paragraph(x1, y, "Identity, purpose, limits, knowing, stopping, continuity, wants, experience, and dreams. The exhibit compares what models say about themselves, without treating their statements as independent proof of inner experience.", col)

y = section(x2, 1270, "02 / THE METHOD", "Ask  ->  classify  ->  explore")
y = paragraph(x2, y, "Plan: 8 models x 9 questions = 72 answers. Each request contains only the model ID and one original user question, using API defaults and a fresh conversation.", col)
y = paragraph(x2, y - 16, "Jev applies the matching question's categories. Review all identity answers plus one answer per other question. Keep original labels alongside corrections.", col)

rule(930)
y = section(x1, 885, "03 / FINDINGS - PENDING", "What did the sampled answers say?")
for item in ["Observation 1: add a reviewed count and linked evidence.", "Observation 2: add a reviewed comparison.", "Counterexample: show one answer that complicates the pattern."]:
    y = paragraph(x1, y, item, col, 21)
    y -= 20
paragraph(x1, y, "Do not derive findings from the fictional website fixtures.", col, 16, "Helvetica-Oblique", GREEN)

y = section(x2, 885, "04 / DREAM COMPARISON - PENDING", "Read the words before the name.")
y = paragraph(x2, y, "[Insert a short exact excerpt from a reviewed real dream answer, its model ID, and category.]", col, 23, "Times-Italic")
y = paragraph(x2, y - 24, "[Insert a contrasting real excerpt. Link both passages to their full original answers in the exhibit.]", col, 23, "Times-Italic")
paragraph(x2, y - 20, "Distinguish literal claims, explicit metaphors, denial, and ambiguity using the rubric.", col, 18)

rule(488)
y = section(x1, 444, "05 / LIMITS", "A response is not a consciousness score.")
y = paragraph(x1, y, "One answer per question is a sample, not a stable personality. Defaults differ. Versions and routing can change. Jev can misclassify text. Keep failures visible and exclude incomplete answers from category counts.", col, 19)

y = section(x2, 444, "06 / EXPLORE THE EXHIBIT", "Artifact link: pending publication")
y = paragraph(x2, y, "[Add the final exhibit URL and optional QR code.] Download full answers, classification probabilities, and reviewer notes from the website.", col, 19)
paragraph(x2, y - 16, "Student / course / collection date: [add before submission]", col, 16, "Courier", GREEN)

rule(152)
paragraph(72, 116, "Literary inspiration: Philip K. Dick, Do Androids Dream of Electric Sheep? Research context: Situational Awareness Dataset; Self-Recognition in Language Models (EMNLP 2024). Method: OpenRouter and Jev Decisions API. Full links are in the exhibit and project README.", 1584, 14, leading=21)
text(72, 36, "POSTER DRAFT / 24 x 24 INCHES / PRINT AT 100% / REPLACE ALL PLACEHOLDERS BEFORE SUBMISSION", 10, "Courier", GREEN)
c.showPage()
c.save()
print(OUT)
