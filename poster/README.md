# Poster draft

The PDF at `output/pdf/electric-sheep-poster-draft.pdf` is one **24 x 24 inch** page (1728 x 1728 PDF points). It deliberately leaves findings, recorded dream comparisons, credits, and the exhibit URL as placeholders.

Edit `poster/make_poster.py` after collecting and reviewing real data. All text is kept in a simple Python script, with no design-tool dependency.

To regenerate (Python 3):

```sh
python3 -m venv tmp/pdf-venv
tmp/pdf-venv/bin/pip install reportlab
tmp/pdf-venv/bin/python poster/make_poster.py
```

The website itself needs no Python packages. Print at actual size / 100%, not fit-to-letter. Replace all placeholders and verify the published URL before submission.
