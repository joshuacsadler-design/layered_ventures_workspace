#!/usr/bin/env python3
"""
Infusist Series 001 - Controlled Aesthetic Collection (Glossy baseline)

UPDATED FOR YOUR WORKFLOW:
- Primary iterative test size: 6x8 (stocked)
- Validation test size: 8x12
- Masters default to 8x12 (so validation and final are aligned)

Generates ONLY first-hand original images (no mockups, no photos-of-prints),
plus 6x8 and 8x12 test sheets and analysis exports.

Outputs (in --out folder):
  Masters (default 8x12 @ 300dpi):
    INF001_NOCTURNE_STEEL_v1.png
    INF001_FUSED_CURRENT_v1.png
    INF001_HUMAN_FRACTION_v1.png
    INF001_COMBUSTION_VECTOR_v1.png

  Test sheets (diagnostic layout matched):
    INF001_TESTSHEET_6x8_v1.png
    INF001_TESTSHEET_8x12_v1.png

  Analysis exports:
    INF001_CONTROLLED_AESTHETIC_EXPORT.csv
    INF001_PRINT_RUNS_TEMPLATE.csv
    INF001_SCORECARD_TEMPLATE.csv
    INF001_PATCH_MEASUREMENTS_TEMPLATE.csv

Requirements:
  pip install pillow numpy

PowerShell run:
  py .\create_infusist_series_001.py --out ".\INFUSIST_SERIES_001_GLOSSY" --dpi 300 --seed 2400
"""

import argparse
import csv
import math
import os
from dataclasses import dataclass
from typing import Tuple, List, Dict

import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw, ImageFont


# -----------------------------
# Config
# -----------------------------

@dataclass
class SeriesConfig:
    series_id: str = "INF001"
    series_name: str = "Controlled Aesthetic"
    printer: str = "ET2400"
    ink_type: str = "Dye"
    color_space: str = "sRGB"
    bit_depth: int = 8

    # Testing baseline
    substrate: str = "Glossy"
    temp_f: int = 400
    dwell_s: int = 60
    pressure: str = "Medium"
    icc_profile: str = "sRGB_Default"
    curve_version: str = "v1"


# -----------------------------
# Helpers
# -----------------------------

def parse_size_inches(size_str: str, dpi: int) -> Tuple[int, int]:
    parts = size_str.lower().replace(" ", "").split("x")
    if len(parts) != 2:
        raise ValueError("Size must be like 6x8, 8x12, 8.5x11, etc.")
    w_in = float(parts[0])
    h_in = float(parts[1])
    return int(round(w_in * dpi)), int(round(h_in * dpi))


def set_dpi(img: Image.Image, dpi: int) -> Image.Image:
    img.info["dpi"] = (dpi, dpi)
    return img


def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)


def to_uint8(rgb01: np.ndarray) -> np.ndarray:
    return (clamp01(rgb01) * 255.0 + 0.5).astype(np.uint8)


def soft_vignette(h: int, w: int, strength: float = 0.35) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2.0, h / 2.0
    r = np.sqrt(((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0)) ** 2)
    v = 1.0 - strength * (r ** 1.6)
    return clamp01(v)


def add_noise(rgb01: np.ndarray, amount: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = rng.normal(0.0, amount, size=rgb01.shape).astype(np.float32)
    return clamp01(rgb01 + n)


def motion_blur(gray: Image.Image, angle_deg: float, radius: int) -> Image.Image:
    rotated = gray.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    blurred = rotated.filter(ImageFilter.BoxBlur(radius=radius))
    back = blurred.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)
    bw, bh = back.size
    ow, oh = gray.size
    left = (bw - ow) // 2
    top = (bh - oh) // 2
    return back.crop((left, top, left + ow, top + oh))


def overlay_blend(base: np.ndarray, over: np.ndarray, opacity: float) -> np.ndarray:
    b = base
    o = over
    low = 2.0 * b * o
    high = 1.0 - 2.0 * (1.0 - b) * (1.0 - o)
    out = np.where(b < 0.5, low, high)
    return clamp01(b * (1.0 - opacity) + out * opacity)


def screen_blend(base: np.ndarray, over: np.ndarray, opacity: float) -> np.ndarray:
    b = base
    o = over
    out = 1.0 - (1.0 - b) * (1.0 - o)
    return clamp01(b * (1.0 - opacity) + out * opacity)


# -----------------------------
# Calibration + Diagnostics
# -----------------------------

def draw_bottom_calibration_band(
    img: Image.Image,
    dpi: int,
    band_mm: float = 4.0,
    steps=(0, 3, 5, 7, 10),
    patch_mm: float = 2.0,
    blend_strength: float = 0.10,  # lower = more hidden
) -> Image.Image:
    w, h = img.size
    mm_to_px = lambda mm: int(round((mm / 25.4) * dpi))
    band_h = max(1, mm_to_px(band_mm))
    patch = max(1, mm_to_px(patch_mm))

    arr = np.asarray(img).astype(np.uint8)
    band_y0 = h - band_h
    band = arr[band_y0:h, :, :].astype(np.float32) / 255.0

    block_w = max(1, int(w * 0.055))
    gap = max(1, int(block_w * 0.20))
    x = max(1, int(w * 0.02))
    for s in steps:
        lum = s / 100.0
        block = np.zeros((band_h, block_w, 3), dtype=np.float32) + lum
        band[:, x:x + block_w, :] = band[:, x:x + block_w, :] * (1.0 - blend_strength) + block * blend_strength
        x += block_w + gap

    def blend_patch(px, py, rgb):
        nonlocal band
        x0, y0 = px, py
        x1, y1 = min(w, x0 + patch), min(band_h, y0 + patch)
        if x1 <= x0 or y1 <= y0:
            return
        rgb01 = np.array(rgb, dtype=np.float32) / 255.0
        band[y0:y1, x0:x1, :] = band[y0:y1, x0:x1, :] * (1.0 - blend_strength) + rgb01 * blend_strength

    px1 = max(0, w - int(w * 0.06))
    py1 = max(0, band_h - patch - max(1, patch // 2))
    blend_patch(px1, py1, (10, 10, 10))
    blend_patch(px1 + patch + max(1, patch // 2), py1, (118, 118, 118))

    arr[band_y0:h, :, :] = (clamp01(band) * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def make_gray_ramp(w: int, h: int, start: float, end: float) -> Image.Image:
    t = np.linspace(start, end, w, dtype=np.float32)[None, :]
    ramp = np.repeat(t, h, axis=0)
    rgb = np.stack([ramp, ramp, ramp], axis=2)
    return Image.fromarray(to_uint8(rgb), mode="RGB")


def make_color_blocks(block: int) -> Image.Image:
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (0, 255, 255), (255, 0, 255), (255, 255, 0),
        (255, 255, 255),
    ]
    levels = [0.80, 0.90, 1.00]
    w = block * len(colors) * len(levels)
    h = block
    img = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for lvl in levels:
        for c in colors:
            cc = (int(c[0] * lvl), int(c[1] * lvl), int(c[2] * lvl))
            d.rectangle([x, 0, x + block - 1, h - 1], fill=cc)
            x += block
    return img


def try_get_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_microtext_panel(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (10, 10, 14))
    d = ImageDraw.Draw(img)

    font_title = try_get_font(max(14, int(min(w, h) * 0.08)))
    font_small = try_get_font(max(12, int(min(w, h) * 0.055)))
    font_med = try_get_font(max(14, int(min(w, h) * 0.065)))

    d.text((10, 8), "Microtext + Line Tests", fill=(230, 230, 230), font=font_title)

    y = int(10 + font_title.size * 1.5) if hasattr(font_title, "size") else 40
    d.text((10, y), "Small: INFUSISTLAB ET2400 | 0123456789 | ABCDEFGHIJKLM", fill=(235, 235, 235), font=font_small)
    y += int(font_small.size * 2.0) if hasattr(font_small, "size") else 28
    d.text((10, y), "Medium: INFUSISTLAB ET2400 | 0123456789 | ABCDEFGHIJKLM", fill=(235, 235, 235), font=font_med)
    y += int(font_med.size * 2.2) if hasattr(font_med, "size") else 40

    for i in range(12):
        y0 = y + i * 5
        d.line((10, y0, w - 10, y0), fill=(235, 235, 235), width=1)

    d.line((w - 160, 40, w - 20, 180), fill=(235, 235, 235), width=1)
    return img


# -----------------------------
# Artwork Generators (FIRST-HAND)
# -----------------------------

def make_nocturne_steel(w: int, h: int, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    base_l = (0.00 + 0.08 * (y ** 1.6))
    base = np.repeat(base_l, w, axis=1)
    rgb = np.stack([base, base, base], axis=2)

    n = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    noise_img = Image.fromarray((n * 255).astype(np.uint8), mode="L")
    brushed = motion_blur(noise_img, angle_deg=90.0, radius=max(6, int(min(w, h) * 0.003)))
    brushed = brushed.filter(ImageFilter.GaussianBlur(radius=max(1, int(min(w, h) * 0.0015))))

    brushed01 = (np.asarray(brushed).astype(np.float32) / 255.0)
    brushed_rgb = np.stack([brushed01, brushed01, brushed01], axis=2)
    rgb = overlay_blend(rgb, brushed_rgb, opacity=0.18)

    v = soft_vignette(h, w, strength=0.28)[:, :, None]
    rgb = clamp01(rgb * v)
    rgb = add_noise(rgb, amount=0.010, seed=seed + 11)
    return Image.fromarray(to_uint8(rgb), mode="RGB")


def make_fused_current(w: int, h: int, seed: int) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:w]
    x = (xx / (w - 1)).astype(np.float32)
    y = (yy / (h - 1)).astype(np.float32)

    bg = np.zeros((h, w, 3), dtype=np.float32)
    bg[..., 0] = 5 / 255.0
    bg[..., 1] = 10 / 255.0
    bg[..., 2] = 25 / 255.0

    curve = 0.55 + 0.10 * np.sin(2.0 * math.pi * (x - 0.2))
    d = np.abs(y - curve)
    ribbon = np.exp(-(d ** 2) / (2.0 * (0.012 ** 2)))

    cool = np.array([0.0, 0.78, 1.0], dtype=np.float32)
    warm = np.array([1.0, 0.35, 0.0], dtype=np.float32)
    t = clamp01((x - 0.42) / 0.58)
    col = (1.0 - t)[..., None] * cool + t[..., None] * warm

    glow = ribbon[..., None] * col
    wide = np.exp(-(d ** 2) / (2.0 * (0.030 ** 2)))[..., None] * col * 0.55

    rgb = bg.copy()
    rgb = screen_blend(rgb, glow, opacity=0.85)
    rgb = screen_blend(rgb, wide, opacity=0.65)

    cx, cy = 0.55, 0.52
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    radial = np.exp(-(r ** 2) / (2.0 * (0.28 ** 2)))[..., None]
    rgb = clamp01(rgb + radial * 0.06)

    rgb = add_noise(rgb, amount=0.012, seed=seed + 21)
    v = soft_vignette(h, w, strength=0.22)[:, :, None]
    rgb = clamp01(rgb * v)
    return Image.fromarray(to_uint8(rgb), mode="RGB")


def make_human_fraction(w: int, h: int, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    x = ((xx / (w - 1)) * 2.0 - 1.0).astype(np.float32)
    y = ((yy / (h - 1)) * 2.0 - 1.0).astype(np.float32)

    a, b = 0.55, 0.75
    face = 1.0 - ((x / a) ** 2 + (y / b) ** 2)
    face = clamp01(face)

    nose = np.exp(-((x - 0.05) ** 2) / (2.0 * (0.07 ** 2))) * np.exp(-((y + 0.05) ** 2) / (2.0 * (0.30 ** 2)))
    eye1 = np.exp(-((x + 0.18) ** 2) / (2.0 * (0.08 ** 2))) * np.exp(-((y + 0.05) ** 2) / (2.0 * (0.06 ** 2)))
    eye2 = np.exp(-((x - 0.22) ** 2) / (2.0 * (0.08 ** 2))) * np.exp(-((y + 0.05) ** 2) / (2.0 * (0.06 ** 2)))

    relief = face + 0.55 * nose - 0.35 * (eye1 + eye2)
    relief = clamp01(relief)

    gy, gx = np.gradient(relief)
    nx = -gx
    ny = -gy
    nz = np.ones_like(nx) * 0.9
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    nx, ny, nz = nx / norm, ny / norm, nz / norm

    Lw = np.array([-0.6, -0.1, 0.8], dtype=np.float32)
    Lc = np.array([0.7, 0.05, 0.5], dtype=np.float32)
    Lw = Lw / (np.linalg.norm(Lw) + 1e-6)
    Lc = Lc / (np.linalg.norm(Lc) + 1e-6)

    dot_w = clamp01(nx * Lw[0] + ny * Lw[1] + nz * Lw[2])
    dot_c = clamp01(nx * Lc[0] + ny * Lc[1] + nz * Lc[2])

    skin = np.array([0.70, 0.52, 0.44], dtype=np.float32)
    warm = np.array([1.0, 0.62, 0.28], dtype=np.float32)
    cool = np.array([0.18, 0.70, 1.0], dtype=np.float32)

    rgb = np.zeros((h, w, 3), dtype=np.float32)
    rgb[..., 0] = 2 / 255.0
    rgb[..., 1] = 2 / 255.0
    rgb[..., 2] = 6 / 255.0

    mask = (face > 0.02).astype(np.float32)[..., None]
    base_col = skin[None, None, :] * relief[..., None]
    light_w = warm[None, None, :] * (dot_w[..., None] ** 1.3)
    light_c = cool[None, None, :] * (dot_c[..., None] ** 1.6) * 0.75

    shaded = base_col * 0.85 + light_w * 0.65 + light_c * 0.55

    n = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    pores = (n - 0.5) * 0.06
    shaded = clamp01(shaded + pores[..., None] * (relief[..., None] ** 1.2))

    rgb = clamp01(rgb * (1.0 - mask) + shaded * mask)
    v = soft_vignette(h, w, strength=0.30)[:, :, None]
    rgb = clamp01(rgb * v)
    rgb = add_noise(rgb, amount=0.010, seed=seed + 31)
    return Image.fromarray(to_uint8(rgb), mode="RGB")


def make_combustion_vector(w: int, h: int, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    x = (xx / (w - 1)).astype(np.float32)
    y = (yy / (h - 1)).astype(np.float32)

    rgb = np.zeros((h, w, 3), dtype=np.float32)
    rgb[..., 0] = 8 / 255.0
    rgb[..., 1] = 10 / 255.0
    rgb[..., 2] = 14 / 255.0

    def cylinder_field(cx, cy, radius, angle_deg, length=1.2):
        ang = math.radians(angle_deg)
        xr = (x - cx) * math.cos(ang) + (y - cy) * math.sin(ang)
        yr = -(x - cx) * math.sin(ang) + (y - cy) * math.cos(ang)
        ax = np.exp(-((xr / (0.55 * length)) ** 8))
        d = np.abs(yr)
        cyl = np.exp(-(d ** 2) / (2.0 * (radius ** 2))) * ax
        return cyl, xr, yr

    cylinders = [
        (0.35, 0.35, 0.035, -25),
        (0.52, 0.40, 0.040, -25),
        (0.66, 0.52, 0.045, -25),
        (0.42, 0.62, 0.030, -25),
    ]

    steel_base = np.array([0.35, 0.37, 0.40], dtype=np.float32)
    highlight = np.array([0.90, 0.92, 0.95], dtype=np.float32)
    warm_spec = np.array([0.95, 0.55, 0.20], dtype=np.float32)

    for i, (cx, cy, r, ang) in enumerate(cylinders):
        cyl, xr, yr = cylinder_field(cx, cy, r, ang)
        ridge = np.exp(-((yr) ** 2) / (2.0 * ((r * 0.25) ** 2))) * np.exp(-((xr) ** 2) / (2.0 * (0.18 ** 2)))
        shade = 0.20 + 0.80 * cyl
        base = steel_base[None, None, :] * shade[..., None]
        spec = (ridge ** 1.4) * 0.85
        col = base + highlight[None, None, :] * spec[..., None] * 0.85

        if i % 2 == 0:
            gl = np.exp(-((xr + 0.08) ** 2) / (2.0 * (0.10 ** 2))) * np.exp(-((yr) ** 2) / (2.0 * ((r * 0.18) ** 2)))
            col = clamp01(col + warm_spec[None, None, :] * (gl[..., None] * 0.20))

        rgb = screen_blend(rgb, col, opacity=0.85)

    n = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    tex = Image.fromarray((n * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=1))
    tex01 = np.asarray(tex).astype(np.float32) / 255.0
    tex_rgb = np.stack([tex01, tex01, tex01], axis=2)
    rgb = overlay_blend(rgb, tex_rgb, opacity=0.14)

    arr = to_uint8(rgb)
    img = Image.fromarray(arr, mode="RGB")

    v = (soft_vignette(h, w, strength=0.20) * 255.0).astype(np.uint8)
    vig = Image.fromarray(v, mode="L")
    img = ImageChops.multiply(img, Image.merge("RGB", (vig, vig, vig)))

    out = np.asarray(img).astype(np.float32) / 255.0
    out = add_noise(out, amount=0.010, seed=seed + 41)
    return Image.fromarray(to_uint8(out), mode="RGB")


# -----------------------------
# Saving
# -----------------------------

def save_png(img: Image.Image, path: str, dpi: int):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format="PNG", optimize=True, dpi=(dpi, dpi))


# -----------------------------
# Test sheet generator (matched layout)
# -----------------------------

def make_testsheet(cfg: SeriesConfig, dpi: int, size_in: str, tiles: List[Image.Image]) -> Image.Image:
    """
    Matched diagnostic layout so 6x8 and 8x12 results compare well.
    For 6x8, microtext gets smaller and may be partially omitted if space is tight.
    """
    w, h = parse_size_inches(size_in, dpi)
    sheet = Image.new("RGB", (w, h), (8, 8, 12))
    d = ImageDraw.Draw(sheet)

    # Size-aware typography
    font_title = try_get_font(28 if size_in == "6x8" else 34)
    font_small = try_get_font(14 if size_in == "6x8" else 18)

    margin = int(round(dpi * (0.18 if size_in == "6x8" else 0.25)))
    gap = int(round(dpi * (0.10 if size_in == "6x8" else 0.15)))

    # Header
    d.text((margin, margin // 2), f"{cfg.series_id} TESTSHEET {size_in}", fill=(235, 235, 235), font=font_title)
    d.text(
        (margin, margin // 2 + (36 if size_in == "6x8" else 44)),
        f"{cfg.printer} | {cfg.substrate} | {cfg.temp_f}F {cfg.dwell_s}s | {cfg.pressure} | {cfg.icc_profile} | {cfg.curve_version} | SCALE 100% | MIRROR YES",
        fill=(200, 200, 200),
        font=font_small
    )

    header_h = int(round(dpi * (0.80 if size_in == "6x8" else 0.95)))
    y0 = header_h

    # 2x2 tile grid
    tile_area_w = w - 2 * margin
    tile_area_h = int(h * (0.50 if size_in == "6x8" else 0.58))
    tile_w = (tile_area_w - gap) // 2
    tile_h = (tile_area_h - gap) // 2

    positions = [
        (margin, y0),
        (margin + tile_w + gap, y0),
        (margin, y0 + tile_h + gap),
        (margin + tile_w + gap, y0 + tile_h + gap),
    ]

    for i in range(4):
        img = tiles[i].copy().resize((tile_w, tile_h), resample=Image.LANCZOS)
        sheet.paste(img, positions[i])

    # Diagnostics
    diag_y = y0 + tile_area_h + gap
    ramp_h = int(round(dpi * (0.20 if size_in == "6x8" else 0.30)))
    ramp_w = tile_area_w

    ramp1 = make_gray_ramp(ramp_w, ramp_h, 0.00, 0.12)  # shadow floor
    ramp2 = make_gray_ramp(ramp_w, ramp_h, 0.12, 1.00)  # mid to highlights
    sheet.paste(ramp1, (margin, diag_y))
    sheet.paste(ramp2, (margin, diag_y + ramp_h + 6))

    blocks = make_color_blocks(block=int(round(dpi * (0.14 if size_in == "6x8" else 0.22))))
    blocks_y = diag_y + 2 * ramp_h + 14
    if blocks.size[0] <= ramp_w and (blocks_y + blocks.size[1] < h - margin):
        sheet.paste(blocks, (margin, blocks_y))

    micro_y = blocks_y + blocks.size[1] + 8
    micro_h = h - micro_y - margin
    micro_w = int(tile_area_w * 0.58)

    # Microtext panel (always on 8x12; conditional on 6x8)
    if size_in == "8x12" and micro_h > 160:
        micro = draw_microtext_panel(micro_w, micro_h)
        sheet.paste(micro, (margin + tile_area_w - micro_w, micro_y))
    elif size_in == "6x8" and micro_h > 140:
        micro = draw_microtext_panel(micro_w, micro_h)
        sheet.paste(micro, (margin + tile_area_w - micro_w, micro_y))

    # Bottom hidden calibration
    sheet = draw_bottom_calibration_band(sheet, dpi=dpi, band_mm=4.0, steps=(0, 3, 5, 7, 10), patch_mm=2.0, blend_strength=0.10)
    return sheet


# -----------------------------
# CSV Exports
# -----------------------------

def write_csv(path: str, headers: List[str], rows: List[List[str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)


def make_exports(out_dir: str, cfg: SeriesConfig, artworks: List[Dict[str, str]]):
    p1 = os.path.join(out_dir, f"{cfg.series_id}_CONTROLLED_AESTHETIC_EXPORT.csv")
    headers1 = [
        "SeriesID","SeriesName","Artwork","FileName","Printer","InkType","ColorSpace","BitDepth",
        "Substrate","Temp","Dwell","Pressure","ICC_Profile","CurveVersion","MasterSize","TestSizePrimary","TestSizeValidation"
    ]
    rows1 = []
    for a in artworks:
        rows1.append([
            cfg.series_id, cfg.series_name, a["Artwork"], a["FileName"],
            cfg.printer, cfg.ink_type, cfg.color_space, str(cfg.bit_depth),
            cfg.substrate, str(cfg.temp_f), str(cfg.dwell_s), cfg.pressure, cfg.icc_profile, cfg.curve_version,
            "8x12", "6x8", "8x12"
        ])
    write_csv(p1, headers1, rows1)

    p2 = os.path.join(out_dir, f"{cfg.series_id}_PRINT_RUNS_TEMPLATE.csv")
    headers2 = [
        "RunID","SeriesID","Date","Operator",
        "Printer","InkType","Substrate","PaperType",
        "PrintSize","DriverQuality","Scaling","Mirror","Borderless",
        "ICC_Profile","CurveVersion","TempF","DwellSec","Pressure",
        "Humidity","AmbientTemp","Notes"
    ]
    rows2 = [[
        "", cfg.series_id, "", "",
        cfg.printer, cfg.ink_type, cfg.substrate, "Glossy",
        "6x8", "Best/High", "100%", "Yes", "No",
        cfg.icc_profile, cfg.curve_version, str(cfg.temp_f), str(cfg.dwell_s), cfg.pressure,
        "", "", ""
    ]]
    write_csv(p2, headers2, rows2)

    p3 = os.path.join(out_dir, f"{cfg.series_id}_SCORECARD_TEMPLATE.csv")
    headers3 = [
        "RunID","SeriesID","PrintSize","Artwork","FileName",
        "ShadowSeparation_1to5","Banding_0to5","SaturationControl_1to5","EdgeClarity_1to5",
        "SkinNeutrality_1to5","Overall_1to5",
        "PassFail","ObservedIssues","Notes"
    ]
    rows3 = []
    for a in artworks:
        rows3.append(["", cfg.series_id, "6x8", a["Artwork"], a["FileName"], "", "", "", "", "", "", "", "", ""])
    write_csv(p3, headers3, rows3)

    p4 = os.path.join(out_dir, f"{cfg.series_id}_PATCH_MEASUREMENTS_TEMPLATE.csv")
    headers4 = ["RunID","SeriesID","PrintSize","Artwork","PatchName","ExpectedRGB","MeasuredRGB","DeltaNotes"]
    patch_defs = [
        ("BlackPatch", "10,10,10"),
        ("Gray18Patch", "118,118,118"),
        ("Step_0pct", "0,0,0"),
        ("Step_3pct", "8,8,8"),
        ("Step_5pct", "13,13,13"),
        ("Step_7pct", "18,18,18"),
        ("Step_10pct","26,26,26"),
    ]
    rows4 = []
    for a in artworks:
        for pn, exp in patch_defs:
            rows4.append(["", cfg.series_id, "6x8", a["Artwork"], pn, exp, "", ""])
    write_csv(p4, headers4, rows4)


# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="INFUSIST_SERIES_001_GLOSSY", help="Output folder")
    ap.add_argument("--dpi", type=int, default=300, help="DPI for export")
    ap.add_argument("--seed", type=int, default=2400, help="Seed for deterministic generation")
    ap.add_argument("--master_size", default="8x12", help='Master size in inches (default 8x12)')
    ap.add_argument("--test_primary", default="6x8", help='Primary test size (default 6x8)')
    ap.add_argument("--test_validation", default="8x12", help='Validation test size (default 8x12)')
    args = ap.parse_args()

    dpi = args.dpi
    cfg = SeriesConfig()
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    # Masters
    mw, mh = parse_size_inches(args.master_size, dpi)

    items = [
        ("Nocturne Steel", f"{cfg.series_id}_NOCTURNE_STEEL_v1.png", make_nocturne_steel),
        ("Fused Current", f"{cfg.series_id}_FUSED_CURRENT_v1.png", make_fused_current),
        ("Human Fraction", f"{cfg.series_id}_HUMAN_FRACTION_v1.png", make_human_fraction),
        ("Combustion Vector", f"{cfg.series_id}_COMBUSTION_VECTOR_v1.png", make_combustion_vector),
    ]

    artworks_meta = []
    masters_for_sheet: List[Image.Image] = []

    for idx, (name, filename, fn) in enumerate(items):
        print(f"Generating master: {name} -> {filename}")
        img = fn(mw, mh, seed=args.seed + idx * 1000)
        img = draw_bottom_calibration_band(img, dpi=dpi, band_mm=4.0, steps=(0, 3, 5, 7, 10), patch_mm=2.0, blend_strength=0.10)
        img = set_dpi(img, dpi=dpi)
        save_png(img, os.path.join(out_dir, filename), dpi=dpi)

        artworks_meta.append({"Artwork": name, "FileName": filename})
        masters_for_sheet.append(img)

    # Test sheets
    print(f"Generating test sheets ({args.test_primary} + {args.test_validation})...")
    sheet_primary = make_testsheet(cfg, dpi=dpi, size_in=args.test_primary, tiles=masters_for_sheet)
    sheet_primary = set_dpi(sheet_primary, dpi=dpi)
    save_png(sheet_primary, os.path.join(out_dir, f"{cfg.series_id}_TESTSHEET_{args.test_primary.replace('.','p')}_v1.png"), dpi=dpi)

    sheet_val = make_testsheet(cfg, dpi=dpi, size_in=args.test_validation, tiles=masters_for_sheet)
    sheet_val = set_dpi(sheet_val, dpi=dpi)
    save_png(sheet_val, os.path.join(out_dir, f"{cfg.series_id}_TESTSHEET_{args.test_validation.replace('.','p')}_v1.png"), dpi=dpi)

    # CSV exports
    print("Writing CSV exports...")
    make_exports(out_dir, cfg, artworks_meta)

    print("\nDONE.")
    print(f"Output folder: {os.path.abspath(out_dir)}")
    print("Reminder: Print tests at 100% scale, Mirror=Yes, Borderless=No for apples-to-apples comparisons.")


if __name__ == "__main__":
    main()