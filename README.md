# ci-workflows

Reusable GitHub Actions workflows shared across NotifyNL repositories.

## This repo needs to be public

GitHub only allows a private repository's reusable workflows to be consumed by
*other private repositories* — "Access is allowed only from private repositories."
`notifynl-api` and `notifynl-admin` are public, so any workflow they call with
`uses:` must live in a public repo too, or the call fails with a misleading
`workflow was not found` error.

No test code or credentials live here. Secrets are supplied by the caller via
`secrets: inherit`; the data stays private in the private caller repos.
