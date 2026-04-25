"""
metrics.py
Builds the district-level emergency access index with baseline and alternative specifications.
"""
import pandas as pd
import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
from pathlib import Path

ROOT          = Path(__file__).parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"


def minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return series * 0
    return (series - mn) / (mx - mn)


def calc_spatial_access(df_cp: pd.DataFrame, df_ipress: pd.DataFrame, umbral_km: float) -> pd.DataFrame:
    umbral_grados = umbral_km / 111.0
    ipress_coords = df_ipress[["norte", "este"]].values
    tree = cKDTree(ipress_coords)

    cp_valid = df_cp.dropna(subset=["x", "y", "ubigeo"]).copy()
    distancias, _ = tree.query(cp_valid[["x", "y"]].values, k=1)
    cp_valid["tiene_acceso"] = distancias <= umbral_grados

    acceso = cp_valid.groupby("ubigeo").agg(
        n_cp=("tiene_acceso", "count"),
        n_cp_con_acceso=("tiene_acceso", "sum")
    ).reset_index()
    acceso["pct_acceso"] = acceso["n_cp_con_acceso"] / acceso["n_cp"]
    return acceso


def build_index(gdf_base: pd.DataFrame, emerg_por_dist: pd.DataFrame,
                acceso_dist: pd.DataFrame, sufijo: str) -> pd.DataFrame:
    df = gdf_base[["ubigeo", "distrito", "departamen", "provincia",
                   "n_ipress", "n_centros_poblados", "comp1_disponibilidad"]].copy()

    df = df.merge(emerg_por_dist[["ubigeo", "comp2_actividad"]], on="ubigeo", how="left")
    df["comp2_actividad"] = df["comp2_actividad"].fillna(0)

    df = df.merge(acceso_dist[["ubigeo", "pct_acceso"]], on="ubigeo", how="left")
    df["pct_acceso"] = df["pct_acceso"].fillna(0)
    df = df.rename(columns={"pct_acceso": "comp3_acceso"})

    df["comp1_norm"] = minmax(df["comp1_disponibilidad"].fillna(0))
    df["comp2_norm"] = minmax(df["comp2_actividad"])
    df["comp3_norm"] = minmax(df["comp3_acceso"])

    df[f"score_{sufijo}"] = (df["comp1_norm"] + df["comp2_norm"] + df["comp3_norm"]) / 3
    return df


def run_metrics_pipeline():
    print("=== Pipeline de métricas ===")

    gdf_base = gpd.read_file(PROCESSED_DIR / "distritos_base.gpkg")
    gdf_base["comp1_disponibilidad"] = (
        gdf_base["n_ipress"] / gdf_base["n_centros_poblados"].replace(0, np.nan)
    )

    df_emerg = pd.read_csv(PROCESSED_DIR / "emergencias_clean.csv", dtype={"ubigeo": str})
    emerg_por_dist = df_emerg.groupby("ubigeo").agg(
        total_atenciones=("nro_total_atenciones", "sum"),
        n_ipress_reportantes=("co_ipress", "nunique")
    ).reset_index()
    emerg_por_dist["comp2_actividad"] = (
        emerg_por_dist["total_atenciones"] / emerg_por_dist["n_ipress_reportantes"]
    )

    gdf_cp_full = gpd.read_file(PROCESSED_DIR / "centros_poblados_distritales.gpkg")
    df_cp = pd.DataFrame(gdf_cp_full.drop(columns="geometry"))
    del gdf_cp_full

    df_ipress = pd.read_csv(PROCESSED_DIR / "ipress_clean.csv", dtype={"ubigeo": str},
                             usecols=["codigo_unico", "ubigeo", "norte", "este"]
                             ).dropna(subset=["norte", "este"])

    print("Calculando acceso espacial baseline (5 km)...")
    acceso_5km = calc_spatial_access(df_cp, df_ipress, umbral_km=5)

    print("Calculando acceso espacial alternativa (15 km)...")
    acceso_15km = calc_spatial_access(df_cp, df_ipress, umbral_km=15)

    df_baseline    = build_index(gdf_base, emerg_por_dist, acceso_5km,  "baseline")
    df_alternativa = build_index(gdf_base, emerg_por_dist, acceso_15km, "alternativa")

    df_final = df_baseline.merge(
        df_alternativa[["ubigeo", "score_alternativa", "comp3_norm"]].rename(
            columns={"comp3_norm": "comp3_norm_alt"}),
        on="ubigeo"
    )
    df_final["diferencia_scores"] = df_final["score_alternativa"] - df_final["score_baseline"]
    df_final["clasificacion"] = pd.qcut(
        df_final["score_baseline"], q=3,
        labels=["Subatendido", "Acceso medio", "Mejor atendido"]
    )

    df_final.to_csv(PROCESSED_DIR / "distrito_scores.csv", index=False)
    print(f"Guardado: distrito_scores.csv | shape: {df_final.shape}")
    return df_final


if __name__ == "__main__":
    run_metrics_pipeline()
    print("=== Listo ===")
