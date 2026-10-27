from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from .metrics import SegmentationMeter, classification_summary


@dataclass
class EpochStats:
    loss: float
    loss_seg: float
    loss_cls: float
    seg_metrics: dict[str, float]
    cls_metrics: dict[str, float]


def _to_device(batch: dict[str, object], device: torch.device) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    image = batch["image"]
    mask = batch["mask"]
    class_id = batch["class_id"]

    assert isinstance(image, torch.Tensor)
    assert isinstance(mask, torch.Tensor)

    image = image.to(device)
    mask = mask.to(device)

    class_t = torch.as_tensor(class_id, dtype=torch.long, device=device)
    return image, mask, class_t


@torch.no_grad()
def evaluate(
    *,
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    seg_weight: float,
    cls_weight: float,
    threshold: float = 0.5,
    num_classes: int = 37,
) -> EpochStats:
    model.eval()

    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()

    seg_meter = SegmentationMeter()
    y_true: list[int] = []
    y_pred: list[int] = []

    loss_total = 0.0
    loss_seg_total = 0.0
    loss_cls_total = 0.0
    n_batches = 0

    for batch in tqdm(loader, desc="eval", leave=False):
        image, mask, class_t = _to_device(batch, device)
        seg_logits, cls_logits = model(image)

        loss_seg = bce(seg_logits, mask)
        loss_cls = ce(cls_logits, class_t)
        loss = seg_weight * loss_seg + cls_weight * loss_cls

        loss_total += float(loss.item())
        loss_seg_total += float(loss_seg.item())
        loss_cls_total += float(loss_cls.item())
        n_batches += 1

        seg_meter.update_from_logits(seg_logits, mask, threshold=threshold)

        preds = torch.argmax(cls_logits, dim=1)
        y_true.extend(class_t.detach().cpu().tolist())
        y_pred.extend(preds.detach().cpu().tolist())

    seg_metrics = seg_meter.compute()
    cls_metrics = classification_summary(y_true, y_pred, average="macro", num_classes=num_classes)

    return EpochStats(
        loss=loss_total / max(n_batches, 1),
        loss_seg=loss_seg_total / max(n_batches, 1),
        loss_cls=loss_cls_total / max(n_batches, 1),
        seg_metrics=seg_metrics,
        cls_metrics=cls_metrics,
    )


def train_one_epoch(
    *,
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    seg_weight: float,
    cls_weight: float,
) -> tuple[float, float, float]:
    model.train()

    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()

    loss_total = 0.0
    loss_seg_total = 0.0
    loss_cls_total = 0.0
    n_batches = 0

    for batch in tqdm(loader, desc="train", leave=False):
        image, mask, class_t = _to_device(batch, device)

        optimizer.zero_grad(set_to_none=True)
        seg_logits, cls_logits = model(image)

        loss_seg = bce(seg_logits, mask)
        loss_cls = ce(cls_logits, class_t)
        loss = seg_weight * loss_seg + cls_weight * loss_cls

        loss.backward()
        optimizer.step()

        loss_total += float(loss.item())
        loss_seg_total += float(loss_seg.item())
        loss_cls_total += float(loss_cls.item())
        n_batches += 1

    return (
        loss_total / max(n_batches, 1),
        loss_seg_total / max(n_batches, 1),
        loss_cls_total / max(n_batches, 1),
    )
