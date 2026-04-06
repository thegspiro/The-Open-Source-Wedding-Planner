# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.10.x  | Yes                |
| < 2.10  | No                 |

## Reporting a Vulnerability

**For sensitive security issues** (e.g., authentication bypass, SQL injection, data exposure):

- Email: **security@thegspiro.dev**
- Do NOT open a public GitHub issue.
- Include a description of the vulnerability, steps to reproduce, and any potential impact.

**For non-sensitive issues** (e.g., missing input validation, dependency updates):

- Open a GitHub issue at [thegspiro/the-open-source-wedding-planner](https://github.com/thegspiro/the-open-source-wedding-planner/issues) with the `security` label.

## Expected Response Time

- Acknowledgment within **48 hours**.
- Initial assessment within **5 business days**.
- Fix or mitigation for confirmed vulnerabilities within **30 days**, depending on severity.

## What Constitutes a Security Issue

- Authentication or authorization bypass
- SQL injection or other injection attacks
- Cross-site scripting (XSS) or cross-site request forgery (CSRF)
- Exposure of sensitive user data (passwords, personal information)
- Session hijacking or fixation
- Insecure default configurations that could lead to compromise

## Out of Scope

- Denial-of-service attacks against self-hosted instances
- Issues in dependencies without a demonstrated exploit in this application
- Social engineering
