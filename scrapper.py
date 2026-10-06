# scrapper.py
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.drayage.com/directory/dray-rates.cfm?state=IL"

def main():
    print(f"Iniciando navegador Playwright para acceder a: {TARGET_URL}")
    
    with sync_playwright() as p:
        # Lanzamos Chromium en modo headless
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Falsificamos el User-Agent para imitar un entorno de escritorio común
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        try:
            # wait_until="domcontentloaded" espera a que el HTML base y scripts se ejecuten
            response = page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Playwright devuelve un objeto response; si es None, hubo un error de red
            status = response.status if response else "Desconocido"
            print(f"Código HTTP de respuesta: {status}")
            
            if status == 200:
                print("✅ Bypass exitoso. El firewall permitió la conexión con el navegador real.")
                html = page.content()
                print("Fragmento del HTML:")
                print(html[:500])
            else:
                print("❌ El bypass falló. El servidor bloqueó la petición.")
                
        except Exception as e:
            print(f"Error de ejecución: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    main()