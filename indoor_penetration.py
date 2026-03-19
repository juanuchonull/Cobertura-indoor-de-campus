#!/usr/bin/env python3
"""Estudio de penetración indoor en edificio real.

Calcula pérdidas outdoor-to-indoor para tres puntos de usuario y compara Prx con umbrales de servicio.
"""

import numpy as np
import pandas as pd

# Parámetros de enlace
Ptx = 43  # dBm
Gtx = 15  # dBi
Grx = 0   # dBi

# Umbrales
UMBRAL_VOZ = -95
UMBRAL_DATOS = -85

# Datos de puntos en el edificio
points = [
    {
        'punto': 'P1 entrada',
        'dist_m': 80,
        'muro_fachada': 15,
        'muro_interior': 3,
        'forjado': 0,
    },
    {
        'punto': 'P2 aula 2ª',
        'dist_m': 120,
        'muro_fachada': 15,
        'muro_interior': 6,
        'forjado': 15,
    },
    {
        'punto': 'P3 semisótano',
        'dist_m': 100,
        'muro_fachada': 15,
        'muro_interior': 3,
        'forjado': 18,
    },
]


def pl_cost231(d_km, f_mhz, h_bts=25, h_mt=1.5):
    """COST231-Hata en zona urbana (aprox)."""
    a_hm = (1.1 * np.log10(f_mhz) - 0.7) * h_mt - (1.56 * np.log10(f_mhz) - 0.8)
    pl = (
        46.3
        + 33.9 * np.log10(f_mhz)
        - 13.82 * np.log10(h_bts)
        - a_hm
        + (44.9 - 6.55 * np.log10(h_bts)) * np.log10(d_km)
        + 3
    )
    return pl


def calc_result(point, f_mhz):
    d_km = max(0.001, point['dist_m'] / 1000.0)
    pl_outdoor = pl_cost231(d_km, f_mhz)
    pl_pen = point['muro_fachada'] + point['muro_interior'] + point['forjado']
    pl_total = pl_outdoor + pl_pen
    prx = Ptx + Gtx + Grx - pl_total
    return {
        'punto': point['punto'],
        'f_mhz': f_mhz,
        'dist_m': point['dist_m'],
        'PL_outdoor': round(pl_outdoor, 1),
        'PL_pen': round(pl_pen, 1),
        'PL_total': round(pl_total, 1),
        'Prx': round(prx, 1),
        'cumple_voz': 'SI' if prx >= UMBRAL_VOZ else 'NO',
        'cumple_datos': 'SI' if prx >= UMBRAL_DATOS else 'NO',
    }


def main():
    freq_list = [700, 1800, 2600]
    results = []

    for p in points:
        for f in freq_list:
            results.append(calc_result(p, f))

    df = pd.DataFrame(results)

    print('\n=== Resultados: Prx y cumplimiento de umbrales ===\n')
    print(df.to_string(index=False))

    # Resumen por punto y frecuencia
    resumen = (
        df.groupby(['punto', 'f_mhz'])[['Prx']].mean().unstack().round(1)
    )
    print('\n\n=== Resumen de Prx por punto y frecuencia ===\n')
    print(resumen)

    # Recomendación simple
    print('\n\n=== Recomendación rápida ===\n')
    for p in points:
        row_1800 = df[(df['punto'] == p['punto']) & (df['f_mhz'] == 1800)].iloc[0]
        if row_1800['cumple_datos'] == 'NO':
            print(f"- {p['punto']}: no cumple datos en 1800 MHz -> evaluar DAS/small cell y/o 700 MHz")
        elif row_1800['cumple_voz'] == 'NO':
            print(f"- {p['punto']}: no cumple voz en 1800 MHz -> evaluar DAS/small cell")
        else:
            print(f"- {p['punto']}: cumple voz y datos en 1800 MHz. Macro ok en este punto.")


if __name__ == '__main__':
    main()
