## Agent skills

### Issue tracker

Issues are tracked in Linear (workspace: emrcel, team: MAR). See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the default mattpocock/skills label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Deployment

Hugo static site deployed to **GitHub Pages via GitHub Actions** (`.github/workflows/hugo.yaml`), triggered on push to `main`. Custom domain: `sayakatolik.com` (see `CNAME`). The CI runner rebuilds the site itself with `--minify` and the Pages base URL — the committed `public/` directory is only for local preview and is **not** what gets served.

To deploy: commit and `git push origin main`. Watch the run with `gh run watch`.

**Critical:** GitHub Pages must stay in **GitHub Actions** mode (`build_type: workflow`), not "Deploy from a branch." If it flips to `legacy` (branch `main`, path `/`), Pages serves the repo root — which has no `index.html` (the site lives in `public/`) — so the live site 404s **even though the Actions workflow still reports success**. If `sayakatolik.com` 404s after a green deploy, check this first:

```
gh api repos/eusebiusmarcel/sayakatolik/pages -q .build_type   # must be "workflow"
gh api -X PUT repos/eusebiusmarcel/sayakatolik/pages -f build_type=workflow   # fix
```

The custom domain (`cname`) is stored separately and survives the switch.

## Local preview

Preview with `hugo server -D --renderToMemory`. **Do not** run a production
`hugo --minify` build while previewing: `config.toml`'s `baseURL` is the production
domain, so a production build writes absolute `https://sayakatolik.com/...` URLs (and
fingerprinted asset names) into the tracked `public/`, and a disk-serving dev server
then serves those — making not-yet-deployed images/CSS appear blank. Serving from
memory (`--renderToMemory`) keeps preview independent of `public/`. Rebuild `public/`
with `hugo --minify` only as the **last step before deploy**.
