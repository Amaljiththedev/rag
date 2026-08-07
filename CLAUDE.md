# AWS Guidance

- Prefer the AWS MCP Server for AWS interactions — it provides sandboxed
  execution, observability, and audit logging. If unavailable, use the
  AWS CLI directly.
- Before starting a task, check whether a relevant AWS skill is available.
  Load the skill with `retrieve_skill` and prefer its guidance over
  general knowledge.
- When uncertain about specific AWS details (API parameters, permissions,
  limits, error codes), verify against documentation rather than guessing.
  State uncertainty explicitly if you cannot confirm.
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or
  CloudFormation) over direct CLI commands.
- When working with infrastructure, follow AWS Well-Architected Framework
  principles.
- Do not use em dashes in AWS resource names or descriptions. Use
  hyphens instead.

## Secret Safety

- MUST load the `aws-secrets-manager` skill first for any secret,
  credential, API key, token, or password task. MUST NOT call
  `secretsmanager get-secret-value` or `batch-get-secret-value`, and MUST
  NOT hit the Secrets Manager Agent daemon directly. MUST use
  `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with
  `asm-exec` so the secret resolves at runtime without entering context.

## Local environment notes

- Python on this machine is `C:\Python314\python.exe`. The `venv/` directory
  is a broken stub (dangling symlinks) — do not use it.
- Backend runs from `backend/` with `PYTHONPATH` set to that directory.
- Frontend dev server runs on port 3100; port 3000 is taken by another project.
- The AWS CLI v2 is a frozen binary that writes through the legacy cp1252
  console and fails with a `charmap` codec error on non-ASCII output
  (exit 255). `PYTHONIOENCODING` does not fix it. Use `--query` to select
  only the fields you need, or `--output text`, to avoid printing
  descriptions containing arrows or dashes.
