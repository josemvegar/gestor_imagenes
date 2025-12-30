import os
import json
import csv
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote

# ==========================================
#              CONFIGURACIÓN
# ==========================================

# 1. CONFIGURACIÓN DE RUTAS NUEVAS
NEW_URL_PREFIX = "https://firmavirtual.legal/wp-content/uploads/2025/12/"
NEW_URL_SUFFIX = ""  
INPUT_EXTENSIONS = ('.webp', '.jpg', '.jpeg', '.png', '.pdf', 'webm')

# 2. NOMBRES DE ARCHIVOS
FILE_LIST_JSON = "1_listado_nuevas.json"    
FILE_ALIGNED_CSV = "2_pares_alineados.csv"  
FILE_MAPPING_OUTPUT = "3_mapeo_final.py.txt" # Cambié la extensión para que sepas que es código python
FILE_ERRORS_JSON = "4_errores_404.json"     
FILE_ERRORS_CSV = "4_errores_404.csv"

# ==========================================
#              FUNCIONES AUXILIARES
# ==========================================

def agregar_sufijo(filename, sufijo):
    if not sufijo: return filename
    path = Path(filename)
    return f"{path.stem}{sufijo}{path.suffix}"

def obtener_stem_desde_url(url_o_nombre):
    """Extrae el nombre base limpio (sin extensión)"""
    if not url_o_nombre: return ""
    path = urlparse(url_o_nombre).path
    path_decoded = unquote(path)
    filename = os.path.basename(path_decoded)
    return Path(filename).stem.lower().strip()

# ==========================================
#              TAREAS
# ==========================================

def tarea_1_generar_listado_local():
    print("\n--- TAREA 1: Escaneando carpeta local ---")
    archivos = sorted([f for f in os.listdir('.') if f.lower().endswith(INPUT_EXTENSIONS)])
    
    listado_urls = []
    
    for archivo in archivos:
        nombre_final = agregar_sufijo(archivo, NEW_URL_SUFFIX)
        url_completa = f"{NEW_URL_PREFIX}{nombre_final}"
        
        listado_urls.append({
            "archivo_local": archivo,
            "url_generada": url_completa,
            "stem": obtener_stem_desde_url(archivo)
        })

    with open(FILE_LIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(listado_urls, f, indent=4)
        
    print(f"✅ Procesados {len(listado_urls)} archivos locales.")

def tarea_2_alineacion_inteligente():
    print("\n--- TAREA 2: Alineación Inteligente ---")
    
    if not os.path.exists(FILE_LIST_JSON):
        print("⚠️ Debes correr la Tarea 1 primero.")
        return

    csv_input_old = input("Ingresa el nombre del CSV con las URLs antiguas (ej. antiguas.csv): ")
    if not os.path.exists(csv_input_old):
        print("❌ Archivo no encontrado.")
        return

    # 1. Cargar lista NUEVA
    with open(FILE_LIST_JSON, 'r', encoding='utf-8') as f:
        lista_nueva = json.load(f)
    
    for item in lista_nueva:
        if 'stem' not in item:
            item['stem'] = obtener_stem_desde_url(item['archivo_local'])
    lista_nueva.sort(key=lambda x: x['stem'])

    # 2. Cargar lista ANTIGUA (CSV)
    lista_antigua = []
    with open(csv_input_old, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                full_url = row[0].strip()
                stem = obtener_stem_desde_url(full_url)
                if stem:
                    lista_antigua.append({"url_completa": full_url, "stem": stem})
    
    lista_antigua.sort(key=lambda x: x['stem'])

    # 3. Algoritmo de Alineación
    filas_alineadas = []
    i = 0 
    j = 0 
    matches = 0

    while i < len(lista_antigua) or j < len(lista_nueva):
        val_old = lista_antigua[i]['stem'] if i < len(lista_antigua) else "~"
        val_new = lista_nueva[j]['stem'] if j < len(lista_nueva) else "~"

        if val_old == val_new:
            filas_alineadas.append([lista_antigua[i]['url_completa'], lista_nueva[j]['url_generada']])
            i += 1; j += 1; matches += 1
        elif val_old < val_new:
            filas_alineadas.append([lista_antigua[i]['url_completa'], ""])
            i += 1
        else:
            filas_alineadas.append(["", lista_nueva[j]['url_generada']])
            j += 1

    with open(FILE_ALIGNED_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["OLD_URL_FULL", "NEW_URL_FULL"]) 
        writer.writerows(filas_alineadas)

    print(f"✅ Alineación completada. Coincidencias: {matches}")

def tarea_3_crear_mapeo_formato_custom():
    print("\n--- TAREA 3: Creando Diccionario (Sin backslashes) ---")
    
    if not os.path.exists(FILE_ALIGNED_CSV):
        print(f"⚠️ Primero ejecuta la Tarea 2.")
        return

    # Usaremos una lista de tuplas para mantener el orden
    mapeo_items = []
    
    try:
        with open(FILE_ALIGNED_CSV, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Saltar header
            
            for row in reader:
                if len(row) >= 2:
                    old_url = row[0].strip()
                    new_url = row[1].strip()
                    
                    if old_url and new_url:
                        # Construimos las cadenas EXACTAS que pides
                        # Usamos comillas dobles para el HTML
                        key = f'src="{old_url}"'
                        value = f'src="{new_url}"'
                        mapeo_items.append((key, value))
        
        # --- ESCRITURA MANUAL DEL ARCHIVO ---
        # No usamos json.dump para evitar el escapado automático (\)
        with open(FILE_MAPPING_OUTPUT, 'w', encoding='utf-8') as f:
            f.write("{\n") # Inicio del diccionario
            
            total = len(mapeo_items)
            for index, (k, v) in enumerate(mapeo_items):
                # Formato: 'key': 'value'
                # La coma va al final excepto en el último elemento
                coma = "," if index < total - 1 else ""
                
                # Escribimos la línea con indentación y comillas simples afuera
                linea = f"    '{k}' => '{v}'{coma}\n"
                f.write(linea)
                
            f.write("}") # Cierre del diccionario
            
        print(f"✅ Archivo generado con éxito: {len(mapeo_items)} pares.")
        print(f"📂 Archivo de salida: {FILE_MAPPING_OUTPUT}")
        print("ℹ️  Este archivo usa comillas simples (') para envolver las claves y valores.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def tarea_4_verificar_enlaces():
    print("\n--- TAREA 4: Verificando enlaces 404 ---")
    
    if not os.path.exists(FILE_LIST_JSON):
        print("⚠️ Ejecuta Tarea 1 primero.")
        return

    with open(FILE_LIST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errores = []
    print(f"Verificando {len(data)} enlaces...")
    headers = {'User-Agent': 'Mozilla/5.0'}

    for item in data:
        url = item['url_generada']
        try:
            res = requests.head(url, headers=headers, timeout=5)
            if res.status_code == 405: res = requests.get(url, headers=headers, timeout=5)

            if res.status_code == 404:
                print(f"❌ 404: {url}")
                errores.append(item)
        except:
            print(f"Error conexión: {url}")

    with open(FILE_ERRORS_JSON, 'w', encoding='utf-8') as f:
        json.dump(errores, f, indent=4)
    
    with open(FILE_ERRORS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["Archivo", "URL Fallida"])
        for e in errores: w.writerow([e['archivo_local'], e['url_generada']])

    print(f"Enlaces rotos encontrados: {len(errores)}")

def tarea_5_reparacion_automatica():
    print("\n--- TAREA 5: Reparación Automática (-1) ---")
    REPAIR_SUFFIX = "-1"

    if not os.path.exists(FILE_ERRORS_JSON) or not os.path.exists(FILE_LIST_JSON):
        print("⚠️ Faltan archivos.")
        return

    with open(FILE_LIST_JSON, 'r', encoding='utf-8') as f:
        listado = json.load(f)
    with open(FILE_ERRORS_JSON, 'r', encoding='utf-8') as f:
        errores = json.load(f)

    if not errores:
        print("No hay errores para reparar.")
        return

    archivos_erroneos = [e['archivo_local'] for e in errores]
    count = 0

    for item in listado:
        if item['archivo_local'] in archivos_erroneos:
            item['url_generada'] = f"{NEW_URL_PREFIX}{agregar_sufijo(item['archivo_local'], REPAIR_SUFFIX)}"
            count += 1

    with open(FILE_LIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(listado, f, indent=4)

    print(f"✅ Reparados {count} enlaces.")
    print("RECUERDA: Ejecuta Tarea 2 de nuevo para actualizar el mapeo con las URLs corregidas.")

# ==========================================
#              MENÚ
# ==========================================
def menu():
    while True:
        print("\n--- GESTOR DE URLs v4 (Salida limpia) ---")
        print("1. Escanear carpeta local")
        print("2. Generar CSV Alineado")
        print("3. Generar Diccionario Final (Formato Python limpio)")
        print("4. Verificar 404")
        print("5. Auto-corregir 404")
        print("6. Salir")
        
        op = input("Opción: ")
        if op == '1': tarea_1_generar_listado_local()
        elif op == '2': tarea_2_alineacion_inteligente()
        elif op == '3': tarea_3_crear_mapeo_formato_custom()
        elif op == '4': tarea_4_verificar_enlaces()
        elif op == '5': tarea_5_reparacion_automatica()
        elif op == '6': break

if __name__ == "__main__":
    menu()