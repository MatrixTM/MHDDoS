# Security Policy

## Reporting a vulnerability

Do not open a public issue for a security problem.

Use GitHub's private advisory form:

https://github.com/MatrixTM/MHDDoS/security/advisories/new

Include:

- the affected version or commit;
- a minimal reproduction;
- the impact and affected component;
- any suggested fix.

You should get an acknowledgement within a few days. Please give the maintainers time to release a fix before publishing details.

## Scope

In scope:

- remote code execution, command injection, or path traversal in `start.py` or the web panels;
- authentication or authorization flaws in the panels;
- dependency vulnerabilities that affect the shipped code;
- unsafe defaults that expose the panel or its tokens.

Out of scope:

- the tool doing what it is designed to do against a target you supplied;
- reports that require a modified local build;
- missing hardening with no demonstrated impact;
- social engineering or physical access.

## Supported versions

Security fixes land on `main` and the latest release. Older releases may not receive patches.

## Safe harbour

Good-faith research on this repository is welcome. Do not test against third-party systems without permission.
