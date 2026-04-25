import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path

ROOT          = Path(__file__).parent
FIGURES_DIR   = ROOT / "output" / "figures"
PROCESSED_DIR = ROOT / "data" / "processed"

st.set_page_config(
    page_title="Acceso a Emergencias en Perú",
    page_icon="🏥",
    layout="wide"
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data & Methodology",
    "📊 Static Analysis",
    "🗺️ GeoSpatial Results",
    "🔍 Interactive Exploration"
])

with tab1:
    st.title("Desigualdad en el acceso a emergencias de salud en Perú")
    st.markdown("*Análisis distrital basado en disponibilidad de IPRESS, actividad asistencial y acceso espacial de centros poblados*")

    # Métricas clave
    st.header("Cifras clave del proyecto")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distritos analizados", "1,873")
    c2.metric("IPRESS con coordenadas", "7,941")
    c3.metric("Centros poblados", "135,942")
    c4.metric("Atenciones de emergencia", "977,373")

    st.divider()

    # Problema
    st.header("¿Qué problema estudia este proyecto?")
    st.markdown("""
    El acceso a atención de emergencias en Perú es profundamente desigual.
    Mientras algunos distritos concentran establecimientos de salud, actividad
    asistencial y centros poblados bien conectados, otros carecen de cualquiera
    de estas condiciones.

    Este proyecto responde cuatro preguntas analíticas obligatorias:
    - **Q1:** ¿Qué distritos tienen menor o mayor disponibilidad de IPRESS y actividad de emergencia?
    - **Q2:** ¿Qué distritos tienen centros poblados con débil acceso espacial a IPRESS?
    - **Q3:** ¿Qué distritos están más subatendidos o mejor atendidos al combinar las tres dimensiones?
    - **Q4:** ¿Cuánto cambian los resultados si se modifica la definición de acceso?
    """)

    st.divider()

    # Fuentes de datos
    st.header("Fuentes de datos")
    st.markdown("""
    | Dataset | Filas brutas | Filas limpias | Descripción |
    |---|---|---|---|
    | IPRESS – MINSA | 20,819 | 20,790 | Establecimientos de salud con categoría y coordenadas |
    | Producción Asistencial en Emergencia | 1,046,838 | 977,373 | Atenciones por IPRESS, año y mes (2022–2025) |
    | Centros Poblados – INEI | 136,587 | 135,942 | Asentamientos humanos georeferenciados |
    | Distritos – INEI | 1,873 | 1,873 | Polígonos distritales con UBIGEO |

    Todos los datasets usan **CRS EPSG:4326 (WGS84)**. El identificador común entre datasets es el
    **UBIGEO**: código de 6 dígitos (2 departamento + 2 provincia + 2 distrito).
    """)

    with st.expander("📖 Diccionario de variables clave"):
        st.markdown("""
        | Variable | Dataset | Descripción |
        |---|---|---|
        | `ubigeo` | Todos | Código distrital de 6 dígitos (identificador común) |
        | `norte` / `este` | IPRESS | Coordenadas geográficas — NORTE = longitud (X), ESTE = latitud (Y) |
        | `categoria` | IPRESS | Nivel de atención: I-1, I-2, I-3, I-4, II-1, II-2, II-E, III-1, III-2, III-E |
        | `nro_total_atenciones` | Emergencias | Atenciones de emergencia por IPRESS, mes y año |
        | `NE_XXXX` | Emergencias | Valor suprimido por confidencialidad estadística (~13.3% de registros) |
        | `x` / `y` | Centros Poblados | Coordenadas geográficas del asentamiento |
        | `iddist` | Distritos | Equivalente a UBIGEO en el shapefile original |
        | `geometry` | Distritos / CPs | Geometría espacial en formato WKB (GeoPackage) |
        """)

    st.divider()

    # Limpieza
    st.header("Decisiones de limpieza")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("IPRESS")
        st.markdown("""
        - Eliminados **3 registros** con coordenadas (0°, 0°) — inválidas geográficamente
        - Eliminados **26 duplicados** por código único
        - Solo **7,941 de 20,790** tienen coordenadas válidas (38%) → limita el análisis espacial
        - Nivel extraído de `categoria` con `split("-")[0]` (ej. "II-1" → "II")
        """)
        st.subheader("Emergencias")
        st.markdown("""
        - Valores `NE_XXXX` → tratados como `NaN` (supresión estadística, no ausencia real)
        - Duplicados eliminados por `[año, mes, ubigeo, co_ipress, sexo, edad]`
        - 683 distritos sin datos de emergencia → reciben `comp2 = 0`
        """)
    with col_b:
        st.subheader("Centros Poblados")
        st.markdown("""
        - UBIGEO extraído de los primeros 6 caracteres del campo `CÓDIGO`
        - 645 duplicados eliminados → 135,942 CPs válidos
        - 218 CPs sin asignación distrital por ningún método (0.16%)
        """)
        st.subheader("Distritos")
        st.markdown("""
        - Sin registros inválidos — 1,873 polígonos completos
        - `IDDIST` renombrado a `ubigeo` para compatibilidad entre datasets
        - CRS verificado: EPSG:4326 en todos los archivos
        """)

    st.divider()

    # Metodología
    st.header("Construcción del índice de acceso")
    st.markdown("""
    El índice combina tres componentes normalizados con min-max y promedio igualitario:
    """)

    st.markdown("""
    | # | Componente | Fórmula | Pregunta | Justificación |
    |---|---|---|---|---|
    | 1 | **Disponibilidad** | IPRESS / CPs del distrito | Q1 | Mide si el distrito tiene suficientes establecimientos para su cantidad de asentamientos |
    | 2 | **Actividad** | Atenciones totales / IPRESS reportantes | Q1 | Captura si los establecimientos efectivamente atienden emergencias |
    | 3 | **Acceso espacial** | % de CPs a ≤ X km de un IPRESS | Q2 | Mide conectividad física entre población y servicios |
    """)

    st.markdown("""
    **Score final = (comp1_norm + comp2_norm + comp3_norm) / 3**

    **¿Por qué pesos iguales?** No se dispone de evidencia empírica para asignar pesos diferenciales.
    El promedio igualitario es la opción más transparente y replicable.

    **¿Por qué min-max?** Permite comparar componentes en escalas distintas sin asumir distribución normal.
    Limitación: es sensible a outliers extremos (ej. Lima con 620,000 atenciones/IPRESS).

    **Distancias:** calculadas con `scipy.spatial.cKDTree` sobre coordenadas en grados decimales.
    Conversión aproximada: 1° ≈ 111 km (válida para la latitud de Perú, sin considerar terreno ni vías).
    """)

    st.divider()

    # Sensibilidad
    st.header("Análisis de sensibilidad (Q4)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Umbral baseline", "5 km", "31.3% CPs con acceso")
    col2.metric("Umbral alternativa", "15 km", "43.2% CPs con acceso")
    col3.metric("Distritos sin cambio", "1,191 / 1,873", "63.6%")

    st.markdown("""
    Se varió el umbral de acceso espacial de 5 km (baseline) a 15 km (alternativa).
    El cambio afecta principalmente al tercil medio: distritos cuyos CPs están entre 5 y 15 km de un IPRESS
    mejoran su clasificación. Los extremos (mejor y peor atendidos) son **robustos al cambio de umbral**.
    """)

    st.divider()

    # Limitaciones
    st.header("Limitaciones")
    st.warning("""
    **Limitaciones principales del análisis:**
    - El **62% de las IPRESS no tienen coordenadas** → el acceso espacial subestima la cobertura real.
    - Los **valores NE_XXXX** en emergencias excluyen el 13.3% de los registros — posible sesgo en zonas rurales.
    - La conversión grados → km es una **aproximación plana** que ignora accidentes geográficos y vías reales.
    - **Sin datos de población** por distrito → el índice no está ponderado por habitantes.
    - Los **pesos iguales** entre componentes son una decisión metodológica, no derivada de evidencia empírica.
    - La normalización min-max es **sensible a outliers**: Lima distorsiona los componentes 1 y 2.
    """)

with tab2:
    st.title("Análisis estático")
    st.markdown("Gráficos generados con matplotlib y seaborn. Cada visualización fue elegida para responder una pregunta analítica específica — no para mostrar datos por mostrarlos.")

    st.header("Gráfico 1 — Distribución del índice de acceso (Q4)")
    st.image(str(FIGURES_DIR / "dist_scores.png"))
    st.markdown("""
    **Decisión metodológica:** Se eligió un panel doble en lugar de un histograma simple porque la distribución
    es extremadamente sesgada (mediana ≈ 0.012). Un histograma tradicional oculta la variación real.
    La escala logarítmica en el panel izquierdo permite ver todos los rangos; el KDE en el panel derecho
    muestra cómo cambia la distribución entre distritos con acceso positivo al ampliar el umbral de 5 a 15 km.

    **Hallazgo clave:** La mayoría de distritos tiene score cercano a cero — el acceso a emergencias
    está muy concentrado en pocos distritos. Ampliar el umbral desplaza la distribución hacia la derecha,
    pero no cambia el patrón estructural de desigualdad. *Responde Q4.*
    """)

    st.divider()

    st.header("Gráfico 2 — Top / Bottom 10 distritos (Q3)")
    st.image(str(FIGURES_DIR / "top_bottom.png"))
    st.markdown("""
    **Decisión metodológica:** Las barras horizontales permiten leer los nombres de distrito sin rotación
    y comparar magnitudes directamente. Se eligió este gráfico sobre un ranking tabular porque la diferencia
    visual entre el top y el bottom (0.72 vs 10⁻⁶) es más impactante que una tabla de números.
    El bottom 10 excluye los 3 distritos sin centros poblados registrados para evitar casos triviales.

    **Hallazgo clave:** Arequipa (ciudad) lidera con score 0.72. Los distritos más subatendidos tienen
    scores en el orden de 10⁻⁶ — diferencia de más de 5 órdenes de magnitud. La desigualdad es extrema. *Responde Q3.*
    """)

    st.divider()

    st.header("Gráfico 3 — Acceso promedio por departamento (Q1)")
    st.image(str(FIGURES_DIR / "acceso_por_departamento.png"))
    st.markdown("""
    **Decisión metodológica:** Se eligió el nivel departamental (no distrital) para mostrar patrones
    regionales sin saturar el gráfico con 1,873 barras. La línea de promedio nacional permite identificar
    qué regiones están sistemáticamente por encima o por debajo.

    **Hallazgo clave:** Apurímac, Junín e Ica lideran — no por tener los mejores hospitales, sino por
    tener pocos distritos relativamente homogéneos con buena cobertura. Lima está debajo del promedio
    nacional porque sus 171 distritos son muy heterogéneos: San Isidro y Huarochirí en el mismo promedio. *Responde Q1.*
    """)

    st.divider()

    st.header("Gráfico 4 — Acceso espacial por clasificación (Q2)")
    st.image(str(FIGURES_DIR / "acceso_espacial_clasificacion.png"))
    st.markdown("""
    **Decisión metodológica:** El box plot muestra distribución completa (no solo promedio) del componente
    espacial por grupo de clasificación. Se eligió sobre un bar chart de promedios porque permite ver
    la dispersión interna de cada grupo y detectar solapamientos.

    **Hallazgo clave:** La separación entre grupos es clara en el componente espacial: los "Subatendidos"
    tienen mediana ≈ 0% de CPs con acceso; los "Mejor atendidos" superan el 75%. Esto valida que
    la clasificación por terciles captura diferencias geográficas reales, no solo estadísticas. *Responde Q2.*
    """)

    st.divider()

    st.header("Gráfico 5 — Top 10 distritos con mayor cambio entre versiones (Q4)")
    st.image(str(FIGURES_DIR / "sensibilidad_baseline_alternativa.png"))
    st.markdown("""
    **Decisión metodológica:** Se eligió un bar chart apilado (baseline + ganancia) sobre un scatter
    porque identifica directamente QUÉ distritos cambian y CUÁNTO — información más accionable que
    ver la nube de puntos completa. El umbral espacial (5 vs 15 km) es el parámetro con mayor
    incertidumbre metodológica del índice: no existe evidencia empírica de cuál es la distancia
    "razonable" en la geografía peruana.

    **Hallazgo clave:** Los distritos que más cambian son aquellos donde los CPs están entre 5 y 15 km
    de un IPRESS — zonas periurbanas y sierra con acceso marginal. Los distritos extremos (mejor y peor
    atendidos) son robustos al cambio de umbral, lo que valida la clasificación. *Responde Q4.*
    """)

with tab3:
    st.title("Resultados geoespaciales")
    st.markdown("Mapas estáticos generados con GeoPandas. Muestran la distribución territorial del índice y sus componentes.")

    st.header("Mapa 1 — Índice de acceso baseline por distrito (Q3)")
    st.image(str(FIGURES_DIR / "mapa_acceso.png"), width=600)
    st.markdown("""
    La costa sur y sierra central concentran los distritos con mayor acceso (tonos rojos).
    La selva nororiental (Loreto, Amazonas, Ucayali) muestra acceso mínimo —
    centros poblados muy dispersos y pocas IPRESS con coordenadas registradas.
    """)

    st.divider()

    st.header("Mapa 2 — Los 3 componentes del índice (Q1 + Q2)")
    st.image(str(FIGURES_DIR / "mapa_componentes.png"))
    st.markdown("""
    - **Disponibilidad (azul):** dispersa por todo el país — algunos distritos pequeños con pocas IPRESS pero aún menos CPs tienen ratio alto.
    - **Actividad (verde):** muy concentrada — solo distritos con hospitales activos reportantes aparecen con color. El 63% del país sin datos de emergencia queda en blanco.
    - **Acceso espacial (naranja):** el componente más informativo geográficamente. La brecha costa/sierra vs selva es evidente.
    La escala está recortada al percentil 95 para evitar que outliers extremos compriman la variación visible.
    """)

    st.divider()

    st.header("Tabla — Clasificación distrital (Q3)")

    df_tabla = pd.read_csv(PROCESSED_DIR / "distrito_scores.csv", dtype={"ubigeo": str})

    col_filtro, col_orden = st.columns(2)
    with col_filtro:
        clasif_sel = st.multiselect(
            "Filtrar por clasificación",
            options=["Subatendido", "Acceso medio", "Mejor atendido"],
            default=["Subatendido", "Acceso medio", "Mejor atendido"]
        )
    with col_orden:
        orden_sel = st.selectbox(
            "Ordenar por",
            options=["score_baseline", "score_alternativa", "comp3_acceso"],
            format_func=lambda x: {
                "score_baseline": "Score baseline",
                "score_alternativa": "Score alternativa",
                "comp3_acceso": "Acceso espacial"
            }[x]
        )

    df_mostrar = (
        df_tabla[df_tabla["clasificacion"].isin(clasif_sel)]
        .sort_values(orden_sel, ascending=False)
        [["distrito", "departamen", "clasificacion", "score_baseline", "score_alternativa", "comp3_acceso"]]
        .rename(columns={
            "distrito": "Distrito",
            "departamen": "Departamento",
            "clasificacion": "Clasificación",
            "score_baseline": "Score baseline",
            "score_alternativa": "Score alternativa",
            "comp3_acceso": "Acceso espacial (%)"
        })
        .reset_index(drop=True)
    )
    df_mostrar["Acceso espacial (%)"] = (df_mostrar["Acceso espacial (%)"] * 100).round(1)
    df_mostrar["Score baseline"] = df_mostrar["Score baseline"].round(4)
    df_mostrar["Score alternativa"] = df_mostrar["Score alternativa"].round(4)

    st.dataframe(df_mostrar, use_container_width=True, height=400)
    st.caption(f"{len(df_mostrar):,} distritos mostrados")

    st.divider()
    st.header("Tabla final del análisis — output/tables/")
    st.markdown("""
    Tabla consolidada con todos los componentes e índices por distrito.
    Incluye los 3 componentes en escala original, scores baseline y alternativa, y clasificación final.
    Guardada en `output/tables/distrito_scores_final.csv`.
    """)
    df_descarga = pd.read_csv(ROOT / "output" / "tables" / "distrito_scores_final.csv",
                               dtype={"ubigeo": str})
    st.dataframe(df_descarga, use_container_width=True, height=300)
    st.download_button(
        label="⬇️ Descargar tabla completa (CSV)",
        data=df_descarga.to_csv(index=False).encode("utf-8"),
        file_name="distrito_scores_final.csv",
        mime="text/csv"
    )



with tab4:
    st.title("Exploración interactiva")
    st.markdown("Mapas Folium interactivos. Haz hover sobre los distritos o puntos para ver detalles.")

    st.header("Mapa 1 — Clasificación de acceso por distrito (Q3)")
    st.markdown("""
    Distritos coloreados por clasificación: 🔴 Subatendido · 🟡 Acceso medio · 🔵 Mejor atendido.
    Hover para ver score baseline y departamento.
    """)
    html_mapa = open(FIGURES_DIR / "mapa_interactivo.html", "r", encoding="utf-8").read()
    components.html(html_mapa, height=550, scrolling=False)

    st.divider()

    st.header("Mapa 2 — Puntos de IPRESS por nivel de atención (Q1)")
    st.markdown("""
    Cada punto es una IPRESS con coordenadas válidas (7,941 establecimientos).
    🟢 Nivel I · 🟠 Nivel II · 🔴 Nivel III · ⚫ Sin categoría.
    Click sobre un punto para ver nombre y UBIGEO.
    """)
    html_ipress = open(FIGURES_DIR / "mapa_ipress.html", "r", encoding="utf-8").read()
    components.html(html_ipress, height=550, scrolling=False)

    st.divider()

    st.header("Comparación baseline vs alternativa por distrito (Q4)")
    st.markdown("Selecciona un departamento para ver cómo cambian los scores entre versiones.")

    df_comp = pd.read_csv(PROCESSED_DIR / "distrito_scores.csv", dtype={"ubigeo": str})

    dept_sel = st.selectbox(
        "Departamento",
        options=sorted(df_comp["departamen"].unique())
    )

    df_dept = (
        df_comp[df_comp["departamen"] == dept_sel]
        .sort_values("score_baseline", ascending=False)
        [["distrito", "clasificacion", "score_baseline", "score_alternativa", "diferencia_scores"]]
        .rename(columns={
            "distrito": "Distrito",
            "clasificacion": "Clasificación",
            "score_baseline": "Score baseline (5 km)",
            "score_alternativa": "Score alternativa (15 km)",
            "diferencia_scores": "Diferencia"
        })
        .reset_index(drop=True)
    )
    df_dept["Score baseline (5 km)"]   = df_dept["Score baseline (5 km)"].round(4)
    df_dept["Score alternativa (15 km)"] = df_dept["Score alternativa (15 km)"].round(4)
    df_dept["Diferencia"]               = df_dept["Diferencia"].round(4)

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Distritos en " + dept_sel, len(df_dept))
    col_m2.metric("Score baseline promedio", round(df_dept["Score baseline (5 km)"].mean(), 4))
    col_m3.metric("Score alternativa promedio", round(df_dept["Score alternativa (15 km)"].mean(), 4),
                  delta=round(df_dept["Diferencia"].mean(), 4))

    st.dataframe(df_dept, use_container_width=True, height=400)
