"""
Diagram Analysis Utilities

This module provides utility functions for analyzing Mermaid diagrams using NetworkX graphs.
All functions are designed to be imported and used in other modules.

Functions:
- Dataset loading utilities
- Graph analysis utilities
- Statistics calculation utilities
- Visualization utilities
- Export utilities
"""

import json
from collections import defaultdict
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datasets import load_from_disk
from tqdm import tqdm

from vlm_diagram_eval.parsing.graph import get_graph_from_json

# =============================================================================
# DATASET LOADING UTILITIES
# =============================================================================


def load_dataset(dataset_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load dataset from disk and return train/val DataFrames.

    Args:
        dataset_path (str): Path to the dataset directory

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Train and validation DataFrames
    """
    ds = load_from_disk(dataset_path)
    train_df = ds["train"].to_pandas()
    val_df = ds["val"].to_pandas()
    return train_df, val_df


def filter_supported_diagrams(df: pd.DataFrame, supported_types: list[str] = None) -> pd.DataFrame:
    """
    Filter dataset to only include supported diagram types.

    Args:
        df (pd.DataFrame): Input DataFrame
        supported_types (List[str]): List of supported diagram types

    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if supported_types is None:
        supported_types = ["flowchart", "graph", "stateDiagram"]

    # Filter by diagram type if available
    if "diagram_type" in df.columns:
        return df[df["diagram_type"].isin(supported_types)]
    else:
        # Try to identify from the code content
        def identify_diagram_type(code):
            if isinstance(code, str):
                code_lower = code.lower().strip()
                for diagram_type in supported_types:
                    if code_lower.startswith(diagram_type):
                        return diagram_type
            return "unknown"

        df = df.copy()
        df["inferred_type"] = df["code"].apply(identify_diagram_type)
        return df[df["inferred_type"].isin(supported_types)]


# =============================================================================
# GRAPH ANALYSIS UTILITIES
# =============================================================================


def parse_mermaid_to_graph(mermaid_code: str):
    """
    Parse Mermaid code to NetworkX graph.

    Args:
        mermaid_code (str): Mermaid diagram code

    Returns:
        NetworkX graph or None if parsing fails
    """
    if get_graph_from_json is None:
        raise ImportError("parser_service not available")

    try:
        return get_graph_from_json(mermaid_code)
    except Exception as e:
        print(f"Error parsing Mermaid code: {e}")
        return None


def calculate_basic_graph_stats(G) -> dict[str, Any]:
    """
    Calculate basic graph statistics.

    Args:
        G: NetworkX graph

    Returns:
        Dict containing basic statistics
    """
    if G is None or G.number_of_nodes() == 0:
        return {"node_count": 0, "total_edge_count": 0, "real_edge_count": 0, "subgraph_edge_count": 0}

    stats = {}
    stats["node_count"] = G.number_of_nodes()
    stats["total_edge_count"] = G.number_of_edges()

    # Separate real edges from subgraph edges
    real_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("label") != "subgraph"]
    subgraph_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("label") == "subgraph"]

    stats["real_edge_count"] = len(real_edges)
    stats["subgraph_edge_count"] = len(subgraph_edges)

    return stats


def calculate_subgraph_stats(G) -> dict[str, Any]:
    """
    Calculate subgraph-related statistics.

    Args:
        G: NetworkX graph

    Returns:
        Dict containing subgraph statistics
    """
    if G is None:
        return {
            "subgraph_count": 0,
            "nodes_per_subgraph": {},
            "subgraph_sizes": [],
            "max_subgraph_size": 0,
            "avg_subgraph_size": 0,
        }

    subgraph_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("label") == "subgraph"]

    # Count unique subgraphs
    subgraphs = set(v for u, v, d in subgraph_edges)

    # Group nodes by subgraph
    nodes_per_subgraph = defaultdict(list)
    for u, v, d in subgraph_edges:
        nodes_per_subgraph[v].append(u)

    subgraph_sizes = [len(nodes) for nodes in nodes_per_subgraph.values()]

    return {
        "subgraph_count": len(subgraphs),
        "nodes_per_subgraph": dict(nodes_per_subgraph),
        "subgraph_sizes": subgraph_sizes,
        "max_subgraph_size": max(subgraph_sizes) if subgraph_sizes else 0,
        "avg_subgraph_size": np.mean(subgraph_sizes) if subgraph_sizes else 0,
    }


def calculate_node_degree_stats(G) -> dict[str, Any]:
    """
    Calculate node degree statistics.

    Args:
        G: NetworkX graph

    Returns:
        Dict containing degree statistics
    """
    if G is None or G.number_of_nodes() == 0:
        return {
            "dangling_node_count": 0,
            "dangling_nodes": [],
            "max_in_degree": 0,
            "max_out_degree": 0,
            "avg_in_degree": 0,
            "avg_out_degree": 0,
            "incoming_edges_per_node": {},
            "outgoing_edges_per_node": {},
        }

    # Calculate degree information
    in_degrees = [G.in_degree(node) for node in G.nodes()]
    out_degrees = [G.out_degree(node) for node in G.nodes()]

    # Find dangling nodes (degree 0)
    dangling_nodes = [n for n in G.nodes() if G.degree(n) == 0]

    # Per-node degree information
    incoming_edges_per_node = {node: G.in_degree(node) for node in G.nodes()}
    outgoing_edges_per_node = {node: G.out_degree(node) for node in G.nodes()}

    return {
        "dangling_node_count": len(dangling_nodes),
        "dangling_nodes": dangling_nodes,
        "max_in_degree": max(in_degrees) if in_degrees else 0,
        "max_out_degree": max(out_degrees) if out_degrees else 0,
        "avg_in_degree": np.mean(in_degrees) if in_degrees else 0,
        "avg_out_degree": np.mean(out_degrees) if out_degrees else 0,
        "incoming_edges_per_node": incoming_edges_per_node,
        "outgoing_edges_per_node": outgoing_edges_per_node,
    }


def calculate_decision_node_stats(G) -> dict[str, Any]:
    """
    Calculate decision node statistics.

    Args:
        G: NetworkX graph

    Returns:
        Dict containing decision node statistics
    """
    if G is None or G.number_of_nodes() == 0:
        return {
            "decision_node_count": 0,
            "decision_nodes": [],
            "decision_node_details": {},
            "total_decision_paths": 0,
            "avg_paths_per_decision": 0,
            "max_paths_per_decision": 0,
            "decision_path_labels": [],
        }

    # Identify decision nodes by shape (diamond) or high out-degree with labeled edges
    decision_nodes = []
    decision_node_details = {}
    all_path_labels = []

    for node, node_data in G.nodes(data=True):
        # Check if node is a decision node based on:
        # 1. Shape is diamond/rhombus
        # 2. Multiple outgoing edges with labels (indicating branching paths)
        node_shape = node_data.get("shape", "")
        out_degree = G.out_degree(node)

        # Get outgoing edges with labels
        outgoing_edges = [(node, target, edge_data) for node, target, edge_data in G.edges(node, data=True)]
        labeled_outgoing = [
            edge for edge in outgoing_edges if edge[2].get("label") and edge[2].get("label") != "subgraph"
        ]

        # Consider it a decision node if:
        # - Shape is diamond/rhombus, OR
        # - Has multiple labeled outgoing edges (branching logic)
        is_decision_node = node_shape.lower() in ["diamond", "rhombus"] or len(labeled_outgoing) >= 2

        if is_decision_node:
            decision_nodes.append(node)

            # Collect decision path information
            decision_paths = []
            proceeding_nodes = []

            for _, target, edge_data in labeled_outgoing:
                path_label = edge_data.get("label", "unlabeled")
                decision_paths.append(
                    {
                        "option_label": path_label,
                        "target_node": target,
                        "target_label": G.nodes[target].get("label", target),
                    }
                )
                proceeding_nodes.append(target)
                all_path_labels.append(path_label)

            decision_node_details[node] = {
                "node_id": node,
                "node_label": node_data.get("label", node),
                "node_shape": node_shape,
                "decision_paths": decision_paths,
                "path_count": len(decision_paths),
                "proceeding_nodes": proceeding_nodes,
            }

    # Calculate statistics
    path_counts = [details["path_count"] for details in decision_node_details.values()]

    return {
        "decision_node_count": len(decision_nodes),
        "decision_nodes": decision_nodes,
        "decision_node_details": decision_node_details,
        "total_decision_paths": sum(path_counts),
        "avg_paths_per_decision": np.mean(path_counts) if path_counts else 0,
        "max_paths_per_decision": max(path_counts) if path_counts else 0,
        "decision_path_labels": all_path_labels,
    }


def analyze_graph_statistics(G) -> dict[str, Any]:
    """
    Analyze comprehensive graph statistics from a NetworkX graph.

    Args:
        G: NetworkX directed graph

    Returns:
        Dict: Dictionary containing all graph statistics
    """
    if G is None:
        return get_empty_stats()

    # Combine all statistics
    stats = {}
    stats.update(calculate_basic_graph_stats(G))
    stats.update(calculate_subgraph_stats(G))
    stats.update(calculate_node_degree_stats(G))
    stats.update(calculate_decision_node_stats(G))

    return stats


def get_empty_stats() -> dict[str, Any]:
    """
    Return empty statistics dictionary for failed parsing.

    Returns:
        Dict with zero values for all statistics
    """
    return {
        "node_count": 0,
        "total_edge_count": 0,
        "real_edge_count": 0,
        "subgraph_edge_count": 0,
        "subgraph_count": 0,
        "nodes_per_subgraph": {},
        "subgraph_sizes": [],
        "max_subgraph_size": 0,
        "avg_subgraph_size": 0,
        "dangling_node_count": 0,
        "dangling_nodes": [],
        "max_in_degree": 0,
        "max_out_degree": 0,
        "avg_in_degree": 0,
        "avg_out_degree": 0,
        "incoming_edges_per_node": {},
        "outgoing_edges_per_node": {},
        "decision_node_count": 0,
        "decision_nodes": [],
        "decision_node_details": {},
        "total_decision_paths": 0,
        "avg_paths_per_decision": 0,
        "max_paths_per_decision": 0,
        "decision_path_labels": [],
    }


# =============================================================================
# ANALYSIS UTILITIES
# =============================================================================


def analyze_single_diagram(mermaid_code: str, diagram_id: Any = None) -> dict[str, Any]:
    """
    Analyze a single Mermaid diagram and return comprehensive statistics.

    Args:
        mermaid_code (str): Mermaid diagram code
        diagram_id: Optional identifier for the diagram

    Returns:
        Dict containing all graph statistics and metadata
    """
    try:
        # Parse the Mermaid code into a NetworkX graph
        G = parse_mermaid_to_graph(mermaid_code)

        if G is None:
            raise ValueError("Failed to parse diagram")

        # Analyze statistics
        stats = analyze_graph_statistics(G)

        # Add metadata
        stats["diagram_id"] = diagram_id
        stats["success"] = True
        stats["error"] = None

        return stats, G
    except Exception as e:
        # Return failed parsing stats
        stats = get_empty_stats()
        stats["diagram_id"] = diagram_id
        stats["success"] = False
        stats["error"] = str(e)

        return stats, None


def analyze_dataset_batch(df: pd.DataFrame, split_name: str = "", show_progress: bool = True) -> list[dict[str, Any]]:
    """
    Analyze statistics for all diagrams in a dataset split.

    Args:
        df (pd.DataFrame): DataFrame containing diagram data
        split_name (str): Name of the split (train/val)
        show_progress (bool): Whether to show progress bar

    Returns:
        List of dictionaries containing statistics for each diagram
    """
    results = []
    failed_count = 0

    if show_progress:
        print(f"\nAnalyzing {len(df)} diagrams in {split_name} split...")

    iterator = tqdm(df.iterrows(), total=len(df), desc=f"Processing {split_name}") if show_progress else df.iterrows()

    for idx, row in iterator:
        # Get the Mermaid code
        mermaid_code = row["code"]
        diagram_id = row.get("id", idx)

        # Analyze diagram
        stats, graph = analyze_single_diagram(mermaid_code, diagram_id)

        # Add split information
        stats["split"] = split_name
        stats["index"] = idx

        results.append(stats)

        if not stats["success"]:
            failed_count += 1

    if show_progress:
        print(f"Completed {split_name}: {len(results) - failed_count} successful, {failed_count} failed")

    return results


# =============================================================================
# STATISTICS AND SUMMARY UTILITIES
# =============================================================================


def calculate_dataset_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate summary statistics for a collection of diagram analyses.

    Args:
        results (List[Dict]): List of analysis results

    Returns:
        Dict containing summary statistics
    """
    if not results:
        return {}

    # Convert to DataFrame for easier analysis
    results_df = pd.DataFrame(results)
    successful_df = results_df[results_df["success"] == True]

    summary = {
        "total_diagrams": len(results_df),
        "successful_parses": len(successful_df),
        "failed_parses": len(results_df) - len(successful_df),
        "success_rate": len(successful_df) / len(results_df) * 100 if len(results_df) > 0 else 0,
    }

    if len(successful_df) > 0:
        # Statistical summaries for numeric columns
        numeric_columns = [
            "node_count",
            "real_edge_count",
            "subgraph_count",
            "dangling_node_count",
            "max_in_degree",
            "max_out_degree",
            "avg_in_degree",
            "avg_out_degree",
            "max_subgraph_size",
        ]

        for col in numeric_columns:
            if col in successful_df.columns:
                summary[f"{col}_mean"] = successful_df[col].mean()
                summary[f"{col}_std"] = successful_df[col].std()
                summary[f"{col}_min"] = successful_df[col].min()
                summary[f"{col}_max"] = successful_df[col].max()
                summary[f"{col}_median"] = successful_df[col].median()

    return summary


def print_analysis_summary(summary: dict[str, Any]) -> None:
    """
    Print a formatted summary of dataset analysis.

    Args:
        summary (Dict): Summary statistics from calculate_dataset_summary
    """
    print("\n" + "=" * 60)
    print("DATASET ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"Total diagrams processed: {summary.get('total_diagrams', 0)}")
    print(f"Successfully parsed: {summary.get('successful_parses', 0)}")
    print(f"Failed to parse: {summary.get('failed_parses', 0)}")
    print(f"Success rate: {summary.get('success_rate', 0):.2f}%")

    # Print statistics for each metric
    metrics = [
        ("node_count", "Node Count"),
        ("real_edge_count", "Real Edge Count"),
        ("subgraph_count", "Subgraph Count"),
        ("dangling_node_count", "Dangling Node Count"),
        ("max_in_degree", "Max In-Degree"),
        ("max_out_degree", "Max Out-Degree"),
        ("decision_node_count", "Decision Node Count"),
        ("total_decision_paths", "Total Decision Paths"),
        ("avg_paths_per_decision", "Avg Paths per Decision"),
    ]

    print("\nStatistical Summary:")
    print("-" * 30)

    for col, display_name in metrics:
        mean_key = f"{col}_mean"
        if mean_key in summary:
            print(f"{display_name}:")
            print(f"  Mean: {summary[mean_key]:.2f}")
            print(f"  Std:  {summary[f'{col}_std']:.2f}")
            print(f"  Min:  {summary[f'{col}_min']}")
            print(f"  Max:  {summary[f'{col}_max']}")
            print(f"  Median: {summary[f'{col}_median']:.2f}")
            print()


# =============================================================================
# VISUALIZATION UTILITIES
# =============================================================================


def create_statistics_plots(
    results: list[dict[str, Any]], output_path: str = "diagram_statistics.png", figsize: tuple[int, int] = (15, 10)
) -> None:
    """
    Create visualization plots for diagram statistics.

    Args:
        results (List[Dict]): Analysis results
        output_path (str): Path to save the plot
        figsize (Tuple): Figure size
    """
    # Filter successful results
    successful_results = [r for r in results if r.get("success", False)]

    if not successful_results:
        print("No successful results to visualize")
        return

    df = pd.DataFrame(successful_results)

    # Create figure with subplots - increase to 3x3 for more plots
    fig, axes = plt.subplots(3, 3, figsize=figsize)
    fig.suptitle("Diagram Statistics Distribution", fontsize=16)

    # Define plots
    plots = [
        ("node_count", "Node Count Distribution", "Number of Nodes"),
        ("real_edge_count", "Edge Count Distribution", "Number of Edges"),
        ("subgraph_count", "Subgraph Count Distribution", "Number of Subgraphs"),
        ("dangling_node_count", "Dangling Nodes Distribution", "Number of Dangling Nodes"),
        ("max_in_degree", "Max In-Degree Distribution", "Max In-Degree"),
        ("max_out_degree", "Max Out-Degree Distribution", "Max Out-Degree"),
        ("decision_node_count", "Decision Node Count Distribution", "Number of Decision Nodes"),
        ("total_decision_paths", "Decision Paths Distribution", "Total Decision Paths"),
        ("avg_paths_per_decision", "Paths per Decision Distribution", "Avg Paths per Decision"),
    ]

    for i, (col, title, xlabel) in enumerate(plots):
        row, col_idx = i // 3, i % 3

        if col in df.columns:
            axes[row, col_idx].hist(df[col], bins=min(20, len(df[col].unique())), alpha=0.7)
            axes[row, col_idx].set_title(title)
            axes[row, col_idx].set_xlabel(xlabel)
            axes[row, col_idx].set_ylabel("Frequency")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Visualization saved to {output_path}")
    plt.show()


# =============================================================================
# EXPORT UTILITIES
# =============================================================================


def save_results_to_csv(results: list[dict[str, Any]], output_path: str = "diagram_statistics.csv") -> None:
    """
    Save analysis results to CSV file.

    Args:
        results (List[Dict]): Analysis results
        output_path (str): Output file path
    """
    df = pd.DataFrame(results)

    # Flatten complex columns for CSV export
    simple_columns = []
    for col in df.columns:
        if col not in [
            "nodes_per_subgraph",
            "incoming_edges_per_node",
            "outgoing_edges_per_node",
            "dangling_nodes",
            "subgraph_sizes",
        ]:
            simple_columns.append(col)

    simple_df = df[simple_columns]
    simple_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")


def save_results_to_json(results: list[dict[str, Any]], output_path: str = "diagram_statistics.json") -> None:
    """
    Save analysis results to JSON file (preserves complex data structures).

    Args:
        results (List[Dict]): Analysis results
        output_path (str): Output file path
    """

    # Convert numpy types to native Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            serializable_result[key] = convert_types(value)
        serializable_results.append(serializable_result)

    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)
    print(f"Results saved to {output_path}")


# =============================================================================
# DISPLAY UTILITIES
# =============================================================================


def print_single_diagram_stats(stats: dict[str, Any]) -> None:
    """
    Print statistics for a single diagram in a readable format.

    Args:
        stats (Dict): Statistics dictionary from analyze_graph_statistics
    """
    print("=" * 50)
    print("DIAGRAM STATISTICS")
    print("=" * 50)

    if not stats.get("success", True):
        print(f"Failed to analyze diagram: {stats.get('error', 'Unknown error')}")
        return

    print(f"1. Node count: {stats.get('node_count', 0)}")
    print(f"2. Real edge count: {stats.get('real_edge_count', 0)}")
    print(f"3. Subgraph edge count: {stats.get('subgraph_edge_count', 0)}")
    print(f"4. Subgraph count: {stats.get('subgraph_count', 0)}")
    print(f"5. Dangling node count: {stats.get('dangling_node_count', 0)}")
    print(f"6. Decision node count: {stats.get('decision_node_count', 0)}")
    print(f"7. Total decision paths: {stats.get('total_decision_paths', 0)}")

    dangling_nodes = stats.get("dangling_nodes", [])
    if dangling_nodes:
        print(f"   Dangling nodes: {dangling_nodes}")

    # Decision node details
    decision_details = stats.get("decision_node_details", {})
    if decision_details:
        print("\n8. Decision Node Analysis:")
        for node_id, details in decision_details.items():
            print(f"   Decision Node: {details['node_label']} (ID: {node_id})")
            print(f"     Shape: {details['node_shape']}")
            print(f"     Number of paths: {details['path_count']}")
            for path in details["decision_paths"]:
                print(f"       → '{path['option_label']}' leads to: {path['target_label']} (ID: {path['target_node']})")

    incoming_edges = stats.get("incoming_edges_per_node", {})
    if incoming_edges:
        print("\n9. Incoming edges per node:")
        for node, count in incoming_edges.items():
            print(f"   Node {node}: {count} incoming edges")

    outgoing_edges = stats.get("outgoing_edges_per_node", {})
    if outgoing_edges:
        print("\n10. Outgoing edges per node:")
        for node, count in outgoing_edges.items():
            print(f"   Node {node}: {count} outgoing edges")

    nodes_per_subgraph = stats.get("nodes_per_subgraph", {})
    print("\n11. Nodes per subgraph:")
    if nodes_per_subgraph:
        for subgraph_id, nodes in nodes_per_subgraph.items():
            print(f"   Subgraph {subgraph_id}: {len(nodes)} nodes ({nodes})")
    else:
        print("   No subgraphs found")

    print("=" * 50)


# =============================================================================
# HIGH-LEVEL ANALYSIS FUNCTIONS
# =============================================================================


def analyze_complete_dataset(
    dataset_path: str, supported_types: list[str] = None, output_prefix: str = "diagram_analysis"
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Complete analysis pipeline for a dataset.

    Args:
        dataset_path (str): Path to the dataset
        supported_types (List[str]): Supported diagram types
        output_prefix (str): Prefix for output files

    Returns:
        Tuple of (all_results, summary_stats)
    """
    if supported_types is None:
        supported_types = ["flowchart", "graph"]

    # Load and filter data
    print("Loading dataset...")
    train_df, val_df = load_dataset(dataset_path)

    print("Filtering to supported diagram types...")
    train_filtered = filter_supported_diagrams(train_df, supported_types)
    val_filtered = filter_supported_diagrams(val_df, supported_types)

    print(f"Train: {len(train_filtered)} diagrams (from {len(train_df)} total)")
    print(f"Val: {len(val_filtered)} diagrams (from {len(val_df)} total)")

    # Analyze both splits
    all_results = []

    if len(train_filtered) > 0:
        train_results = analyze_dataset_batch(train_filtered, "train")
        all_results.extend(train_results)

    if len(val_filtered) > 0:
        val_results = analyze_dataset_batch(val_filtered, "val")
        all_results.extend(val_results)

    # Calculate summary
    summary = calculate_dataset_summary(all_results)
    print_analysis_summary(summary)

    # Save results
    save_results_to_csv(all_results, f"{output_prefix}.csv")
    save_results_to_json(all_results, f"{output_prefix}.json")

    # Create visualizations
    create_statistics_plots(all_results, f"{output_prefix}_plots.png")

    return all_results, summary


# =============================================================================
# EXAMPLE/TEST FUNCTIONS
# =============================================================================


def run_example_analysis():
    """Run example analysis with test diagrams."""

    test_diagram = """graph TD
    subgraph Forest Garden Layers
        C[Canopy Layer]
        S[Shrub Layer]
        H[Herbaceous Layer]
        R[Root Layer]
        M[Soil Microbiome]
    end
    subgraph System Architecture Layers
        UI[User Interface]
        ML[Middle Logic]
        DS[Data Services]
        DB[Database]
        IS[Infrastructure]
    end
    C --- UI
    S --- ML
    H --- DS
    R --- DB
    M --- IS
    C --> S
    S --> H
    H --> R
    R --> M
    UI --> ML
    ML --> DS
    DS --> DB
    DB --> IS"""

    test_diagram2 = """flowchart TB
    subgraph "Internal Processing"
        direction TB
        I1[Frame Analysis] --> I2[Compatibility Assessment]
        I2 --> I3[Integration Possibilities]
        I3 --> I4[Formulation Design]
    end
    subgraph "Entity A Reality Frame"
        direction TB
        A1[Ontological Primitives] --> A2[Value Structures]
        A2 --> A3[Causal Models]
        A3 --> A4[Priority Rankings]
    end
    subgraph "Entity B Reality Frame"
        direction TB
        B1[Ontological Primitives] --> B2[Value Structures]
        B2 --> B3[Causal Models]
        B3 --> B4[Priority Rankings]
    end
    subgraph "Intersubjective Agreement Space"
        direction TB
        S1[Shared Primitives] --> S2[Compatible Values]
        S2 --> S3[Negotiated Causality]
        S3 --> S4[Balanced Priorities]
    end
    A4 --> I1
    B4 --> I1
    I4 --> S1
    style I1 fill:#f9f,stroke:#333
    style I4 fill:#f9f,stroke:#333
    style A1 fill:#ccf,stroke:#333
    style B1 fill:#cfc,stroke:#333
    style S1 fill:#fcf,stroke:#333"""

    print("Analyzing test diagram 1...")
    stats1, graph1 = analyze_single_diagram(test_diagram)
    print_single_diagram_stats(stats1)

    print("\nAnalyzing test diagram 2...")
    stats2, graph2 = analyze_single_diagram(test_diagram2)
    print_single_diagram_stats(stats2)


def main():
    """Main function for testing/example usage."""
    dataset_path = "data/BigBeautifulDiagramDataset"
    # Option 1: Run example analysis
    run_example_analysis()

    # Option 2: Run full dataset analysis (uncomment to use)
    # all_results, summary = analyze_complete_dataset(dataset_path)


if __name__ == "__main__":
    main()
