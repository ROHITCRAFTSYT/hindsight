# Security Policy

## Supported versions

Hindsight was built for a hackathon and has no release branches. Fixes land
on `master` only.

## Reporting a vulnerability

Report privately through GitHub's
[security advisory form](https://github.com/ROHITCRAFTSYT/hindsight/security/advisories/new)
rather than opening a public issue. Expect an acknowledgement within seven days.

Include the affected endpoint or file, steps to reproduce, and what an
attacker gains.

## Scope

In scope:

- Leaking `COGNEE_CLOUD_API_KEY` or `LLM_API_KEY` through an API response,
  log line, or error page — the upstream error bodies from Cognee Cloud are
  surfaced to the caller, which is the likeliest place for this to happen.
- Anything in a `dataset` value that escapes the intended dataset when
  `/api/remember`, `/api/forget`, or `/api/graph` forwards it to Cognee.
- Content stored via `/api/remember` that is later replayed by `/api/recall`
  or `/api/recap` in a way that executes in the frontend (stored XSS).
- Vulnerable dependency versions pinned by this repository.

Out of scope:

- Vulnerabilities in Cognee itself or in the configured LLM provider —
  report those upstream.
- The default `CORS_ORIGINS` and the absence of authentication. Hindsight
  ships as a local single-user demo; see the deployment note below.

## Deploying beyond localhost

The backend has **no authentication and no per-user isolation**. Every caller
shares one memory store and can read, write, and forget anything in it. The
defaults assume the API is reachable only from your own machine.

If you expose it publicly, put an authenticating reverse proxy in front of it,
narrow `CORS_ORIGINS` to the real frontend origin, and keep `DEMO_MODE=false`
with real keys stored outside the repository. Reports that consist of
"the public deployment I made has no auth" are configuration, not a bug.

## Secrets

Keys are read from `backend/.env`, which `.gitignore` excludes. Only
`.env.example` — placeholders, no values — is tracked. If you ever commit a
real key, rotate it in the provider dashboard; removing the commit is not
enough.
