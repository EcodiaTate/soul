# core/vector_ops.py — Embedding + Dimensionality Ops
import openai
import numpy as np
from sklearn.preprocessing import normalize
from umap import UMAP
from hdbscan import HDBSCAN
from typing import List, Dict, Tuple

from core.llm_tools import prompt_claude, prompt_gpt
from core.logging_engine import log_action

# --- Constants ---
EMBED_DIM = 1536
CLUSTER_MIN_SAMPLES = 5
CLUSTER_MIN_CLUSTER_SIZE = 8

embedding_model_options = ["openai", "claude", "gemini"]

# --- Core Embedding ---
def embed_text(text: str, model: str = "openai") -> List[float]:
    """Return a 1536-dim embedding for a given text using the specified model."""
    try:
        if model == "openai":
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response['data'][0]['embedding']
        elif model == "claude":
            # Claude embedding via LLM simulation
            prompt = f"Return a normalized 1536-dim embedding vector for: {text}"
            return prompt_claude(prompt)
        elif model == "gemini":
            prompt = f"Generate an embedding vector (1536-dim) for: {text}"
            return prompt_gpt(prompt)  # fallback for Gemini
    except Exception as e:
        log_action("vector_ops", "embed_error", f"Failed to embed text: {str(e)}")
        return [0.0] * EMBED_DIM

# --- Dimensionality Reduction ---
def reduce_dimensions(embeddings: List[List[float]], n_components: int = 2) -> List[List[float]]:
    """Apply UMAP to reduce high-dim embeddings to lower-dim for clustering or viz."""
    umap_model = UMAP(n_components=n_components, random_state=42)
    return umap_model.fit_transform(embeddings).tolist()

# --- Clustering ---
def cluster_embeddings(embeddings: List[List[float]]) -> Tuple[List[int], Dict]:
    """Apply HDBSCAN and return cluster labels + metadata (e.g., soft memberships)."""
    cluster_model = HDBSCAN(
        min_samples=CLUSTER_MIN_SAMPLES,
        min_cluster_size=CLUSTER_MIN_CLUSTER_SIZE,
        prediction_data=True
    )
    cluster_labels = cluster_model.fit_predict(embeddings)
    return cluster_labels.tolist(), {"model": cluster_model, "labels": cluster_labels}

def get_soft_cluster_memberships(embedding: List[float], cluster_model) -> Dict[str, float]:
    """Return soft membership scores across clusters for a single embedding."""
    import hdbscan.prediction
    membership = hdbscan.prediction.membership_vector(cluster_model, [embedding])[0]
    return {f"cluster_{i}": float(score) for i, score in enumerate(membership)}

# --- Optional Cluster Labeling ---
def label_clusters(clusters: Dict, texts: List[str]) -> Dict[int, str]:
    """Use Claude/GPT to generate human-readable labels for each cluster."""
    prompt = f"Given the following grouped texts, label each group with a meaningful concept:\n{clusters}"
    label_output = prompt_claude(prompt)
    return label_output  # Must be structured by calling function
