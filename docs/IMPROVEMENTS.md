# Improvement audit — 16 September 2026

## Correctness checkpoint

Repeated citations lost later pinpoints and contexts. Online resolution accepted a successful URL without confirming the citation in identity metadata.

Implemented: preserve every citation occurrence and require publisher identity metadata. Regression tests exercise the failure cases and
the original suite remains required. GitHub Actions runs tests, lint and package builds.

## Requested next release

The user requested the ranked product improvements, including optional local browser
workspaces. This extends the earlier CLI-only scope in CLAUDE.md. Existing command-line
interfaces and deterministic libraries remain supported. Browser workspaces must preserve
source evidence and explicit human review; they must not infer legal conclusions.

Workspace implementation, integration tests and release validation are in progress.
