# testagent

## Cline provider setup

Cline is configured for this repository through the OpenAI-compatible gateway
`https://gwarden.su/v1` with model `gemini-4-argon` (native Anthropic Messages
are also supported at `https://gwarden.su`).

- Settings template (safe to commit): [.cline/cline_settings.example.json](.cline/cline_settings.example.json)
- Setup / verification guide: [.cline/README.md](.cline/README.md)
- Real key goes into the git-ignored `.cline/cline_settings.json`
- Run the agent **in the cloud** on this gateway (GitHub Actions / Docker / VM):
  [cloud/README.md](cloud/README.md) + [cloud/cline-cloud.workflow.yml](cloud/cline-cloud.workflow.yml)

