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

ESTADOS_OBJETIVO = ["IL", "CA", "TX"]

def obtener_version_chrome_sistema():
    """Detecta automáticamente la versión principal de Chrome instalada en el sistema operativo."""
    try:
        if sys.platform.startswith("linux"):
            cmd = ["google-chrome", "--version"]
        else:
            cmd = ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Core\\Chrome\\BLBeacon", "/v", "version"]
            
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        
        if not output.strip() and not sys.platform.startswith("linux"):
            cmd_alt = ["reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Google\\Chrome\\BLBeacon", "/v", "version"]
            result_alt = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=5)
            output = result_alt.stdout + result_alt.stderr

        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
        if match:
            version_mayor = int(match.group(1))
            print(f"Version de Chrome detectada en el sistema: {version_mayor}")
            return version_mayor
    except Exception as e:
        print(f"Aviso en autodeteccion de version: {e}")
    
    return 154

def extraer_tarifas_estado(driver, estado):
    url = f"https://www.drayage.com/directory/dray-rates.cfm?state={estado}"
    print(f"\nConsultando tarifas para el estado: {estado} -> URL: {url}")
    
    driver.get(url)
    time.sleep(10) # Pausa táctica para Cloudflare
    
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if "attention required" in soup.text.lower() or "cloudflare" in soup.text.lower():
        print(f"[ALERTA] Cloudflare interceptó la sesión para el estado {estado}.")
        return []

    tabla_tarifas = soup.find('table')
    registros_limpios = []
    
    if tabla_tarifas:
        filas = tabla_tarifas.find_all('tr')[1:]
        for fila in filas:
            columnas = fila.find_all('td')
            if len(columnas) >= 4:
                registro = {
                    "origin": columnas[0].get_text(strip=True),
                    "destination": columnas[1].get_text(strip=True),
                    "state": estado,
                    "rate": columnas[3].get_text(strip=True)
                }
                registros_limpios.append(registro)
                
        print(f"[EXITO] Se extrajeron {len(registros_limpios)} registros limpios para {estado}.")
    else:
        print(f"[AVISO] No se visualizo la tabla de tarifas para {estado}.")
        
    return registros_limpios

def main():
    print("Iniciando automatizacion autonoma en entorno Windows (Cloud)...")
    
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument("--window-position=-2000,-2000")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    version_sistema = obtener_version_chrome_sistema()
    print(f"Configurando undetected-chromedriver con version_main={version_sistema}")
    
    driver = uc.Chrome(options=options, version_main=version_sistema, use_subprocess=True)
    
    try:
        todos_los_datos = []
        for estado in ESTADOS_OBJETIVO:
            datos_estado = extraer_tarifas_estado(driver, estado)
            todos_los_datos.extend(datos_estado)
            time.sleep(5)
            
        print(f"\n--- RESUMEN GENERAL ---")
        print(f"Total de registros limpios recolectados: {len(todos_los_datos)}")
        if todos_los_datos:
            print("Muestra del primer registro estructurado:")
            print(todos_los_datos[0])
            
    except Exception as e:
        print(f"Error critico en el proceso de scraping: {e}")
        sys.exit(1)
    finally:
        print("Cerrando navegador autonomo...")
        driver.quit()

if __name__ == "__main__":
    main()