# scrapper.py
from curl_cffi import requests

TARGET_URL = "https://www.drayage.com/directory/dray-rates.cfm?state=IL"

def main():
    print(f"Iniciando petición a través del túnel WARP...")
    
    # Enrutamos el tráfico HTTP/HTTPS por el proxy SOCKS5 local de WARP
    proxies = {
        "http": "socks5://127.0.0.1:40000",
        "https": "socks5://127.0.0.1:40000"
    }
    
    try:
        response = requests.get(
            TARGET_URL, 
            impersonate="chrome110", 
            proxies=proxies,
            timeout=30
        )
        
        print(f"Código HTTP de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Bypass exitoso. El firewall validó la conexión WARP con TLS falsificado.")
            print("Fragmento del HTML:")
            print(response.text[:500])
        else:
            print("❌ El servidor bloqueó la petición.")
            
    except Exception as e:
        print(f"Error de ejecución: {e}")

if __name__ == "__main__":
    main()