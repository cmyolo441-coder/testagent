# Cline in the cloud with your own gateway (`gwarden.su`)

Goal: run the **real Cline agent** in the cloud on `gemini-4-argon` through
`https://gwarden.su/v1` — not on Cline credits.

## Why this file exists

`app.cline.bot` (Cline Cloud Agents dashboard) **cannot** take a custom Base URL
or API key. Its model picker only offers `ClineFree`, `ClinePass` and
`Cline (usage-billing)`
([docs](https://docs.cline.bot/usage/cloud-agents) → *Choose a model*). That is
why `gemini-4-argon` never appears there — no BYOK, no third-party provider.

The way to get "cloud + your model" is to run the **same agent** (Cline CLI /
Cline SDK) inside a cloud environment you control: GitHub Actions, a container,
a VM, Fly.io, Railway, GCE, Kubernetes, … Every option below uses provider
`openai-compatible` with

```
Base URL : https://gwarden.su/v1      (Anthropic-native alt: https://gwarden.su)
API Key  : GWAR-...                   (secret, never committed)
Model ID : gemini-4-argon
```

## Model select — kaise choose kare

Model har jagah ek hi env var se aata hai: `CLINE_MODEL` (default `gemini-4-argon`).
Picker nahi hai, kyunki custom gateway par Cline khud model ID bhejta hai.

```bash
# kaunse models available hain (96 ids)
GWARDEN_API_KEY="$GWARDEN_API_KEY" bash cloud/list-models.sh | head -20
```

**1. GitHub Actions** — workflow me `model` input hai (dropdown):

```bash
gh workflow run cline-cloud.yml \
  -f task="fix the failing tests" \
  -f branch=main \
  -f model=gemini-3.1-pro
```

Ya GitHub UI: Actions → *Cline cloud agent* → Run workflow → **Model ID** dropdown
(`gemini-4-argon`, `gemini-3.1-pro`, `gemini-3.8-flash`, `claude-opus-5`,
`claude-fable-5`, `glm-5.3`) → Run.

**2. Docker / VM** — env var badlo:

```bash
docker run --rm -e GWARDEN_API_KEY=... -e CLINE_MODEL=claude-opus-5 \
  -e CLINE_TASK="review this PR" -v "$PWD:/workspace" cline-gwarden
```

**3. Cline CLI (interactive TUI)** — `/model` se live switch:

```bash
cline auth -p openai-compatible -k "$GWARDEN_API_KEY" -b https://gwarden.su/v1 -m gemini-4-argon
cline -i          # TUI khulega, phir /model type karke model chuno
```

**4. IDE extension** — Settings → API Configuration → OpenAI Compatible →
Model dropdown (list `GET /v1/models` se aati hai; khali lage to ID manually
type karo).

## Option A — GitHub Actions (fastest, free cloud, no server)

Template: [`cloud/cline-cloud.workflow.yml`](cline-cloud.workflow.yml)
(this sandbox's GitHub App token cannot create workflow files, so install it
with the script below — your own token can).

> Note: actions secrets and workflow files need permissions this sandbox's
> GitHub App does not have (`403 Resource not accessible by integration`), so
> run steps 1–3 below with your own `gh` login once.

```bash
bash cloud/install-workflow.sh          # copies it to .github/workflows/cline-cloud.yml
git add .github/workflows/cline-cloud.yml cloud && git commit -m "ci: add Cline cloud agent" && git push

# one-time: store the gateway key as a repo secret
gh secret set GWARDEN_API_KEY --body "$GWARDEN_API_KEY"   # or: --body 'GWAR-...'

# run a task in the cloud
gh workflow run cline-cloud.yml -f task="Add a README section explaining the build" -f branch=main
gh run watch
```

The workflow:

1. checks out the branch,
2. installs Cline CLI (`cline@3.0.73`),
3. runs `cloud/run-cline-cloud.sh` → `cline auth -p openai-compatible -b … -m gemini-4-argon`
   followed by `cline --json --auto-approve true "<task>"`,
4. pushes `cline/cloud-<run-id>` and opens a PR when the agent changed files,
5. uploads `cline-run.jsonl` (full agent event log) as an artifact.

You can also comment `@cline <task>` on any issue in the repo to trigger it.

## Option B — Container / VM (Fly.io, Railway, GCE, Kubernetes, your VPS)

```bash
# build once
docker build -t cline-gwarden cloud

# run a task against a checkout (mounted at /workspace)
docker run --rm \
  -e GWARDEN_API_KEY="$GWARDEN_API_KEY" \
  -e CLINE_TASK="Run the test suite and fix what breaks" \
  -v "$PWD:/workspace" \
  cline-gwarden
```

or with compose:

```bash
cd cloud
GWARDEN_API_KEY=... CLINE_TASK="Summarise the repo structure" docker compose run --rm cline
```

Anything that can run a container works — the only requirements are Node 22,
`git`, and outbound HTTPS to `gwarden.su`. The wrapper
[`run-cline-cloud.sh`](run-cline-cloud.sh) configures the provider and then
execs the agent, so no interactive login is ever needed.

| Env var | Default | Meaning |
| --- | --- | --- |
| `GWARDEN_API_KEY` | — (required) | gateway key |
| `CLINE_TASK` | — (required) | prompt/task for the agent |
| `CLINE_BASE_URL` | `https://gwarden.su/v1` | OpenAI-compatible endpoint |
| `CLINE_MODEL` | `gemini-4-argon` | model id |
| `CLINE_TIMEOUT` | `1800` | seconds |
| `CLINE_AUTO_APPROVE` | `true` | auto-approve tools (headless) |
| `CLINE_CWD` | `/workspace` | working directory |
| `CLINE_CONFIG` / `CLINE_DATA_DIR` | CLI default | isolate `~/.cline` state |

## Option C — Cline Enterprise remote configuration (dashboard-managed)

The only "official dashboard" path: Cline Enterprise admins can push an
organisation-wide **OpenAI Compatible** provider from the hosted admin console
(`docs.cline.bot` → Enterprise → Remote configuration → *Configure OpenAI
Compatible Provider (Admin)*). Members then inherit that provider. It needs an
Enterprise plan; it is not available on a personal `app.cline.bot` account.

## Verified locally (same agent, same gateway)

```console
$ cline auth -p openai-compatible -k "$GWARDEN_API_KEY" -m gemini-4-argon -b https://gwarden.su/v1
Provider configured: openai-compatible (gemini-4-argon)

$ cline --json --auto-approve true -c /workspace/.tools/scratch \
    'Create a file named hello.txt containing exactly the word READY'
{"type":"agent_event","event":{"type":"done","reason":"completed",
 "text":"Done — /workspace/.tools/scratch/hello.txt now contains exactly READY ...",
 "iterations":3,"usage":{"inputTokens":15133,"outputTokens":123,"totalCost":0}}}
{"type":"run_result","finishReason":"completed","iterations":3,
 "model":{"id":"gemini-4-argon","provider":"openai-compatible"},"durationMs":14929}

$ cat /workspace/.tools/scratch/hello.txt
READY
```

Wrapper (`cloud/run-cline-cloud.sh`) was also run end-to-end — second task,
`ready.txt` created in 5.9 s, model `gemini-4-argon`, provider
`openai-compatible`.

`~/.cline/data/settings/providers.json` after `cline auth`:

```json
{
  "lastUsedProvider": "openai-compatible",
  "providers": {
    "openai-compatible": {
      "settings": {
        "provider": "openai-compatible",
        "apiKey": "GWAR-...",
        "model": "gemini-4-argon",
        "baseUrl": "https://gwarden.su/v1"
      }
    }
  }
}
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `gemini-4-argon` missing from a picker | You are on `app.cline.bot` (no BYOK) — use one of the options above. |
| `401` / `403` from the gateway | Key rotated or wrong; re-run `cline auth`. |
| Empty model dropdown in the IDE | Type the model id manually; `GET /v1/models` returns 96 models. |
| Agent hangs in CI | Lower `CLINE_TIMEOUT`, check the `cline-run.jsonl` artifact. |
