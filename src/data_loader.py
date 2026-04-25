"""
data_loader.py
Loads and summarizes the four raw datasets used in the project.
"""
import pandas as pd
import geopandas as gpd
from pathlib import Path

ROOT    = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"


def load_ipress():
    path = RAW_DIR / "TB_IPRESS.xlsx"
    df = pd.read_excel(path)
    print(f"IPRESS: {df.shape} | cols: {df.columns.tolist()}")
    return df


def load_emergencias():
    frames = []
    for f in sorted(RAW_DIR.glob("*.csv")):
        if "emergencia" in f.name.lower() or "produccion" in f.name.lower():
            frames.append(pd.read_csv(f, encoding="latin1"))
    df = pd.concat(frames, ignore_index=True)
    print(f"Emergencias: {df.shape}")
    return df


def load_centros_poblados():
    path = next(RAW_DIR.glob("*entros*oblados*"))
    gdf = gpd.read_file(path)
    print(f"Centros Poblados: {gdf.shape} | CRS: {gdf.crs}")
    return gdf


def load_distritos():
    path = next(RAW_DIR.glob("*ISTRITOS*"))
    gdf = gpd.read_file(path)
    print(f"Distritos: {gdf.shape} | CRS: {gdf.crs}")
    return gdf


if __name__ == "__main__":
    print("=== Cargando datasets ===")
    load_ipress()
    load_centros_poblados()
    load_distritos()
    print("=== Listo ===")
