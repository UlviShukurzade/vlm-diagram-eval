# Results

Detail behind the summary in the [README](../README.md). Figures are in
[`figures/`](figures), LaTeX source for every table in [`tables/`](tables).

## Experimental setup

| | |
|---|---|
| Models | GPT-4.1, GPT-o4-mini |
| Prompt tiers | `base`, `v1`, `v2`, `v3` (plus `v3-medium` / `v3-high` reasoning effort for o4-mini) |
| Diagram types | flowchart, graph, state diagram, class diagram |
| Difficulty strata | Easy, Moderate, Hard |
| Corpus | ~14,500 Mermaid sources with rendered images |

Each image is transcribed to Mermaid by the model, parsed to a graph through the containerised
Mermaid parser, and compared to the ground-truth `.mmd` parsed by the identical path — so parser
behaviour cancels out and only transcription differences are measured.

## Metrics

**`WLSimilarityGrakel`** — Weisfeiler-Lehman subtree kernel (grakel, `n_iter=3`, normalised) over
node and edge labels. The headline metric: sensitive to both topology and labelling.

**`DirectedSpectralSimilarity` / `UndirectedSpectralSimilarity`** — distance between Laplacian
spectra. Captures global shape while ignoring node identity, which makes it a useful cross-check
against WL: agreement between them suggests a genuine structural difference rather than a labelling
artefact.

**`DirectedErrorEvaluator`** — interpretable counts rather than a single score: `Count_Missing`,
`Count_Hallucinated`, `Count_Flipped`, `Score_F1`, `Score_Jaccard`. Flipped edges are separated out
because a reversed arrow is a semantic error that aggregate similarity scores tend to hide.

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

## Structural complexity

Spearman correlation between WL similarity and each component of the structural complexity index
(GPT-4.1, v3): [`tables/wl_gpt4_v3_correlation.tex`](tables/wl_gpt4_v3_correlation.tex).

| Component | Spearman ρ |
|---|---|
| `sci_edges` | −0.369 |
| `sci_nodes` | −0.324 |
| `sci_nesting` | −0.231 |
| `sci_decisions` | −0.223 |
| `sci_connectivity` | −0.169 |

All five are negative, so every axis of complexity degrades transcription. Edge count leads node
count, which is the more interesting half: models track *entities* more reliably than the
*relationships* between them — consistent with `DirectedErrorEvaluator` isolating flipped and
hallucinated edges as the dominant error modes.

Distributions and per-difficulty breakdowns:
[`figures/sci_components_heatmap.png`](figures/sci_components_heatmap.png),
[`figures/sci_difficulty_by_component.png`](figures/sci_difficulty_by_component.png),
[`figures/sci_relative_contribution.png`](figures/sci_relative_contribution.png).

## Significance testing

Mixed-effects model output is in [`tables/anova_model_summary.txt`](tables/anova_model_summary.txt);
the notebook that produces it is [`../notebooks/anova.ipynb`](../notebooks/anova.ipynb).

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
