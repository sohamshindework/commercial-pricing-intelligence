"""Reporting layer: load validated exports for the web app and memo.

No business logic here — only reads the Parquet/CSV produced by the milestone
runners, so the app and the memo share the pipeline's single source of truth.
"""
