# ci-workflows

Reusable GitHub Actions workflows shared across NotifyNL repositories.

## Actions

### `pytest-report`

Reports pytest's junit xml as a check run with `dorny/test-reporter`, with xfailed
tests and superseded upstream tests (notifynl-utils' `superseded_tests_nl.toml`
plugin) as their own counts in the title, badge and table. dorny only knows passed,
failed and skipped, and would count xfailed tests as skipped.

```yaml
      - uses: Worth-NL/ci-workflows/.github/actions/pytest-report@main
        if: ${{ !cancelled() }}
```

Inputs: `name` (check run, default `PyTest Tests`), `path` (default
`reports/pytest-*.xml`), `badge-title` (default `PYTEST`), `token`. The job needs
`checks: write`.

## This repo needs to be public

GitHub only allows a private repository's reusable workflows to be consumed by
*other private repositories* — "Access is allowed only from private repositories."
`notifynl-api` and `notifynl-admin` are public, so any workflow they call with
`uses:` must live in a public repo too, or the call fails with a misleading
`workflow was not found` error.

No test code or credentials live here. Secrets are supplied by the caller via
`secrets: inherit`; the data stays private in the private caller repos.
