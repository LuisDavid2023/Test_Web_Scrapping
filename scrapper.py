import sys
import io

# Forzamos la codificación UTF-8 para evitar errores de caracteres especiales en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
import subprocess
import re
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

ESTADOS_OBJETIVO = ["IL"] # Probemos inicialmente solo con IL para aislar la prueba y acelerar el log

def obtener_version_chrome_sistema():
    """Detecta automáticamente la versión principal de Chrome instalada en el sistema."""
    try:
        if sys.platform.startswith("linux"):
            cmd = ["google-chrome", "--version"]
        else:
            cmd = ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"]
            
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        
        if not output.strip() and not sys.platform.startswith("linux"):
            cmd_alt = ["reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Google\\Chrome\\BLBeacon", "/v", "version"]
            result_alt = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=5)
            output = result_alt.stdout + result_alt.stderr

        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
        if match:
            version_mayor = int(match.group(1))
            print(f"Versión de Chrome detectada en el sistema: {version_mayor}")
            return version_mayor
    except Exception as e:
        print(f"Aviso en autodetección de versión: {e}")
    
    return 154

def extraer_tarifas_estado(driver, estado):
    url = f"https://www.drayage.com/directory/dray-rates.cfm?state={estado}"
    print(f"\nConsultando tarifas para el estado: {estado} -> URL: {url}")
    
    driver.get(url)
    time.sleep(12) # Pausa para renderizado de la página
    
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Imprimimos información vital de diagnóstico sobre lo que ve el navegador
    print(f"[DEBUG] Título de la página obtenida: {soup.title.string if soup.title else 'Sin título'}")
    
    # Buscamos filas por la clase específica
    filas = soup.find_all('tr', class_='rowhoverhighlight')
    print(f"[DEBUG] Filas encontradas con 'rowhoverhighlight': {len(filas)}")
    
    # Si no encuentra filas con la clase, imprimimos un fragmento del texto para analizarlo
    if len(filas) == 0:
        print("[DEBUG] Fragmento del texto de la página:", soup.get_text()[:300].replace('\n', ' '))

    registros_limpios = []
    for fila in filas:
        columnas = fila.find_all('td')
        if len(columnas) >= 4:
            origin = columnas[0].get_text(strip=True)
            zip_code = columnas[1].get_text(strip=True)
            state_dest = columnas[2].get_text(strip=True)
            city_dest = columnas[3].get_text(strip=True)
            
            rate_cell = fila.find('td', align='right')
            rate = rate_cell.get_text(strip=True) if rate_cell else "N/A"
            
            registro = {
                "origin": origin,
                "zip_code": zip_code,
                "state": state_dest if state_dest else estado,
                "city": city_dest,
                "rate": rate
            }
            registros_limpios.append(registro)
            
    print(f"[EXITO] Registros limpios extraídos para {estado}: {len(registros_limpios)}")
    return registros_limpios

def main():
    print("Iniciando automatización con auditoría de DOM...")
    
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument("--window-position=-2000,-2000")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    version_sistema = obtener_version_chrome_sistema()
    driver = uc.Chrome(options=options, version_main=version_sistema, use_subprocess=True)
    
    try:
        todos_los_datos = []
        for estado in ESTADOS_OBJETIVO:
            datos_estado = extraer_tarifas_estado(driver, estado)
            todos_los_datos.extend(datos_estado)
            
        print(f"\n--- RESUMEN GENERAL ---")
        print(f"Total acumulado de registros: {len(todos_los_datos)}")
        if todos_los_datos:
            print("Primer registro:", todos_los_datos[0])
            
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()