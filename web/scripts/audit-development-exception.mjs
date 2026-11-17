import { spawnSync } from "node:child_process";

const ACCEPTED_ADVISORY = "https://github.com/advisories/GHSA-fc5q-39xc-vjpf";
const result = spawnSync("npm", ["audit", "--json", "--audit-level=high"], {
  encoding: "utf8",
  shell: false,
});

// Keep the complete audit visible in local output and CI logs. The exception below
// changes only the final gate decision; it does not hide or rewrite npm's findings.
process.stdout.write(result.stdout);
process.stderr.write(result.stderr);

let report;
try {
  report = JSON.parse(result.stdout);
} catch {
  console.error("Unable to parse the full npm audit report.");
  process.exit(result.status || 1);
}

const vulnerabilities = report.vulnerabilities ?? {};
const names = Object.keys(vulnerabilities);
const advisoryUrls = new Set();
let invalidReference = false;

function reachesAcceptedAdvisory(name, visiting = new Set()) {
  if (visiting.has(name)) return false;
  const entry = vulnerabilities[name];
  if (!entry) {
    invalidReference = true;
    return false;
  }

  const next = new Set(visiting);
  next.add(name);
  let accepted = false;
  for (const cause of entry.via ?? []) {
    if (typeof cause === "string") {
      const branchAccepted = reachesAcceptedAdvisory(cause, next);
      accepted = branchAccepted || accepted;
    } else {
      advisoryUrls.add(cause.url);
      accepted = cause.url === ACCEPTED_ADVISORY || accepted;
    }
  }
  return accepted;
}

const unaccepted = names.filter((name) => !reachesAcceptedAdvisory(name));
const counts = report.metadata?.vulnerabilities ?? {};
const noCriticalFindings = counts.critical === 0;
const onlyAcceptedAdvisory =
  advisoryUrls.size === 1 && advisoryUrls.has(ACCEPTED_ADVISORY);

if (
  result.status === 1 &&
  names.length > 0 &&
  unaccepted.length === 0 &&
  !invalidReference &&
  noCriticalFindings &&
  onlyAcceptedAdvisory
) {
  console.log(
    `Accepted temporary development-tooling exception: ${ACCEPTED_ADVISORY} ` +
      `(${counts.high} reported dependency paths).`,
  );
  process.exit(0);
}

console.error(
  `Full npm audit contains findings outside the accepted exception. ` +
    `Unaccepted packages: ${unaccepted.join(", ") || "none"}.`,
);
process.exit(result.status || 1);
