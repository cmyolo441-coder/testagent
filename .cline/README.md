# Cline provider configuration (gwarden.su)

Repository-level Cline settings for this workspace.
`cline_settings.example.json` holds the provider keys exactly as Cline stores
them in its `globalState`, so the file can be imported or copy/pasted into the
Cline settings UI. **No secrets are committed** — your real key lives in the
git-ignored `cline_settings.json` next to it (or in Cline's own settings).

## Endpoint details

| Setting | Value |
| --- | --- |
| Provider | OpenAI Compatible (default) or Anthropic |
| Base URL (OpenAI override) | `https://gwarden.su/v1` |
| Base URL (Anthropic) | `https://gwarden.su` |
| API Key | your `GWAR-...` gateway key (see below) |
| Model ID | `gemini-4-argon` |

Both protocols are supported by the gateway:

- OpenAI Chat: `POST https://gwarden.su/v1/chat/completions`
- Native Anthropic Messages: `POST https://gwarden.su/v1/messages` (full
  `tool_calls` / `tool_use` support)

## Local settings file

```bash
cp .cline/cline_settings.example.json .cline/cline_settings.json
# then put your GWAR-... key into openAiApiKey / anthropicApiKey
```

`.cline/cline_settings.json` is listed in `.gitignore`, so the key never enters
git history. Never commit the real key.

## ⚠️ app.cline.bot dashboard me custom provider NAHI lagta

Cline Cloud Agents (browser dashboard, `app.cline.bot` → Agents) sirf teen
providers support karta hai — `ClineFree`, `ClinePass`, `Cline (usage-billing)`
(source: Cline docs, "Cline Cloud Agents" → *Choose a model*). Wahan Base URL /
API Key daalne ka field hi nahi hai, isliye `gwarden.su` ya `gemini-4-argon`
model picker me kabhi nahi dikhega. Dashboard ke provider dropdown me sirf wahi
teen options aayenge.

Custom endpoint (BYOK) yahan chalta hai:

| Client | Provider option | Base URL |
| --- | --- | --- |
| VS Code / JetBrains extension (Cline sidebar) | OpenAI Compatible | `https://gwarden.su/v1` |
| Cline Desktop app | OpenAI Compatible | `https://gwarden.su/v1` |
| Cline CLI / TUI | OpenAI Compatible | `https://gwarden.su/v1` |
| Anthropic-native in any of the above | Anthropic | `https://gwarden.su` |

Dashboard par agar `gemini-4-argon` nahi dikh raha to ye bug nahi hai — provider
hi available nahi hai. Cloud me hi chalana ho to **same agent** ko apne cloud
me chalao (GitHub Actions / Docker / VM) — poora setup:
[`cloud/README.md`](../cloud/README.md). Ek command me:

```bash
gh secret set GWARDEN_API_KEY --body '<your GWAR key>'
gh workflow run cline-cloud.yml -f task="fix the failing tests" -f branch=main
```

Dashboard ke bottom me **Install Cline CLI** / **Install in your IDEs** buttons
bhi wahi raste hain (CLI + IDE extension me custom provider chalta hai).



## Apply in the Cline extension (VS Code / Cline sidebar)

1. Open the Cline panel and click the gear icon (Settings).
2. Under **API Configuration**, pick **OpenAI Compatible**.
3. Fill in:
   - Base URL: `https://gwarden.su/v1`
   - API Key: your `GWAR-...` key
   - Model ID: `gemini-4-argon`
4. (Optional) Expand the model configuration and set context window
   `1000000`, max output tokens `64000`, and enable image support.
5. Click **Done**.

Prefer Anthropic-native tool use? Repeat the steps with provider **Anthropic**,
Base URL `https://gwarden.su`, the same API key and the same model ID. Cline
appends `/v1/messages` automatically.

**Agar model dropdown khali / `gemini-4-argon` na dikhe:** Cline model list
`GET {baseUrl}/models` se laata hai — gwarden 96 models return karta hai, par
dropdown refresh karna pad sakta hai. Model ID field me `gemini-4-argon`
type/hard-code kar do, tab bhi kaam karega (verified: `200` on both protocols).


## Apply for the Cline CLI / headless runs

The CLI reads the same keys from its settings file
(`~/.cline/data/globalStorage/settings/cline_settings.json`) — copy your local
`cline_settings.json` there, or export environment variables:

```bash
export OPENAI_API_BASE="https://gwarden.su/v1"
export OPENAI_API_KEY="$GWARDEN_API_KEY"
export OPENAI_MODEL="gemini-4-argon"

# or for the Anthropic-style client
export ANTHROPIC_BASE_URL="https://gwarden.su"
export ANTHROPIC_API_KEY="$GWARDEN_API_KEY"
export ANTHROPIC_MODEL="gemini-4-argon"
```

## Verify the credentials

```bash
# list models exposed by the gateway
curl -sS https://gwarden.su/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# OpenAI Chat completion
curl -sS https://gwarden.su/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-4-argon","messages":[{"role":"user","content":"say OK"}],"max_tokens":16}'

# Native Anthropic Messages
curl -sS https://gwarden.su/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-4-argon","max_tokens":16,"messages":[{"role":"user","content":"say OK"}]}'
```

The model reports a 1,000,000 token context window and 64,000 max output
tokens (`GET /v1/models`).

