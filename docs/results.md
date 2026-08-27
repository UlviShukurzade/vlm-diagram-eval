# Results

Detail behind the summary in the [README](../README.md). Figures are in
[`figures/`](figures), LaTeX source for every table in [`tables/`](tables).

## Experimental setup

| | |
|---|---|
| Models | GPT-4.1, GPT-o4-mini |
| Prompt tiers | 4 per task: Tier 0 baseline + guardrails, few-shot, self-correction (o4-mini additionally runs Tier 3 at medium and high reasoning effort) |
| Diagram types | flowchart, graph, state diagram (**class diagrams excluded** — thesis §4.5) |
| Difficulty strata | Easy (SCI < 12), Moderate (12–25), Hard (SCI > 25) |
| Corpus | 14,487 scraped → 12,525 filtered → **900 evaluated** (100 per type per tier) |
| Rendering | 2× scale via Mermaid CLI (`mmdc`) |

Each image is transcribed to Mermaid by the model, parsed to a graph through the containerised
Mermaid parser, and compared to the ground-truth `.mmd` parsed by the identical path — so parser
behaviour cancels out and only transcription differences are measured.

## Metrics

**`WLSimilarityGrakel`** — Weisfeiler-Lehman subtree kernel (grakel, `n_iter=3`, normalised) over
node and edge labels. The refinement depth matches thesis §4.3.1, which fixes h = 3. The headline
metric: sensitive to both topology and labelling.

**`DirectedSpectralSimilarity` / `UndirectedSpectralSimilarity`** — distance between Laplacian
spectra. Captures global shape while ignoring node identity, which makes it a useful cross-check
against WL: agreement between them suggests a genuine structural difference rather than a labelling
artefact.

**`DirectedErrorEvaluator`** — interpretable counts rather than a single score: `Count_Missing`,
`Count_Hallucinated`, `Count_Flipped`, `Score_F1`, `Score_Jaccard`. Flipped edges are separated out
because a reversed arrow is a semantic error that aggregate similarity scores tend to hide.

## Prompt tiers

Four tiers per task. The thesis labels them three different ways; the techniques are identical.

| Thesis body | Results tables | Appendix A.2/A.3 | Technique |
|---|---|---|---|
| Tier 0 | `base` | V1 | Baseline, zero-shot |
| Tier 1 | `v1` | V2 | Syntactic / definition guardrails |
| Tier 2 | `v2` | V3 | Few-shot demonstrations |
| Tier 3 | `v3` | V4 | Structured self-correction |

The `v3-med` / `v3-high` columns are not extra tiers — they are Tier 3 run at two reasoning-effort
settings, available only on o4-mini.

## Average WL similarity

Full table: [`tables/Average_WL_similarity_wide.tex`](tables/Average_WL_similarity_wide.tex).
Best prompt tier per model is bolded.

| Diagram | Difficulty | 4.1 base | 4.1 v1 | 4.1 v2 | 4.1 v3 | o4 base | o4 v1 | o4 v2 | o4 v3-med | o4 v3-high |
|---|---|---|---|---|---|---|---|---|---|---|
| Flowchart | Easy | 0.840 | 0.801 | 0.808 | **0.892** | 0.820 | 0.820 | 0.864 | 0.865 | **0.888** |
| Flowchart | Moderate | 0.701 | 0.619 | 0.699 | **0.731** | 0.773 | 0.791 | 0.817 | **0.850** | 0.818 |
| Flowchart | Hard | **0.727** | 0.661 | 0.669 | 0.652 | 0.731 | 0.714 | **0.784** | 0.736 | 0.726 |
| Graph | Easy | 0.860 | 0.804 | 0.763 | **0.885** | 0.902 | **0.924** | 0.908 | 0.906 | 0.919 |
| Graph | Moderate | 0.774 | 0.703 | 0.792 | **0.800** | 0.853 | 0.875 | 0.893 | **0.897** | 0.861 |
| Graph | Hard | 0.701 | 0.606 | 0.705 | **0.763** | 0.768 | 0.760 | 0.769 | **0.795** | 0.765 |
| State | Easy | 0.658 | 0.406 | 0.651 | **0.748** | 0.705 | 0.557 | 0.698 | 0.678 | **0.722** |
| State | Moderate | **0.462** | 0.282 | 0.457 | 0.430 | 0.455 | 0.408 | **0.504** | 0.484 | 0.481 |
| State | Hard | 0.332 | 0.200 | **0.362** | 0.356 | 0.338 | 0.328 | 0.308 | 0.321 | **0.358** |

### Diagram type dominates

State diagrams sit far below flowcharts and graphs at every difficulty and for every model. Hard
state diagrams (0.32–0.36) score roughly half what hard flowcharts do (0.65–0.78). The gap is wider
than the gap between models, and wider than the gap between prompt tiers — the diagram formalism
matters more than either.

The plausible cause is that state diagram semantics are carried by things that are visually implicit:
nested states, and `[*]` initial/final pseudo-states that have no distinct visual form.

### Prompt engineering helps least where it is needed most

The v3 tier wins on Easy rows almost everywhere, but its margin narrows as difficulty rises and
reverses on hard flowcharts, where GPT-4.1's `base` prompt beats it (0.727 vs 0.652). Prompt
elaboration appears to help models that are already close, and not to rescue ones that are lost.

`v1` is consistently the weakest tier for GPT-4.1 — notably worse than `base` — which suggests that
tier's instructions actively interfere.

## Structural drivers of degradation

Thesis §6.1 fits a linear regression over all similarity scores across metrics and settings
(N = 24,300), with heteroscedasticity-robust HC3 standard errors. Predictors: node count, edge
count, decision count, parent count, model, prompt tier, and metric.

Overall model: F = 244.7, p < 0.001, R² = 0.104.

| Predictor | β | p |
|---|---|---|
| Parent count (nesting) | −0.0414 | < 0.001 |
| Edge count | −0.0317 | < 0.001 |
| Node count | +0.0194 | < 0.001 |
| Decision count | +0.0189 | < 0.001 |

Edge count and hierarchical nesting are negative: relational density and structural grouping both
independently reduce reconstruction quality. Node count and decision count are **positive** once
edge density is controlled for — which the thesis reads as evidence that raw element count is not
the difficulty factor. A diagram that grows in nodes without a proportional growth in edges gets
slightly *easier*.

> **Note on an internal inconsistency.** §6.1 states that edge count "emerges as the strongest
> negative structural predictor (β = −0.0317)", but reports parent count at β = −0.0414 — larger in
> magnitude. Unless the claim refers to standardised coefficients, which are not reported, parent
> count is the stronger negative predictor. Worth resolving before this text is reused in a paper.

Distributions and per-difficulty breakdowns:
[`figures/sci_components_heatmap.png`](figures/sci_components_heatmap.png),
[`figures/sci_difficulty_by_component.png`](figures/sci_difficulty_by_component.png),
[`figures/sci_relative_contribution.png`](figures/sci_relative_contribution.png).

## Structural Complexity Index

Thesis §4.4.2 defines, for a directed graph G = (V, E) with N = |V|, E = |E|, D decision nodes
(out-degree > 1) and P distinct parent identifiers:

```
SCI(G) = 0.5·N + 1.0·E + 1.0·(E/N) + 3.0·D + 3.0·P
```

Difficulty tiers: Easy < 12, Moderate 12–25, Hard > 25.

The reference implementation (`calculate_sci_components`) lives in the thesis working tree's
`filter_eligible.ipynb` and is **not yet ported into this repository** — see the README's
limitations note.

## Component quantification and the modality gap

Thesis sections 5.2 and 5.3. Models are asked only to *count* structure — nodes, edges, branches,
containers — first from an image, then from Mermaid source. The difference isolates what vision
costs:

    delta_MAE = MAE_image - MAE_mermaid        positive: image-based inference is worse

| Component | GPT-4.1 image | GPT-4.1 mermaid | Δ | o4-mini image | o4-mini mermaid | Δ |
|---|---|---|---|---|---|---|
| Nodes | 1.898 | 1.489 | **+0.409** | 1.559 | 1.503 | +0.056 |
| Edges | 1.113 | 0.634 | **+0.479** | 0.712 | 0.594 | +0.118 |
| Decisions | 0.498 | 0.594 | −0.096 | 0.233 | 0.212 | +0.021 |
| Parents | 0.299 | 0.204 | +0.095 | 0.247 | 0.284 | −0.037 |

Nodes and edges carry the gap; decisions and containers are near zero or negative. GPT-4.1's gap is
roughly seven times o4-mini's on nodes — the stronger text model loses more when forced through
vision.

Reproduce with:

```bash
python scripts/modality_gap.py --data-dir <inference results>
```

### A convention worth knowing

Unparseable model responses are scored as a prediction of **0**, so the error becomes the full
ground-truth count, and the row stays in the denominator. Parse failure is treated as maximally
wrong rather than dropped.

The thesis does not state this, but it is what produced the published numbers: it is the only
convention that reproduces Table 5.13, and dropping failed rows instead shifts MAE by up to 0.24.
`tests/test_quantification.py` pins it so it cannot drift.

## Significance testing

Regression output is in [`tables/anova_model_summary.txt`](tables/anova_model_summary.txt); the
notebook that produces it is [`../notebooks/anova.ipynb`](../notebooks/anova.ipynb). Note the thesis
reports OLS with HC3 robust errors — despite the filename, it does not present an ANOVA or a
mixed-effects model.

## Reproducing

```bash
make setup
make parser
uv run jupyter lab notebooks/evaluation_pipeline.ipynb
```

The notebooks expect the full dataset, not the committed sample — see
[`../scripts/download_data.py`](../scripts/download_data.py).
[`../notebooks/worked_example.ipynb`](../notebooks/worked_example.ipynb) is a single worked example and is
the fastest way to see the pipeline end to end.
