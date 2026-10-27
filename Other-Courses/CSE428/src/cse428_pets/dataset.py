from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class PetSample:
    image_id: str
    class_id: int  # 0-based [0..36]
    species_id: int  # 0-based (0=cat, 1=dog)
    breed_id: int  # 0-based
    image_path: Path
    mask_path: Path


@dataclass(frozen=True)
class LabelInfo:
    class_id_to_breed: dict[int, str]
    class_id_to_species: dict[int, int]  # 0=cat, 1=dog


def species_name(species_id: int) -> str:
    return "cat" if species_id == 0 else "dog"


def _breed_from_image_id(image_id: str) -> str:
    parts = image_id.split("_")
    if len(parts) <= 1:
        return image_id
    return "_".join(parts[:-1])


def parse_list_file(list_path: Path) -> tuple[list[tuple[str, int, int, int]], LabelInfo]:
    """Parse annotations/list.txt.

    Returns:
        rows: list of (image_id, class_id0, species_id0, breed_id0)
        label_info: mapping for class_id -> breed/species
    """

    class_id_to_breed: dict[int, str] = {}
    class_id_to_species: dict[int, int] = {}

    rows: list[tuple[str, int, int, int]] = []

    for raw_line in list_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        image_id, class_id_s, species_id_s, breed_id_s = line.split()
        class_id0 = int(class_id_s) - 1
        species_id0 = int(species_id_s) - 1
        breed_id0 = int(breed_id_s) - 1

        rows.append((image_id, class_id0, species_id0, breed_id0))

        if class_id0 not in class_id_to_breed:
            class_id_to_breed[class_id0] = _breed_from_image_id(image_id)
        if class_id0 not in class_id_to_species:
            class_id_to_species[class_id0] = species_id0

    return rows, LabelInfo(class_id_to_breed=class_id_to_breed, class_id_to_species=class_id_to_species)


def parse_split_file(split_path: Path) -> list[tuple[str, int, int, int]]:
    """Parse annotations/trainval.txt or annotations/test.txt."""

    rows: list[tuple[str, int, int, int]] = []
    for raw_line in split_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        image_id, class_id_s, species_id_s, breed_id_s = line.split()
        rows.append((image_id, int(class_id_s) - 1, int(species_id_s) - 1, int(breed_id_s) - 1))
    return rows


def build_samples(
    *,
    repo_root: Path,
    split_rows: Iterable[tuple[str, int, int, int]],
) -> list[PetSample]:
    """Build PetSample entries from split rows.

    Expects:
      - images/<image_id>.jpg
      - annotations/trimaps/<image_id>.png
    """

    images_dir = repo_root / "images"
    trimaps_dir = repo_root / "annotations" / "trimaps"

    samples: list[PetSample] = []
    for image_id, class_id0, species_id0, breed_id0 in split_rows:
        image_path = images_dir / f"{image_id}.jpg"
        mask_path = trimaps_dir / f"{image_id}.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Missing image: {image_path}")
        if not mask_path.exists():
            raise FileNotFoundError(f"Missing mask: {mask_path}")
        samples.append(
            PetSample(
                image_id=image_id,
                class_id=class_id0,
                species_id=species_id0,
                breed_id=breed_id0,
                image_path=image_path,
                mask_path=mask_path,
            )
        )

    return samples


def load_image_pil(sample: PetSample) -> Image.Image:
    return Image.open(sample.image_path).convert("RGB")


def load_trimap_mask(sample: PetSample) -> np.ndarray:
    """Loads the raw trimap mask as a numpy array of shape (H,W) with integer values."""

    mask = Image.open(sample.mask_path)
    return np.array(mask, dtype=np.uint8)


def trimap_to_binary_mask(trimap: np.ndarray) -> np.ndarray:
    """Convert Oxford-IIIT Pet trimap to a binary foreground mask.

    Original trimap encoding (dataset convention):
      - 1: foreground
      - 2: background
      - 3: boundary

    Guideline requirement: change boundary pixels to foreground.

    Returns:
      uint8 array in {0,1} where 1=foreground.
    """

    # Treat everything except explicit background (2) as foreground.
    return (trimap != 2).astype(np.uint8)


class MaskMode(str):
    pass


MaskModeLiteral = Literal["binary", "trimap"]


def prepare_mask(trimap: np.ndarray, mode: MaskModeLiteral = "binary") -> np.ndarray:
    if mode == "binary":
        return trimap_to_binary_mask(trimap)
    if mode == "trimap":
        # Map to 0..2
        # 1->0 foreground, 2->1 background, 3->2 boundary
        out = trimap.astype(np.int64) - 1
        out[out < 0] = 0
        out[out > 2] = 2
        return out.astype(np.uint8)
    raise ValueError(f"Unknown mask mode: {mode}")
