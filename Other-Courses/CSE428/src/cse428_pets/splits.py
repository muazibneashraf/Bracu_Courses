from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .dataset import LabelInfo, PetSample, build_samples, parse_list_file, parse_split_file


@dataclass(frozen=True)
class DatasetSplits:
    train: list[PetSample]
    val: list[PetSample]
    test: list[PetSample]
    label_info: LabelInfo


def make_splits(*, repo_root: Path, val_ratio: float = 0.2, seed: int = 42) -> DatasetSplits:
    annotations_dir = repo_root / "annotations"
    list_path = annotations_dir / "list.txt"
    trainval_path = annotations_dir / "trainval.txt"
    test_path = annotations_dir / "test.txt"

    _rows, label_info = parse_list_file(list_path)

    trainval_rows = parse_split_file(trainval_path)
    test_rows = parse_split_file(test_path)

    # Stratified split by class_id when sklearn is available.
    try:
        from sklearn.model_selection import train_test_split

        image_ids = [r[0] for r in trainval_rows]
        class_ids = [r[1] for r in trainval_rows]

        train_ids, val_ids = train_test_split(
            image_ids,
            test_size=val_ratio,
            random_state=seed,
            shuffle=True,
            stratify=class_ids,
        )
        train_set = set(train_ids)
        val_set = set(val_ids)
        train_rows = [r for r in trainval_rows if r[0] in train_set]
        val_rows = [r for r in trainval_rows if r[0] in val_set]
    except Exception:
        # Fallback: deterministic split without stratification.
        trainval_rows_sorted = sorted(trainval_rows, key=lambda x: x[0])
        n_val = int(len(trainval_rows_sorted) * val_ratio)
        val_rows = trainval_rows_sorted[:n_val]
        train_rows = trainval_rows_sorted[n_val:]

    train = build_samples(repo_root=repo_root, split_rows=train_rows)
    val = build_samples(repo_root=repo_root, split_rows=val_rows)
    test = build_samples(repo_root=repo_root, split_rows=test_rows)

    return DatasetSplits(train=train, val=val, test=test, label_info=label_info)
