"""Semantic clustering pipeline for source-note aggregation."""

from __future__ import annotations

import hashlib
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import duckdb

from .config import (
    DEFAULT_DB_PATH,
    EMBEDDING_MODEL_NAME,
    SEMANTIC_DEFAULT_N_CLUSTERS,
)
from .database import (
    create_semantic_tables,
    load_existing_embeddings,
    load_semantic_sources,
    replace_cluster_run,
    upsert_embeddings,
)
from .models import ClusterItem, SemanticSourceRecord
from .templates import render_aggregator_by_domain, render_cluster_note, render_clusters_index
from .vault import ensure_vault_directories


def _safe_write(path: Path, content: str, dry_run: bool) -> str:
    if path.exists():
        return "skipped"
    if dry_run:
        return "planned"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def build_embedding_input(record: SemanticSourceRecord) -> str:
    """Build compact semantic text used as embedding input."""
    return f"{record.title.strip()}\nDomain: {record.domain.strip()}\nType: {record.source_type}"


def compute_embeddings(records: list[SemanticSourceRecord], model_name: str) -> dict[str, list[float]]:
    """Compute dense vectors for source records using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        cache_dir = (Path.cwd() / ".cache" / "huggingface").resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(cache_dir))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(cache_dir / "hub"))
        model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
        texts = [build_embedding_input(record) for record in records]
        vectors = model.encode(texts, normalize_embeddings=True)

        by_url: dict[str, list[float]] = {}
        for idx, record in enumerate(records):
            by_url[record.url_norm] = vectors[idx].tolist()
        return by_url
    except Exception as exc:
        print(f"[SEMANTIC] Falha ao carregar sentence-transformers ({exc}). Usando fallback local de hash embeddings.")
        return _compute_hash_embeddings(records)


def _compute_hash_embeddings(records: list[SemanticSourceRecord], dimensions: int = 128) -> dict[str, list[float]]:
    """Compute deterministic hash-based embeddings when ML runtime is unavailable."""
    by_url: dict[str, list[float]] = {}
    for record in records:
        vec = [0.0] * dimensions
        for token in build_embedding_input(record).lower().split():
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:2], "big") % dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vec)) or 1.0
        by_url[record.url_norm] = [value / norm for value in vec]
    return by_url


def _euclidean_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((ax - bx) ** 2 for ax, bx in zip(a, b)))


def cluster_embeddings(
    ordered_records: list[SemanticSourceRecord],
    embedding_by_url: dict[str, list[float]],
    n_clusters: int,
) -> tuple[list[tuple[str, int, float]], dict[int, list[SemanticSourceRecord]]]:
    """Cluster embeddings and return assignments with centroid distances."""
    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:
        raise RuntimeError("Dependencia ausente: instale scikit-learn para usar build-semantic.") from exc

    vectors = [embedding_by_url[record.url_norm] for record in ordered_records]
    cluster_count = max(1, min(n_clusters, len(vectors)))

    if len(vectors) == 1:
        assignments = [(ordered_records[0].url_norm, 0, 0.0)]
        return assignments, {0: [ordered_records[0]]}

    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    labels = model.fit_predict(vectors)

    by_cluster: dict[int, list[SemanticSourceRecord]] = defaultdict(list)
    assignments: list[tuple[str, int, float]] = []
    for idx, record in enumerate(ordered_records):
        cluster_id = int(labels[idx])
        centroid = model.cluster_centers_[cluster_id].tolist()
        distance = _euclidean_distance(vectors[idx], centroid)
        assignments.append((record.url_norm, cluster_id, distance))
        by_cluster[cluster_id].append(record)

    return assignments, by_cluster


def extract_top_terms(records: list[SemanticSourceRecord], max_terms: int = 5) -> list[str]:
    """Extract frequent non-trivial terms from cluster titles."""
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "para",
        "com",
        "como",
        "uma",
        "mais",
        "that",
        "this",
        "your",
        "into",
    }
    tokens: list[str] = []
    for record in records:
        for token in record.title.lower().replace("/", " ").replace("-", " ").split():
            clean = "".join(char for char in token if char.isalnum())
            if len(clean) >= 4 and clean not in stopwords:
                tokens.append(clean)

    counts = Counter(tokens)
    return [term for term, _ in counts.most_common(max_terms)]


def optional_enrich_cluster_with_llm(provider: str, top_terms: list[str]) -> tuple[str, str]:
    """Optional placeholder for future provider integration.

    V1 keeps local deterministic labels while provider integration is not configured.
    """
    label = " / ".join(top_terms[:3]) if top_terms else "Sem tema dominante"
    if provider == "none":
        return label, ""
    summary = f"Resumo automatico indisponivel (provider={provider}). Cluster rotulado por termos frequentes."
    return label, summary


def build_semantic(
    db_path: Path = DEFAULT_DB_PATH,
    vault_path: Path | None = None,
    min_visit_count: int | None = None,
    n_clusters: int = SEMANTIC_DEFAULT_N_CLUSTERS,
    model_name: str = EMBEDDING_MODEL_NAME,
    llm_provider: str = "none",
    dry_run: bool = False,
    limit: int | None = None,
) -> None:
    """Build semantic clustering artifacts in DuckDB and Obsidian vault."""
    from .config import resolve_default_vault_path

    vault_path = vault_path or resolve_default_vault_path()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    ensure_vault_directories(vault_path=vault_path, dry_run=dry_run)

    records = load_semantic_sources(db_path=db_path, min_visit_count=min_visit_count, limit=limit)
    if not records:
        print("[SEMANTIC] Nenhuma fonte elegivel para clusterizacao.")
        return

    with duckdb.connect(str(db_path)) as connection:
        create_semantic_tables(connection)
        cached_embeddings = load_existing_embeddings(connection, model_name=model_name)

        # Step 1: fill missing embeddings.
        missing_records = [record for record in records if record.url_norm not in cached_embeddings]
        if missing_records:
            new_embeddings = compute_embeddings(missing_records, model_name=model_name)
            upsert_embeddings(
                connection,
                (
                    (record.url_norm, record.title, record.domain, model_name, new_embeddings[record.url_norm])
                    for record in missing_records
                ),
            )
            cached_embeddings.update(new_embeddings)

        # Step 2: enforce one embedding dimension across all records in this run.
        candidate_dims = [
            len(cached_embeddings[record.url_norm])
            for record in records
            if record.url_norm in cached_embeddings
        ]
        if not candidate_dims:
            raise RuntimeError("Nao foi possivel obter embeddings para as fontes selecionadas.")

        target_dim = Counter(candidate_dims).most_common(1)[0][0]
        stale_records = [
            record
            for record in records
            if record.url_norm in cached_embeddings and len(cached_embeddings[record.url_norm]) != target_dim
        ]
        if stale_records:
            print(
                f"[SEMANTIC] Recomputando {len(stale_records)} embeddings com dimensao divergente "
                f"(target_dim={target_dim})."
            )
            refreshed_embeddings = compute_embeddings(stale_records, model_name=model_name)
            upsert_embeddings(
                connection,
                (
                    (record.url_norm, record.title, record.domain, model_name, refreshed_embeddings[record.url_norm])
                    for record in stale_records
                ),
            )
            cached_embeddings.update(refreshed_embeddings)

        assignments, by_cluster = cluster_embeddings(records, cached_embeddings, n_clusters=n_clusters)

        cluster_metadata_rows: list[tuple[int, str, str, list[str], int]] = []
        cluster_items: dict[int, list[ClusterItem]] = {}
        for cluster_id, cluster_records in sorted(by_cluster.items()):
            top_terms = extract_top_terms(cluster_records)
            label, summary = optional_enrich_cluster_with_llm(llm_provider, top_terms)
            cluster_metadata_rows.append((cluster_id, label, summary, top_terms, len(cluster_records)))

            items: list[ClusterItem] = []
            for record in cluster_records:
                items.append(
                    ClusterItem(
                        cluster_id=cluster_id,
                        url_norm=record.url_norm,
                        title=record.title,
                        domain=record.domain,
                        visit_count=record.visit_count,
                        source_type=record.source_type,
                        path=record.path,
                    )
                )
            cluster_items[cluster_id] = items

        if not dry_run:
            replace_cluster_run(connection, run_id=run_id, assignments=assignments, metadata=cluster_metadata_rows)

    metadata_dict = {
        cluster_id: {
            "label": label,
            "summary": summary,
            "top_terms": top_terms,
            "size": size,
        }
        for cluster_id, label, summary, top_terms, size in cluster_metadata_rows
    }

    counters = defaultdict(int)
    for cluster_id, items in sorted(cluster_items.items()):
        meta = metadata_dict[cluster_id]
        cluster_filename = f"Cluster-{cluster_id:03d}.md"
        cluster_path = vault_path / "03 - Aggregators" / "Clusters" / cluster_filename
        status = _safe_write(
            cluster_path,
            render_cluster_note(cluster_id=cluster_id, label=str(meta["label"]), summary=str(meta["summary"]), items=items),
            dry_run=dry_run,
        )
        counters[f"cluster_{status}"] += 1

    idx_status = _safe_write(
        vault_path / "03 - Aggregators" / "Clusters Index.md",
        render_clusters_index(metadata_dict),
        dry_run=dry_run,
    )
    counters[f"index_{idx_status}"] += 1

    domain_status = _safe_write(
        vault_path / "03 - Aggregators" / "By Domain.md",
        render_aggregator_by_domain(cluster_items),
        dry_run=dry_run,
    )
    counters[f"domain_{domain_status}"] += 1

    mode = "DRY-RUN" if dry_run else "WRITE"
    print(f"[{mode}] Semantic run_id: {run_id}")
    print(f"[{mode}] Cofre: {vault_path}")
    print(f"[{mode}] Fontes clusterizadas: {len(records)}")
    for key in sorted(counters):
        print(f"{key}: {counters[key]}")
