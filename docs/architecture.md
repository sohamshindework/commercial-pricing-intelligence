# Architecture

This project deliberately separates the complete local analytical system from the
aggregate-only public portfolio demo. The diagrams below describe the implemented
components; they do not imply a production data platform or a publicly hosted API.

## System architecture

```mermaid
flowchart LR
  subgraph Source[Public source]
    UCI["UCI Online Retail II<br/>CC BY 4.0"]
  end

  subgraph Local[Local analytical mode — not publicly deployed]
    Download["Checksum-verified ingestion"]
    Validate["Validation and cleaning rules"]
    Duck[("Read-only DuckDB<br/>analytical warehouse")]
    Python["Python reporting and modelling"]
    API["Typed FastAPI<br/>local loopback only"]
  end

  subgraph Public[Public portfolio mode — static frontend only]
    Export["Deterministic static export"]
    JSON["Approved aggregate JSON"]
    React["React + TypeScript<br/>five client routes"]
    Host["Static hosting<br/>Vercel-compatible"]
  end

  UCI --> Download --> Validate --> Duck
  Duck --> Python
  Duck --> API
  Python --> API
  Python --> Export --> JSON --> React --> Host
  API -. "local analytical mode" .-> React
```

The public path contains no FastAPI process, DuckDB file, raw transaction data,
customer-level records, invoice identifiers or internal development endpoint. The
frontend chooses either the local API client or the static data client at build time.

## Analytical pipeline

```mermaid
flowchart TD
  Ingest["Ingest 1,067,371 source transactions"] --> Clean["Validate, clean and retain 1,033,062 rows"]
  Clean --> Reconcile["Reconcile £18,981,261.52 net product revenue"]
  Reconcile --> Revenue["Revenue analysis<br/>trend and price/volume/mix bridges"]
  Reconcile --> Customer["Customer analysis<br/>RFM, cohorts and time-based value evaluation"]
  Reconcile --> Product["Product classification<br/>held-out macro-F1 0.873"]
  Reconcile --> Pricing["Pricing analysis<br/>dispersion and descriptive scenarios"]
  Pricing --> Power["Experiment feasibility<br/>1,713 available vs 21,102 required SKUs per arm"]
  Revenue --> Executive["Evidence-linked executive recommendations"]
  Customer --> Executive
  Product --> Executive
  Power --> Executive
```

Customer value uses the historical-value baseline selected on a time-based holdout.
Pricing outputs are scenario ranges, not realised uplift or causal profit estimates.
The proposed experiment is not adequately powered to establish a 5% effect.

## Static demo flow

```mermaid
flowchart LR
  Verified["Verified analytical outputs"] --> Contracts["FastAPI response contracts"]
  Contracts --> Exporter["Deterministic exporter<br/>validation + privacy checks"]
  Exporter --> Snapshot["Aggregate JSON<br/>56 filter selections<br/>4,739 product rows<br/>231 pricing scenarios"]
  Snapshot --> Client["Static data client"]
  Client --> Overview["/"]
  Client --> Revenue["/revenue"]
  Client --> Customers["/customers"]
  Client --> Pricing["/pricing"]
  Client --> Executive["/executive"]
  Filters["Market + product-family filters"] --> Client
  Sliders["Precomputed capture scenarios"] --> Client
```

The snapshot is byte-reproducible and carries an analytical SHA-256 fingerprint.
Public interaction is limited to the exported market/family combinations, product
pages and pricing scenarios. Arbitrary date filtering remains disabled because it
would require publishing finer-grained data than the portfolio demo permits.
