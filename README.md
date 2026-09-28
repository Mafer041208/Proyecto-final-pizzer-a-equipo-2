# Proyecto-final-pizzer-a-equipo-2

Sistema de caja para una pizzería. El programa original de consola sigue disponible en `# Pizzeria avance 4.py`; `app.py` es una versión web inicial.

## Ejecutar la app web

Desde la terminal de VS Code, en la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit abrirá la app en `http://localhost:8501`.

Accesos de prueba: `admin` / `1234` o `cajero` / `5678`.

La app guarda inventario, cajas y ventas en `pizzeria_app.db`. Esa base se crea al iniciar y se conserva entre ejecuciones. Las credenciales son únicamente para pruebas; cámbialas antes de publicar la app o usarla con información real.
