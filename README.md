# 🍕 Amore & Masa - Sistema POS e Inventario

Este repositorio contiene el **Proyecto Final para la materia de Fundamentos de Programación** en Universidad Tecmilenio. Se trata de un sistema de Punto de Venta (POS) e inventario para la pizzería artesanal *Amore & Masa*.

---

## 📌 ¿Qué es este proyecto?

El sistema es una aplicación web interactiva desarrollada para resolver la problemática de registro manual de pedidos y desabasto imprevisto de insumos[cite: 5]. Permite cobrar pedidos, calcular impuestos/descuentos automáticamente, emitir tickets digitales y mantener el control del inventario en gramos[cite: 5].

---

## ⚙️ ¿Cómo funciona el código?

La aplicación está construida en **Python** utilizando **Streamlit** para la interfaz visual y **SQLite3** para la base de datos[cite: 5]. Su funcionamiento se divide en cuatro partes principales:

1. **Gestión de Cajas y Usuarios:** Permite iniciar sesión como cajero y seleccionar la estación de trabajo (Caja #1 o Caja #2).
2. **Punto de Venta (POS):** 
   - El cajero selecciona las pizzas, tamaños y cantidades.
   - El código verifica que existan suficiente cantidad de insumos en gramos antes de procesar la orden[cite: 5].
   - Aplica automáticamente la tasa de IVA (16%), descuentos y calcula el cambio en efectivo o valida autorizaciones de tarjeta[cite: 5].
3. **Control Automático de Inventario:** Cada pizza vendida descuenta ingredientes de la base de datos en tiempo real según recetas base y multiplicadores por tamaño (Chica $1.0\times$, Mediana $1.5\times$, Grande $2.0\times$)[cite: 5].
4. **Base de Datos Relacional (`pizzeria_app.db`):** Guarda de forma permanente las ventas, el folio acumulado por caja, el total cobrado y las existencias de insumos.

---

## 🚀 Cómo ejecutar la aplicación

1. **Instalar Streamlit:**
   ```bash
   pip install streamlit
