import time
import sys
import subprocess
import re
from curl_cffi import requests
import undetected_chromedriver as uc

TARGET_URL = "https://www.drayage.com/directory/dray-rates.cfm?state=IL"

def obtener_version_chrome_sistema():
    """Detecta automáticamente la versión principal de Chrome instalada en el sistema operativo."""
    try:
        # Comando para consultar la versión de chrome/chromium en Linux o Windows
        cmd = ["google-chrome", "--version"] if sys.platform.startswith("linux") else ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        
        # Extraemos el número de versión mayor usando expresiones regulares (ej: 154, 155, etc.)
        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
        if match:
            version_mayor = int(match.group(1))
            print(f"Versión de Chrome detectada en el sistema: {version_mayor}")
            return version_mayor
    except Exception as e:
        print(f"No se pudo detectar automáticamente la versión: {e}")
    
    return None

def obtener_cookies_cloudflare():
    print("Fase 1: Configurando Selenium con autodetección de versión...")
    
    options = uc.ChromeOptions()
    
    if sys.platform.startswith("linux"):
        options.headless = True
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    else:
        options.headless = False
        options.add_argument("--window-position=-2000,-2000")
        options.add_argument("--window-size=1024,768")

    # Detectamos la versión exacta que tiene el runner o tu PC en este preciso instante
    version_sistema = obtener_version_chrome_sistema()
    
    # Inicializamos el driver pasando dinámicamente la versión detectada
    if version_sistema:
        driver = uc.Chrome(options=options, version_main=version_sistema, use_subprocess=True)
    else:
        # Fallback por si la detección falla
        driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print(f"Navegando a {TARGET_URL} para generar la sesión...")
        driver.get(TARGET_URL)
        
        print("Esperando la resolución del desafío de Cloudflare (12 segundos)...")
        time.sleep(12)
        
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        print("✅ Cookies de sesión capturadas exitosamente.")
        return cookies_dict, user_agent
        
    finally:
        print("Cerrando la instancia de Selenium...")
        driver.quit()

def extraer_datos_con_curl(cookies, user_agent):
    print("\nFase 2: Ejecutando peticiones con curl_cffi...")
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.drayage.com/",
    }
    
    try:
        response = requests.get(
            TARGET_URL,
            impersonate="chrome110",
            headers=headers,
            cookies=cookies,
            timeout=20
        )
        
        print(f"Código HTTP de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ¡Bypass y extracción exitosos en GitHub Actions!")
            print("Fragmento del HTML obtenido:")
            print(response.text[:500])
        else:
            print(f"❌ El servidor rechazó la petición. Código: {response.status_code}")
            
    except Exception as e:
        print(f"Error durante la petición HTTP: {e}")

def main():
    cookies, user_agent = obtener_cookies_cloudflare()
    
    if cookies:
        extraer_datos_con_curl(cookies, user_agent)
    else:
        print("❌ No se pudieron obtener las cookies de sesión necesarias.")

if __name__ == "__main__":
    main()