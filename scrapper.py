# scraper.py
from curl_cffi import requests

TARGET_URL = "https://www.drayage.com/directory/dray-rates.cfm?state=IL"

def main():
    print(f"Iniciando petición a: {TARGET_URL}")
    
    try:
        # El parámetro impersonate="chrome110" falsifica el TLS Handshake
        response = requests.get(TARGET_URL, impersonate="chrome110", timeout=15)
        
        print(f"Código HTTP de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Bypass exitoso. El firewall permitió la conexión.")
            # Imprimimos los primeros 500 caracteres para confirmar que tenemos el HTML
            print("Fragmento del HTML:")
            print(response.text[:500])
        else:
            print("❌ El bypass falló. El servidor bloqueó la petición.")
            
    except Exception as e:
        print(f"Error de ejecución: {e}")

if __name__ == "__main__":
    main()