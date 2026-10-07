import time
import sys
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# Lista de estados intermodales objetivo que iteraremos por lotes
ESTADOS_OBJETIVO = ["IL", "CA", "TX"]  # Puedes expandir esta lista según tus necesidades

def extraer_tarifas_estado(driver, estado):
    url = f"https://www.drayage.com/directory/dray-rates.cfm?state={estado}"
    print(f"\nConsultando tarifas para el estado: {estado} -> URL: {url}")
    
    driver.get(url)
    
    # Pausa táctica de estabilización y resolución del desafío de Cloudflare por lote
    time.sleep(10)
    
    html_content = driver.page_source
    
    # Parseo y limpieza con BeautifulSoup (equivalente robusto a Cheerio en Python)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Verificamos si Cloudflare bloqueó la sesión
    if "attention required" in soup.text.lower() or "cloudflare" in soup.text.lower():
        print(f"❌ Alerta: Cloudflare interceptó la sesión para el estado {estado}.")
        return []

    tabla_tarifas = soup.find('table')
    registros_limpios = []
    
    if tabla_tarifas:
        filas = tabla_tarifas.find_all('tr')[1:] # Omitir encabezados
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
                
        print(f"✅ Éxito: Se extrajeron {len(registros_limpios)} registros limpios para {estado}.")
    else:
        print(f"⚠️ No se visualizó la tabla de tarifas para {estado}.")
        
    return registros_limpios

def main():
    print("Iniciando automatización autónoma en entorno Windows (Cloud)...")
    
    options = uc.ChromeOptions()
    # En Windows Runner podemos correr con ventana minimizada o headless nativo seguro de Windows
    options.headless = False # Windows maneja mejor el motor gráfico simulado
    options.add_argument("--window-position=-2000,-2000") # Oculto fuera de pantalla
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        todos_los_datos = []
        for estado in ESTADOS_OBJETIVO:
            datos_estado = extraer_tarifas_estado(driver, estado)
            todos_los_datos.extend(datos_estado)
            # Pausa de cortesía entre peticiones por lotes para evitar baneo por tasa de solicitudes (Rate Limiting)
            time.sleep(5)
            
        print(f"\n--- RESUMEN GENERAL ---")
        print(f"Total de registros limpios recolectados en todos los estados: {len(todos_los_datos)}")
        print("Muestra del primer registro estructurado:")
        if todos_los_datos:
            print(todos_los_datos[0])
            
    except Exception as e:
        print(f"Error crítico en el proceso de scraping: {e}")
        sys.exit(1)
    finally:
        print("Cerrando navegador autónomo...")
        driver.quit()

if __name__ == "__main__":
    main()