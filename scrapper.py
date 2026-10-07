import sys
import io

# Forzamos la codificación UTF-8 para evitar errores en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
import subprocess
import re
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ESTADOS_OBJETIVO = ["IL", "CA", "TX"]

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
    
    try:
        # Sincronización inteligente: Esperamos hasta 25 segundos a que el WAF libere 
        # la redirección y aparezca al menos una fila de la tabla en el DOM.
        print("Esperando a que Cloudflare libere la página y cargue la tabla...")
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr.rowhoverhighlight"))
        )
        print("¡Tabla detectada correctamente en el DOM!")
    except Exception as e:
        print(f"[AVISO] Tiempo de espera agotado esperando la tabla para {estado}: {e}")
    
    # Extraemos el HTML una vez que los elementos están listos
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    
    filas = soup.find_all('tr', class_='rowhoverhighlight')
    print(f"Filas limpias capturadas para {estado}: {len(filas)}")
    
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
            
    print(f"[EXITO] Se procesaron {len(registros_limpios)} registros para {estado}.")
    return registros_limpios

def main():
    print("Iniciando automatización con espera inteligente (WebDriverWait)...")
    
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
            time.sleep(3)
            
        print(f"\n--- RESUMEN GENERAL ---")
        print(f"Total acumulado de registros recolectados: {len(todos_los_datos)}")
        if todos_los_datos:
            print("Muestra del primer registro estructurado:")
            print(todos_los_datos[0])
            
    except Exception as e:
        print(f"Error crítico en el proceso: {e}")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()