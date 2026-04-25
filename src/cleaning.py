"""
cleaning.py
Cleans all four raw datasets and saves processed outputs to data/processed/.
"""
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from utils import rename_columns, ubigeo_to_str

ROOT          = Path(__file__).parent.parent
RAW_DIR       = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_ipress():
    df = pd.read_excel(RAW_DIR / "TB_IPRESS.xlsx")
    df = rename_columns(df)

    cols = ["codigo_unico", "nombre_del_establecimiento", "clasificacion",
            "categoria", "departamento", "provincia", "distrito",
            "ubigeo", "norte", "este", "estado", "camas"]
    df = df[[c for c in cols if c in df.columns]]

    df["ubigeo"] = ubigeo_to_str(df["ubigeo"])

    # Eliminar coordenadas inválidas (0,0) y duplicados
    df = df[~((df["norte"] == 0) & (df["este"] == 0))]
    df = df.drop_duplicates(subset=["codigo_unico"])

    df.to_csv(PROCESSED_DIR / "ipress_clean.csv", index=False)
    print(f"IPRESS limpio: {df.shape} → ipress_clean.csv")
    return df


def clean_emergencias():
    frames = []
    for f in sorted(RAW_DIR.glob("Produccion*.csv")):
        frames.append(pd.read_csv(f, encoding="latin1"))
    df = pd.concat(frames, ignore_index=True)
    df = rename_columns(df)

    # Valores suprimidos NE_XXXX → NaN
    ne_cols = ["nro_total_atenciones", "nro_total_atendidos"]
    for col in ne_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ubigeo"] = ubigeo_to_str(df["ubigeo"])

    dup_cols = ["anho", "mes", "ubigeo", "co_ipress", "sexo", "edad"]
    df = df.drop_duplicates(subset=[c for c in dup_cols if c in df.columns])

    df.to_csv(PROCESSED_DIR / "emergencias_clean.csv", index=False)
    print(f"Emergencias limpio: {df.shape} → emergencias_clean.csv")
    return df


def clean_centros_poblados():
    path = next(RAW_DIR.glob("*entros*oblados*"))
    gdf = gpd.read_file(path)
    gdf = rename_columns(gdf)

    # Extraer UBIGEO de los primeros 6 caracteres de CÓDIGO
    cod_col = next((c for c in gdf.columns if "codigo" in c or "c_digo" in c), None)
    if cod_col:
        gdf["ubigeo"] = gdf[cod_col].astype(str).str[:6]

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.set_crs(epsg=4326)

    gdf = gdf.drop_duplicates()
    gdf.to_file(PROCESSED_DIR / "centros_poblados_clean.gpkg", driver="GPKG")
    print(f"Centros Poblados limpio: {gdf.shape} → centros_poblados_clean.gpkg")
    return gdf


def clean_distritos():
    path = next(RAW_DIR.glob("*ISTRITO*"))
    gdf = gpd.read_file(path)
    gdf = rename_columns(gdf)

    # Renombrar IDDIST → ubigeo
    if "iddist" in gdf.columns:
        gdf = gdf.rename(columns={"iddist": "ubigeo"})

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf.to_file(PROCESSED_DIR / "distritos_clean.gpkg", driver="GPKG")
    print(f"Distritos limpio: {gdf.shape} → distritos_clean.gpkg")
    return gdf


if __name__ == "__main__":
    print("=== Limpieza de datos ===")
    clean_ipress()
    clean_emergencias()
    clean_centros_poblados()
    clean_distritos()
    print("=== Listo ===")
