"""
visualization.py
Generates all static charts, GeoPandas maps, and Folium interactive maps.
Outputs saved to output/figures/ and output/tables/.
"""
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import folium
from pathlib import Path

ROOT          = Path(__file__).parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR   = ROOT / "output" / "figures"
TABLES_DIR    = ROOT / "output" / "tables"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    cols_scores = [
        "ubigeo", "distrito", "departamen", "provincia",
        "n_ipress", "n_centros_poblados", "comp1_disponibilidad",
        "comp2_actividad", "comp3_acceso", "comp1_norm", "comp2_norm",
        "comp3_norm", "score_baseline", "clasificacion",
        "score_alternativa", "comp3_norm_alt", "diferencia_scores"
    ]
    df_scores = pd.read_csv(PROCESSED_DIR / "distrito_scores.csv", dtype={"ubigeo": str})
    gdf_base  = gpd.read_file(PROCESSED_DIR / "distritos_base.gpkg")
    df_ipress = pd.read_csv(
        PROCESSED_DIR / "ipress_clean.csv", dtype={"ubigeo": str},
        usecols=["codigo_unico", "nombre_del_establecimiento", "ubigeo", "norte", "este", "categoria"]
    ).dropna(subset=["norte", "este"])
    df_ipress["nivel"] = df_ipress["categoria"].str.split("-").str[0]

    gdf = gdf_base.merge(df_scores[cols_scores], on="ubigeo", how="left")
    return df_scores, gdf, df_ipress


def plot_distribution(df_scores):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(df_scores["score_baseline"].dropna(), bins=40, alpha=0.6, color="steelblue", label="Baseline (5 km)")
    axes[0].hist(df_scores["score_alternativa"].dropna(), bins=40, alpha=0.6, color="coral", label="Alternativa (15 km)")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Índice de acceso (0–1)")
    axes[0].set_ylabel("Número de distritos (escala log)")
    axes[0].set_title("Distribución completa (escala logarítmica)")
    axes[0].legend()
    sns.despine(ax=axes[0])

    base_pos = df_scores.loc[df_scores["score_baseline"] > 0, "score_baseline"]
    alt_pos  = df_scores.loc[df_scores["score_alternativa"] > 0, "score_alternativa"]
    sns.kdeplot(base_pos, ax=axes[1], color="steelblue", fill=True, alpha=0.4, label=f"Baseline (n={len(base_pos):,})")
    sns.kdeplot(alt_pos,  ax=axes[1], color="coral",     fill=True, alpha=0.4, label=f"Alternativa (n={len(alt_pos):,})")
    axes[1].set_xlabel("Índice de acceso (0–1)")
    axes[1].set_ylabel("Densidad")
    axes[1].set_title("Distribución entre distritos con acceso > 0")
    axes[1].legend()
    sns.despine(ax=axes[1])

    fig.suptitle("Distribución del índice de acceso a emergencias por distrito", fontsize=13)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "dist_scores.png", dpi=150)
    plt.close()
    print("Guardado: dist_scores.png")


def plot_top_bottom(df_scores):
    df_valid = df_scores.dropna(subset=["score_baseline"]).copy()
    top10 = df_valid.nlargest(10, "score_baseline")[["distrito", "departamen", "score_baseline"]]
    bot10 = df_valid[df_valid["n_centros_poblados"] > 0].nsmallest(10, "score_baseline")[["distrito", "departamen", "score_baseline"]]
    top10["label"] = top10["distrito"] + " (" + top10["departamen"] + ")"
    bot10["label"] = bot10["distrito"] + " (" + bot10["departamen"] + ")"

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].barh(top10["label"], top10["score_baseline"], color="seagreen", alpha=0.85)
    axes[0].set_title("Top 10 — Mayor acceso")
    axes[0].invert_yaxis()
    sns.despine(ax=axes[0])
    axes[1].barh(bot10["label"], bot10["score_baseline"], color="tomato", alpha=0.85)
    axes[1].set_title("Bottom 10 — Menor acceso")
    axes[1].invert_yaxis()
    sns.despine(ax=axes[1])
    fig.suptitle("Distritos con mayor y menor acceso a emergencias (baseline 5 km)", fontsize=13)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_bottom.png", dpi=150)
    plt.close()
    print("Guardado: top_bottom.png")


def plot_department(df_scores):
    dept_avg = df_scores.groupby("departamen")["score_baseline"].mean().sort_values().reset_index()
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(dept_avg["departamen"], dept_avg["score_baseline"], color="steelblue", alpha=0.85)
    nacional = df_scores["score_baseline"].mean()
    ax.axvline(nacional, color="tomato", linestyle="--", linewidth=1.5, label=f"Promedio nacional = {nacional:.3f}")
    ax.set_xlabel("Score baseline promedio")
    ax.set_title("Índice de acceso promedio por departamento (Baseline 5 km)")
    ax.legend()
    sns.despine(ax=ax)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "acceso_por_departamento.png", dpi=150)
    plt.close()
    print("Guardado: acceso_por_departamento.png")


def plot_spatial_access_by_class(df_scores):
    fig, ax = plt.subplots(figsize=(9, 5))
    orden = ["Subatendido", "Acceso medio", "Mejor atendido"]
    palette = {"Subatendido": "#d73027", "Acceso medio": "#fee090", "Mejor atendido": "#4575b4"}
    sns.boxplot(data=df_scores, x="clasificacion", y="comp3_acceso", order=orden, palette=palette, width=0.5, ax=ax)
    ax.set_xlabel("Clasificación de distrito")
    ax.set_ylabel("% de CPs a ≤5 km de un IPRESS")
    ax.set_title("Acceso espacial por clasificación de distrito (Q2)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    sns.despine(ax=ax)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "acceso_espacial_clasificacion.png", dpi=150)
    plt.close()
    print("Guardado: acceso_espacial_clasificacion.png")


def plot_sensitivity(df_scores):
    top_cambio = df_scores.nlargest(10, "diferencia_scores")[
        ["distrito", "departamen", "score_baseline", "diferencia_scores"]].copy()
    top_cambio["label"] = top_cambio["distrito"] + "\n(" + top_cambio["departamen"] + ")"
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_cambio["label"], top_cambio["score_baseline"], color="steelblue", alpha=0.85, label="Baseline (5 km)")
    ax.barh(top_cambio["label"], top_cambio["diferencia_scores"],
            left=top_cambio["score_baseline"], color="coral", alpha=0.85, label="Ganancia con 15 km")
    ax.set_xlabel("Score de acceso")
    ax.set_title("Top 10 distritos con mayor cambio entre versiones (Q4)")
    ax.legend()
    ax.invert_yaxis()
    sns.despine(ax=ax)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "sensibilidad_baseline_alternativa.png", dpi=150)
    plt.close()
    print("Guardado: sensibilidad_baseline_alternativa.png")


def plot_choropleth(gdf):
    fig, ax = plt.subplots(1, 1, figsize=(8, 12))
    gdf.plot(ax=ax, column="score_baseline", cmap="YlOrRd", linewidth=0.1, edgecolor="white",
             legend=True, legend_kwds={"label": "Índice de acceso (0–1)", "orientation": "horizontal", "shrink": 0.5, "pad": 0.01})
    ax.set_title("Índice de acceso a emergencias por distrito\n(Baseline: umbral 5 km)", fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "mapa_acceso.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Guardado: mapa_acceso.png")


def plot_components(gdf):
    componentes = [
        ("comp1_norm", "Disponibilidad\n(IPRESS / CP)", "Blues"),
        ("comp2_norm", "Actividad\n(Atenciones / IPRESS)", "Greens"),
        ("comp3_norm", "Acceso espacial\n(% CP a ≤5 km)", "Oranges"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    for ax, (col, titulo, cmap) in zip(axes, componentes):
        vmax = gdf[col].quantile(0.95)
        gdf.plot(ax=ax, column=col, cmap=cmap, vmin=0, vmax=vmax, linewidth=0.1, edgecolor="white",
                 legend=True, legend_kwds={"orientation": "horizontal", "shrink": 0.6, "pad": 0.01})
        ax.set_title(titulo, fontsize=13, pad=12)
        ax.axis("off")
    fig.suptitle("Componentes del índice de acceso a emergencias\n(escala recortada al percentil 95)", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "mapa_componentes.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Guardado: mapa_componentes.png")


def build_folium_classification(gdf):
    gdf_f = gdf[["ubigeo", "distrito", "departamen", "score_baseline", "clasificacion", "geometry"]].copy()
    gdf_f = gdf_f.to_crs(epsg=4326)
    gdf_f["geometry"] = gdf_f["geometry"].simplify(tolerance=0.01, preserve_topology=True)
    gdf_f["score_baseline"] = gdf_f["score_baseline"].round(4)

    color_map = {"Subatendido": "#d73027", "Acceso medio": "#fee090", "Mejor atendido": "#4575b4"}

    def estilo(feature):
        return {"fillColor": color_map.get(feature["properties"].get("clasificacion"), "#cccccc"),
                "color": "white", "weight": 0.5, "fillOpacity": 0.7}

    m = folium.Map(location=[-9.2, -75.0], zoom_start=5, tiles="CartoDB positron")
    folium.GeoJson(gdf_f.__geo_interface__, style_function=estilo,
                   tooltip=folium.GeoJsonTooltip(
                       fields=["distrito", "departamen", "score_baseline", "clasificacion"],
                       aliases=["Distrito:", "Departamento:", "Score:", "Clasificación:"]
                   )).add_to(m)
    m.save(str(FIGURES_DIR / "mapa_interactivo.html"))
    print("Guardado: mapa_interactivo.html")


def build_folium_ipress(df_ipress):
    nivel_colors = {"I": "green", "II": "orange", "III": "red", "Sin Categoría": "gray"}
    m = folium.Map(location=[-9.2, -75.0], zoom_start=5, tiles="CartoDB positron")
    for _, row in df_ipress.iterrows():
        nivel = str(row.get("nivel", "Sin Categoría"))
        folium.CircleMarker(
            location=[row["este"], row["norte"]], radius=3,
            color=nivel_colors.get(nivel, "gray"), fill=True, fill_opacity=0.7,
            popup=folium.Popup(f"<b>{row['nombre_del_establecimiento']}</b><br>Nivel: {nivel}", max_width=220)
        ).add_to(m)
    m.save(str(FIGURES_DIR / "mapa_ipress.html"))
    print("Guardado: mapa_ipress.html")


def save_final_table(df_scores):
    tabla = df_scores[[
        "ubigeo", "distrito", "departamen", "provincia",
        "n_ipress", "n_centros_poblados", "comp1_disponibilidad",
        "comp2_actividad", "comp3_acceso", "score_baseline",
        "score_alternativa", "diferencia_scores", "clasificacion"
    ]].rename(columns={
        "departamen": "departamento",
        "n_ipress": "n_ipress_distrito",
        "comp1_disponibilidad": "comp1_ipress_por_cp",
        "comp2_actividad": "comp2_atenciones_por_ipress",
        "comp3_acceso": "comp3_pct_cp_acceso_5km",
        "diferencia_scores": "cambio_baseline_a_alternativa"
    })
    tabla.to_csv(TABLES_DIR / "distrito_scores_final.csv", index=False)
    print("Guardado: distrito_scores_final.csv")


if __name__ == "__main__":
    print("=== Generando visualizaciones ===")
    df_scores, gdf, df_ipress = load_data()

    plot_distribution(df_scores)
    plot_top_bottom(df_scores)
    plot_department(df_scores)
    plot_spatial_access_by_class(df_scores)
    plot_sensitivity(df_scores)
    plot_choropleth(gdf)
    plot_components(gdf)
    build_folium_classification(gdf)
    build_folium_ipress(df_ipress)
    save_final_table(df_scores)
    print("=== Listo ===")
