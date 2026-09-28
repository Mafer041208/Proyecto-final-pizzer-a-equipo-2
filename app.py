import json
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Definimos el título que aparece en la pestaña del navegador y el ícono
st.set_page_config(
    page_title="Pizzería Amore & Masa | Caja 🍕",
    page_icon="🍕",
    layout="wide"
)

# Ruta donde se guardará el archivo de la base de datos SQLite en nuestra carpeta
DATABASE_PATH = Path(__file__).with_name("pizzeria_app.db")

# --- DATOS BASE DEL SISTEMA ---
# Usuarios registrados para probar el sistema (Usuario: Contraseña)
USERS = {
    "admin": "1234",
    "cajero": "5678"
}

# Insumos y gramos necesarios para una receta base (1 pizza chica)
INGREDIENTS = {
    "harina": ("Harina de Trigo", 250),
    "queso": ("Queso Mozzarella", 150),
    "salsa": ("Salsa de Tomate Italiana", 100),
    "pep": ("Pepperoni", 80),
    "jamon": ("Jamón", 70),
    "pina": ("Piña", 70),
}

# Multiplicadores para saber cuántos ingredientes usar según el tamaño
SIZES = {
    "Chica": 1.0,
    "Mediana": 1.5,
    "Grande": 2.0
}

# Precios base para cada especialidad
PIZZAS = {
    "Pepperoni": 120.0,
    "Hawaiana": 115.0
}

# Límite para mostrar la alerta amarilla de stock bajo (en gramos)
LOW_STOCK_LIMIT = 500


# --- FUNCIONES DE BASE DE DATOS (SQLITE) ---

# Abre la conexión con la base de datos sqlite3
def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

# Crea las tablas si no existen la primera vez que se abre la app
def initialize_database():
    with connect_database() as connection:
        # Tabla para rastrear la cantidad de ingredientes disponibles
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                ingredient TEXT PRIMARY KEY,
                quantity REAL NOT NULL CHECK (quantity >= 0)
            )
            """
        )
        # Tabla para guardar el resumen acumulado de cada caja (Caja 1 y Caja 2)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS drawers (
                drawer_id INTEGER PRIMARY KEY CHECK (drawer_id IN (1, 2)),
                pizzas INTEGER NOT NULL DEFAULT 0,
                pepperoni INTEGER NOT NULL DEFAULT 0,
                hawaiian INTEGER NOT NULL DEFAULT 0,
                folio INTEGER NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0
            )
            """
        )
        # Tabla donde guardamos cada venta realizada (el historial de tickets)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sales (
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
            )
            """
        )
        # Carga del inventario inicial (en gramos) si está vacío
        connection.executemany(
            "INSERT OR IGNORE INTO inventory (ingredient, quantity) VALUES (?, ?)",
            [
                ("harina", 5000.0),
                ("queso", 3000.0),
                ("salsa", 2000.0),
                ("pep", 1000.0),
                ("jamon", 1000.0),
                ("pina", 1000.0),
            ],
        )
        # Habilitar los registros iniciales para las dos cajas disponibles
        connection.executemany(
            "INSERT OR IGNORE INTO drawers (drawer_id) VALUES (?)",
            [(1,), (2,)],
        )

# Trae las existencias actuales del inventario
def load_inventory():
    with connect_database() as connection:
        rows = connection.execute(
            "SELECT ingredient, quantity FROM inventory"
        ).fetchall()
    return {row["ingredient"]: row["quantity"] for row in rows}

# Trae los datos guardados de la caja seleccionada
def load_drawer(drawer_id):
    with connect_database() as connection:
        return connection.execute(
            "SELECT * FROM drawers WHERE drawer_id = ?", (drawer_id,)
        ).fetchone()

# Función rápida para darle formato visual bonito de dinero a los precios ($120.00)
def format_money(value):
    return f"${value:,.2f}"


# --- PROCESAMIENTO Y LÓGICA DE LA VENTA ---

# Esta función calcula los totales, revisa si hay insumos suficientes y guarda la compra
def save_sale(drawer_id, username, nickname, items, discount_rate, payment, cash_received, card_auth_code=""):
    # Hacemos los cálculos matemáticos (Subtotal, Descuento, IVA 16% y Total)
    subtotal = round(sum(item["price"] * item["quantity"] for item in items), 2)
    discount = round(subtotal * discount_rate, 2)
    discounted_subtotal = round(subtotal - discount, 2)
    tax = round(discounted_subtotal * 0.16, 2)
    total = round(discounted_subtotal + tax, 2)

    # Validamos que el dinero entregado sea suficiente si es en efectivo
    if payment == "Efectivo" and cash_received < total:
        return False, f"Faltan {format_money(total - cash_received)} para completar el pago."

    # Calculamos exactamente cuántos gramos de ingrediente se gastarán
    requirements = {key: 0.0 for key in INGREDIENTS}
    for item in items:
        multiplier = SIZES[item["size"]]
        recipe = ("pep",) if item["pizza"] == "Pepperoni" else ("jamon", "pina")
        requirements["harina"] += 250 * multiplier * item["quantity"]
        requirements["queso"] += 150 * multiplier * item["quantity"]
        requirements["salsa"] += 100 * multiplier * item["quantity"]
        for ingredient in recipe:
            requirements[ingredient] += INGREDIENTS[ingredient][1] * multiplier * item["quantity"]

    connection = connect_database()
    try:
        connection.execute("BEGIN IMMEDIATE")
        
        # Comprobamos que no se intente vender algo si no hay suficiente ingrediente
        stock = {
            row["ingredient"]: row["quantity"]
            for row in connection.execute("SELECT ingredient, quantity FROM inventory")
        }
        insufficient = [
            INGREDIENTS[key][0]
            for key, amount in requirements.items()
            if stock[key] < amount
        ]
        if insufficient:
            connection.rollback()
            return False, "Inventario insuficiente de: " + ", ".join(insufficient) + "."

        # Generamos el folio único para el ticket
        drawer = connection.execute(
            "SELECT * FROM drawers WHERE drawer_id = ?", (drawer_id,)
        ).fetchone()
        folio = drawer["folio"] + 1
        ticket = f"Caja #{drawer_id}-{folio:04d}"
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Conteo de pizzas vendidas por tipo
        pizza_count = sum(item["quantity"] for item in items)
        pepperoni_count = sum(
            item["quantity"] for item in items if item["pizza"] == "Pepperoni"
        )
        hawaiian_count = pizza_count - pepperoni_count
        change_due = round(cash_received - total, 2) if payment == "Efectivo" else 0.0

        # Descontamos los insumos gastados del inventario
        for key, amount in requirements.items():
            if amount:
                connection.execute(
                    "UPDATE inventory SET quantity = quantity - ? WHERE ingredient = ?",
                    (amount, key),
                )

        # Actualizamos las estadísticas de la caja
        connection.execute(
            """
            UPDATE drawers
            SET pizzas = pizzas + ?, pepperoni = pepperoni + ?,
                hawaiian = hawaiian + ?, folio = ?, total = total + ?
            WHERE drawer_id = ?
            """,
            (pizza_count, pepperoni_count, hawaiian_count, folio, total, drawer_id),
        )

        payment_description = payment
        if payment == "Tarjeta" and card_auth_code:
            payment_description = f"Tarjeta (Autorización: {card_auth_code})"

        # Guardamos el ticket en la tabla de ventas
        connection.execute(
            """
            INSERT INTO sales (
                sold_at, drawer_id, ticket, username, nickname, items, pizzas,
                subtotal, discount, tax, total, payment, cash_received, change_due
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                drawer_id,
                ticket,
                username,
                nickname,
                json.dumps(items, ensure_ascii=False),
                pizza_count,
                subtotal,
                discount,
                tax,
                total,
                payment_description,
                cash_received if payment == "Efectivo" else total,
                change_due,
            ),
        )
        connection.commit()
        return True, {
            "ticket": ticket,
            "sold_at": now,
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "total": total,
            "change": change_due,
            "payment": payment_description,
        }
    except sqlite3.Error as error:
        connection.rollback()
        return False, f"No se pudo guardar la venta: {error}"
    finally:
        connection.close()


# --- INTERFAZ 1: PANTALLA DE LOGIN ---

def show_login():
    left, form_column, right = st.columns([1, 1.2, 1])
    with form_column:
        # Imagen con el logo transparente subida al GitHub
        st.image("logo.png", use_container_width=True)
        st.markdown("<h3 style='text-align: center; margin-top: -10px;'> ¡Bienvenido!</h3>", unsafe_allow_html=True)
        st.write("")
        
        # Formulario donde el cajero ingresa sus datos
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            nickname = st.text_input("Nombre para el ticket")
            drawer_id = st.selectbox("Seleccionar Caja", [1, 2], format_func=lambda value: f"Caja #{value}")
            submitted = st.form_submit_button("Entrar al Sistema", type="primary", use_container_width=True)
            
        # Comprobamos si el usuario y contraseña son válidos
        if submitted:
            if USERS.get(username.strip()) == password and nickname.strip():
                st.session_state.update(
                    logged_in=True,
                    username=username.strip(),
                    nickname=nickname.strip(),
                    drawer_id=drawer_id,
                )
                st.rerun()
            st.error("Verifica el usuario, la contraseña y asegúrate de ingresar un nombre.")
        st.info("Cuentas de prueba: admin / 1234  o  cajero / 5678")


# --- INTERFAZ 2: REGISTRO DE VENTAS Y MENÚ ---

def show_sales():
    # Si el cajero dio clic en limpiar, reseteamos todos los contadores de pizzas a 0
    if st.session_state.pop("clear_order", False):
        for pizza in PIZZAS:
            for size in SIZES:
                st.session_state[f"qty_{pizza}_{size}"] = 0

    st.title("🇮🇹 Menú & Registro de Pedidos")
    st.caption(f"Atendiendo en Caja #{st.session_state.drawer_id} · Cajero/a: {st.session_state.nickname}")

    # Tabla con los nombres de tamaños
    st.subheader("Selección de Pizzas")
    headers = st.columns([1.3, 1, 1, 1])
    headers[0].markdown("**Especialidad**")
    for column, size in zip(headers[1:], SIZES):
        column.markdown(f"**{size}**")

    # Generamos los campos numéricos para cada pizza y tamaño
    quantities = {}
    for pizza in PIZZAS:
        columns = st.columns([1.3, 1, 1, 1])
        precio_base = PIZZAS[pizza]
        columns[0].markdown(f"**{pizza}**<br><small style='color: var(--text-color); opacity: 0.7;'>Base: ${precio_base:.0f}</small>", unsafe_allow_html=True)
        for column, size in zip(columns[1:], SIZES):
            quantities[(pizza, size)] = column.number_input(
                f"{pizza} {size}", min_value=0, max_value=30, step=1,
                key=f"qty_{pizza}_{size}", label_visibility="collapsed",
            )

    # Opciones de pago y selección de descuentos
    st.subheader("Opciones de Pago y Descuentos")
    col_desc, col_pago = st.columns(2)
    with col_desc:
        discount_rate = st.selectbox(
            "Descuento aplicable", [0.0, 0.05, 0.10, 0.15],
            format_func=lambda value: f"{value:.0%} de descuento",
        )
    with col_pago:
        payment = st.radio("Forma de Pago", ["Efectivo", "Tarjeta"], horizontal=True)

    cash_received = 0.0
    card_auth_code = ""

    if payment == "Efectivo":
        cash_received = st.number_input("Efectivo recibido ($)", min_value=0.0, step=10.0)
    else:
        card_auth_code = st.text_input("Código de autorización bancaria (6 dígitos)", max_chars=6)

    # Filtramos solo las pizzas seleccionadas (que tengan cantidad mayor a 0)
    items = []
    for (pizza, size), quantity in quantities.items():
        if quantity:
            items.append({
                "pizza": pizza,
                "size": size,
                "quantity": quantity,
                "price": PIZZAS[pizza] * SIZES[size],
            })

    # Muestra el total en tiempo real sin necesidad de presionar enviar
    subtotal = round(sum(item["price"] * item["quantity"] for item in items), 2)
    total_estimado = round((subtotal - subtotal * discount_rate) * 1.16, 2)
    
    summary_col, action_col = st.columns([2, 1])
    with summary_col:
        st.metric("Total Estimado (con IVA)", format_money(total_estimado))
    with action_col:
        st.write("")
        if st.button("Limpiar Selección", use_container_width=True):
            st.session_state["clear_order"] = True
            st.rerun()

    # Botón principal para confirmar el registro del pedido
    submitted = st.button("Confirmar y Registrar Venta", type="primary", use_container_width=True)

    if submitted:
        if not items:
            st.error("Selecciona al menos una pizza para continuar.")
            return

        if payment == "Tarjeta":
            if not card_auth_code.isdigit() or len(card_auth_code) != 6:
                st.error("El código de autorización bancaria debe contener exactamente 6 dígitos numéricos.")
                return

        success, result = save_sale(
            st.session_state.drawer_id,
            st.session_state.username,
            st.session_state.nickname,
            items,
            discount_rate,
            payment,
            cash_received,
            card_auth_code,
        )
        if not success:
            st.error(result)
            return

        st.session_state["last_sale"] = result
        st.session_state["clear_order"] = True
        st.rerun()

    # Muestra el ticket generado justo después de registrar la compra
    result = st.session_state.get("last_sale")
    if result:
        st.success(f"Venta registrada exitosamente · Ticket {result['ticket']}")
        
        with st.expander("Ver Ticket de Compra", expanded=True):
            st.markdown(f"**PIZZERÍA AMORE & MASA**")
            st.markdown(f"**Folio:** {result['ticket']} | **Fecha:** {result['sold_at']}")
            st.markdown(f"**Atendido por:** {st.session_state.nickname}")
            st.markdown(f"**Método de Pago:** {result['payment']}")
            st.markdown(f"Subtotal: {format_money(result['subtotal'])}")
            st.markdown(f"Descuento: -{format_money(result['discount'])}")
            st.markdown(f"IVA (16%): {format_money(result['tax'])}")
            st.markdown(f"### Total Pagado: {format_money(result['total'])}")
            if "Efectivo" in result['payment']:
                st.markdown(f"**Cambio Devuelto:** {format_money(result['change'])}")


# --- INTERFAZ 3: CONTROL DE INVENTARIO ---

def show_inventory():
    st.title("📦 Control de Inventario")
    st.caption("Existencias compartidas entre las cajas")
    
    inventory = load_inventory()
    columns = st.columns(len(INGREDIENTS))
    
    # Mostramos las tarjetas con las existencias de cada ingrediente
    for column, (key, (label, _)) in zip(columns, INGREDIENTS.items()):
        quantity = inventory[key]
        column.metric(label, f"{quantity:,.0f} g")
        if quantity <= LOW_STOCK_LIMIT:
            column.warning("Stock bajo")

    # Formulario para recargar gramos al inventario
    st.subheader("Reabastecer Insumos")
    with st.form("restock_form"):
        additions = {}
        columns = st.columns(3)
        for index, (key, (label, _)) in enumerate(INGREDIENTS.items()):
            additions[key] = columns[index % 3].number_input(
                f"{label} a agregar (gramos)", min_value=0.0, step=500.0, key=f"restock_{key}"
            )
        submitted = st.form_submit_button("Guardar Reabastecimiento", type="primary")

    if submitted:
        with connect_database() as connection:
            for key, amount in additions.items():
                if amount:
                    connection.execute(
                        "UPDATE inventory SET quantity = quantity + ? WHERE ingredient = ?",
                        (amount, key),
                    )
        st.success("Inventario actualizado correctamente.")
        st.rerun()


# --- INTERFAZ 4: CORTE Y REPORTES ---

def show_reports():
    st.title("📊 Corte y Reporte de Ventas")
    drawer_id = st.session_state.drawer_id
    drawer = load_drawer(drawer_id)

    # Tarjetas métricas con las ventas acumuladas
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Totales", drawer["folio"])
    c2.metric("Pizzas Vendidas", drawer["pizzas"])
    c3.metric("Ingreso Acumulado", format_money(drawer["total"]))

    st.info(
        f"Desglose por especialidad en Caja #{drawer_id}: "
        f"Pizzas de Pepperoni: **{drawer['pepperoni']}** unidades | "
        f"Pizzas Hawaianas: **{drawer['hawaiian']}** unidades"
    )

    # Muestra el historial completo de ventas en una tabla interactiva
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT sold_at AS "Fecha y Hora", ticket AS Folio, nickname AS Cajero,
                   pizzas AS Pizzas, payment AS "Forma de Pago", total AS Total
            FROM sales WHERE drawer_id = ? ORDER BY id DESC LIMIT 100
            """,
            (drawer_id,),
        ).fetchall()

    if rows:
        st.subheader("Historial de Transacciones Recientes")
        st.dataframe([dict(row) for row in rows], hide_index=True, use_container_width=True)
    else:
        st.caption("Aún no se registran ventas en esta caja durante la sesión actual.")


# --- FUNCIÓN PRINCIPAL Y CONTROL DE RUTAS ---

def main():
    # Inyectamos CSS para dar un diseño italiano (Verde y Terracota)
    st.markdown(
        """
        <style>
        .stApp {
            font-family: 'Georgia', serif;
        }
        /* Color verde albahaca solo en la barra de menú lateral */
        [data-testid="stSidebar"] {
            background-color: #1E392A !important;
        }
        [data-testid="stSidebar"] * {
            color: rgba(255, 255, 255, 0.95) !important;
        }
        /* Cajas de métricas adaptadas al tema de Streamlit */
        div[data-testid="stMetric"] {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--border-color);
            padding: 12px;
            border-radius: 8px;
        }
        /* Botones principales con tono rojo terracota */
        .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
            background-color: #A03322 !important;
            border-color: #A03322 !important;
            color: #FFFFFF !important;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Preparamos las tablas en SQLite al arrancar la aplicación
    initialize_database()

    # Si la persona no se ha logueado, se muestra la pantalla de Login
    if not st.session_state.get("logged_in"):
        show_login()
        return

    # Menú lateral para navegar entre pantallas
    with st.sidebar:
        st.markdown("## 🍕 Amore & Masa")
        st.markdown("<p style='font-size:0.9em; opacity:0.8;'>Pizzería Artesanal Italiana</p>", unsafe_allow_html=True)
        st.caption(f"Usuario: {st.session_state.username} · Caja #{st.session_state.drawer_id}")
        
        page = st.radio("Navegación", ["Ventas", "Inventario", "Reportes"], label_visibility="collapsed")
        
        if st.button("Cerrar Sesión", use_container_width=True):
            for key in ("logged_in", "username", "nickname", "drawer_id"):
                st.session_state.pop(key, None)
            st.rerun()

    # Cambia de vista según la opción seleccionada en la barra lateral
    if page == "Ventas":
        show_sales()
    elif page == "Inventario":
        show_inventory()
    else:
        show_reports()


# Arranca la ejecución de la app
if __name__ == "__main__":
    main()
