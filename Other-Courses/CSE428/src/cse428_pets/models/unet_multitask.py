from __future__ import annotations

import torch
import torch.nn as nn


class DoubleConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class AttentionGate(nn.Module):
    """Attention gate for Attention U-Net skip connections."""

    def __init__(self, *, skip_ch: int, gate_ch: int, inter_ch: int) -> None:
        super().__init__()
        self.w_skip = nn.Sequential(
            nn.Conv2d(skip_ch, inter_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_ch),
        )
        self.w_gate = nn.Sequential(
            nn.Conv2d(gate_ch, inter_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_ch),
        )
        self.psi = nn.Sequential(
            nn.Conv2d(inter_ch, 1, kernel_size=1, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, skip: torch.Tensor, gate: torch.Tensor) -> torch.Tensor:
        # skip and gate are assumed to have same spatial size.
        x1 = self.w_skip(skip)
        g1 = self.w_gate(gate)
        psi = self.psi(self.relu(x1 + g1))
        return skip * psi


class UNetMultiTask(nn.Module):
    """U-Net / Attention U-Net with a classification head on the encoder bottleneck."""

    def __init__(
        self,
        *,
        num_classes: int = 37,
        in_channels: int = 3,
        base_channels: int = 64,
        use_attention: bool = False,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.use_attention = use_attention

        ch1 = base_channels
        ch2 = base_channels * 2
        ch3 = base_channels * 4
        ch4 = base_channels * 8
        ch5 = base_channels * 16

        self.enc1 = DoubleConv(in_channels, ch1)
        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = DoubleConv(ch1, ch2)
        self.pool2 = nn.MaxPool2d(2)
        self.enc3 = DoubleConv(ch2, ch3)
        self.pool3 = nn.MaxPool2d(2)
        self.enc4 = DoubleConv(ch3, ch4)
        self.pool4 = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(ch4, ch5)

        self.up4 = nn.ConvTranspose2d(ch5, ch4, kernel_size=2, stride=2)
        self.dec4 = DoubleConv(ch4 + ch4, ch4)
        self.up3 = nn.ConvTranspose2d(ch4, ch3, kernel_size=2, stride=2)
        self.dec3 = DoubleConv(ch3 + ch3, ch3)
        self.up2 = nn.ConvTranspose2d(ch3, ch2, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(ch2 + ch2, ch2)
        self.up1 = nn.ConvTranspose2d(ch2, ch1, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(ch1 + ch1, ch1)

        if use_attention:
            self.att4 = AttentionGate(skip_ch=ch4, gate_ch=ch4, inter_ch=ch4 // 2)
            self.att3 = AttentionGate(skip_ch=ch3, gate_ch=ch3, inter_ch=ch3 // 2)
            self.att2 = AttentionGate(skip_ch=ch2, gate_ch=ch2, inter_ch=ch2 // 2)
            self.att1 = AttentionGate(skip_ch=ch1, gate_ch=ch1, inter_ch=ch1 // 2)
        else:
            self.att4 = self.att3 = self.att2 = self.att1 = None

        self.seg_head = nn.Conv2d(ch1, 1, kernel_size=1)

        self.cls_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(1),
            nn.Linear(ch5, ch5 // 4),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(ch5 // 4, num_classes),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))
        b = self.bottleneck(self.pool4(e4))

        cls_logits = self.cls_head(b)

        d4 = self.up4(b)
        s4 = self.att4(e4, d4) if self.att4 is not None else e4
        d4 = self.dec4(torch.cat([s4, d4], dim=1))

        d3 = self.up3(d4)
        s3 = self.att3(e3, d3) if self.att3 is not None else e3
        d3 = self.dec3(torch.cat([s3, d3], dim=1))

        d2 = self.up2(d3)
        s2 = self.att2(e2, d2) if self.att2 is not None else e2
        d2 = self.dec2(torch.cat([s2, d2], dim=1))

        d1 = self.up1(d2)
        s1 = self.att1(e1, d1) if self.att1 is not None else e1
        d1 = self.dec1(torch.cat([s1, d1], dim=1))

        seg_logits = self.seg_head(d1)
        return seg_logits, cls_logits
