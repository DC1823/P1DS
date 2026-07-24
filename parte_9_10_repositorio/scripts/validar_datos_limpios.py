import csv
import re
from collections import Counter
from pathlib import Path

RUTA = Path('datos/DATOS_LIMPIOS.csv')
COLUMNAS = [
    'codigo_establecimiento','distrito','departamento','municipio','establecimiento',
    'direccion','telefono_principal','supervisor','director','nivel','sector','area',
    'estado_establecimiento','modalidad','jornada','plan','direccion_departamental',
    'telefono_valido','posible_duplicado'
]
DEPARTAMENTOS = {
    'ALTA VERAPAZ','BAJA VERAPAZ','CHIMALTENANGO','CHIQUIMULA','EL PROGRESO','ESCUINTLA',
    'GUATEMALA','HUEHUETENANGO','IZABAL','JALAPA','JUTIAPA','PETEN','QUETZALTENANGO',
    'QUICHE','RETALHULEU','SACATEPEQUEZ','SAN MARCOS','SANTA ROSA','SOLOLA',
    'SUCHITEPEQUEZ','TOTONICAPAN','ZACAPA'
}
DOMINIOS = {
    'nivel': {'DIVERSIFICADO'},
    'sector': {'COOPERATIVA','MUNICIPAL','OFICIAL','PRIVADO'},
    'area': {'RURAL','URBANA','SIN ESPECIFICAR'},
    'estado_establecimiento': {'ABIERTA','CERRADA DEFINITIVAMENTE','CERRADA TEMPORALMENTE','TEMPORAL NOMBRAMIENTO','TEMPORAL TITULOS'},
    'modalidad': {'BILINGUE','MONOLINGUE'},
    'jornada': {'DOBLE','INTERMEDIA','MATUTINA','NOCTURNA','SIN JORNADA','VESPERTINA'},
}

def fail(msg, errors):
    errors.append(msg)
    print('[X]', msg)

def ok(msg):
    print('[✓]', msg)

def main():
    with RUTA.open(encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    errors = []
    if list(rows[0].keys()) == COLUMNAS: ok('Estructura de 19 columnas correcta.')
    else: fail('Las columnas no coinciden con el esquema final.', errors)

    tuples = [tuple(r[c] for c in COLUMNAS) for r in rows]
    dups = len(tuples)-len(set(tuples))
    if dups == 0: ok('No existen duplicados exactos.')
    else: fail(f'Existen {dups} duplicados exactos.', errors)

    spaces = [(i+2,c) for i,r in enumerate(rows) for c in COLUMNAS[:17] if r[c] != r[c].strip()]
    if not spaces: ok('No existen espacios al inicio o final de textos.')
    else: fail(f'Existen {len(spaces)} celdas con espacios externos.', errors)

    invalid_phone = [r['telefono_principal'] for r in rows if r['telefono_principal'] and not re.fullmatch(r'\d{8}',r['telefono_principal'])]
    mismatch_phone = [i+2 for i,r in enumerate(rows) if (r['telefono_valido']=='True') != bool(r['telefono_principal'] and re.fullmatch(r'\d{8}',r['telefono_principal']) and len(set(r['telefono_principal']))>1)]
    if not invalid_phone and not mismatch_phone: ok('Teléfonos y bandera telefono_valido son consistentes.')
    else: fail(f'Teléfonos inválidos: {len(invalid_phone)}; banderas inconsistentes: {len(mismatch_phone)}.', errors)

    invalid_dep = sorted({r['departamento'] for r in rows if r['departamento'] and r['departamento'] not in DEPARTAMENTOS})
    if not invalid_dep: ok('Departamentos no vacíos pertenecen al catálogo de 22 departamentos.')
    else: fail(f'Departamentos inválidos: {invalid_dep}', errors)

    for col, domain in DOMINIOS.items():
        invalid = sorted({r[col] for r in rows if r[col] and r[col] not in domain})
        if invalid: fail(f'{col}: valores fuera de dominio {invalid}', errors)
        else: ok(f'{col}: valores dentro del dominio permitido.')

    bad_codes = [r['codigo_establecimiento'] for r in rows if r['codigo_establecimiento'] and not re.fullmatch(r'\d{2}-\d{2}-\d{4}-\d{2}',r['codigo_establecimiento'])]
    if not bad_codes: ok('Todos los códigos no vacíos cumplen el formato NN-NN-NNNN-NN.')
    else: fail(f'Códigos con formato inválido: {len(bad_codes)}.', errors)

    print('\n'+'='*50)
    if errors:
        print('ESTADO: APROBADO CON OBSERVACIONES')
        for e in errors: print('-',e)
    else:
        print('ESTADO: APROBADO')
    print('Registros:',len(rows))
    print('Posibles duplicados marcados:',sum(r['posible_duplicado']=='True' for r in rows))
    print('Registros sin código:',sum(not r['codigo_establecimiento'] for r in rows))
    print('Registros sin departamento:',sum(not r['departamento'] for r in rows))

if __name__=='__main__': main()
