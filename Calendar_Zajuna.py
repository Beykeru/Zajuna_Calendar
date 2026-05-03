import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import tkinter as tk
from tkinter import messagebox, filedialog # Agregamos filedialog
import os

class BotStatusWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Extracción de eventos - Zajuna")
        self.root.geometry("350x180+1000+150") 
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#f0f0f0")
        
        self.label = tk.Label(self.root, text="Iniciando...", font=("Arial", 11, "bold"), bg="#f0f0f0", wraplength=350)
        self.label.pack(pady=20)
        
        self.timer_label = tk.Label(self.root, text="", font=("Consolas", 14), fg="#d32f2f", bg="#f0f0f0")
        self.timer_label.pack(pady=10)
        
    def actualizar(self, mensaje, tiempo=""):
        self.label.config(text=mensaje)
        if tiempo:
            self.timer_label.config(text=f"Tiempo restante: {tiempo}s")
        else:
            self.timer_label.config(text="")
        self.root.update()

    def cerrar(self):
        self.root.destroy()

def sincronizador_zajuna():
    status = BotStatusWindow()
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True) 
    
    driver = webdriver.Chrome(options=options)
    wait_action = WebDriverWait(driver, 20)

    while True:
        try:
            status.actualizar("Abriendo Zajuna...")
            driver.get("https://zajuna.sena.edu.co")
            
            tiempo_limite = 180
            logueado = False
            status.actualizar("Esperando ingreso manual...")
            
            for segundo in range(tiempo_limite, 0, -1):
                status.actualizar("Esperando ingreso manual...", segundo)
                elementos = driver.find_elements(By.ID, "page-my-index")
                if elementos:
                    logueado = True
                    break
                time.sleep(1) 
            
            if not logueado:
                raise Exception("Tiempo de espera para login agotado.")

            status.actualizar("Entrando al curso de ADSO...")
            driver.get("https://zajuna.sena.edu.co/zajuna/course/view.php?id=109418")

            status.actualizar("Navegando al calendario...")
            enlace_cal = wait_action.until(EC.presence_of_element_located((By.LINK_TEXT, "Full calendar")))
            driver.execute_script("arguments[0].click();", enlace_cal)

            status.actualizar("Cargando eventos...")
            time.sleep(7) 
            
            datos_calendario = []
            elementos_evento = driver.find_elements(By.CSS_SELECTOR, "a[data-type='event'], .eventname")
            
            for evento in elementos_evento:
                try:
                    nombre_tarea = evento.text.strip()
                    if not nombre_tarea or nombre_tarea.lower().startswith("hide"):
                        continue
                    contenedor_dia = evento.find_element(By.XPATH, "./ancestor::td[contains(@class, 'day')]")
                    fecha = contenedor_dia.get_attribute("data-title")
                    datos_calendario.append({"Evidencia": nombre_tarea, "Fecha_SENA": fecha, "Estado": "Pendiente"})
                except:
                    continue

            df = pd.DataFrame(datos_calendario)
            
            if not df.empty:
                # --- VENTANA PARA PREGUNTAR DÓNDE GUARDAR ---
                status.actualizar("Esperando ubicación de guardado...")
                ruta_excel = filedialog.asksaveasfilename(
                    title="Guardar Control de Evidencias ADSO",
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    initialfile="mis_tareas_zajuna.xlsx"
                )

                if ruta_excel:
                    # 1. Guardar Excel
                    df['Fecha_SENA'] = df['Fecha_SENA'].str.replace(' events', '', case=False)
                    df.to_excel(ruta_excel, index=False)
                    
                    # 2. Generar y Guardar CSV para Calendar en la misma ubicación
                    df_calendar = df.copy()
                    fechas_dt = pd.to_datetime(df_calendar['Fecha_SENA'], errors='coerce')
                    df_calendar['Start Date'] = fechas_dt.apply(
                        lambda x: x.replace(year=2026).strftime('%m/%d/%Y') if pd.notnull(x) else ""
                    )
                    df_calendar = df_calendar.rename(columns={'Evidencia': 'Subject', 'Estado': 'Description'})
                    
                    ruta_csv = ruta_excel.replace(".xlsx", "_para_calendar.csv")
                    df_calendar[['Subject', 'Start Date', 'Description']].to_csv(
                        ruta_csv, index=False, sep=',', encoding='utf-8-sig'
                    )
                    
                    status.actualizar("Archivos guardados con éxito.")
                    messagebox.showinfo("Éxito", f"Archivos guardados en:\n\n1. {os.path.basename(ruta_excel)}\n2. {os.path.basename(ruta_csv)}")
                    
                    driver.quit()
                    status.cerrar()
                    break
                else:
                    status.actualizar("Guardado cancelado.")
                    if not messagebox.askretrycancel("Aviso", "No seleccionaste ubicación. ¿Reintentar?"):
                        driver.quit()
                        status.cerrar()
                        break
            else:
                status.actualizar("No se hallaron evidencias.")
                time.sleep(2)

        except Exception as e:
            status.actualizar("Error detectado.")
            if not messagebox.askretrycancel("Error", f"Ocurrió un problema:\n{e}"):
                driver.quit()
                status.cerrar()
                break

if __name__ == "__main__":
    sincronizador_zajuna()