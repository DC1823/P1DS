#Proyecto 1


import pandas as pd
import numpy as np
import re

df=pd.read_csv("DATOS_CRUDOS.csv", sep=",",encoding="ISO-8859-1", dtype=str, on_bad_lines='skip')
df.head()
df.columns = df.columns.str.strip()  # Eliminar espacios en los nombres de las columnas
#A.
print("Dimenciones del dataset(Filas, Columnas):", df.shape)
print("Columnas del dataset:", df.columns)
print("="*20)
#B.
print("Tipos de datos de cada columna:", df.dtypes)
print(df.dtypes)
#C.
print("\nValores nulos por columna:")
faltantes=df.isnull().sum() +(df.isna().sum()+(df=="NULL").sum()+(df=="Na").sum())
porcentaje_faltantes=(faltantes/len(df))*100
tab_faltantes=pd.DataFrame({
    "faltantes": faltantes,
    "porcentaje": porcentaje_faltantes.round(2)
}).sort_values(by="faltantes", ascending=False)

print(tab_faltantes)

#D
print("\nValores unicos por variable:")
valores_unicos=df.nunique()
print(valores_unicos)

#E
print("\nValores duplicados por variable:")
duplicados=df.duplicated().sum()
print(duplicados)

#F
print("\n" + "="*20)
print("Inconsistencias en variables:")
print("="*20)


col_inconsistentes = ['NIVEL', 'SECTOR', 'AREA', 'STATUS']

for col in col_inconsistentes:
    if col in df.columns:
        print(f"\n Distribución de valores unicos para '{col}':")
        inconsistencias = df[col].value_counts(dropna=False)
        print(inconsistencias)
#G
print("\n" + "="*20)
print("Validar formatos")
patron_cod=r'^\d{2}-\d{2}-\d{4}-\d{2}$'
codigos_invalidos = df['CODIGO'].dropna().apply(lambda x: bool(re.match(patron_cod, str(x)))==False).sum()
print("\nCódigos no válidos:")
print(codigos_invalidos)

#telefonos con 8 digitos
tel_invalidos = df['TELEFONO'].dropna().apply(lambda x: bool(re.match(r'^\d{8}$', str(x)))==False).sum()
print("\nTeléfonos no válidos (8 dígitos):")   
print(tel_invalidos)

#H
print("\n" + "="*20)
print("Caracteres especiales en variables de texto:")
patron_caracteres_especiales = r'[^a-zA-Z0-9\s]'
caracteres_especiales = df['ESTABLECIMIENTO'].astype(str).str.contains(patron_caracteres_especiales, na=False)  
print("Filas con caracteres especiales en 'ESTABLECIMIENTO':")
print("'\n")


#################################################################
print("\n" + "="*20)
print("Reporte: No hay valores nulos en las variables de texto, pero se encontraron caracteres especiales en la columna 'ESTABLECIMIENTO'.")
print("Se elimina en la fase de limpieza.Hay 7,262 códigos unicos, lo que significa que hay duplicados en los nombnres de los establecimientos. ")
print("En las variables de texto, se encontraron inconsistencias (22) en las columnas 'NIVEL', 'SECTOR', 'AREA' y 'STATUS'. Estan dañadas o desplazadas.")
print("Se marcan que hay 7283 teléfonos no válidos, posiblemente por formato de excel que completa el número con ceros a la izquierda. Por lo que se realiza limpieza de datos en la fase de limpieza. ")

################################################################
#limpieza
df.columns = df.columns.str.strip()  # Eliminar espacios en los nombres de las columnas
df=df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)  # Eliminar espacios en los valores de las columnas de tipo objeto
df.replace(["", " ", "NULL", "Na", "null"], np.nan, inplace=True)
#0 de los telefonos
if 'TELEFONO' in df.columns:
    df['TELEFONO'] = df['TELEFONO'].astype(str).str.replace(r'\.0$', '', regex=True)  # Eliminar ceros a la izquierda en la columna 'TELEFONO'
    df['TELEFONO']=df['TELEFONO'].replace(["nan", "None", "", " "], np.nan)  # Reemplazar "nan" y "None" por NaN en la columna 'TELEFONO'

###cambios
print("\n" + "="*20)
print("\n[NUEVO] Valores nulors por columna después de la limpieza:")
faltantes_post_limpieza = df.isnull().sum() 
porcentaje_faltantes_post_limpieza = (faltantes_post_limpieza / len(df)) * 100
tab_faltantes_post_limpieza = pd.DataFrame({
    "faltantes": faltantes_post_limpieza,
    "porcentaje": porcentaje_faltantes_post_limpieza.round(2)
}).sort_values(by="faltantes", ascending=False)

print(tab_faltantes_post_limpieza.head(10))

print("\n" + "="*20)
telefonos_invalidos_post_limpieza = df['TELEFONO'].dropna().apply(lambda x: bool(re.match(r'^\d{8}$', str(x)))==False).sum()
tel_nulos_post_limpieza = df['TELEFONO'].isnull().sum()
print("\n[NUEVO] Teléfonos no válidos (8 dígitos) después de la limpieza:")
print(tel_nulos_post_limpieza)
