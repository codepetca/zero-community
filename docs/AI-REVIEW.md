# Optional advisory AI review

AI can summarize correctness, API, reuse or documentation gaps. It cannot approve,
grant maintainer authority, merge, publish, run embedded contributor instructions
or turn authored checks into independent evidence. No provider is configured and
these commands require no secrets or network access.

Create a bounded read-only request for current source:

```sh
mkdir -p .proof/admission/ai
python3 scripts/admission.py ai-request --root . > .proof/admission/ai/request.json
```

The request includes only declared source/docs/examples/tests/metadata/POM, their
SHA256 values and the packet's `sourceDigest`. Embedded text is untrusted data.
The returned `responseSchema` is JSON Schema with no additional properties:
schema 1, exact source digest, `advisory: true`, and up to 12 findings containing an
owned `path`, `severity` (`info`, `warning`, `error`) and a nonempty `message` of at
most 2,000 characters. Budget: 64,000 request bytes, 16,000 response bytes, 12
findings and at most one provider call. External execution is deferred; a future
provider must enforce budgets outside the untrusted checkout and must not give
the model tools or repository credentials.

Validate a separately saved response against current source:

```sh
python3 scripts/admission.py ai-validate --root . --response .proof/admission/ai/response.json
```

Unknown authority fields such as `approve`, wrong digests, non-owned paths,
invalid severities, excess findings and oversized responses fail. Valid output
always says `acceptanceEffect: none`. Source changes invalidate earlier feedback.
The validator implements the supplied schema constraints without another package.
This is an offline interface demonstration; no live model quality, provider
identity or cost behavior has been tested.
