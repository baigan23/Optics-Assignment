# Fraunhofer Diffraction - Virtual Optics Lab

**Physics programming assignment | Python**

This project simulates how light spreads after passing through different openings (apertures). It studies a **single slit, double slit, rectangular aperture, and circular aperture** using a **2D Fast Fourier Transform (FFT)** and compares the simulated intensity with theoretical formulas.

## Files

- `YOUR_ROLL_NUMBER.pdf` - report in simple language, with formulas, actual results and complete source code as an appendix.
- `main.py` - full standalone Python program.
- `input.json` - editable physical parameters.
- `requirements.txt` - required Python libraries.
- `outputs/figures/` - generated patterns and intensity-curve PNGs.
- `outputs/data/` - numerical and theoretical intensity CSV files.
- `outputs/summary.json` - computed errors and predicted fringe positions.
- `EXPLAIN_IN_VIVA.md` - a short script and common oral questions.

## Run it 

1. Install Python 3.10 or later, if needed.
2. Open a terminal in this project folder.
3. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run the simulation:

   ```bash
   python main.py
   ```

All figures, numeric CSVs, and summary results will be saved inside `outputs/`.

## Edit experiment parameters

Open `input.json`. You can change `wavelength_nm`, `screen_distance_m`, the sizes of the apertures and other listed values. Run the code again to regenerate outputs. Keep the aperture sizes substantially smaller than `aperture_window_mm` and keep the grid fine enough to represent the openings accurately. The graphs are normalized so each pattern has a maximum intensity of 1.

 
 
**Note:** The program uses a simplified ideal optical model: coherent monochromatic light, a plane wave, a screen in the far-field region, and no absorption or lens imperfections.
