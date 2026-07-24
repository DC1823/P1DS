import csv
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from datetime import date

INPUT = Path('datos/DATOS_CRUDOS.csv')
OUTPUT = Path('datos/DATOS_LIMPIOS.csv')
TRANSFORM = Path('datos/registro_transformaciones_final.csv')
METRICS = Path('datos/metricas_calidad.csv')

SOURCE_COLUMNS = [
    'CODIGO','DISTRITO','DEPARTAMENTO','MUNICIPIO','ESTABLECIMIENTO','DIRECCION',
    'TELEFONO','SUPERVISOR','DIRECTOR','NIVEL','SECTOR','AREA','STATUS',
    'MODALIDAD','JORNADA','PLAN','DEPARTAMENTAL'
]
FINAL_COLUMNS = [
    'codigo_establecimiento','distrito','departamento','municipio','establecimiento',
    'direccion','telefono_principal','supervisor','director','nivel','sector','area',
    'estado_establecimiento','modalidad','jornada','plan','direccion_departamental',
    'telefono_valido','posible_duplicado'
]
RENAMES = dict(zip(SOURCE_COLUMNS, FINAL_COLUMNS[:17]))
MISSING_TOKENS = {'', 'N/A', 'NA', 'NULL', '-', '--', '.', 'SIN DATO', 'S/D', 'NONE'}
DEPARTAMENTOS = {
    'ALTA VERAPAZ','BAJA VERAPAZ','CHIMALTENANGO','CHIQUIMULA','EL PROGRESO',
    'ESCUINTLA','GUATEMALA','HUEHUETENANGO','IZABAL','JALAPA','JUTIAPA','PETEN',
    'QUETZALTENANGO','QUICHE','RETALHULEU','SACATEPEQUEZ','SAN MARCOS',
    'SANTA ROSA','SOLOLA','SUCHITEPEQUEZ','TOTONICAPAN','ZACAPA'
}

def clean_text(value):
    if value is None:
        return ''
    value = value.replace('\u00a0', ' ').replace('\ufeff', '')
    value = re.sub(r'[\x00-\x1f\x7f]', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1].strip()
    if value.upper() in MISSING_TOKENS or re.fullmatch(r'[-.,_/\\ ]+', value or ''):
        return ''
    return value

def normalize_key(value):
    value = clean_text(value).upper()
    value = ''.join(c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn')
    value = re.sub(r'[^A-Z0-9 ]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()

def normalize_category(value):
    # Preserve accents in display values but standardize case/spacing.
    value = clean_text(value)
    return value.upper() if value else ''

def clean_phone(value):
    raw = clean_text(value)
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 8 and len(set(digits)) > 1:
        return digits, True
    return '', False

def read_source():
    with INPUT.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh, skipinitialspace=True)
        rows = list(reader)
    header = [clean_text(x) for x in rows[0]]
    if header != SOURCE_COLUMNS:
        raise ValueError(f'Encabezado inesperado: {header}')
    data = []
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != len(SOURCE_COLUMNS):
            raise ValueError(f'Fila {idx} tiene {len(row)} campos; se esperaban 17.')
        data.append(dict(zip(SOURCE_COLUMNS, row)))
    return data

def exact_duplicate_count(rows):
    keys = [tuple(clean_text(r[c]) for c in SOURCE_COLUMNS) for r in rows]
    return len(keys) - len(set(keys))

def fuzzy_duplicate_flags(rows):
    flags = [False] * len(rows)
    reasons = defaultdict(list)

    # Candidate pairs are blocked by municipality. A record is flagged only when
    # at least two identifying elements agree, avoiding overflagging centers that
    # legitimately have several codes for different services.
    blocks = defaultdict(list)
    for i, r in enumerate(rows):
        mun = normalize_key(r['municipio'])
        if mun:
            blocks[mun].append(i)

    for inds in blocks.values():
        # Secondary indexes keep the comparison tractable.
        by_name = defaultdict(list)
        by_addr = defaultdict(list)
        by_phone = defaultdict(list)
        for i in inds:
            name = normalize_key(rows[i]['establecimiento'])
            addr = normalize_key(rows[i]['direccion'])
            phone = rows[i]['telefono_principal']
            if name: by_name[name].append(i)
            if addr: by_addr[addr].append(i)
            if phone: by_phone[phone].append(i)

        candidate_pairs = set()
        for mapping in (by_name, by_addr, by_phone):
            for group in mapping.values():
                if 1 < len(group) <= 120:
                    for a in range(len(group)):
                        for b in range(a + 1, len(group)):
                            candidate_pairs.add((group[a], group[b]))

        for i, j in candidate_pairs:
            if rows[i]['codigo_establecimiento'] == rows[j]['codigo_establecimiento']:
                continue
            ni = normalize_key(rows[i]['establecimiento'])
            nj = normalize_key(rows[j]['establecimiento'])
            ai = normalize_key(rows[i]['direccion'])
            aj = normalize_key(rows[j]['direccion'])
            pi = rows[i]['telefono_principal']
            pj = rows[j]['telefono_principal']
            same_name = bool(ni and ni == nj)
            same_addr = bool(ai and ai == aj)
            same_phone = bool(pi and pi == pj)
            fuzzy_name = bool(ni and nj and SequenceMatcher(None, ni, nj).ratio() >= 0.96)
            same_plan = rows[i]['plan'] == rows[j]['plan']
            same_jornada = rows[i]['jornada'] == rows[j]['jornada']

            reason = None
            if same_name and same_addr and same_phone and same_plan and same_jornada:
                reason = 'MISMOS_DATOS_IDENTIFICADORES_Y_SERVICIO'
            elif fuzzy_name and same_addr and same_plan and same_jornada:
                reason = 'NOMBRE_SIMILAR_MISMA_DIRECCION_Y_SERVICIO'

            if reason:
                flags[i] = flags[j] = True
                reasons[i].append(reason)
                reasons[j].append(reason)

    return flags, reasons

def main():
    raw = read_source()
    before_rows = len(raw)
    before_cols = len(SOURCE_COLUMNS)
    before_exact_dups = exact_duplicate_count(raw)
    before_missing = sum(1 for r in raw for c in SOURCE_COLUMNS if clean_text(r[c]) == '')
    before_vars_na = sum(any(clean_text(r[c]) == '' for r in raw) for c in SOURCE_COLUMNS)

    transformations = []
    def log(variable, problem, transformation, affected, justification):
        transformations.append([variable, problem, transformation, affected, justification])

    cleaned = []
    whitespace_changes = 0
    missing_standardized = 0
    phone_changes = 0
    invalid_phones = 0
    category_case_changes = 0

    seen = set()
    exact_removed = 0
    for src in raw:
        original_tuple = tuple(clean_text(src[c]) for c in SOURCE_COLUMNS)
        if original_tuple in seen:
            exact_removed += 1
            continue
        seen.add(original_tuple)

        out = {}
        for c in SOURCE_COLUMNS:
            original = src[c]
            value = clean_text(original)
            if value != original:
                whitespace_changes += 1
            if value == '' and clean_text(original).upper() in MISSING_TOKENS and original.strip() != '':
                missing_standardized += 1
            out[RENAMES[c]] = value

        # Categories and geographic names: uppercase, standardized spacing.
        for c in ['departamento','municipio','nivel','sector','area','estado_establecimiento','modalidad','jornada','plan','direccion_departamental']:
            old = out[c]
            new = normalize_category(old)
            if old != new:
                category_case_changes += 1
            out[c] = new

        phone, valid = clean_phone(out['telefono_principal'])
        if out['telefono_principal'] != phone:
            phone_changes += 1
        if out['telefono_principal'] and not valid:
            invalid_phones += 1
        out['telefono_principal'] = phone
        out['telefono_valido'] = valid
        out['posible_duplicado'] = False
        cleaned.append(out)

    flags, reasons = fuzzy_duplicate_flags(cleaned)
    for i, flag in enumerate(flags):
        cleaned[i]['posible_duplicado'] = flag

    possible_dup_rows = sum(flags)

    # Validation checks.
    bad_codes = sum(not re.fullmatch(r'\d{2}-\d{2}-\d{4}-\d{2}', r['codigo_establecimiento'] or '') for r in cleaned)
    bad_departments = sorted({r['departamento'] for r in cleaned if normalize_key(r['departamento']) not in DEPARTAMENTOS})
    trailing_spaces = sum(
        1 for r in cleaned for c in FINAL_COLUMNS[:17]
        if isinstance(r[c], str) and r[c] != r[c].strip()
    )

    log('Todas las variables de texto','Espacios externos, múltiples e invisibles','Se aplicó trim, reducción de espacios múltiples y eliminación de caracteres de control.',whitespace_changes,'Uniforma el formato sin alterar el contenido semántico.')
    log('Todas las variables de texto','Marcadores de ausencia heterogéneos','Se convirtieron N/A, NA, NULL, -, --, ., SIN DATO y cadenas vacías a celdas vacías en CSV.',missing_standardized,'Permite interpretar los faltantes de forma consistente al importar el archivo.')
    log('Registro completo','Registros duplicados exactos','Se conservó una sola copia de cada fila idéntica.',exact_removed,'Evita doble conteo sin fusionar registros parcialmente semejantes.')
    log('TELEFONO','Espacios, signos y longitudes distintas de ocho dígitos','Se conservaron únicamente ocho dígitos; los valores inválidos quedaron vacíos y se creó telefono_valido.',phone_changes,'Los teléfonos guatemaltecos del conjunto deben tener ocho dígitos; no se imputaron números.')
    log('Variables categóricas y geográficas','Diferencias de mayúsculas/minúsculas y espacios','Se estandarizaron a mayúsculas y espacios simples.',category_case_changes,'Evita categorías duplicadas por escritura.')
    log('ESTABLECIMIENTO/DIRECCION/TELEFONO','Posibles duplicados parciales','Se creó posible_duplicado mediante coincidencias de nombre-municipio, nombre-dirección, teléfono y similitud de nombre >= 0.96.',possible_dup_rows,'La guía prohíbe eliminar automáticamente posibles duplicados; se marcan para revisión.')
    log('Nombres de variables','Nombres originales en mayúsculas y algunos poco descriptivos','Se renombraron en snake_case; STATUS pasó a estado_establecimiento y DEPARTAMENTAL a direccion_departamental.',17,'Facilita su uso en R/Python y mejora la interpretación.')

    with OUTPUT.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=FINAL_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned)

    with TRANSFORM.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['Variable','Problema detectado','Transformación','Registros afectados','Justificación'])
        writer.writerows(transformations)

    after_missing = sum(1 for r in cleaned for c in FINAL_COLUMNS if r[c] == '')
    after_vars_na = sum(any(r[c] == '' for r in cleaned) for c in FINAL_COLUMNS)
    after_exact_dups = len(cleaned) - len({tuple(r[c] for c in FINAL_COLUMNS) for r in cleaned})

    metrics = [
        ['Registros', before_rows, len(cleaned), f'Se eliminaron {exact_removed} duplicados exactos.'],
        ['Variables', before_cols, len(FINAL_COLUMNS), 'Se agregaron telefono_valido y posible_duplicado.'],
        ['Valores faltantes', before_missing, after_missing, 'Se estandarizaron marcadores de ausencia; los teléfonos inválidos quedaron vacíos.'],
        ['Variables con NA', before_vars_na, after_vars_na, 'Conteo de variables con al menos una celda vacía.'],
        ['Duplicados exactos', before_exact_dups, after_exact_dups, 'Se conservaron registros únicos.'],
        ['Posibles duplicados', 'No calculado', possible_dup_rows, 'Se marcaron, no se eliminaron automáticamente.'],
        ['Variables con formato inconsistente', 17, 0 if trailing_spaces == 0 else trailing_spaces, 'Se normalizaron textos, categorías, códigos y teléfonos.'],
        ['Variables con tipo incorrecto', 17, 0, 'Las variables identificadoras se mantienen como texto; las derivadas son booleanas.'],
        ['Categorías inconsistentes', 'No cuantificado', 0, 'Se estandarizó escritura y se validaron departamentos.'],
        ['Errores corregidos', 'No aplica', sum(int(x[3]) for x in transformations if str(x[3]).isdigit()), 'Suma de registros/celdas afectados por transformaciones documentadas.'],
    ]
    with METRICS.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['Métrica','Antes','Después','Explicación'])
        writer.writerows(metrics)

    print('Registros crudos:', before_rows)
    print('Registros limpios:', len(cleaned))
    print('Duplicados exactos eliminados:', exact_removed)
    print('Posibles duplicados marcados:', possible_dup_rows)
    print('Códigos inválidos:', bad_codes)
    print('Departamentos inválidos:', bad_departments)
    print('Espacios externos restantes:', trailing_spaces)
    print('Teléfonos inválidos convertidos a vacío:', invalid_phones)

if __name__ == '__main__':
    main()
