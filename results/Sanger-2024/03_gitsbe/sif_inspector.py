#!/usr/bin/env python
import argparse
from pathlib import Path

import pandas as pd


SUPPORTED_INTERACTIONS = {"activate", "inhibit"}    # CHANGE if other interactions are supported in the future

def parse_sif(path):
    edges = []
    malformed = []

    with open(path, "r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) != 3:
                malformed.append(
                    {
                        "line_number": line_number,
                        "line_content": line,
                        "error_message": "Expected exactly 3 tab-separated columns",
                    }
                )
                continue

            source, interaction, target = (p.strip() for p in parts)

            if not source or not interaction or not target:
                malformed.append(
                    {
                        "line_number": line_number,
                        "line_content": line,
                        "error_message": "Source, interaction, and target must be non-empty",
                    }
                )
                continue

            if interaction not in SUPPORTED_INTERACTIONS:
                malformed.append(
                    {
                        "line_number": line_number,
                        "line_content": line,
                        "error_message": f"Unsupported interaction '{interaction}'",
                    }
                )
                continue

            edges.append(
                {
                    "source": source,
                    "interaction": interaction,
                    "target": target,
                }
            )

    edges_df = pd.DataFrame(edges, columns=["source", "interaction", "target"])
    malformed_df = pd.DataFrame(
        malformed, columns=["line_number", "line_content", "error_message"]
    )
    return edges_df, malformed_df


def compute_node_sets(edges):
    if edges.empty:
        empty_inputs = pd.DataFrame(columns=["node", "n_outgoing"])
        empty_outputs = pd.DataFrame(columns=["node", "n_incoming"])
        empty_internal = pd.DataFrame(columns=["node", "n_incoming", "n_outgoing"])
        return empty_inputs, empty_outputs, empty_internal

    outgoing_counts = (
        edges.groupby("source", as_index=False).size().rename(columns={"source": "node", "size": "n_outgoing"})
    )
    incoming_counts = (
        edges.groupby("target", as_index=False).size().rename(columns={"target": "node", "size": "n_incoming"})
    )

    sources = set(outgoing_counts["node"])
    targets = set(incoming_counts["node"])

    candidate_inputs = sorted(sources - targets)
    candidate_outputs = sorted(targets - sources)
    internal_nodes = sorted(sources & targets)

    candidate_inputs_df = (
        outgoing_counts[outgoing_counts["node"].isin(candidate_inputs)]
        .loc[:, ["node", "n_outgoing"]]
        .sort_values("node")
        .reset_index(drop=True)
    )
    candidate_outputs_df = (
        incoming_counts[incoming_counts["node"].isin(candidate_outputs)]
        .loc[:, ["node", "n_incoming"]]
        .sort_values("node")
        .reset_index(drop=True)
    )

    internal_df = (
        pd.merge(
            incoming_counts[incoming_counts["node"].isin(internal_nodes)],
            outgoing_counts[outgoing_counts["node"].isin(internal_nodes)],
            on="node",
            how="inner",
        )
        .loc[:, ["node", "n_incoming", "n_outgoing"]]
        .sort_values("node")
        .reset_index(drop=True)
    )

    return candidate_inputs_df, candidate_outputs_df, internal_df


def detect_high_degree_nodes(edges, max_in_degree, max_total_degree):
    columns = [
        "node",
        "n_incoming",
        "n_outgoing",
        "total_degree",
        "high_in_degree",
        "high_total_degree",
        "risk_type",
        "recommendation",
    ]

    if edges.empty:
        return pd.DataFrame(columns=columns)

    outgoing_counts = (
        edges.groupby("source", as_index=False).size().rename(columns={"source": "node", "size": "n_outgoing"})
    )
    incoming_counts = (
        edges.groupby("target", as_index=False).size().rename(columns={"target": "node", "size": "n_incoming"})
    )

    degree_counts = pd.merge(incoming_counts, outgoing_counts, on="node", how="outer").fillna(0)
    degree_counts["n_incoming"] = degree_counts["n_incoming"].astype(int)
    degree_counts["n_outgoing"] = degree_counts["n_outgoing"].astype(int)
    degree_counts["total_degree"] = degree_counts["n_incoming"] + degree_counts["n_outgoing"]
    degree_counts["high_in_degree"] = degree_counts["n_incoming"] >= max_in_degree
    degree_counts["high_total_degree"] = degree_counts["total_degree"] >= max_total_degree

    high_degree_nodes = degree_counts[
        degree_counts["high_in_degree"] | degree_counts["high_total_degree"]
    ].copy()

    def determine_risk_type(row):
        if row["high_in_degree"] and row["high_total_degree"]:
            return "high_in_and_total_degree"
        if row["high_in_degree"]:
            return "high_in_degree"
        return "high_total_degree"

    high_degree_nodes["risk_type"] = high_degree_nodes.apply(determine_risk_type, axis=1)
    high_degree_nodes["recommendation"] = (
        "Review before Gitsbe; high-degree regulation may generate complex Boolean rules and slow or break Oris preprocessing."
    )

    high_degree_nodes = (
        high_degree_nodes.loc[:, columns]
        .sort_values(["n_incoming", "total_degree"], ascending=[False, False])
        .reset_index(drop=True)
    )

    return high_degree_nodes


def detect_self_loops(edges):
    if edges.empty:
        return pd.DataFrame(columns=["source", "interaction", "target"])
    return (
        edges[edges["source"] == edges["target"]]
        .loc[:, ["source", "interaction", "target"]]
        .reset_index(drop=True)
    )


def detect_conflicting_edges(edges):
    if edges.empty:
        return pd.DataFrame(
            columns=["source", "target", "has_activation", "has_inhibition", "issue_type"]
        )

    grouped = (
        edges.groupby(["source", "target"])["interaction"]
        .agg(lambda values: set(values))
        .reset_index(name="interaction_set")
    )
    grouped["has_activation"] = grouped["interaction_set"].apply(lambda s: "->" in s)
    grouped["has_inhibition"] = grouped["interaction_set"].apply(lambda s: "-|" in s)

    conflicts = grouped[grouped["has_activation"] & grouped["has_inhibition"]].copy()
    conflicts["issue_type"] = "conflicting_regulation"

    return (
        conflicts.loc[
            :, ["source", "target", "has_activation", "has_inhibition", "issue_type"]
        ]
        .sort_values(["source", "target"])
        .reset_index(drop=True)
    )


def write_reports(results, out_dir):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results["candidate_inputs"].to_csv(out_path / "sif_candidate_inputs.csv", index=False)
    results["candidate_outputs"].to_csv(
        out_path / "sif_candidate_outputs.csv", index=False
    )
    results["internal_nodes"].to_csv(out_path / "sif_internal_nodes.csv", index=False)
    results["self_loops"].to_csv(out_path / "sif_self_loops.csv", index=False)
    results["conflicting_edges"].to_csv(
        out_path / "sif_conflicting_edges.csv", index=False
    )
    results["high_degree_nodes"].to_csv(
        out_path / "sif_high_degree_nodes.csv", index=False
    )
    results["malformed_lines"].to_csv(
        out_path / "sif_malformed_lines.csv", index=False
    )
    results["summary"].to_csv(out_path / "sif_summary.csv", index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect a SIF network file before running Gitsbe."
    )
    parser.add_argument("sif_file", help="Path to input SIF file")
    parser.add_argument(
        "--out",
        default="sif_inspection",
        help="Output folder (default: sif_inspection)",
    )
    parser.add_argument(
        "--max-in-degree",
        type=int,
        default=10,
        help="Maximum allowed incoming degree before flagging a node (default: 10)",
    )
    parser.add_argument(
        "--max-total-degree",
        type=int,
        default=15,
        help="Maximum allowed total degree before flagging a node (default: 15)",
    )
    args = parser.parse_args()

    edges, malformed_lines = parse_sif(args.sif_file)

    candidate_inputs, candidate_outputs, internal_nodes = compute_node_sets(edges)
    self_loops = detect_self_loops(edges)
    conflicting_edges = detect_conflicting_edges(edges)
    high_degree_nodes = detect_high_degree_nodes(
        edges, args.max_in_degree, args.max_total_degree
    )

    all_nodes = set(edges["source"]).union(set(edges["target"])) if not edges.empty else set()
    summary = pd.DataFrame(
        [
            {"metric": "n_nodes", "value": len(all_nodes)},
            {"metric": "n_edges", "value": len(edges)},
            {"metric": "n_candidate_inputs", "value": len(candidate_inputs)},
            {"metric": "n_candidate_outputs", "value": len(candidate_outputs)},
            {"metric": "n_internal_nodes", "value": len(internal_nodes)},
            {"metric": "n_self_loops", "value": len(self_loops)},
            {"metric": "n_conflicting_edges", "value": len(conflicting_edges)},
            {"metric": "n_high_degree_nodes", "value": len(high_degree_nodes)},
            {"metric": "n_high_in_degree_nodes", "value": int(high_degree_nodes["high_in_degree"].sum())},
            {"metric": "n_high_total_degree_nodes", "value": int(high_degree_nodes["high_total_degree"].sum())},
            {"metric": "max_in_degree", "value": args.max_in_degree},
            {"metric": "max_total_degree", "value": args.max_total_degree},
        ],
        columns=["metric", "value"],
    )

    results = {
        "candidate_inputs": candidate_inputs,
        "candidate_outputs": candidate_outputs,
        "internal_nodes": internal_nodes,
        "self_loops": self_loops,
        "conflicting_edges": conflicting_edges,
        "high_degree_nodes": high_degree_nodes,
        "malformed_lines": malformed_lines,
        "summary": summary,
    }

    write_reports(results, args.out)

    print(f"Processed SIF file: {args.sif_file}")
    print(f"Output folder: {args.out}")
    print(f"Edges: {len(edges)} | Nodes: {len(all_nodes)}")
    print(
        "Candidate inputs: "
        f"{len(candidate_inputs)} | Candidate outputs: {len(candidate_outputs)} | Internal nodes: {len(internal_nodes)}"
    )
    print(
        "Self-loops: "
        f"{len(self_loops)} | Conflicting edges: {len(conflicting_edges)} | Malformed lines: {len(malformed_lines)}"
    )
    print(
        "High-degree nodes: "
        f"{len(high_degree_nodes)} | Flagged by in-degree: {int(high_degree_nodes['high_in_degree'].sum())} | "
        f"Flagged by total degree: {int(high_degree_nodes['high_total_degree'].sum())} | "
        f"Thresholds max in-degree: {args.max_in_degree} | Thresholds max total-degree: {args.max_total_degree}"
    )


if __name__ == "__main__":
    main()
