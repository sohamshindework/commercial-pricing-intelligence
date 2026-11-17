# Publication readiness assessment

## Current status

Soham confirmed ownership and publication authority on 2026-11-17, selected the MIT
licence for project-authored material and authorised the standalone `LICENSE` file.
The UCI dataset and third-party dependencies retain their own licences.

B6 publication and deployment completed on 2026-11-17:

- GitHub: <https://github.com/sohamshindework/commercial-pricing-intelligence>
- Production: <https://commercial-pricing-intelligence.vercel.app/>
- Vercel project root: `web/` (Vite static demo only)

## Verification completed on 2026-11-17

The interrupted B5.1 tree was verified without reverting the React Router 7 or
Tailwind CSS 4 upgrades:

| Gate | Result |
|---|---|
| Complete Python suite | 131 passed; one upstream Starlette/httpx deprecation warning |
| Explicit FastAPI suite | 30 passed |
| Ruff / `pip check` | Passed / passed |
| Python dependency audit | No known vulnerabilities (local project package is not on PyPI) |
| TypeScript / ESLint | Passed / passed |
| Vitest | 16 passed across 7 files |
| Local/API build | Passed |
| Static-demo build | Passed |
| Production npm audit | 0 vulnerabilities |
| Full npm audit | 11 high-severity paths to one unresolved `picomatch` advisory |
| Static artifact inspection | 17 files; 7,194,129 bytes; no forbidden data or backend reference |
| Static snapshot | 6,491,681 bytes; two fresh exports were byte-identical |
| Analytical fingerprint | `30b614584bffe85269041367fddb38c7e24441125577cc65a8425961765021a0` |
| Secret scanning | Gitleaks history and working-tree scans found no leaks |
| Browser regression | Five direct routes and client navigation passed at 1440 px and 390 px |

Browser checks also covered market and product-family filtering, product pagination,
all three revenue-decomposition lenses, precomputed pricing sliders, mobile
navigation, the keyboard skip link, disabled date filters, attribution visibility,
console output and horizontal overflow. No console warnings or errors were observed.
The build-time artifact scan rejects external backend fetches and internal endpoint
references; the rendered static build contained none.

The pre-remediation lockfile from the repository's existing `HEAD` was audited
separately for an exact comparison:

| Audit scope | Before B5.1 | Current tree |
|---|---:|---:|
| Full dependency tree | 28 total: 2 low, 8 moderate, 16 high, 2 critical | 11 high paths to one advisory |
| Production dependencies | 3 high | 0 |

The removed findings included React Router, PostCSS, Vitest/tinypool, esbuild,
minimatch, ESLint and the Tailwind 3 watcher/glob chain. No forced audit fix or
security-gate suppression was used.

Current screenshots are stored under `assets/screenshots/`, including all five routes
and a 390 px mobile overview. The system, analytical pipeline and static-demo flow are
documented in `docs/architecture.md`.

## Third-party and data review

- **Dataset:** UCI Online Retail II, Chen (2019), DOI `10.24432/C5CG6D`, CC BY 4.0.
  The README contains the dataset title, author, year, repository, DOI and licence.
  The static application also exposes dataset, DOI and CC BY 4.0 links.
- **Raw data:** the XLSX/ZIP files, landing Parquet, DuckDB warehouse and detailed
  analytical exports are ignored and excluded from the deployable artifact.
- **Frontend assets:** the static build uses no externally hosted fonts, images,
  analytics or tracking scripts. Charts and interface elements are generated from
  project code and aggregate JSON.
- **Dependencies:** npm and Python packages are installed dependencies rather than
  copied third-party source. Their permissive package licences and notices remain with
  those packages. A final release should preserve any dependency notice files required
  by the selected distribution method.
- **Project screenshots/workbooks:** they are not part of the Vite deployable artifact.
  Soham confirmed authority to publish the repository copies.
No committed source header or deployable asset was found that asserts a conflicting
copyright or copyleft licence. This is a repository review, not legal advice.

The direct npm dependencies declare MIT or Apache-2.0 licences. The principal Python
dependencies declare MIT, BSD-3-Clause or Apache-2.0 licences, with some packages
publishing their full licence text rather than a normalized metadata expression. This
inventory does not replace preserving package notices where distribution requires it.

## Source-code licence

Project-authored source and documentation are released under the authorised MIT
licence, `Copyright (c) 2026 Soham Shinde`.

The UCI dataset remains CC BY 4.0 regardless of the source-code licence. A project
licence must not imply relicensing of the dataset.

## Security exception awaiting upstream remediation

`picomatch` CVE-2026-112366 / GHSA-fc5q-39xc-vjpf affects the latest published
version, 4.0.7; the GitHub advisory currently lists no known patched version and npm
still reports 4.0.7 as latest. The full audit reports 11 high-severity dependency-path
findings through Vite, Vitest, `tinyglobby`, `fdir` and TypeScript ESLint. These are
multiple paths to the same underlying advisory, not 11 distinct vulnerabilities. The
copies are development-only transitive dependencies used for trusted project file
globs. They are absent from `npm audit --omit=dev`, absent from the browser bundle and
receive no user-controlled or network-provided glob input in this repository.
Exploitation would require a crafted repeated-extglob pattern such as the advisory's
single-branch cases to reach `picomatch` parsing and block the Node event loop.

Current advisory and package records:

- <https://github.com/advisories/GHSA-fc5q-39xc-vjpf>
- <https://www.npmjs.com/package/picomatch?activeTab=versions>

Until a patched upstream release exists, a documented, time-bounded risk acceptance is
reasonable for a static portfolio build if all of these controls remain true:

1. Development and preview servers bind to loopback only.
2. CI builds only reviewed repository content and uses the exact lockfile.
3. Untrusted pull requests do not receive secrets or privileged runners.
4. The production artifact is rescanned and contains no Node development dependencies.
5. Dependency alerts are monitored and the lockfile is updated promptly when a patched
   `picomatch` release becomes available.

The full npm audit remains intentionally visible and will continue to surface the
finding. Soham explicitly accepted this temporary development-tooling risk on
2026-11-17 under the controls above. CI prints the complete audit, then permits only
dependency paths that resolve exclusively to this exact advisory. Any new advisory or
critical finding fails the gate.

## Publication checklist

- [x] Soham confirms ownership and authority to publish all project-authored material.
- [x] Soham selects the public source-code licence.
- [x] Add the corresponding standalone licence file and align package metadata.
- [x] Soham accepts the documented temporary `picomatch` development-tooling risk.
- [x] Re-run Python, API, Ruff, TypeScript, ESLint, Vitest and both production builds.
- [x] Re-run Python/npm audits, Gitleaks and the deployable-artifact privacy scan.
- [x] Confirm the analytical fingerprint and static-export reproducibility.
- [x] Confirm the prospective repository contains no raw data, warehouse, secret-bearing
      environment files, secrets,
      private customer information or unrelated material.
- [x] Verify all five routes, direct refreshes, links and 390 px mobile layout locally.
- [x] Repeat the route and mobile verification on the target host.
- [x] Retain UCI citation, DOI and CC BY 4.0 attribution in the README and application.

## External release verification

- The public repository was created exclusively as
  `sohamshindework/commercial-pricing-intelligence` and published from Soham's verified
  GitHub session. Release commits use Soham's GitHub-provided noreply identity.
- GitHub Actions passed the Python, frontend, audit, artifact-hygiene and secret-scan
  jobs for the published release.
- The Vercel GitHub App is restricted to this repository. The project deploys only the
  `web/` root through the Vite configuration in `web/vercel.json`; no backend service,
  warehouse or raw/private analytical material is deployed.
- Production verification covered all five direct routes and client navigation,
  market filtering, KPI reconciliation, pricing-scenario recalculation, 390 px mobile
  navigation, attribution visibility, horizontal overflow and browser console output.
  No console warnings or errors were observed.
