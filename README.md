# axonpush

**This repository has moved to [axonpush/sdks](https://github.com/axonpush/sdks).**

The Python SDK now lives at
[`packages/python`](https://github.com/axonpush/sdks/tree/master/packages/python),
alongside the TypeScript and .NET SDKs. All three generate from one OpenAPI
contract produced by the backend, and CI compares their resource surfaces
against each other so they cannot drift apart.

## Nothing changes for you

```
pip install axonpush
```

Same package, same index.

## Where things went

| | |
|---|---|
| Source | [`axonpush/sdks` → `packages/python`](https://github.com/axonpush/sdks/tree/master/packages/python) |
| Issues and pull requests | [axonpush/sdks/issues](https://github.com/axonpush/sdks/issues) |
| Releases | tagged `sdk-py-v*` in the new repository |

## About this repository

It is archived and read-only.

History came across with `git filter-repo`, so per-file history survives in the
new repository. The `v*` tags stay here as the provenance for the PyPI releases
published from them; the new repository namespaces its tags `sdk-py-v*`,
because `v0.0.6` meant three different things across the SDKs that were merged.
