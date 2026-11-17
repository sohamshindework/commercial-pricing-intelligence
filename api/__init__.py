"""FastAPI backend for Commercial Analytics & Pricing Strategy.

Read-only, typed analytical endpoints. Interactive aggregates come from
`commercial_intelligence.reporting.queries` (parameterized warehouse queries);
fixed-period analytics (CLV evaluation, classification, revenue decomposition)
come from `commercial_intelligence.reporting.exports`. No business logic lives
here — this layer only validates input and shapes typed responses.
"""
