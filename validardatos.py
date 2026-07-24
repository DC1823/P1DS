import pandas as pd


DEPARTAMENTOS = {
    "ALTA VERAPAZ",
    "BAJA VERAPAZ",
    "CHIMALTENANGO",
    "CHIQUIMULA",
    "EL PROGRESO",
    "ESCUINTLA",
    "GUATEMALA",
    "HUEHUETENANGO",
    "IZABAL",
    "JALAPA",
    "JUTIAPA",
    "PETÉN",
    "QUETZALTENANGO",
    "QUICHÉ",
    "RETALHULEU",
    "SACATEPÉQUEZ",
    "SAN MARCOS",
    "SANTA ROSA",
    "SOLOLÁ",
    "SUCHITEPÉQUEZ",
    "TOTONICAPÁN",
    "ZACAPA",
}

TIPOS_ESPERADOS = {
    "codigo_establecimiento": "object",
    "telefono_valido": "bool",
    "posible_duplicado": "bool",
}

COLUMNAS_CATEGORICAS = [
    "sector",
    "area",
    "status",
    "modalidad",
    "jornada",
    "plan",
]


def validar_duplicados(df):
    duplicados = df.duplicated().sum()

    if duplicados:
        return (
            False,
            f"[X] Registros duplicados: Se encontraron {duplicados} filas completamente idénticas.",
        )

    return True, "[✓] Sin registros duplicados exactos."


def validar_espacios(df):
    columnas = df.select_dtypes(include="object").columns

    columnas_error = [
        col
        for col in columnas
        if df[col].dropna().astype(str).str.contains(r"^\s|\s$", regex=True).any()
    ]

    if columnas_error:
        return (
            False,
            f"[X] Espacios en blanco: Las columnas {columnas_error} tienen espacios al inicio o final.",
        )

    return True, "[✓] Sin espacios invisibles en los textos."


def validar_telefonos(df):
    if "telefono_principal" not in df.columns:
        return True, "[✓] Columna telefono_principal no encontrada."

    telefonos = (
        df["telefono_principal"]
        .dropna()
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
    )

    invalidos = telefonos[~telefonos.str.fullmatch(r"\d{8}")]

    if not invalidos.empty:
        return (
            False,
            f"[X] Formato de teléfono: {len(invalidos)} registros no tienen exactamente 8 dígitos (ej. {invalidos.iloc[0]}).",
        )

    return True, "[✓] Teléfonos con formato consistente de 8 dígitos."


def validar_departamentos(df):
    if "departamento" not in df.columns:
        return True, "[✓] Columna departamento no encontrada."

    invalidos = (
        df.loc[~df["departamento"].isin(DEPARTAMENTOS), "departamento"]
        .dropna()
        .unique()
    )

    if len(invalidos):
        return (
            False,
            f"[X] Catálogo ubicación: Departamentos no reconocidos o mal escritos -> {list(invalidos)}",
        )

    return True, "[✓] Departamentos pertenecen al catálogo correspondiente."


def validar_tipos(df):
    errores = [
        f"La columna '{col}' es {df[col].dtype}, se esperaba {tipo}"
        for col, tipo in TIPOS_ESPERADOS.items()
        if col in df.columns and str(df[col].dtype) != tipo
    ]

    if errores:
        return False, "[X] Tipo de datos incorrecto: " + ", ".join(errores)

    return True, "[✓] Variables principales tienen el tipo de dato esperado."


def validar_categorias(df):
    columnas = [
        col
        for col in COLUMNAS_CATEGORICAS
        if col in df.columns
        and df[col].dropna().nunique()
        != df[col].dropna().astype(str).str.strip().str.lower().nunique()
    ]

    if columnas:
        return (
            False,
            f"[X] Categorías duplicadas por escritura en las columnas: {', '.join(columnas)}",
        )

    return (
        True,
        "[✓] Sin categorías duplicadas por diferencias de escritura.",
    )


def cargar_dataset(ruta):
    try:
        return pd.read_csv(ruta)
    except FileNotFoundError:
        print("Error: No se encontró el archivo especificado.")
        return None


def ejecutar_pruebas_calidad(ruta_archivo):
    print(f"--- INICIANDO PRUEBAS DE CALIDAD: {ruta_archivo} ---\n")

    df = cargar_dataset(ruta_archivo)

    if df is None:
        return

    pruebas = [
        validar_duplicados,
        validar_espacios,
        validar_telefonos,
        validar_departamentos,
        validar_tipos,
        validar_categorias,
    ]

    errores = []

    for prueba in pruebas:
        exito, mensaje = prueba(df)

        if exito:
            print(mensaje)
        else:
            errores.append(mensaje)

    print("\n" + "=" * 50)
    print("REPORTE FINAL DE VALIDACIÓN")
    print("=" * 50)

    if errores:
        print("ESTADO: REPROBADO\n")

        for error in errores:
            print(error)
    else:
        print("ESTADO: APROBADO. ¡El conjunto de datos es consistente y de alta calidad!")


if __name__ == "__main__":
    ejecutar_pruebas_calidad("DATOS_LIMPIOS.csv")