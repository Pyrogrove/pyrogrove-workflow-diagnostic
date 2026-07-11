# Secrets and Data Boundary

## Allowed

- Synthetic workflow narratives.
- Synthetic business names and records.
- Local generated test evidence.
- Public, non-sensitive source documentation.

## Prohibited

- Real client data.
- Personal or confidential data.
- Production credentials.
- API keys committed to Git.
- Streamlit secrets committed to Git.
- Private keys, certificates, tokens, cookies, or exported browser sessions.

## Control

The `.gitignore` blocks common secret and local-runtime files.

Before every commit:

```powershell
git status --short
git diff --cached
```

Do not stage anything whose purpose or sensitivity is unclear.
