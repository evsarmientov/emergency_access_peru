"""
utils.py
Funciones auxiliares compartidas por todo el pipeline.
"""

import re
import unicodedata
import pandas as pd


def to_snake(col: str) -> str:
    # Eliminamos tildes y diacríticos (á → a, ñ → n, etc.)
    nfd = unicodedata.normalize("NFD", col)
    sin_tildes = "".join(c for c in nfd if unicodedata.category(c) != "Mn")

    # Convertimos a minúsculas y reemplazamos espacios/símbolos por guión bajo
    limpio = sin_tildes.lower().strip()
    limpio = re.sub(r"[^a-z0-9]+", "_", limpio)
    return limpio.strip("_")


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Aplica to_snake a todas las columnas del DataFrame de una sola vez
    return df.rename(columns={c: to_snake(c) for c in df.columns})


def ubigeo_to_str(series: pd.Series) -> pd.Series:
    # Convierte UBIGEO numérico a string de 6 dígitos con ceros a la izquierda
    return (
        series
        .dropna()
        .astype(int)
        .astype(str)
        .str.zfill(6)
        .reindex(series.index)
    )
