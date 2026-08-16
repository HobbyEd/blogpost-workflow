# Dit project

Blogpost-workflow voor edwinvandillen.nl. Control plane in Python
(`scripts/orchestrator/`), execution plane via `scripts/worker.py`.
Schrijfstijl staat alleen in `reference/huisstijl.md`. Deploy alleen in
`reference/deploy.md`.

## Kennisgraaf (eerst dit)

Er staat een kennisgraaf in `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`).

Bij vragen over architectuur, afhankelijkheden, "waar zit X" of "wat hangt
hiervan af": eerst `graphify query "…"`, niet de boom doorlezen.

- Bestaat `graphify-out/graph.json` niet: zeg dat, en bouw hem met `/graphify .`.
- Na substantiële codewijzigingen: `/graphify --update`.
- De graaf zelf staat niet in git (`graphify-out/` is genegeerd). Deze wijzer wel.
