from __future__ import annotations

import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .dataset import LabelInfo, PetSample, load_image_pil, load_trimap_mask, prepare_mask, species_name


def overlay_mask_rgb(image_rgb: np.ndarray, mask01: np.ndarray, *, alpha: float = 0.35) -> np.ndarray:
    """Overlay a binary mask (0/1) onto an RGB image using a green tint."""

    if image_rgb.dtype != np.uint8:
        raise ValueError("image_rgb must be uint8")
    if mask01.dtype != np.uint8:
        mask01 = mask01.astype(np.uint8)
    if mask01.ndim != 2:
        raise ValueError("mask01 must be HxW")

    out = image_rgb.astype(np.float32).copy()
    green = np.array([0, 255, 0], dtype=np.float32)

    m = mask01[..., None].astype(np.float32)
    out = out * (1.0 - alpha * m) + green * (alpha * m)

    return np.clip(out, 0, 255).astype(np.uint8)


def _breed_pretty(breed: str) -> str:
    return breed.replace("_", " ")


def plot_random_overlay_grid(
    *,
    samples: list[PetSample],
    label_info: LabelInfo,
    n: int = 9,
    seed: int | None = None,
) -> None:
    """Plots a 3x3 grid of random images with true mask overlays."""

    if seed is not None:
        random.seed(seed)

    idxs = random.sample(range(len(samples)), k=n)

    fig, axes = plt.subplots(3, 3, figsize=(10, 10))
    axes = axes.reshape(-1)

    for ax, idx in zip(axes, idxs, strict=True):
        s = samples[idx]
        img = np.array(load_image_pil(s), dtype=np.uint8)
        trimap = load_trimap_mask(s)
        mask01 = prepare_mask(trimap, mode="binary")
        vis = overlay_mask_rgb(img, mask01)

        breed = label_info.class_id_to_breed.get(s.class_id, "unknown")
        sp = species_name(s.species_id)
        ax.imshow(vis)
        ax.set_title(f"{_breed_pretty(breed)} ({sp})")
        ax.axis("off")

    plt.tight_layout()
    plt.show()


def compute_iou_binary(mask_true01: np.ndarray, mask_pred01: np.ndarray) -> float:
    t = mask_true01.astype(bool)
    p = mask_pred01.astype(bool)
    inter = np.logical_and(t, p).sum()
    union = np.logical_or(t, p).sum()
    return float(inter / union) if union > 0 else 1.0


def plot_prediction_triplet(
    *,
    image_rgb: np.ndarray,
    mask_true01: np.ndarray,
    mask_pred01: np.ndarray,
    true_label: str,
    pred_label: str,
    iou: float,
) -> None:
    """Plots the exact 3-panel layout required by the guideline."""

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    axes[0].imshow(image_rgb)
    axes[0].set_title("Original image")
    axes[0].axis("off")

    axes[1].imshow(overlay_mask_rgb(image_rgb, mask_true01))
    axes[1].set_title("Image + True mask overlay")
    axes[1].axis("off")

    axes[2].imshow(overlay_mask_rgb(image_rgb, mask_pred01))
    axes[2].set_title("Image + Predict mask overlay")
    axes[2].axis("off")

    fig.suptitle(
        f"Original class - \"{true_label}\"\n"
        f"Predicted class - \"{pred_label}\"\n"
        f"IoU - {iou * 100:.1f}%",
        fontsize=14,
    )

    plt.tight_layout()
    plt.show()
