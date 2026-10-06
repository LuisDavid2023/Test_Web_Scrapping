import time
import sys
from curl_cffi import requests
import undetected_chromedriver as uc

TARGET_URL = "https://www.drayage.com/directory/dray-rates.cfm?state=IL"

def obtener_cookies_cloudflare():
    print("Fase 1: Configurando Selenium para el entorno de ejecución...")
    
    options = uc.ChromeOptions()
    
    # Si estamos en Linux (GitHub Actions), obligatoriamente usamos headless avanzado
    # Si estamos en tu PC local, podemos usar la posición oculta anterior.
    if sys.platform.startswith("linux"):
        options.headless = True
        options.add_argument("--headless=new")
    else:
        options.headless = False
        options.add_argument("--window-position=-2000,-2000")
        options.add_argument("--window-size=1024,768")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Inicializamos el driver (en GitHub Actions descargará el chromedriver compatible con Linux automáticamente)
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print(f"Navegando a {TARGET_URL} para generar la sesión...")
        driver.get(TARGET_URL)
        
        print("Esperando la resolución del desafío de Cloudflare (12 segundos)...")
        time.sleep(12)
        
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        print("✅ Cookies de sesión capturadas exitosamente en la nube.")
        return cookies_dict, user_agent
        
    finally:
        print("Cerrando la instancia de Selenium...")
        driver.quit()

def extraer_datos_con_curl(cookies, user_agent):
    print("\nFase 2: Ejecutando peticiones con curl_cffi a través del túnel WARP...")
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.drayage.com/",
    }
    
    # Nota: Como el script correrá en la misma máquina virtual donde se conecta WARP,
    # el tráfico saldrá automáticamente por el proxy local configurado en el pipeline.
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
            # AQUÍ EN EL FUTURO CONECTAREMOS EL POST A BASE44
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