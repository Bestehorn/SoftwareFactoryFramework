# Prompt — issue #46: GitHub `call`: non-JSON request bodies, uploads and the 307 re-send

Tier: M — one design choice (body input, request media type, host, the `307` re-send) across `call`, the record layer and the transport.

Kind: FEATURE.

## Goal

`call <operation-id>` (#28) sends a body only as one JSON object to `https://api.github.com`. Give it the three documented request forms it lacks: an `application/octet-stream` body to `https://uploads.github.com` (`repos/upload-release-asset`, left pending by #27 DL-002), a `text/plain` body (`markdown/render-raw`, left pending by #33 DL-001), and the same-origin `307` re-send of `PATCH`/`DELETE` (`repos/update`, `repos/delete`); map the two pending records.

## Scope

The issue's ACs and UBs (issue body). Out of scope: other request forms; the GitLab twin; the real-forge run (#10). The issue's open questions are design questions, answered in `design.md`. The two records live in modules #27 and #33 change: this branch rebases onto both before its implementation.
