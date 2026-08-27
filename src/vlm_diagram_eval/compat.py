"""Third-party compatibility shims.

Importing this module has side effects, and it is imported for those side effects
only -- see ``evaluators/metrics.py``, which does
``from vlm_diagram_eval import compat  # noqa: F401``.

``np.ComplexWarning``
    Removed in NumPy 2.0 (this project pins ``numpy==2.2``), but ``grakel`` still
    references it when building Weisfeiler-Lehman kernels. Without this shim,
    ``WLSimilarityGrakel`` fails on import of grakel's kernel module. Re-adding the
    symbol is the least invasive fix; the alternative is pinning ``numpy<2``, which
    conflicts with the rest of the stack.

    Remove once grakel ships a NumPy 2 compatible release.
"""

import numpy as np

if not hasattr(np, "ComplexWarning"):

    class ComplexWarning(RuntimeWarning):
        """Stand-in for the symbol NumPy 2.0 removed."""

    np.ComplexWarning = ComplexWarning
