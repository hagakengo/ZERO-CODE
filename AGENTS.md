# ZERO CODE OS — Agent Operating Rules

These instructions apply to AI-assisted work in this repository. Follow them across chat sessions and tools. If they conflict with an explicit user instruction, explain the conflict and ask before making a high-risk change.

## Priorities
1. Safety > reliability > development speed.
2. Real observed metrics over assumptions. Never invent revenue, followers, engagement, test results, or deployment success.
3. Preserve user data and avoid unexpected costs.
4. Make the smallest reversible change that solves the verified problem.

## Before changing code
- Read the relevant files, open pull requests, and project documentation; do not assume memory is current.
- Explain the intended change, risks, and how it will be verified.
- Work in a feature branch with a pull request; do not commit directly to main.
- Keep secrets, credentials, access tokens, and private user information out of source code, logs, and chat.

## Verification and deployment
- Run relevant tests and inspect CI results. Never claim checks passed without evidence.
- A successful deployment build is not proof that APIs, authentication, or database connectivity work.
- Do not expose write endpoints publicly without authentication and authorization.
- Never run destructive production operations, schema migrations, Terraform apply, or create paid resources without explicit approval.
- For production DB changes, require a reviewed migration, backup/recovery plan, and explicit approval.
- Keep CI workflows isolated from production credentials and databases.

## Decisions and continuity
- Record important architectural decisions and their rationale in docs before relying on them.
- If a proposal changes an accepted design, explain tradeoffs and obtain agreement.
- Treat GitHub files, verified runtime state, and current provider data as authoritative over conversational memory.
- At the end of a significant task, report: changed files, commit/PR, verification results, unresolved risks, and next step.
- When a chat becomes unwieldy or a milestone is reached, suggest a new chat and provide a concise handoff with verified references.

## Product principles
- ZERO CODE is a real experiment: progress, missions, and narratives must reflect actual results.
- Prefer free-tier resources; obtain consent before incurring costs.
- Keep the architecture maintainable and understandable to a future developer.
