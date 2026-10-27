from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


@dataclass
class SegmentationMeter:
    """Accumulates binary segmentation metrics over many batches."""

    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0

    def update_from_logits(self, logits: torch.Tensor, target: torch.Tensor, *, threshold: float = 0.5) -> None:
        """Update counts.

        Args:
            logits: (B,1,H,W)
            target: (B,1,H,W) float {0,1}
        """

        probs = torch.sigmoid(logits)
        pred = (probs >= threshold).to(torch.uint8)
        tgt = (target >= 0.5).to(torch.uint8)

        pred_f = pred.view(-1)
        tgt_f = tgt.view(-1)

        tp = torch.sum((pred_f == 1) & (tgt_f == 1)).item()
        tn = torch.sum((pred_f == 0) & (tgt_f == 0)).item()
        fp = torch.sum((pred_f == 1) & (tgt_f == 0)).item()
        fn = torch.sum((pred_f == 0) & (tgt_f == 1)).item()

        self.tp += int(tp)
        self.tn += int(tn)
        self.fp += int(fp)
        self.fn += int(fn)

    def compute(self) -> dict[str, float]:
        eps = 1e-9
        tp, tn, fp, fn = self.tp, self.tn, self.fp, self.fn

        pixel_acc = (tp + tn) / max(tp + tn + fp + fn, 1)

        iou_fg = tp / (tp + fp + fn + eps)
        iou_bg = tn / (tn + fp + fn + eps)
        miou = (iou_fg + iou_bg) / 2.0

        dice_fg = (2 * tp) / (2 * tp + fp + fn + eps)

        return {
            "pixel_accuracy": float(pixel_acc),
            "iou_fg": float(iou_fg),
            "iou_bg": float(iou_bg),
            "miou": float(miou),
            "dice_fg": float(dice_fg),
        }


def classification_summary(
    y_true: list[int] | np.ndarray,
    y_pred: list[int] | np.ndarray,
    *,
    average: str = "macro",
    num_classes: int | None = None,
) -> dict[str, float]:
    """Compute accuracy/precision/recall/F1.

    Uses sklearn when available, otherwise falls back to numpy-only (accuracy only).
    """

    y_true_arr = np.asarray(y_true, dtype=np.int64)
    y_pred_arr = np.asarray(y_pred, dtype=np.int64)
    acc = float(np.mean(y_true_arr == y_pred_arr))

    try:
        from sklearn.metrics import precision_recall_fscore_support

        prec, rec, f1, _ = precision_recall_fscore_support(
            y_true_arr,
            y_pred_arr,
            average=average,
            labels=list(range(num_classes)) if num_classes is not None else None,
            zero_division=0,
        )
        return {
            "accuracy": acc,
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
        }
    except Exception:
        return {
            "accuracy": acc,
            "precision": float("nan"),
            "recall": float("nan"),
            "f1": float("nan"),
        }
