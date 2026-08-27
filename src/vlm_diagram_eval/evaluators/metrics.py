# Standard library imports
from typing import Any

# Third-party library imports
import networkx as nx
import numpy as np
import scipy
from grakel import graph_from_networkx
from grakel.kernels import WeisfeilerLehman
from scipy.spatial.distance import euclidean

# Patch numpy for compatibility if needed
from vlm_diagram_eval import compat  # noqa: F401

# Local imports
from vlm_diagram_eval.parsing.graph import get_graph_from_json


def to_networkx_graph(inp: Any, directed: bool = True) -> nx.Graph | nx.DiGraph:
    """Standardize input to a NetworkX graph.

    Args:
        inp: Either a NetworkX graph object or a Mermaid string to be parsed.
        directed: If True, ensures the output is a directed graph.

    Returns:
        A NetworkX Graph or DiGraph object.

    Raises:
        ValueError: If input cannot be converted to a NetworkX graph.
    """
    if isinstance(inp, (nx.Graph, nx.DiGraph)):
        if directed and not inp.is_directed():
            return inp.to_directed()
        return inp

    # Try to parse as Mermaid string
    graph = get_graph_from_json(inp)
    if directed and not graph.is_directed():
        return graph.to_directed()
    return graph


class DirectedSpectralSimilarity:
    """Computes the directed spectral similarity between two graphs.

    This evaluator compares a generated graph to a ground truth graph using spectral properties,
    supporting both Mermaid strings and NetworkX graph objects as input.
    """

    def name(self):
        return "DirectedSpectralSimilarity"

    def evaluate(self, g_truth, g_gen) -> float:
        """Evaluate the directed spectral similarity between two graphs.

        Args:
            g_truth: The ground truth graph, either as a Mermaid string or a NetworkX graph.
            g_gen: The generated graph, either as a Mermaid string or a NetworkX graph.

        Returns:
            float: A similarity score between 0 and 1, where 1 indicates identical graphs.
        """
        # Standardize inputs / Validate
        try:
            G_gt = to_networkx_graph(g_truth, directed=True)
        except Exception:
            return None

        try:
            G_gen = to_networkx_graph(g_gen, directed=True)
        except Exception:
            return 0.0

        # 1. Explicitly calculate the Directed Laplacian Matrix
        # walk_type='random' is standard for PageRank-based spectral gaps
        L_gt = nx.directed_laplacian_matrix(G_gt, walk_type="pagerank", alpha=0.9)
        L_gen = nx.directed_laplacian_matrix(G_gen, walk_type="pagerank", alpha=0.9)

        # 2. Get Eigenvalues manually
        evals_gt = scipy.linalg.eigvalsh(L_gt)
        evals_pred = scipy.linalg.eigvalsh(L_gen)

        # 2. SORTING (Crucial)
        # We must align the frequencies to compare them
        evals_gt = np.sort(evals_gt)[::-1]
        evals_pred = np.sort(evals_pred)[::-1]

        # 3. PADDING (Crucial)
        # Handle cases where AI missed or added nodes
        max_len = max(len(evals_gt), len(evals_pred))

        if len(evals_gt) < max_len:
            evals_gt = np.pad(evals_gt, (0, max_len - len(evals_gt)))
        if len(evals_pred) < max_len:
            evals_pred = np.pad(evals_pred, (0, max_len - len(evals_pred)))

        # 4. Compute Euclidean Distance
        dist = euclidean(evals_gt, evals_pred)

        # 5. Normalize distance by the number of nodes
        # This makes a '1.0' distance mean the same thing for 5 nodes vs 50 nodes
        norm_dist = dist / np.sqrt(max_len)

        # 6. Convert Normalized Distance to Similarity
        # We use a standard sigma=1.0 now because the distance is normalized
        similarity = np.exp(-(norm_dist**2))
        return similarity


class UndirectedSpectralSimilarity:
    """Computes the spectral similarity between two undirected graphs.

    This class compares the normalized Laplacian spectra of a generated graph and a ground truth graph,
    supporting both Mermaid strings and NetworkX graph objects as input.
    """

    def name(self):
        return "UndirectedSpectralSimilarity"

    def evaluate(self, g_truth, g_gen) -> float:
        """Evaluate the undirected spectral similarity between two graphs.

        Args:
            g_truth: The ground truth graph, either as a Mermaid string or a NetworkX graph.
            g_gen: The generated graph, either as a Mermaid string or a NetworkX graph.

        Returns:
            float: A similarity score between 0 and 1, where 1 indicates identical graphs.
        """
        # Standardize inputs
        G_gt = to_networkx_graph(g_truth, directed=False).to_undirected()
        G_gen = to_networkx_graph(g_gen, directed=False).to_undirected()

        evals_gt = nx.normalized_laplacian_spectrum(G_gt)
        evals_pred = nx.normalized_laplacian_spectrum(G_gen)

        # 2. SORTING (Crucial)
        # We must align the frequencies to compare them
        evals_gt = np.sort(evals_gt)[::-1]
        evals_pred = np.sort(evals_pred)[::-1]

        # 3. PADDING (Crucial)
        # Handle cases where AI missed or added nodes
        max_len = max(len(evals_gt), len(evals_pred))

        if len(evals_gt) < max_len:
            evals_gt = np.pad(evals_gt, (0, max_len - len(evals_gt)))
        if len(evals_pred) < max_len:
            evals_pred = np.pad(evals_pred, (0, max_len - len(evals_pred)))

        # 4. Euclidean Distance
        dist = euclidean(evals_gt, evals_pred)

        # 5. Normalize distance by the number of nodes
        # This makes a '1.0' distance mean the same thing for 5 nodes vs 50 nodes
        norm_dist = dist / np.sqrt(max_len)

        # 6. Convert Normalized Distance to Similarity
        # We use a standard sigma=1.0 now because the distance is normalized
        similarity = np.exp(-(norm_dist**2))

        return similarity


class DirectedErrorEvaluator:
    """Evaluates errors in directed graphs, such as missing, extra, and flipped edges.

    This class provides methods to compare a predicted directed graph against a ground truth,
    reporting metrics like F1 score and counts of various edge errors.
    """

    def name(self):
        return "DirectedErrorEvaluator"

    def __init__(self, label_attr="label"):
        """Initialize the DirectedErrorEvaluator.

        Args:
            label_attr (str): The edge attribute name used for labeling. Defaults to "label".
        """
        self.label_attr = label_attr

    def evaluate(self, g_truth, g_gen) -> dict[str, Any]:
        """Evaluate directed graph errors including missing, extra, and flipped edges.

        Args:
            g_truth: The ground truth graph, either as a Mermaid string or a NetworkX graph.
            g_gen: The generated graph, either as a Mermaid string or a NetworkX graph.

        Returns:
            dict: Dictionary containing F1 score, counts of correct/missing/flipped edges, etc.
        """
        # Standardize inputs
        G_truth = to_networkx_graph(g_truth, directed=True)
        G_gen = to_networkx_graph(g_gen, directed=True)

        # 1. Map internal IDs to Text Labels
        # We create a dictionary {node_id: "Label"}
        # This handles cases where AI generates "id_1" for "Server"

        def get_mapping(G):
            """Create a mapping from node IDs to their label attribute as strings.

            Args:
                G: A NetworkX graph.

            Returns:
                dict: Mapping from node ID to label string.
            """
            return {n: str(G.nodes[n].get(self.label_attr, "UNKNOWN")).strip() for n in G.nodes()}

        # Relabel both graphs to use their Text as the ID
        H_truth = nx.relabel_nodes(G_truth, get_mapping(G_truth))
        H_gen = nx.relabel_nodes(G_gen, get_mapping(G_gen))

        # 2. Extract Directed Edges as Sets
        gt_edges = set(H_truth.edges())
        gen_edges = set(H_gen.edges())

        # 3. Calculate Basic Metrics
        intersection = gt_edges.intersection(gen_edges)  # Perfect matches
        missing = gt_edges - gen_edges  # In GT but not Gen
        extras = gen_edges - gt_edges  # In Gen but not GT
        # 4. DETECT FLIPPED ARROWS (The specific penalty you want)
        # We look at the "extras" (wrong edges) and see if the reverse exists in GT
        flipped = set()
        pure_hallucinations = set()

        for u, v in extras:
            if (v, u) in gt_edges:
                flipped.add((u, v))  # It's a direction error
            else:
                pure_hallucinations.add((u, v))  # It's a completely made-up edge

        # 5. Compile Scores
        # You can weigh 'flipped' edges heavily in your final score if you want

        tp = len(intersection)
        fp = len(extras)
        fn = len(missing)

        # Jaccard = Intersection / Union
        union_count = len(gt_edges.union(gen_edges))
        jaccard = len(intersection) / union_count if union_count > 0 else 0.0

        # Standard F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "Score_F1": f1,
            "Count_Correct": len(intersection),
            "Count_Missing": len(missing),
            "Count_Flipped": len(flipped),  # <--- YOUR KEY METRIC
            "Score_Jaccard": jaccard,
            "Count_Hallucinated": len(pure_hallucinations),
            "Details_Flipped": list(flipped),
        }


class WLSimilarityGrakel:
    def name(self):
        return "WLSimilarity"

    def __init__(
        self,
        iterations: int = 3,
        node_label_tag: str = "label",
        edge_label_tag: str = "label",
    ):
        """Direct implementation of WL Kernel using Grakel's native NetworkX utility.

        Args:
            iterations: Number of refinement steps (h).
            node_label_tag: The node attribute tag used for initial coloring (usually 'label').
            edge_label_tag: The edge attribute tag used for initial coloring (usually 'label').
        """
        self.iterations = iterations
        self.node_label_tag = node_label_tag
        self.edge_label_tag = edge_label_tag
        # Initialize the kernel with requested iterations and normalization
        self.gk = WeisfeilerLehman(n_iter=self.iterations, normalize=True)

    def evaluate(self, gt: Any, gen: Any) -> float:
        """Computes the structural similarity between two graphs using Grakel WL kernel.

        Accepts either raw Mermaid strings or NetworkX Graph objects.

        Args:
            gt: Ground truth graph, either as a Mermaid string or a NetworkX graph.
            gen: Generated graph, either as a Mermaid string or a NetworkX graph.

        Returns:
            float: Similarity score between 0 and 1, or None if an error occurs.
        """
        # 1. Standardize inputs with Strict Validation
        try:
            G_gt = to_networkx_graph(gt, directed=True)
        except Exception:
            # GT Invalid -> Cannot evaluate
            return None

        try:
            G_gen = to_networkx_graph(gen, directed=True)
        except Exception:
            # GT Valid but Gen Invalid -> Model Failure -> Score 0.0
            return 0.0

        # 3. Convert standardized NX objects to Grakel format
        # Note: graph_from_networkx expects an iterable of graphs
        g_gt_grakel = list(
            graph_from_networkx(
                [G_gt],
                node_labels_tag=self.node_label_tag,
                edge_labels_tag=self.edge_label_tag,
            )
        )

        g_gen_grakel = list(
            graph_from_networkx(
                [G_gen],
                node_labels_tag=self.node_label_tag,
                edge_labels_tag=self.edge_label_tag,
            )
        )

        # Combine the lists to create a set of graphs for comparison
        # fit_transform on a list of 2 graphs returns a 2x2 similarity matrix
        graphs = g_gt_grakel + g_gen_grakel

        # 4. Compute Kernel similarity
        K = self.gk.fit_transform(graphs)

        similarity = float(K[0, 1])  # Similarity between gt (index 0) and gen (index 1)

        return round(similarity, 4)


# Usage Example:
# evaluator = WLSimilarityGrakel(iterations=3)
# result = evaluator.evaluate(gt_code, gen_code, parser_service=parser_service)
