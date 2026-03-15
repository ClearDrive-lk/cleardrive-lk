# Subresource Integrity (SRI) Guide

## What is SRI?

Subresource Integrity (SRI) lets browsers verify that files fetched from a CDN
(or any external source) have not been modified. If the hash does not match,
those resources are blocked.

## Why use SRI?

- Protect against CDN compromise or tampering
- Ensure external libraries are exactly what you expect
- Improve security posture and compliance readiness

## How we use SRI in this project

- Hashes are tracked in `apps/web/sri-resources.json`
- The helper `apps/web/lib/sri.ts` maps URLs to integrity values
- Dynamic scripts (Google Identity and Google Analytics) use SRI when a hash is configured

## Generate hashes

Run the generator and copy SHA-384 hashes into `apps/web/sri-resources.json`:

```bash
node apps/web/scripts/generate-sri.js "https://accounts.google.com/gsi/client" \
  "https://www.googletagmanager.com/gtag/js?id=YOUR_GA_ID"
```

## Add SRI to scripts

Example:

```html
<script
  src="https://cdn.example.com/library.js"
  integrity="sha384-..."
  crossorigin="anonymous"
></script>
```

## Test SRI

Manual test:

1. Open the browser console
2. Look for integrity errors or blocked resources

Automated test:

```bash
npm --prefix apps/web run test-sri
```

## Common issues

- Missing `crossorigin="anonymous"` will cause SRI checks to fail
- Hash mismatches mean the file changed and you must regenerate hashes
- Some third-party scripts change frequently; keep hashes up to date

## Security headers

We add:

```
Content-Security-Policy: require-sri-for script style;
```
