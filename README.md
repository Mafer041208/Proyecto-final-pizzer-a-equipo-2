# 🍕 Amore & Masa - Sistema de Gestión de Pedidos e Inventario (POS)

Sistema integral de Punto de Venta (POS), control de inventario en gramos y gestión de ventas en tiempo real diseñado para la pizzería artesanal estilo napolitano **Amore & Masa**, ubicada en Monterrey, Nuevo León.

---

## 📋 Tabla de Contenidos

* [Descripción del Proyecto]
* [Problemática y Solución]
* [Características Principales]
* [Arquitectura y Tecnologías]
* [Reglas de Negocio]
* [Estructura de la Base de Datos]
* [Instalación y Configuración]
* [Estructura del Proyecto]
* [Equipo de Desarrollo y Créditos]

---

## 📖 Descripción del Proyecto

**Amore & Masa** es una pizzería artesanal que experimentó un acelerado crecimiento en sus primeros meses de operación. Este sistema sustituye el manejo manual basado en libretas y mensajes de WhatsApp por una solución digital centralizada y visual, la cual automatiza el flujo de caja, el cálculo de impuestos y descuentos, y la deducción exacta de materia prima por pizza vendida.

---

## 🚨 Problemática y Solución

| 🔴 Problemática Manual Anterior | 🟢 Solución Automatizada (POS) |
| :--- | :--- |
| **Desabasto imprevisto:** Insumos agotados a mitad de servicio sin aviso previo. | **Verificación de stock:** Valida la disponibilidad exacta en gramos antes de confirmar cualquier orden. |
| **Errores de cobro:** Inconsistencias en el cálculo de IVA, descuentos y entrega de cambio. | **Motor financiero:** Aplica IVA del 16%, descuentos autorizados y calcula el cambio exacto o valida tarjetas. |
| **Sin visibilidad por turno:** Falta de control en ventas totales y folios emitidos. | **Operación Multi-Caja:** Registro independiente por caja (Caja 1 y 2) con folios únicos y reporte diario. |
| **Pérdida de historial:** Sin registro permanente ni centralizado de las transacciones. | **Base de datos SQLite:** Almacenamiento relacional estructurado y seguro que no se borra al cerrar la sesión. |
---

## ✨ Características Principales

* **🔐 Autenticación y Asignación de Caja:** Control de acceso por credenciales con selección de estación de trabajo (Caja #1 o Caja #2) y personalización del ticket con el nombre del cajero.
* **🛒 Punto de Venta Interactivo (POS):** Captura de pedidos por especialidad y tamaño en tiempo real con precálculo de totales antes de procesar.
* **📦 Control de Inventario Compartido:** Gestión en gramos compartida entre múltiples cajas con alertas de stock crítico ($\le 500\text{ g}$).
* **💳 Modos de Pago Flexibles:**
* **Efectivo:** Validación de importe recibido y cálculo automático de cambio.
* **Tarjeta:** Exige y valida un código de autorización bancario de 6 dígitos obligatorios.


* **🧾 Generación de Tickets:** Recibo digital estructurado con desglose de Subtotal, Descuento, IVA (16%), Total, Cajero y Folio único por caja.
* **📊 Reportes y Corte de Caja:** Monitoreo del volumen de pizzas vendidas, ingresos acumulados y desglose por especialidad (Pepperoni vs. Hawaiana).
* **🔄 Reabastecimiento de Insumos:** Módulo directo para incrementar inventarios al recibir insumos de proveedores.

---

## 🛠️ Arquitectura y Tecnologías

El proyecto está desarrollado completamente en **Python 3** e implementa un patrón modular de separación entre la interfaz de usuario, la lógica de negocio y el acceso a datos.

* **Lenguaje:** Python 3.10+
* **Interfaz Gráfica:** Streamlit (UI Reactiva & Custom CSS)
* **Base de Datos:** SQLite3 (Motor relacional embebido)
* **Módulos Nativos:** `json`, `sqlite3`, `datetime`, `pathlib`

---

## 📐 Reglas de Negocio

### 1. Insumos Base por Pizza Chica (1.0x)



* **Harina de Trigo:** $250\text{ g}$
* **Queso Mozzarella:** $150\text{ g}$
* **Salsa de Tomate Italiana:** $100\text{ g}$
* **Pepperoni (Solo Pepperoni):** $80\text{ g}$
* **Jamón / Piña (Solo Hawaiana):** $70\text{ g}$ c/u

### 2. Escalabilidad por Tamaño (Multiplicadores)

$$\text{Consumo Real} = \text{Receta Base} \times \text{Multiplicador} \times \text{Cantidad}$$

* **Chica:** Multiplicador $1.0\times$
* **Mediana:** Multiplicador $1.5\times$
* **Grande:** Multiplicador $2.0\times$

### 3. Fórmulas Financieras

* $\text{Subtotal} = \sum (\text{Precio Base} \times \text{Multiplicador} \times \text{Cantidad})$
* $\text{Descuento} = \text{Subtotal} \times \text{Tasa Selected (0\%, 5\%, 10\%, 15\%)}$
* $\text{Base Imponible} = \text{Subtotal} - \text{Descuento}$
* $\text{IVA (16\%)} = \text{Base Imponible} \times 0.16$
* $\text{Total} = \text{Base Imponible} + \text{IVA}$

---

## 🗄️ Estructura de la Base de Datos

El archivo `pizzeria_app.db` consta de tres tablas relacionales auto-administradas:

```sql
-- Control de insumos
CREATE TABLE inventory (
    ingredient TEXT PRIMARY KEY,
    quantity REAL NOT NULL CHECK (quantity >= 0)
);

-- Estado financiero acumulado por caja
CREATE TABLE drawers (
    drawer_id INTEGER PRIMARY KEY CHECK (drawer_id IN (1, 2)),
    pizzas INTEGER NOT NULL DEFAULT 0,
    pepperoni INTEGER NOT NULL DEFAULT 0,
    hawaiian INTEGER NOT NULL DEFAULT 0,
    folio INTEGER NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0
);

-- Historial detallado de transacciones y tickets
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sold_at TEXT NOT NULL,
    drawer_id INTEGER NOT NULL,
    ticket TEXT NOT NULL,
    username TEXT NOT NULL,
    nickname TEXT NOT NULL,
    items TEXT NOT NULL,
    pizzas INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    discount REAL NOT NULL,
    tax REAL NOT NULL,
    total REAL NOT NULL,
    payment TEXT NOT NULL,
    cash_received REAL NOT NULL,
    change_due REAL NOT NULL
);

```

---

## 🚀 Instalación y Configuración

### Prerrequisitos

Asegúrate de contar con Python 3.10 o superior instalado en tu sistema.

### Pasos de Ejecución

1. **Clonar el repositorio:**
```bash
git clone https://github.com/tu-usuario/amore-y-masa-pos.git
cd amore-y-masa-pos

```


2. **Crear y activar un entorno virtual (Opcional pero recomendado):**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

```


3. **Instalar dependencias:**
```bash
pip install streamlit

```


4. **Iniciar la aplicación:**
```bash
streamlit run app.py

```


5. **Acceder a la aplicación:**
Abre tu navegador e ingresa a `http://localhost:8501`.

---

## 👤 Credenciales de Prueba

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `1234` | Administrador / Cajero |
| `cajero` | `5678` | Operador de Caja |

---

## 📁 Estructura del Proyecto

```text
amore-y-masa-pos/
├── app.py                # Aplicación principal de Streamlit y lógica de negocio
├── pizzeria_app.db       # Base de datos SQLite (se genera automáticamente)
├── logo.png              # Identidad visual de la pizzería
└── README.md             # Documentación general del proyecto

```

---

## 👥 Equipo de Desarrollo y Créditos

Este proyecto fue desarrollado como Entrega Final para la materia **Fundamentos de Programación** en la **Universidad Tecmilenio**.

### Autores

* 👨‍💻 **Diego Antonio Vargas Ramírez**
* 👨‍💻 **Andoni Acevedo Martínez**
* 👩‍💻 **Ana Teresa Ramírez Hernández**
* 👩‍💻 **María Fernanda Gutiérrez Córdova**
* 👨‍💻 **Mario Vargas Gamboa**

### Docente Evaluador

* 👩‍🏫 **Blanca Aracely Aranda Machorro**


### Asesoría Técnica

* 👨‍💼 **Francisco Arturo Zevada Hurtado** (Especialista en TI)

---

*Amore & Masa — Pizzería Artesanal Napolitana, Monterrey, N.L., México.*
