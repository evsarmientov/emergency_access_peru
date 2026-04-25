# Emergency Healthcare Access Inequality in Peru

Geospatial analytics pipeline to study emergency healthcare access inequality across districts in Peru.

**Live app:** [https://evsarmientov-emergency-access-peru-app-rbwaw6.streamlit.app/](https://evsarmientov-emergency-access-peru-app-rbwaw6.streamlit.app/)

---

## What does the project do?

This project builds a district-level emergency healthcare access index for Peru by combining four public datasets: health facilities (IPRESS), emergency care activity, populated centers, and district boundaries. The pipeline integrates data cleaning, geospatial joins, distance calculations, index construction, static visualizations, interactive maps, and a Streamlit dashboard.

---

## Main analytical goal

To answer which districts in Peru appear relatively better or worse served in emergency healthcare access, and what evidence supports that conclusion. The project addresses four required analytical questions:

- **Q1:** Which districts have lower or higher availability of health facilities and emergency care activity?
- **Q2:** Which districts have populated centers with weaker spatial access to emergency-related health services?
- **Q3:** Which districts appear most underserved or best served when combining all three dimensions?
- **Q4:** How much do results change if the analytical definition of access changes?

---

## Datasets used

| Dataset | Source | Rows (raw) | Description |
|---|---|---|---|
| IPRESS | MINSA | 20,819 | Health facilities with category, coordinates, and beds |
| Producción Asistencial en Emergencia | MINSA | 1,046,838 | Emergency care activity by IPRESS, month and year (2022–2025) |
| Centros Poblados | INEI | 136,587 | Populated centers with geographic coordinates |
| Distritos | INEI | 1,873 | District boundary polygons with UBIGEO code |

All datasets use **CRS EPSG:4326 (WGS84)**. The common identifier is the **UBIGEO**: a 6-digit code (2 department + 2 province + 2 district).

---

## Data cleaning

### IPRESS
- Removed 3 records with coordinates (0°, 0°) — geographically invalid
- Removed 26 duplicates by unique facility code
- Only 7,941 of 20,790 facilities have valid coordinates (38%)
- Facility level extracted from `categoria` using `split("-")[0]` (e.g. "II-1" → "II")
- Output: `data/processed/ipress_clean.csv`

### Emergency care activity
- Values `NE_XXXX` (statistically suppressed by MINSA for confidentiality) treated as `NaN` — not missing data
- Duplicates removed by `[year, month, ubigeo, ipress_code, sex, age]`
- 683 districts with no emergency data receive `comp2 = 0`
- Output: `data/processed/emergencias_clean.csv`

### Populated centers
- UBIGEO extracted from first 6 characters of `CÓDIGO` field
- 645 duplicates removed → 135,942 valid centers
- 218 centers (0.16%) unassigned after all join methods
- Output: `data/processed/centros_poblados_clean.gpkg`

### Districts
- No invalid records — 1,873 complete polygons
- `IDDIST` renamed to `ubigeo` for compatibility
- CRS verified: EPSG:4326
- Output: `data/processed/distritos_clean.gpkg`

---

## District-level metric construction

The index combines three normalized components with equal weights:

| # | Component | Formula | Question |
|---|---|---|---|
| 1 | **Availability** | IPRESS count / populated centers in district | Q1 |
| 2 | **Activity** | Total emergency visits / reporting IPRESS | Q1 |
| 3 | **Spatial access** | % of populated centers within X km of an IPRESS | Q2 |

**Final score = (comp1_norm + comp2_norm + comp3_norm) / 3**

All components are normalized using min-max scaling to [0, 1] before averaging.

**Why equal weights?** No empirical evidence exists to assign differential weights. Equal weighting is the most transparent and replicable option.

**Why min-max?** Allows comparison across components with different scales without assuming normality. Limitation: sensitive to extreme outliers (e.g. Lima with 620,000 visits/IPRESS).

**Spatial distances** are computed using `scipy.spatial.cKDTree` on decimal degree coordinates. Approximate conversion: 1° ≈ 111 km (valid for Peru's latitude range; does not account for terrain or road networks).

### Sensitivity analysis (Q4)

Two versions of the index were built by varying the spatial access threshold:

| Version | Threshold | % of centers with access (avg) |
|---|---|---|
| Baseline | 5 km | 31.3% |
| Alternative | 15 km | 43.2% |

1,191 of 1,873 districts (63.6%) show no change between versions. The spatial threshold was chosen as the sensitivity parameter because it has the highest methodological uncertainty — no empirical evidence exists for what constitutes a "reasonable" distance in Peru's diverse geography.

### Classification

Districts are classified into terciles by baseline score:
- **Subatendido** (bottom third)
- **Acceso medio** (middle third)
- **Mejor atendido** (top third)

---

## How to install dependencies

> **Important:** GeoPandas requires a conda environment for correct installation of spatial dependencies on Windows.

```bash
# 1. Create and activate the environment
conda create -n emergency_peru python=3.11
conda activate emergency_peru

# 2. Install GeoPandas and spatial stack via conda-forge
conda install -c conda-forge geopandas

# 3. Install remaining dependencies
pip install -r requirements.txt
```

---

## How to run the processing pipeline

Run the notebooks in order from the `src/` folder:

```bash
# 1. Data exploration
jupyter notebook src/data_loader.ipynb

# 2. Data cleaning
jupyter notebook src/cleaning.ipynb

# 3. Geospatial integration
jupyter notebook src/geospatial.ipynb

# 4. Metric construction
jupyter notebook src/metrics.ipynb

# 5. Visualizations and outputs
jupyter notebook src/visualization.ipynb
```

All processed outputs are saved to `data/processed/` and `output/`.

---

## How to run the Streamlit app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` and contains 4 tabs:
- **Data & Methodology** — problem statement, sources, cleaning decisions, index construction, limitations
- **Static Analysis** — 5 charts with methodological justification
- **GeoSpatial Results** — static maps and interactive district table
- **Interactive Exploration** — Folium maps and baseline vs alternative comparison by department

---

## Main findings

- Emergency healthcare access in Peru is **extremely unequal**: the top district (Arequipa city, score 0.72) has a score more than 5 orders of magnitude above the bottom districts (score ~10⁻⁶).
- **Median score = 0.012** — more than half of Peru's districts have essentially no measurable access by this index.
- The departments with highest average access are **Apurímac, Junín, and Ica** — not Lima, despite Lima concentrating the best hospitals. Lima's 171 highly heterogeneous districts (from San Isidro to rural Huarochirí) drag the departmental average below the national mean.
- The **northeastern Amazon** (Loreto, Amazonas, Ucayali) shows the lowest spatial access — populated centers are highly dispersed and far from any IPRESS with recorded coordinates.
- The **spatial access component** (comp3) drives most of the observable geographic variation in the composite score. Components 1 and 2 are heavily influenced by extreme outliers that compress most districts toward zero after min-max normalization.
- Expanding the threshold from 5 to 15 km helps **districts with marginal access** (peri-urban and mid-sierra areas) but does not change the ranking of the best or worst served districts.

---

## Main limitations

- **62% of IPRESS lack coordinates** → spatial access underestimates real coverage.
- **NE_XXXX suppressed values** (~13.3% of emergency records) may introduce bias in rural areas where small facilities are more likely suppressed.
- **Degree-to-km conversion is a flat approximation** — does not account for Andean terrain, road networks, or river transit times in the Amazon.
- **No population data** available at district level → the index is not weighted by number of inhabitants.
- **Equal component weights** are a methodological choice, not empirically derived.
- **Min-max normalization is outlier-sensitive**: Lima's extreme emergency activity compresses all other districts toward zero in comp2.
- The index measures **relative access within Peru** — it does not benchmark against any absolute standard of adequate healthcare coverage.
