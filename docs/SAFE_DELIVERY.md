# ZERO CODE OS — safe delivery rules

## Change flow
1. Create a feature branch and open a pull request.
2. Require backend tests and frontend typecheck/build to pass.
3. Review security-sensitive changes and Terraform plans before merging.
4. Merge only after review. Vercel can deploy from the protected main branch.

## Production guardrails
- Do not commit .env files, database URLs, tokens, Terraform state, or provider credentials.
- Never put production secrets in GitHub Actions logs or pull-request workflows.
- Do not run Terraform apply, database migrations, or destructive commands on pull requests.
- Require explicit approval and a verified backup before production schema changes.
- Keep production write/sync endpoints authenticated before public access.
- Confirm health, database connectivity, and authorization behavior after deployment.
- Confirm free-tier implications before provisioning any new infrastructure.

## Database ownership
- SQLAlchemy models describe the schema.
- Alembic revisions change the schema; do not let app startup mutate production schema.
- Baseline the existing Supabase schema before applying any migration.
- Terraform manages supported infrastructure resources, not application table changes.

## Current release caveat
A Vercel READY deployment only confirms a successful build/deployment.
It does not establish that PostgreSQL is connected, API routes are secure,
or that the application is ready for public traffic.
