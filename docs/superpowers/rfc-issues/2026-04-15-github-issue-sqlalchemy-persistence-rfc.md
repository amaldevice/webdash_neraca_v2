# GitHub issue draft — paste into GitHub or `gh issue create --body-file`

**Repository:** `https://github.com/amaldevice/webdash_neraca_v2` — **Issue terbuka:** https://github.com/amaldevice/webdash_neraca_v2/issues/9

**Suggested title:**

```text
[RFC] SQLAlchemy 2.0 portable persistence (SQLite / MySQL / PostgreSQL) + Pythonic CRUD refactor
```

**Suggested labels (create in repo UI if missing):** `enhancement`, `refactoring`, `documentation`, `tech-debt`

**Assign / automation:** GitHub **Copilot coding agent** assignment is usually done in the issue UI after creation (Assignees → Copilot). This draft is sized for human or agent execution in parallel workstreams.

---

## Isi body issue (sumber tunggal)

**Jangan edit duplikat di file ini.** Isu lengkap (ringkas + AC lengkap, hasil review subagent) ada di:

**`docs/superpowers/rfc-issues/2026-04-15-github-issue-body-ONLY.md`**

---

## Create issue via CLI (when `gh` is installed and authenticated)

From repo root:

```powershell
gh issue create `
  --repo amaldevice/webdash_neraca_v2 `
  --title "[RFC] SQLAlchemy 2.0 portable persistence (SQLite / MySQL / PostgreSQL) + Pythonic CRUD refactor" `
  --body-file docs/superpowers/rfc-issues/2026-04-15-github-issue-body-ONLY.md `
  --label enhancement
```

(If `--label enhancement` fails because the label does not exist yet: create the label once in the GitHub UI, or omit the flag.)
