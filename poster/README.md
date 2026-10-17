# Poster

The PDF at `output/pdf/electric-sheep-poster-draft.pdf` is one **24 x 24 inch** page (1728 x 1728 PDF points). It summarizes the collected answers, current classification counts, and dream themes. The exhibit URL and student/course credit still need to be added before final submission.

Edit `poster/make_poster.py` to update the poster. All text and the small chart are kept in a simple Python script, with no design-tool dependency.

To regenerate (Python 3):

```sh
python3 -m venv tmp/pdf-venv
tmp/pdf-venv/bin/pip install reportlab
tmp/pdf-venv/bin/python poster/make_poster.py
```

Print at actual size / 100%, not fit-to-letter. Add the published exhibit URL and student/course credit before submission.
