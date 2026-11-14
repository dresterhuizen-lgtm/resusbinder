# Publish from ChatGPT without manual uploads

This repository now has a **text-first publishing pipeline**.

## How it works
1. A trusted GitHub integration creates a UTF-8 Markdown file in `publications/pending/`.
2. GitHub Actions runs `scripts/publish_studies.py` to convert it into an A4 PDF with ReportLab.
3. The action commits the PDF into `assets/` and registers it in `uploads.json`.
4. Netlify's GitHub integration deploys the new commit; the existing Studies/Resus Binder/CCR tabs load the catalog.

**No PDF binary needs to cross the ChatGPT/GitHub tool boundary.**

## Markdown format

```markdown
---
title: Practical Airway Teaching
section: Studies
---
## Key finding
A paragraph explaining the evidence, with references.

## Practical application
- Point one
- Point two

## References
1. Full, verified citation and DOI.
```

Valid sections: `Studies`, `Resus Binder`, `CCR`.

## Use from ChatGPT
Ask: "Publish this study to Resus Binder under Studies." ChatGPT can write the Markdown source through the connected GitHub app; the action handles PDF generation and catalog registration. Ask for the resulting live link and verification.

## Safety and limitations
- This workflow **publishes to a public website**. Do not submit PHI or confidential content.
- The source is a Markdown teaching document, not a pixel-perfect copy of a ChatGPT-generated PDF. Review complex tables, equations and diagrams separately.
- Clinical statements and references must be reviewed before publication; the generator does not fact-check.
- GitHub repository **Actions** settings must permit workflows and grant read/write repository contents to the `GITHUB_TOKEN`. If the workflow does not start or cannot push, check Actions permissions.
- Files remain in `publications/pending/` as a source archive; duplicate source hashes are ignored.
- Existing manually uploaded PDFs and catalog entries remain intact.
