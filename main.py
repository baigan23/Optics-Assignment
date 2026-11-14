"""Fraunhofer Diffraction - Virtual Optics Lab

Simulates four aperture shapes by computing a 2-D Fourier transform,
then checks the simulated horizontal intensity against the theoretical curve.

Run: python main.py
Input: input.json
Output: outputs/figures, outputs/data, outputs/summary.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Save figures without requiring a graphical display.
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import j1

BASE_DIR = Path(__file__).resolve().parent
FIGURE_DIR = BASE_DIR / "outputs" / "figures"
DATA_DIR = BASE_DIR / "outputs" / "data"
NAMES = {
    "single_slit": "Single slit",
    "double_slit": "Double slit",
    "rectangle": "Rectangular aperture",
    "circular": "Circular aperture",
}


def read_input():
    """Load the experiment values and check that they are sensible."""
    with (BASE_DIR / "input.json").open(encoding="utf-8") as file:
        p = json.load(file)
    if p["grid_points"] < 128 or p["grid_points"] % 2:
        raise ValueError("grid_points must be an even integer >= 128")
    for key in ("wavelength_nm", "screen_distance_m", "aperture_window_mm"):
        if p[key] <= 0:
            raise ValueError(f"{key} must be positive")
    return p


def make_aperture(name, X, Y, p):
    """Return 1 inside an open aperture, and 0 outside it."""
    mm = 1e-3
    if name == "single_slit":
        width = p[name]["width_mm"] * mm
        return (np.abs(X) <= width / 2).astype(float)
    if name == "double_slit":
        width = p[name]["slit_width_mm"] * mm
        separation = p[name]["slit_separation_mm"] * mm
        left = np.abs(X + separation / 2) <= width / 2
        right = np.abs(X - separation / 2) <= width / 2
        return (left | right).astype(float)
    if name == "rectangle":
        width = p[name]["width_mm"] * mm
        height = p[name]["height_mm"] * mm
        return ((np.abs(X) <= width / 2) & (np.abs(Y) <= height / 2)).astype(float)
    if name == "circular":
        radius = p[name]["diameter_mm"] * mm / 2
        return ((X * X + Y * Y) <= radius * radius).astype(float)
    raise ValueError(f"Unknown aperture: {name}")


def theoretical_curve(name, frequency, p):
    """Expected normalized intensity along the horizontal screen axis."""
    mm = 1e-3
    if name == "single_slit":
        a = p[name]["width_mm"] * mm
        return np.sinc(a * frequency) ** 2
    if name == "double_slit":
        a = p[name]["slit_width_mm"] * mm
        d = p[name]["slit_separation_mm"] * mm
        return np.sinc(a * frequency) ** 2 * np.cos(np.pi * d * frequency) ** 2
    if name == "rectangle":
        a = p[name]["width_mm"] * mm
        return np.sinc(a * frequency) ** 2  # Horizontal slice: y = 0.
    if name == "circular":
        diameter = p[name]["diameter_mm"] * mm
        u = np.pi * diameter * np.abs(frequency)
        result = np.ones_like(u)
        nonzero = u != 0
        result[nonzero] = (2 * j1(u[nonzero]) / u[nonzero]) ** 2
        return result
    raise ValueError(f"Unknown aperture: {name}")


def save_csv(name, screen_mm, simulated, expected):
    """Store the numerical result and the theory for easy inspection."""
    destination = DATA_DIR / f"{name}_profile.csv"
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["screen_x_mm", "simulated_intensity_normalized", "theory_intensity_normalized"])
        writer.writerows(zip(screen_mm, simulated, expected))


def save_pattern_plot(name, screen_mm, intensity, simulated, expected, half_width):
    """Show 2-D diffraction on the left and a 1-D check on the right."""
    display = np.abs(screen_mm) <= half_width
    crop = intensity[np.ix_(display, display)]
    x = screen_mm[display]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), layout="constrained")
    # A logarithmic colour scale makes weak diffraction rings easier to see.
    db = 10 * np.log10(np.maximum(crop, 1e-6))
    image = axes[0].imshow(
        db, origin="lower", extent=[x[0], x[-1], x[0], x[-1]],
        cmap="magma", vmin=-45, vmax=0, aspect="equal"
    )
    axes[0].set_title("2-D diffraction pattern")
    axes[0].set_xlabel("Position on screen, x (mm)")
    axes[0].set_ylabel("Position on screen, y (mm)")
    cbar = fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.04)
    cbar.set_label("Relative intensity (dB)")

    axes[1].plot(screen_mm[display], simulated[display], label="Simulated (FFT)", lw=2)
    axes[1].plot(screen_mm[display], expected[display], "--", label="Theory", lw=1.8)
    axes[1].set_title("Horizontal intensity profile")
    axes[1].set_xlabel("Position on screen, x (mm)")
    axes[1].set_ylabel("Normalized intensity")
    axes[1].set_ylim(-0.04, 1.06)
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="upper right", fontsize=9)
    fig.suptitle(NAMES[name], fontsize=14, fontweight="bold")
    fig.savefig(FIGURE_DIR / f"{name}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_overview(results, screen_mm, half_width):
    """One-page visual comparison of all four diffraction patterns."""
    display = np.abs(screen_mm) <= half_width
    x = screen_mm[display]
    fig, axes = plt.subplots(2, 2, figsize=(9, 8), layout="constrained")
    for ax, (name, intensity) in zip(axes.flat, results.items()):
        crop = intensity[np.ix_(display, display)]
        db = 10 * np.log10(np.maximum(crop, 1e-6))
        ax.imshow(db, origin="lower", cmap="magma", vmin=-45, vmax=0,
                  extent=[x[0], x[-1], x[0], x[-1]])
        ax.set_title(NAMES[name], fontweight="bold")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
    fig.suptitle("Fraunhofer diffraction: four aperture shapes", fontsize=14, fontweight="bold")
    fig.savefig(FIGURE_DIR / "all_patterns.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_width_study(screen_mm, p):
    """A small extra experiment: wider slit -> narrower central maximum."""
    wavelength = p["wavelength_nm"] * 1e-9
    z = p["screen_distance_m"]
    frequency = (screen_mm * 1e-3) / (wavelength * z)
    fig, ax = plt.subplots(figsize=(8.2, 4.3), layout="constrained")
    for width_mm in (0.07, 0.10, 0.14):
        curve = np.sinc(width_mm * 1e-3 * frequency) ** 2
        ax.plot(screen_mm, curve, lw=2, label=f"Slit width = {width_mm:.2f} mm")
    ax.set_xlim(-25, 25)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Position on screen (mm)")
    ax.set_ylabel("Normalized intensity")
    ax.set_title("Effect of slit width on diffraction")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(FIGURE_DIR / "slit_width_study.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    p = read_input()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    wavelength = p["wavelength_nm"] * 1e-9
    z = p["screen_distance_m"]
    n = p["grid_points"]
    window = p["aperture_window_mm"] * 1e-3
    dx = window / n
    aperture_axis = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(aperture_axis, aperture_axis)

    # Spatial frequency in the aperture is mapped to a screen location.
    fx = np.fft.fftshift(np.fft.fftfreq(n, d=dx))
    screen_mm = wavelength * z * fx * 1e3
    display_limit = p["plot_half_width_mm"]
    central_region = np.abs(screen_mm) <= 30.0

    overview = {}
    metrics = {}
    for name in NAMES:
        aperture = make_aperture(name, X, Y, p)
        field = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(aperture)))
        intensity = np.abs(field) ** 2
        intensity /= intensity.max()  # All plots use maximum intensity = 1.
        simulated = intensity[n // 2, :]
        expected = theoretical_curve(name, fx, p)

        rmse = float(np.sqrt(np.mean((simulated[central_region] - expected[central_region]) ** 2)))
        metrics[name] = {"rmse_central_30mm": round(rmse, 6)}
        save_csv(name, screen_mm, simulated, expected)
        save_pattern_plot(name, screen_mm, intensity, simulated, expected, display_limit)
        overview[name] = intensity
        print(f"{NAMES[name]:22s} | RMSE (±30 mm) = {rmse:.6f}")

    save_overview(overview, screen_mm, display_limit)
    save_width_study(screen_mm, p)

    # Useful predicted positions for discussion in the report.
    single_width = p["single_slit"]["width_mm"] * 1e-3
    slit_distance = p["double_slit"]["slit_separation_mm"] * 1e-3
    rectangle_width = p["rectangle"]["width_mm"] * 1e-3
    circular_diameter = p["circular"]["diameter_mm"] * 1e-3
    metrics["predictions"] = {
        "single_slit_first_minimum_mm": round(wavelength * z / single_width * 1e3, 3),
        "double_slit_fringe_spacing_mm": round(wavelength * z / slit_distance * 1e3, 3),
        "rectangle_horizontal_first_minimum_mm": round(wavelength * z / rectangle_width * 1e3, 3),
        "circular_first_dark_ring_mm": round(1.22 * wavelength * z / circular_diameter * 1e3, 3),
    }
    metrics["input"] = p
    with (BASE_DIR / "outputs" / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
    print("\nDone. See outputs/figures, outputs/data, and outputs/summary.json")


if __name__ == "__main__":
    main()
