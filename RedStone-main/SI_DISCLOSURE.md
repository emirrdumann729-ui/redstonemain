# Use of Super Intelligence (SI) tools

NASA Space Apps 2026 asks teams to state clearly where and how SI tools were used.

**Tool:** Claude (Anthropic), used as an interactive coding assistant (Claude Code), on 14–15 November 2026.

**What it was used for**

| Area | SI involvement |
|---|---|
| Planning | The roadmap (`ROADMAP.md`) and architecture were drafted with SI, starting from the challenge statement's objectives and "potential considerations" (blink viewer, per-detector coadds, spectra, difference/sum images, Gaia/WISE overlays, URL parameters). The team reviewed and approved each phase before it was built. |
| Source code: `backend/`, `frontend/`, `scripts/`, `spikes/`, `tests/`, `Dockerfile` | Generated with SI assistance under the team's direction. Each source file carries a header line saying so. |
| Documentation: `README.md`, `ROADMAP.md`, `docs/` | Drafted with SI assistance. |
| Data-access research | SI summarised the IRSA/MAST/Gaia documentation and the challenge resources. It ran the measurements in `spikes/`, which compare download methods and validate the WCS and Gaia queries. Results are in `docs/spike_report.md`. |
| Images | None generated. `docs/screenshots/` contains screen captures of the running application showing real SPHEREx, Gaia and CatWISE data. |
| Science data | None generated or altered. Every image, catalogue value and spectrum shown comes from the public archives listed in the README, at the moment the user asks. |

**Human role**

The team chose the challenge, provided the data resources and steered every phase. The team reviewed and
accepted each step and tested the tool in the browser. Correctness was checked with the automated
test suite (`pytest`) and by comparing the results with known facts about the challenge targets:
Barnard's Star's proper motion matches Gaia DR3 to 0.001″, and WISE 0855 appears in CatWISE with its known
8″/yr motion.
