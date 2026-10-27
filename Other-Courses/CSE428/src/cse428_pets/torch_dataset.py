from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import InterpolationMode
from torchvision.transforms import functional as TF

from .dataset import MaskModeLiteral, PetSample, load_image_pil, load_trimap_mask, prepare_mask


@dataclass(frozen=True)
class ImageNormalization:
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)


class OxfordPetsMultiTaskTorchDataset(Dataset[dict[str, object]]):
    def __init__(
        self,
        samples: list[PetSample],
        *,
        image_size: int = 256,
        mask_mode: MaskModeLiteral = "binary",
        augment: bool = False,
        max_rotate_deg: float = 0.0,
        normalization: Optional[ImageNormalization] = ImageNormalization(),
    ) -> None:
        self.samples = samples
        self.image_size = image_size
        self.mask_mode = mask_mode
        self.augment = augment
        self.max_rotate_deg = max_rotate_deg
        self.normalization = normalization

    def __len__(self) -> int:
        return len(self.samples)

    def _maybe_augment(self, image: Image.Image, mask: Image.Image) -> tuple[Image.Image, Image.Image]:
        if random.random() < 0.5:
            image = TF.hflip(image)
            mask = TF.hflip(mask)
        if random.random() < 0.1:
            image = TF.vflip(image)
            mask = TF.vflip(mask)
        if self.max_rotate_deg > 0:
            angle = random.uniform(-self.max_rotate_deg, self.max_rotate_deg)
            image = TF.rotate(image, angle=angle, interpolation=InterpolationMode.BILINEAR)
            mask = TF.rotate(mask, angle=angle, interpolation=InterpolationMode.NEAREST)
        return image, mask

    def __getitem__(self, idx: int) -> dict[str, object]:
        sample = self.samples[idx]

        image = load_image_pil(sample)
        trimap = load_trimap_mask(sample)
        mask_arr = prepare_mask(trimap, mode=self.mask_mode)

        if self.mask_mode == "binary":
            mask_pil = Image.fromarray((mask_arr * 255).astype(np.uint8), mode="L")
        else:
            # 0..2 for 3-class. Store as 0,1,2 values.
            mask_pil = Image.fromarray(mask_arr.astype(np.uint8), mode="L")

        if self.augment:
            image, mask_pil = self._maybe_augment(image, mask_pil)

        # Resize
        image = TF.resize(image, size=[self.image_size, self.image_size], interpolation=InterpolationMode.BILINEAR)
        mask_pil = TF.resize(mask_pil, size=[self.image_size, self.image_size], interpolation=InterpolationMode.NEAREST)

        # To tensor
        image_t = TF.to_tensor(image)
        if self.normalization is not None:
            image_t = TF.normalize(image_t, mean=self.normalization.mean, std=self.normalization.std)

        if self.mask_mode == "binary":
            mask_np = np.array(mask_pil, dtype=np.uint8)
            mask_t = torch.from_numpy(mask_np).float().div(255.0).unsqueeze(0)
        else:
            mask_np = np.array(mask_pil, dtype=np.uint8)
            mask_t = torch.from_numpy(mask_np).long()

        return {
            "image": image_t,
            "mask": mask_t,
            "class_id": int(sample.class_id),
            "species_id": int(sample.species_id),
            "image_id": sample.image_id,
        }
