import json
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Pizzería | Caja", page_icon="🍕", layout="wide")

DATABASE_PATH = Path(__file__).with_name("pizzeria_app.db")
USERS = {"admin": "1234", "cajero": "5678"}
INGREDIENTS = {
    "harina": ("Harina", 250),
    "queso": ("Queso", 150),
    "salsa": ("Salsa", 100),
    "pep": ("Pepperoni", 80),
    "jamon": ("Jamón", 70),
    "pina": ("Piña", 70),
}
SIZES = {"Chica": 1.0, "Mediana": 1.5, "Grande": 2.0}
PIZZAS = {"Pepperoni": 120.0, "Hawaiana": 115.0}
LOW_STOCK_LIMIT = 500


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                ingredient TEXT PRIMARY KEY,
                quantity REAL NOT NULL CHECK (quantity >= 0)
            )
            """
        )
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
        connection.executemany(
            "INSERT OR IGNORE INTO drawers (drawer_id) VALUES (?)",
            [(1,), (2,)],
        )


def load_inventory():
    with connect_database() as connection:
        rows = connection.execute(
            "SELECT ingredient, quantity FROM inventory"
        ).fetchall()
    return {row["ingredient"]: row["quantity"] for row in rows}


def load_drawer(drawer_id):
    with connect_database() as connection:
        return connection.execute(
            "SELECT * FROM drawers WHERE drawer_id = ?", (drawer_id,)
        ).fetchone()


def format_money(value):
    return f"${value:,.2f}"


def save_sale(drawer_id, username, nickname, items, discount_rate, payment, cash_received):
    subtotal = round(sum(item["price"] * item["quantity"] for item in items), 2)
    discount = round(subtotal * discount_rate, 2)
    discounted_subtotal = round(subtotal - discount, 2)
    tax = round(discounted_subtotal * 0.16, 2)
    total = round(discounted_subtotal + tax, 2)

    if payment == "Efectivo" and cash_received < total:
        return False, f"Faltan {format_money(total - cash_received)} para completar el pago."

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
            return False, "Inventario insuficiente: " + ", ".join(insufficient) + "."

        drawer = connection.execute(
            "SELECT * FROM drawers WHERE drawer_id = ?", (drawer_id,)
        ).fetchone()
        folio = drawer["folio"] + 1
        ticket = f"Caja #{drawer_id}-{folio:04d}"
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pizza_count = sum(item["quantity"] for item in items)
        pepperoni_count = sum(
            item["quantity"] for item in items if item["pizza"] == "Pepperoni"
        )
        hawaiian_count = pizza_count - pepperoni_count
        change_due = round(cash_received - total, 2) if payment == "Efectivo" else 0.0

        for key, amount in requirements.items():
            if amount:
                connection.execute(
                    "UPDATE inventory SET quantity = quantity - ? WHERE ingredient = ?",
                    (amount, key),
                )

        connection.execute(
            """
            UPDATE drawers
            SET pizzas = pizzas + ?, pepperoni = pepperoni + ?,
                hawaiian = hawaiian + ?, folio = ?, total = total + ?
            WHERE drawer_id = ?
            """,
            (pizza_count, pepperoni_count, hawaiian_count, folio, total, drawer_id),
        )
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
                payment,
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
        }
    except sqlite3.Error as error:
        connection.rollback()
        return False, f"No se pudo guardar la venta: {error}"
    finally:
        connection.close()


def show_login():
    left, form_column, right = st.columns([1, 1.15, 1])
    with form_column:
        st.markdown("### Pizzería")
        st.title("Iniciar sesión")
        st.caption("Acceso al sistema de caja")
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            nickname = st.text_input("Nombre para el ticket")
            drawer_id = st.selectbox("Caja", [1, 2], format_func=lambda value: f"Caja #{value}")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            if USERS.get(username.strip()) == password and nickname.strip():
                st.session_state.update(
                    logged_in=True,
                    username=username.strip(),
                    nickname=nickname.strip(),
                    drawer_id=drawer_id,
                )
                st.rerun()
            st.error("Revisa el usuario, la contraseña y el nombre.")
        st.caption("Acceso de prueba: admin / 1234 o cajero / 5678")


def show_sales():
    if st.session_state.pop("clear_order", False):
        for pizza in PIZZAS:
            for size in SIZES:
                st.session_state[f"qty_{pizza}_{size}"] = 0

    st.title("Registrar venta")
    st.caption(f"Caja #{st.session_state.drawer_id} · {st.session_state.nickname}")

    with st.form("sale_form"):
        st.subheader("Pedido")
        headers = st.columns([1.2, 1, 1, 1])
        headers[0].markdown("**Pizza**")
        for column, size in zip(headers[1:], SIZES):
            column.markdown(f"**{size}**")

        quantities = {}
        for pizza in PIZZAS:
            columns = st.columns([1.2, 1, 1, 1])
            columns[0].write(pizza)
            for column, size in zip(columns[1:], SIZES):
                quantities[(pizza, size)] = column.number_input(
                    f"{pizza} {size}", min_value=0, max_value=30, step=1,
                    key=f"qty_{pizza}_{size}", label_visibility="collapsed",
                )

        discount_rate = st.selectbox(
            "Descuento", [0.0, 0.05, 0.10, 0.15],
            format_func=lambda value: f"{value:.0%}",
        )
        payment = st.radio("Forma de pago", ["Efectivo", "Tarjeta"], horizontal=True)
        cash_received = 0.0
        if payment == "Efectivo":
            cash_received = st.number_input("Dinero recibido ($)", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("Cobrar y registrar", type="primary")

    items = []
    for (pizza, size), quantity in quantities.items():
        if quantity:
            items.append({
                "pizza": pizza,
                "size": size,
                "quantity": quantity,
                "price": PIZZAS[pizza] * SIZES[size],
            })

    subtotal = round(sum(item["price"] * item["quantity"] for item in items), 2)
    total = round((subtotal - subtotal * discount_rate) * 1.16, 2)
    summary, action = st.columns([2, 1])
    with summary:
        st.metric("Total estimado", format_money(total))
    with action:
        st.write("")
        st.write("")
        if st.button("Vaciar pedido", use_container_width=True):
            st.session_state["clear_order"] = True
            st.rerun()

    if submitted:
        if not items:
            st.error("Agrega al menos una pizza al pedido.")
            return
        success, result = save_sale(
            st.session_state.drawer_id,
            st.session_state.username,
            st.session_state.nickname,
            items,
            discount_rate,
            payment,
            cash_received,
        )
        if not success:
            st.error(result)
            return
        st.session_state["last_sale"] = result
        st.session_state["last_payment"] = payment
        st.session_state["clear_order"] = True
        st.rerun()

    result = st.session_state.get("last_sale")
    if result:
        st.success(f"Venta registrada · {result['ticket']}")
        st.write(
            f"Subtotal: {format_money(result['subtotal'])}  ·  "
            f"Descuento: {format_money(result['discount'])}  ·  "
            f"IVA: {format_money(result['tax'])}  ·  "
            f"Total: **{format_money(result['total'])}**"
        )
        if st.session_state.get("last_payment") == "Efectivo":
            st.write(f"Cambio: **{format_money(result['change'])}**")


def show_inventory():
    st.title("Inventario")
    inventory = load_inventory()
    columns = st.columns(len(INGREDIENTS))
    for column, (key, (label, _)) in zip(columns, INGREDIENTS.items()):
        quantity = inventory[key]
        column.metric(label, f"{quantity:,.0f} g")
        if quantity <= LOW_STOCK_LIMIT:
            column.caption("Stock bajo")

    st.subheader("Reabastecer")
    with st.form("restock_form"):
        additions = {}
        columns = st.columns(3)
        for index, (key, (label, _)) in enumerate(INGREDIENTS.items()):
            additions[key] = columns[index % 3].number_input(
                f"{label} a agregar (g)", min_value=0.0, step=100.0, key=f"restock_{key}"
            )
        submitted = st.form_submit_button("Actualizar inventario", type="primary")
    if submitted:
        with connect_database() as connection:
            for key, amount in additions.items():
                if amount:
                    connection.execute(
                        "UPDATE inventory SET quantity = quantity + ? WHERE ingredient = ?",
                        (amount, key),
                    )
        st.success("Inventario actualizado.")
        st.rerun()


def show_reports():
    st.title("Reportes")
    drawer_id = st.session_state.drawer_id
    drawer = load_drawer(drawer_id)
    first, second, third = st.columns(3)
    first.metric("Ventas", drawer["folio"])
    second.metric("Pizzas", drawer["pizzas"])
    third.metric("Total vendido", format_money(drawer["total"]))
    st.caption(
        f"Pepperoni: {drawer['pepperoni']}  ·  "
        f"Hawaianas: {drawer['hawaiian']}  ·  Caja #{drawer_id}"
    )

    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT sold_at AS Fecha, ticket AS Folio, username AS Usuario,
                   pizzas AS Pizzas, payment AS Pago, total AS Total
            FROM sales WHERE drawer_id = ? ORDER BY id DESC LIMIT 100
            """,
            (drawer_id,),
        ).fetchall()
    if rows:
        st.subheader("Últimas ventas")
        st.dataframe([dict(row) for row in rows], hide_index=True, use_container_width=True)
    else:
        st.info("Todavía no hay ventas registradas en esta caja.")


def main():
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(135deg, #f7f6f1 0%, #edf3f0 100%); }
        [data-testid="stSidebar"] { background: #183c39; }
        [data-testid="stSidebar"] * { color: #f7f6f1; }
        h1, h2, h3 { color: #202b29; }
        div[data-testid="stMetric"] { background: rgba(255,255,255,.78); padding: 14px; border-radius: 6px; }
        .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] { background: #c84b35; border-color: #c84b35; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_database()
    if not st.session_state.get("logged_in"):
        show_login()
        return

    with st.sidebar:
        st.markdown("## Pizzería")
        st.caption(f"{st.session_state.username} · Caja #{st.session_state.drawer_id}")
        page = st.radio("Sección", ["Ventas", "Inventario", "Reportes"], label_visibility="collapsed")
        if st.button("Cerrar sesión", use_container_width=True):
            for key in ("logged_in", "username", "nickname", "drawer_id"):
                st.session_state.pop(key, None)
            st.rerun()

    if page == "Ventas":
        show_sales()
    elif page == "Inventario":
        show_inventory()
    else:
        show_reports()


if __name__ == "__main__":
    main()