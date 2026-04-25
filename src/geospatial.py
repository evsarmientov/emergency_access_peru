"""
geospatial.py
Builds GeoDataFrames, performs spatial joins, and saves district-level outputs.
"""
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

ROOT          = Path(__file__).parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"


def build_ipress_geodataframe():
    df = pd.read_csv(PROCESSED_DIR / "ipress_clean.csv", dtype={"ubigeo": str})
    df_coords = df.dropna(subset=["norte", "este"]).copy()
    # NORTE = longitud (X), ESTE = latitud (Y) — columnas confusamente nombradas
    gdf = gpd.GeoDataFrame(
        df_coords,
        geometry=gpd.points_from_xy(df_coords["norte"], df_coords["este"]),
        crs="EPSG:4326"
    )
    print(f"IPRESS con geometría: {gdf.shape}")
    return gdf


def assign_ipress_to_districts(gdf_ipress, gdf_distritos):
    # Asignación por UBIGEO (100% match esperado)
    merged = gdf_ipress.merge(
        gdf_distritos[["ubigeo", "geometry"]],
        on="ubigeo", how="left", suffixes=("", "_dist")
    )
    print(f"IPRESS asignadas por UBIGEO: {merged['ubigeo'].notna().sum()}")
    return merged


def assign_cp_to_districts(gdf_cp, gdf_distritos):
    # Paso 1: asignación directa por UBIGEO
    gdf_cp_dist = gdf_cp.merge(
        gdf_distritos[["ubigeo"]].rename(columns={"ubigeo": "ubigeo_dist"}),
        left_on="ubigeo", right_on="ubigeo_dist", how="left"
    )
    asignados_ubigeo = gdf_cp_dist["ubigeo_dist"].notna().sum()

    # Paso 2: spatial join para los no asignados
    sin_asignar = gdf_cp_dist[gdf_cp_dist["ubigeo_dist"].isna()].copy()
    if len(sin_asignar) > 0:
        sin_asignar = sin_asignar.drop(columns=["ubigeo_dist"])
        joined = gpd.sjoin(sin_asignar, gdf_distritos[["ubigeo", "geometry"]],
                           how="left", predicate="within")
        joined = joined.rename(columns={"ubigeo_right": "ubigeo_dist"})
        gdf_cp_dist.loc[gdf_cp_dist["ubigeo_dist"].isna(), "ubigeo_dist"] = \
            joined["ubigeo_dist"].values

    print(f"CPs asignados por UBIGEO: {asignados_ubigeo} | "
          f"por spatial join: {gdf_cp_dist['ubigeo_dist'].notna().sum() - asignados_ubigeo} | "
          f"sin asignar: {gdf_cp_dist['ubigeo_dist'].isna().sum()}")
    return gdf_cp_dist


def aggregate_districts(gdf_distritos, gdf_ipress, gdf_cp_dist):
    # Conteo de IPRESS por distrito
    n_ipress = gdf_ipress.groupby("ubigeo").size().rename("n_ipress")
    n_ipress_coords = gdf_ipress.dropna(subset=["geometry"]).groupby("ubigeo").size().rename("n_ipress_con_coords")
    camas = gdf_ipress.groupby("ubigeo")["camas"].sum().rename("n_camas")

    # Nivel de IPRESS (I / II / III)
    gdf_ipress["nivel"] = gdf_ipress["categoria"].str.split("-").str[0]
    nivel_pivot = gdf_ipress.groupby(["ubigeo", "nivel"]).size().unstack(fill_value=0)

    # Conteo de CPs por distrito
    n_cp = gdf_cp_dist.groupby("ubigeo_dist").size().rename("n_centros_poblados")

    gdf_base = gdf_distritos.copy()
    for serie in [n_ipress, n_ipress_coords, camas, n_cp]:
        gdf_base = gdf_base.merge(serie.reset_index(), on="ubigeo", how="left")
    gdf_base = gdf_base.merge(nivel_pivot.reset_index(), on="ubigeo", how="left")
    gdf_base = gdf_base.fillna(0)

    print(f"Distritos base: {gdf_base.shape}")
    return gdf_base


def run_geospatial_pipeline():
    print("=== Pipeline geoespacial ===")
    gdf_distritos = gpd.read_file(PROCESSED_DIR / "distritos_clean.gpkg")
    gdf_cp = gpd.read_file(PROCESSED_DIR / "centros_poblados_clean.gpkg")

    gdf_ipress = build_ipress_geodataframe()
    gdf_cp_dist = assign_cp_to_districts(gdf_cp, gdf_distritos)
    gdf_base = aggregate_districts(gdf_distritos, gdf_ipress, gdf_cp_dist)

    gdf_cp_dist.to_file(PROCESSED_DIR / "centros_poblados_distritales.gpkg", driver="GPKG")
    gdf_base.to_file(PROCESSED_DIR / "distritos_base.gpkg", driver="GPKG")
    print("Guardado: centros_poblados_distritales.gpkg, distritos_base.gpkg")
    return gdf_base


if __name__ == "__main__":
    run_geospatial_pipeline()
    print("=== Listo ===")
