# Partes 9 y 10 — Proyecto 1

## Estructura

- `scripts/generar_datos_limpios.py`: genera el conjunto limpio, métricas y registro de transformaciones.
- `scripts/validar_datos_limpios.py`: ejecuta pruebas automáticas de calidad.
- `datos/DATOS_LIMPIOS.csv`: conjunto limpio final.
- `datos/metricas_calidad.csv`: comparación antes/después.
- `datos/registro_transformaciones_final.csv`: documentación de cambios.
- `docs/parte_9_10_overleaf.tex`: informe de las partes 9 y 10 para Overleaf.
- `docs/Libro_de_Codigos.pdf`: libro de códigos final.
- `docs/Libro_de_Codigos.xlsx`: versión editable del libro de códigos.

## Reproducción

Coloque `DATOS_CRUDOS.csv` dentro de la carpeta `datos` y ejecute desde la raíz:

```bash
python scripts/generar_datos_limpios.py
python scripts/validar_datos_limpios.py
```

## Antes de entregar

Complete en el archivo `.tex`:
- nombre del estudiante;
- fecha real de extracción de los datos;
- cualquier dato institucional solicitado por el profesor.