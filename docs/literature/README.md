# Literature workflow

The PDFs go in `literature/pdfs/`. That folder is gitignored because the files are copyrighted; only our notes are committed.

1. **paper-reader** (`.claude/agents/paper-reader.md`) runs once per PDF. It writes `docs/literature/<key>.md`, where every statement is page-cited and quotes are exact.
2. **novelty-auditor** reads all the notes plus `docs/CLAIMS.md`. It updates each claim's Novelty column and writes `docs/NOVELTY_VERDICT.md`.
3. **related-work-writer** rewrites the paper's Related Work section and references from the notes only.
4. **hostile-reviewer** audits every number in `paper/PAPER.md` against `results/` and lists overclaims and threats to validity.

No step may use memory of a paper instead of its text. Anything not found in a note stays UNVERIFIED.

## Reading list (priority)

| # | Paper | Where | Status |
| --- | --- | --- | --- |
| 1 | When Benchmarks Lie (arXiv 2602.14161) | arXiv | needed |
| 2 | PIDS-Bench (IEEE Access 2026, 10.1109/ACCESS.2026.3728186) | IEEE | needed |
| 3 | PromptShield (CODASPY 2025) | ACM | needed |
| 4 | A Critical Evaluation of Defenses against Prompt Injection Attacks (SACMAT 2026) | ACM | needed |
| 5 | BIPIA (KDD 2025) | ACM | wanted |
| 6 | How Not to Detect Prompt Injections with an LLM (AISec 2025) | ACM | wanted |
| 7 | InjecGuard / PIGuard (arXiv 2410.22770; ACL 2025) | arXiv / ACL | wanted |
| 8 | TaskTracker, "Get my drift?" (SaTML 2025) | IEEE / arXiv | wanted |
| 9 | HackAPrompt (EMNLP 2023) | arXiv / ACL | wanted |
| 10 | Systematic Review of Prompt Injection Attacks (IEEE Access 2026) | IEEE | wanted |
| 11 | MalPID (ComNet 2024) | IEEE | optional |
| 12 | Hidden-in-Plain-Text (WWW 2026) | ACM | optional |
| 13 | DataSentinel (IEEE S&P 2025) | IEEE | optional |
