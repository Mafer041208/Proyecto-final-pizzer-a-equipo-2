# Pizzeria avance 5.0
# Sistema con dos cajas registradoras independientes
# Cada caja conserva sus propias ventas, folios y dinero vendido
# El inventario es compartido entre las cajas
# El usuario inicia sesion en una caja especifica
# La fecha y hora se obtienen automaticamente en cada ticket

# HISTORIAL DE CAMBIOS Y VERSIONES
# 01/09/2026 - A: Inicio del proyecto y armado de la primera versión.

# Actualizaciones:
# 04/09/2026 - M: Definición de la estructura base del programa y declaración de las primeras variables.
# 08/09/2026 - MF: Corrección de errores que salían al momento de ingresar los datos.
# 12/09/2026 - Rx: Ajuste en las funciones para mejorar el rendimiento y corrección de detalles de escritura.
# 17/09/2026 - A: Agregado de validaciones para evitar que el programa se trabe con datos incorrectos.
# 22/09/2026 - M: Limpieza de partes repetidas y cambio de nombres de variables para mayor claridad.
# 26/09/2026 - Rx: ÚLTIMA ACTUALIZACIÓN. Revisión general para verificar el correcto funcionamiento del código.


import time
import os
import math
import threading
import queue
from datetime import datetime


# Usuarios disponibles para iniciar sesion
USUARIOS = {
    "admin": "1234",
    "cajero": "5678"
}


# Limite maximo para pagos en efectivo
LIMITE_EFECTIVO = 10000.0


# Funcion para medir el tiempo de inactividad (Cierra sesion tras 10 minutos)
def obtener_opcion_con_temporizador(
    mensaje_prompt,
    tiempo_limite_segundos=600
):
    respuestas = queue.Queue()
    evento_tiempo = threading.Event()

    # Lee la opcion sin bloquear el contador
    def leer_opcion():
        print(mensaje_prompt, end="", flush=True)
        try:
            opcion = input()
            if not evento_tiempo.is_set():
                respuestas.put(("opcion", opcion))
        except Exception:
            pass

    hilo = threading.Thread(
        target=leer_opcion,
        daemon=True
    )
    hilo.start()

    # Contador de tiempo (10 minutos)
    for segundo in range(tiempo_limite_segundos):
        try:
            tipo, valor = respuestas.get(timeout=1)
            if tipo == "opcion":
                return valor
        except queue.Empty:
            pass

    # Si expira el temporizador de 10 minutos por inactividad
    evento_tiempo.set()
    print("\n\n" + "=" * 55)
    print("Ha pasado mas de 10 minutos sin actividad.")
    print("Cerrando sesion por seguridad y regresando al inicio...")
    print("=" * 55 + "\n")
    return "CANCELAR_PANTALLA_INICIAL"


# Funcion para mostrar el mensaje de carga
def cargar_programa():
    print("\nCargando programa...")

    # La espera es de maximo cinco segundos
    time.sleep(5)

    print("Programa listo.\n")


# Funcion para iniciar sesion
def iniciar_sesion():
    while True:
        print("\nINICIAR SESION")

        usuario = input(
            "Ingrese su usuario: "
        ).strip()

        contrasena = input(
            "Ingrese su contrasena: "
        ).strip()

        if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
            print(
                f"Inicio de sesion correcto. Bienvenido/a {usuario}."
            )

            # Solicita el nombre o nickname
            while True:
                nickname = input(
                    "Ingrese su nombre o nickname: "
                ).strip()

                if nickname != "":
                    break

                print("El nombre no puede estar vacio.")

            # Usa operadores string para dar la bienvenida
            mensaje = "Bienvenido/a " + nickname + " a la Pizzeria."
            print(mensaje)

            return usuario, nickname

        print("Usuario o contrasena incorrectos.")
        print("Intente nuevamente.")


# Funcion para seleccionar la caja registradora
def seleccionar_caja():
    while True:
        print("\nSELECCION DE CAJA")
        print("1. Caja #1")
        print("2. Caja #2")
        print("3. Salir del programa")

        opcion = input(
            "Seleccione la caja: "
        ).strip()

        if opcion == "1":
            return 1

        elif opcion == "2":
            return 2

        elif opcion == "3":
            return None

        else:
            print("Opcion invalida. Intente nuevamente.")


# Crea los archivos iniciales para lectura y registros
def crear_archivos_iniciales():
    archivos_iniciales = {
        "pizzeria_menu.txt": "Menu de la pizzeria.\n",
        "pizzeria_clientes.txt": "Registro de clientes.\n",
        "pizzeria_productos.txt": "Lista de productos.\n",
        "pizzeria_notas.txt": "Notas de la pizzeria.\n",
        "pizzeria_tickets.txt": "Historico de tickets generados.\n",
        "registro_ventas.txt": "Registro resumido de pizzas vendidas y dinero.\n",
        "registro_inventario.txt": "Historial de modificaciones del inventario.\n"
    }

    for nombre, contenido in archivos_iniciales.items():
        if not os.path.exists(nombre):
            try:
                with open(
                    nombre,
                    "w",
                    encoding="utf-8"
                ) as archivo:
                    archivo.write(contenido)
            except OSError:
                print(
                    f"No se pudo crear {nombre}."
                )


# Funciones para el sistema de archivos automatizado

def guardar_ticket_archivo(
    folio, caja, usuario, nickname, fecha_hora, forma_pago_texto,
    cant, total, descuento, porcentaje_descuento, subtotal, iva, total_con_iva,
    pago_recibido=0.0, cambio=0.0
):
    nombre_archivo = "pizzeria_tickets.txt"
    try:
        with open(nombre_archivo, "a", encoding="utf-8") as archivo:
            archivo.write("=" * 58 + "\n")
            archivo.write("                 PIZZERIA - TICKET\n")
            archivo.write("=" * 58 + "\n")
            archivo.write(f"Folio:              Caja #{caja}-{folio:04d}\n")
            archivo.write(f"Fecha y hora:       {fecha_hora}\n")
            archivo.write(f"Usuario:            {usuario}\n")
            archivo.write(f"Cliente/Nickname:   {nickname}\n")
            archivo.write("-" * 58 + "\n")
            archivo.write(f"Pizzas:             {cant}\n")
            archivo.write(f"Subtotal original:  ${total:,.2f}\n")
            archivo.write(
                f"Descuento:          ${descuento:,.2f} "
                f"({porcentaje_descuento * 100:.0f}%)\n"
            )
            archivo.write(f"Subtotal:           ${subtotal:,.2f}\n")
            archivo.write(f"IVA (16%):           ${iva:,.2f}\n")
            archivo.write(f"TOTAL:              ${total_con_iva:,.2f}\n")
            archivo.write("-" * 58 + "\n")
            archivo.write(f"Forma de pago:      {forma_pago_texto}\n")
            if "Efectivo" in forma_pago_texto:
                archivo.write(f"Pago recibido:      ${pago_recibido:,.2f}\n")
                archivo.write(f"Cambio:             ${cambio:,.2f}\n")
            archivo.write("=" * 58 + "\n\n")
    except OSError:
        print("No se pudo registrar el ticket en el archivo.")


def guardar_registro_ventas_resumido(
    folio, caja, usuario, nickname, fecha_hora, cant, cant_pep, cant_haw, total_con_iva
):
    nombre_archivo = "registro_ventas.txt"
    try:
        with open(nombre_archivo, "a", encoding="utf-8") as archivo:
            linea = (
                f"[{fecha_hora}] Caja #{caja} | Folio: {folio:04d} | "
                f"Usuario: {usuario} ({nickname}) | "
                f"Pizzas: {cant} (Pepperoni: {cant_pep}, Hawaiana: {cant_haw}) | "
                f"Dinero total: ${total_con_iva:,.2f}\n"
            )
            archivo.write(linea)
    except OSError:
        print("No se pudo actualizar el registro de ventas resumido.")


def guardar_movimiento_inventario(
    tipo_movimiento, harina, queso, salsa, pep, jamon, pina, usuario, nickname, caja
):
    nombre_archivo = "registro_inventario.txt"
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    try:
        with open(nombre_archivo, "a", encoding="utf-8") as archivo:
            archivo.write(
                f"[{fecha_hora}] Tipo: {tipo_movimiento} | Caja #{caja} | "
                f"Usuario: {usuario} ({nickname}) | "
                f"Harina: {harina:+.2f}g, Queso: {queso:+.2f}g, Salsa: {salsa:+.2f}g, "
                f"Pepperoni: {pep:+.2f}g, Jamon: {jamon:+.2f}g, Pina: {pina:+.2f}g\n"
            )
    except OSError:
        print("No se pudo registrar la modificacion de inventario.")


# Funcion para mostrar los archivos txt
def mostrar_archivos():
    archivos = []

    for archivo in os.listdir("."):
        if archivo.endswith(".txt"):
            archivos.append(archivo)

    return sorted(archivos)


# Funcion para elegir un archivo
def elegir_archivo():
    archivos = mostrar_archivos()

    if len(archivos) == 0:
        print("\n" + "=" * 55)
        print("              ARCHIVOS")
        print("=" * 55)
        print("No hay archivos .txt disponibles.")
        print("=" * 55)
        return None

    print("\n" + "=" * 55)
    print("              ARCHIVOS DISPONIBLES")
    print("=" * 55)

    for i, archivo in enumerate(archivos, start=1):
        print(f"  {i}. {archivo}")

    print("  0. Regresar")
    print("=" * 55)

    while True:
        seleccion = input("\nSeleccione un archivo: ").strip()

        if seleccion == "0":
            return None

        if seleccion.isdigit():
            numero = int(seleccion)

            if 1 <= numero <= len(archivos):
                return archivos[numero - 1]

            print(
                f"Numero invalido. Elija un numero del 1 al {len(archivos)}, "
                "o escriba 0 para regresar."
            )
            continue

        nombre = seleccion.lower()

        if not nombre.endswith(".txt"):
            nombre += ".txt"

        for archivo in archivos:
            if archivo.lower() == nombre:
                return archivo

        print("No se encontro ese archivo.")


# Solicita una fecha y la guarda en una tupla
def solicitar_fecha():
    while True:
        fecha_texto = input(
            "Ingrese la fecha (dd/mm/aaaa): "
        ).strip()

        try:
            fecha_valida = datetime.strptime(
                fecha_texto,
                "%d/%m/%Y"
            )

            dia = fecha_valida.day
            mes = fecha_valida.month
            anio = fecha_valida.year

            Fecha = dia, mes, anio

            return Fecha

        except ValueError:
            print(
                "Fecha invalida. Use el formato dd/mm/aaaa."
            )


# Convierte la tupla de fecha en texto
def fecha_a_texto(Fecha):
    dia, mes, anio = Fecha

    return f"{dia:02d}/{mes:02d}/{anio:04d}"


# Funcion para administrar documentos
def menu_documentos(usuario, nickname, caja):
    while True:
        print("\n" + "=" * 55)
        print("                 GESTION DE ARCHIVOS")
        print("=" * 55)
        print("1. Leer archivo")
        print("2. Escribir en un archivo")
        print("3. Crear archivo nuevo")
        print("4. Cambiar de usuario")
        print("5. Regresar")
        print("=" * 55)

        opcion = obtener_opcion_con_temporizador(
            "Seleccione una opcion: "
        )

        if opcion == "CANCELAR_PANTALLA_INICIAL":
            return "CAMBIAR_USUARIO"

        try:
            opcion = int(opcion)

        except ValueError:
            print("Opcion invalida. Intente nuevamente.")
            continue

        # Leer archivo
        if opcion == 1:
            archivo_seleccionado = elegir_archivo()

            if archivo_seleccionado is not None:
                try:
                    with open(
                        archivo_seleccionado,
                        "r",
                        encoding="utf-8"
                    ) as archivo:
                        contenido = archivo.read()

                    print("\n" + "=" * 55)
                    print(f"              CONTENIDO DE: {archivo_seleccionado}")
                    print("=" * 55)

                    if contenido.strip() == "":
                        print("El archivo esta vacio.")
                    else:
                        print(contenido, end="")

                    print("=" * 55)

                except FileNotFoundError:
                    print("\nNo se pudo abrir el archivo porque ya no existe.")
                except PermissionError:
                    print("\nNo tienes permisos para leer este archivo.")
                except UnicodeDecodeError:
                    print("\nError de codificacion al leer el archivo.")
                except OSError as error:
                    print(f"\nNo se pudo leer el archivo: {error}")

        # Escribir archivo
        elif opcion == 2:
            archivo_seleccionado = elegir_archivo()

            if archivo_seleccionado is not None:
                while True:
                    texto = input(
                        "Escriba el texto que desea guardar: "
                    )

                    if texto.strip() == "":
                        print("El texto no puede estar vacio.")
                        continue

                    Fecha = solicitar_fecha()

                    try:
                        with open(
                            archivo_seleccionado,
                            "a",
                            encoding="utf-8"
                        ) as archivo:
                            archivo.write(
                                f"[{fecha_a_texto(Fecha)}] "
                                f"Usuario: {usuario} | "
                                f"Nickname: {nickname} | "
                                f"Caja: #{caja} | "
                                f"{texto}\n"
                            )

                        print("\nTEXTO GUARDADO CORRECTAMENTE")
                        break

                    except FileNotFoundError:
                        print("El archivo no existe.")
                        break

                    except OSError:
                        print("No se pudo escribir en el archivo.")
                        break

        # Crear archivo
        elif opcion == 3:
            while True:
                nombre_archivo = input(
                    "Ingrese el nombre del nuevo archivo: "
                ).strip()

                if nombre_archivo == "":
                    print("El nombre no puede estar vacio.")
                    continue

                caracteres_invalidos = '<>:"/\\|?*'

                if any(
                    caracter in nombre_archivo
                    for caracter in caracteres_invalidos
                ):
                    print("El nombre contiene caracteres no permitidos.")
                    continue

                if not nombre_archivo.lower().endswith(".txt"):
                    nombre_archivo += ".txt"

                if os.path.exists(nombre_archivo):
                    print("Ese archivo ya existe.")
                    continue

                Fecha = solicitar_fecha()

                try:
                    with open(
                        nombre_archivo,
                        "w",
                        encoding="utf-8"
                    ) as archivo:
                        archivo.write("Archivo creado desde la pizzeria.\n")
                        archivo.write(f"Fecha: {fecha_a_texto(Fecha)}\n")
                        archivo.write(f"Usuario: {usuario}\n")
                        archivo.write(f"Nickname: {nickname}\n")
                        archivo.write(f"Caja: #{caja}\n")

                    print("Archivo creado correctamente.")
                    break

                except OSError:
                    print("No se pudo crear el archivo.")
                    break

        elif opcion == 4:
            print("Regresando a la pantalla inicial.")
            return "CAMBIAR_USUARIO"

        elif opcion == 5:
            return None

        else:
            print("Opcion invalida. Intente nuevamente.")


# Funcion para comprobar el inventario
def comprobar_inventario(
    harina, queso, salsa, pep, jamon, pina,
    harina_necesaria, queso_necesario, salsa_necesaria,
    pep_necesario, jamon_necesario, pina_necesaria
):
    if harina < harina_necesaria:
        print("No hay suficiente harina.")
        return False
    if queso < queso_necesario:
        print("No hay suficiente queso.")
        return False
    if salsa < salsa_necesaria:
        print("No hay suficiente salsa.")
        return False
    if pep < pep_necesario:
        print("No hay suficiente pepperoni.")
        return False
    if jamon < jamon_necesario:
        print("No hay suficiente jamon.")
        return False
    if pina < pina_necesaria:
        print("No hay suficiente pina.")
        return False
    return True


# Funcion para mostrar alertas de inventario
def alertas_inventario(harina, queso, salsa, pep, jamon, pina):
    limite = 500
    print("\nALERTAS DE INVENTARIO")

    if harina <= limite:
        print("Alerta: harina baja.")
    if queso <= limite:
        print("Alerta: queso bajo.")
    if salsa <= limite:
        print("Alerta: salsa baja.")
    if pep <= limite:
        print("Alerta: pepperoni bajo.")
    if jamon <= limite:
        print("Alerta: jamon bajo.")
    if pina <= limite:
        print("Alerta: pina baja.")

    if (
        harina > limite and queso > limite and salsa > limite
        and pep > limite and jamon > limite and pina > limite
    ):
        print("No hay alertas. El inventario esta en buen nivel.")


# Funcion para seleccionar descuento
def seleccionar_descuento():
    while True:
        print("\nDESCUENTO")
        print("1. Sin descuento")
        print("2. 5%")
        print("3. 10%")
        print("4. 15%")

        try:
            opcion = int(input("Seleccione el descuento: "))
        except ValueError:
            print("Opcion invalida.")
            continue

        if opcion == 1:
            return 0.0
        elif opcion == 2:
            return 0.05
        elif opcion == 3:
            return 0.10
        elif opcion == 4:
            return 0.15
        else:
            print("Opcion invalida.")


# Funcion para mostrar el comprobante de pago
def mostrar_comprobante_pago(
    folio, usuario, nickname, caja, fecha_hora, forma_pago_texto,
    cant, total, descuento, porcentaje_descuento, subtotal, iva, total_con_iva
):
    print("\n")
    print("=" * 58)
    print("                 PIZZERIA")
    print("              COMPROBANTE DE PAGO")
    print("=" * 58)
    print(f"Folio:              Caja #{caja}-{folio:04d}")
    print(f"Fecha y hora:       {fecha_hora}")
    print(f"Usuario:            {usuario}")
    print(f"Cliente/Nickname:   {nickname}")
    print("-" * 58)
    print(f"Pizzas:             {cant}")
    print(f"Subtotal original:  ${total:,.2f}")
    print(
        f"Descuento:          ${descuento:,.2f} "
        f"({porcentaje_descuento * 100:.0f}%)"
    )
    print(f"Subtotal:           ${subtotal:,.2f}")
    print(f"IVA (16%):           ${iva:,.2f}")
    print(f"TOTAL PAGADO:       ${total_con_iva:,.2f}")
    print("-" * 58)
    print(f"Forma de pago:      {forma_pago_texto}")
    print("ESTADO:             PAGO EXITOSO")
    print("Transaccion aprobada correctamente.")
    print("=" * 58)
    print("       Gracias por su compra. ¡Vuelva pronto!")
    print("=" * 58)


# Funcion para registrar una venta
def registrar_venta(
    harina, queso, salsa, pep, jamon, pina,
    ventas, ventasPep, ventasHaw, folio,
    usuario, nickname, caja
):
    while True:
        try:
            cant = int(input("\nCuantas pizzas desea?: "))
            if cant <= 0:
                print("La cantidad debe ser mayor que cero.")
                continue
        except ValueError:
            print("Cantidad invalida. Ingrese un numero.")
            continue

        total = 0.0
        harina_necesaria = 0
        queso_necesario = 0
        salsa_necesaria = 0
        pep_necesario = 0
        jamon_necesario = 0
        pina_necesaria = 0

        pepperoni_pedidas = 0
        hawaianas_pedidas = 0

        for i in range(cant):
            print(f"\nPizza {i + 1}")
            print("1. Pepperoni - $120")
            print("2. Hawaiana - $115")

            while True:
                try:
                    tipo = int(input("Seleccione la pizza: "))
                    if tipo in (1, 2):
                        break
                    print("Opcion invalida. Seleccione 1 o 2.")
                except ValueError:
                    print("Opcion invalida. Ingrese un numero.")

            print("\nTamano:")
            print("1. Chica")
            print("2. Mediana")
            print("3. Grande")

            while True:
                try:
                    tamano = int(input("Seleccione el tamano: "))
                    if tamano in (1, 2, 3):
                        break
                    print("Opcion invalida. Seleccione 1, 2 o 3.")
                except ValueError:
                    print("Opcion invalida. Ingrese un numero.")

            if tamano == 1:
                multiplicador = 1.0
            elif tamano == 2:
                multiplicador = 1.5
            else:
                multiplicador = 2.0

            harina_necesaria += 250 * multiplicador
            queso_necesario += 150 * multiplicador
            salsa_necesaria += 100 * multiplicador

            if tipo == 1:
                total += 120 * multiplicador
                pep_necesario += 80 * multiplicador
                pepperoni_pedidas += 1
            else:
                total += 115 * multiplicador
                jamon_necesario += 70 * multiplicador
                pina_necesaria += 70 * multiplicador
                hawaianas_pedidas += 1

        if not comprobar_inventario(
            harina, queso, salsa, pep, jamon, pina,
            harina_necesaria, queso_necesario, salsa_necesaria,
            pep_necesario, jamon_necesario, pina_necesaria
        ):
            print("\nLa venta no puede realizarse por falta de ingredientes.")
            continue

        porcentaje_descuento = seleccionar_descuento()
        descuento = total * porcentaje_descuento
        subtotal = total - descuento
        iva = subtotal * 0.16
        total_con_iva = subtotal + iva

        print(f"\nSubtotal original: ${total:.2f}")
        print(f"Descuento: ${descuento:.2f} ({porcentaje_descuento * 100:.0f}%)")
        print(f"Subtotal con descuento: ${subtotal:.2f}")
        print(f"IVA (16%): ${iva:.2f}")
        print(f"Total: ${total_con_iva:.2f}")

        pago = 0.0
        cambio = 0.0

        while True:
            print("\nFORMA DE PAGO")
            print("1. Efectivo")
            print("2. Tarjeta")

            try:
                forma_pago = int(input("Seleccione una opcion: "))
            except ValueError:
                print("Opcion invalida.")
                continue

            if forma_pago == 1:
                while True:
                    try:
                        pago = float(input("Ingrese el dinero recibido: $"))
                        if not math.isfinite(pago) or pago < 0:
                            print("Cantidad invalida.")
                            continue
                        if pago > LIMITE_EFECTIVO:
                            print(f"El pago supera el limite de ${LIMITE_EFECTIVO:.2f}.")
                            continue
                        if pago < total_con_iva:
                            faltante = total_con_iva - pago
                            print(f"Dinero insuficiente. Faltan ${faltante:.2f}.")
                            continue

                        cambio = pago - total_con_iva
                        break
                    except ValueError:
                        print("Cantidad invalida. Ingrese un numero.")

                forma_pago_texto = "Efectivo"
                break

            elif forma_pago == 2:
                print("\nPago con tarjeta seleccionado.")

                # Solicita confirmacion y el codigo de autorizacion de 6 digitos
                while True:
                    confirmacion = input("Desea confirmar el pago? (s/n): ").lower().strip()

                    if confirmacion == "s":
                        while True:
                            num_autorizacion = input("Ingrese el codigo de autorizacion de 6 digitos: ").strip()
                            if num_autorizacion.isdigit() and len(num_autorizacion) == 6:
                                cambio = 0.0
                                forma_pago_texto = f"Tarjeta (Autorizacion: {num_autorizacion})"
                                print("Pago con tarjeta aprobado.")
                                break
                            else:
                                print("Codigo invalido. Debe ser un numero de exactamente 6 digitos.")
                        break

                    elif confirmacion == "n":
                        print("Pago cancelado.")
                        break
                    else:
                        print("Respuesta invalida. Escriba s o n.")

                if confirmacion == "s":
                    break

            else:
                print("Opcion invalida. Seleccione 1 o 2.")

        # Descontar ingredientes
        harina -= harina_necesaria
        queso -= queso_necesario
        salsa -= salsa_necesaria
        pep -= pep_necesario
        jamon -= jamon_necesario
        pina -= pina_necesaria

        # Registrar reduccion de inventario en archivo
        guardar_movimiento_inventario(
            "VENTA",
            -harina_necesaria, -queso_necesario, -salsa_necesaria,
            -pep_necesario, -jamon_necesario, -pina_necesaria,
            usuario, nickname, caja
        )

        ventas += cant
        ventasPep += pepperoni_pedidas
        ventasHaw += hawaianas_pedidas
        folio += 1

        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        print("\nPIZZERIA")
        print("TICKET")
        print(f"Folio: Caja #{caja}-{folio:04d}")
        print(f"Usuario: {usuario}")
        print(f"Nickname: {nickname}")
        print(f"Caja: #{caja}")
        print(f"Fecha: {fecha_hora}")
        print(f"Forma de pago: {forma_pago_texto}")
        print(f"Pizzas: {cant}")
        print(f"Subtotal original: ${total:.2f}")
        print(f"Descuento: ${descuento:.2f} ({porcentaje_descuento * 100:.0f}%)")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"IVA: ${iva:.2f}")
        print(f"Total: ${total_con_iva:.2f}")

        if forma_pago == 1:
            print(f"Pago recibido: ${pago:.2f}")
            print(f"Cambio: ${cambio:.2f}")

        if forma_pago == 2:
            mostrar_comprobante_pago(
                folio, usuario, nickname, caja, fecha_hora,
                forma_pago_texto, cant, total, descuento,
                porcentaje_descuento, subtotal, iva, total_con_iva
            )

        # Actualizacion automatica del sistema de archivos al generar ticket:
        # 1. Guardar Ticket Completo
        guardar_ticket_archivo(
            folio, caja, usuario, nickname, fecha_hora, forma_pago_texto,
            cant, total, descuento, porcentaje_descuento, subtotal, iva, total_con_iva,
            pago, cambio
        )

        # 2. Guardar Registro de Ventas Resumido (Solo pizzas vendidas y dinero)
        guardar_registro_ventas_resumido(
            folio, caja, usuario, nickname, fecha_hora,
            cant, pepperoni_pedidas, hawaianas_pedidas, total_con_iva
        )

        print("Venta realizada correctamente y registrada en archivos.")

        alertas_inventario(harina, queso, salsa, pep, jamon, pina)

        return (
            harina, queso, salsa, pep, jamon, pina,
            ventas, ventasPep, ventasHaw, folio, total_con_iva
        )


# Funcion para mostrar el reporte de la caja
def mostrar_reporte_caja(
    usuario, nickname, caja, ventas, ventasPep, ventasHaw, folio, total_caja
):
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("\nREPORTE DE VENTAS")
    print(f"Fecha y hora: {fecha_hora}")
    print(f"Usuario: {usuario}")
    print(f"Nickname: {nickname}")
    print(f"Caja: #{caja}")
    print(f"Ventas realizadas: {ventas}")
    print(f"Pepperoni vendidas: {ventasPep}")
    print(f"Hawaianas vendidas: {ventasHaw}")

    if folio > 0:
        print(f"Ultimo folio: Caja #{caja}-{folio:04d}")
    else:
        print("Ultimo folio: Sin ventas")

    print(f"Dinero total vendido: ${total_caja:.2f}")


# Guarda el reporte de la caja en un archivo
def guardar_reporte_caja(
    usuario, nickname, caja, ventas, ventasPep, ventasHaw, folio, total_caja
):
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    nombre_archivo = f"reporte_caja_{caja}.txt"

    try:
        with open(nombre_archivo, "a", encoding="utf-8") as archivo:
            archivo.write("\nREPORTE DE VENTAS\n")
            archivo.write(f"Fecha y hora: {fecha_hora}\n")
            archivo.write(f"Usuario: {usuario}\n")
            archivo.write(f"Nickname: {nickname}\n")
            archivo.write(f"Caja: #{caja}\n")
            archivo.write(f"Ventas realizadas: {ventas}\n")
            archivo.write(f"Pepperoni vendidas: {ventasPep}\n")
            archivo.write(f"Hawaianas vendidas: {ventasHaw}\n")
            archivo.write(f"Ultimo folio: Caja #{caja}-{folio:04d}\n")
            archivo.write(f"Dinero total vendido: ${total_caja:.2f}\n")
            archivo.write("------------------------------\n")

        print(f"Reporte guardado en {nombre_archivo}.")

    except OSError:
        print("No se pudo guardar el reporte.")


# Funcion para guardar el inventario
def guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina):
    inventario["harina"] = harina
    inventario["queso"] = queso
    inventario["salsa"] = salsa
    inventario["pep"] = pep
    inventario["jamon"] = jamon
    inventario["pina"] = pina


# Funcion para pedir cantidades de reabastecimiento
def pedir_cantidad(mensaje):
    while True:
        try:
            cantidad = float(input(mensaje))
            if not math.isfinite(cantidad) or cantidad < 0:
                print("Cantidad invalida.")
                continue
            return cantidad
        except ValueError:
            print("Cantidad invalida.")


# Funcion principal de cada caja
def abrir_caja(usuario, nickname, caja, inventario, estado_caja):
    harina = inventario["harina"]
    queso = inventario["queso"]
    salsa = inventario["salsa"]
    pep = inventario["pep"]
    jamon = inventario["jamon"]
    pina = inventario["pina"]

    ventas = estado_caja["ventas"]
    ventasPep = estado_caja["ventasPep"]
    ventasHaw = estado_caja["ventasHaw"]
    folio = estado_caja["folio"]
    total_caja = estado_caja["total_caja"]

    print("\nPIZZERIA")
    print(f"Usuario: {usuario} | Nickname: {nickname} | Caja #{caja}")
    print("Caja abierta correctamente.")

    while True:
        print("\nPIZZERIA")
        print(f"Usuario: {usuario} | Nickname: {nickname} | Caja #{caja}")
        print("V. Registrar venta")
        print("M. Mostrar menu")
        print("C. Cerrar caja")

        opcion = obtener_opcion_con_temporizador("Seleccione una opcion: ")

        if opcion == "CANCELAR_PANTALLA_INICIAL":
            guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)
            return "CAMBIAR_USUARIO"

        opcion = opcion.strip().upper()

        # Registrar venta
        if opcion == "V":
            resultado = registrar_venta(
                harina, queso, salsa, pep, jamon, pina,
                ventas, ventasPep, ventasHaw, folio,
                usuario, nickname, caja
            )

            (
                harina, queso, salsa, pep, jamon, pina,
                ventas, ventasPep, ventasHaw, folio,
                importe_venta
            ) = resultado

            total_caja += importe_venta

            estado_caja["ventas"] = ventas
            estado_caja["ventasPep"] = ventasPep
            estado_caja["ventasHaw"] = ventasHaw
            estado_caja["folio"] = folio
            estado_caja["total_caja"] = total_caja

            guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)

            print(f"Total acumulado de Caja #{caja}: ${total_caja:.2f}")

        # Mostrar menu secundario
        elif opcion == "M":
            while True:
                print("\nMENU PRINCIPAL")
                print("1. Consultar inventario")
                print("2. Reabastecer")
                print("3. Reportes")
                print("4. Documentos")
                print("5. Regresar a ventas")
                print("6. Cambiar de usuario")

                menu_opcion = obtener_opcion_con_temporizador("Seleccione una opcion: ")

                if menu_opcion == "CANCELAR_PANTALLA_INICIAL":
                    guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)
                    return "CAMBIAR_USUARIO"

                try:
                    menu_opcion = int(menu_opcion)
                except ValueError:
                    print("Opcion invalida.")
                    continue

                if menu_opcion == 1:
                    print("\nINVENTARIO")
                    print(f"Harina: {harina:.2f} g")
                    print(f"Queso: {queso:.2f} g")
                    print(f"Salsa: {salsa:.2f} g")
                    print(f"Pepperoni: {pep:.2f} g")
                    print(f"Jamon: {jamon:.2f} g")
                    print(f"Pina: {pina:.2f} g")

                    alertas_inventario(harina, queso, salsa, pep, jamon, pina)

                elif menu_opcion == 2:
                    print("\nREABASTECER")

                    h_add = pedir_cantidad("Harina a agregar (g): ")
                    q_add = pedir_cantidad("Queso a agregar (g): ")
                    s_add = pedir_cantidad("Salsa a agregar (g): ")
                    p_add = pedir_cantidad("Pepperoni a agregar (g): ")
                    j_add = pedir_cantidad("Jamon a agregar (g): ")
                    pi_add = pedir_cantidad("Pina a agregar (g): ")

                    harina += h_add
                    queso += q_add
                    salsa += s_add
                    pep += p_add
                    jamon += j_add
                    pina += pi_add

                    guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)

                    # Registrar incremento de inventario en archivo
                    guardar_movimiento_inventario(
                        "REABASTECIMIENTO",
                        h_add, q_add, s_add, p_add, j_add, pi_add,
                        usuario, nickname, caja
                    )

                    print("Inventario actualizado correctamente.")

                elif menu_opcion == 3:
                    mostrar_reporte_caja(
                        usuario, nickname, caja,
                        ventas, ventasPep, ventasHaw,
                        folio, total_caja
                    )

                elif menu_opcion == 4:
                    resultado_documentos = menu_documentos(usuario, nickname, caja)

                    if resultado_documentos == "CAMBIAR_USUARIO":
                        guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)
                        return "CAMBIAR_USUARIO"

                elif menu_opcion == 5:
                    break

                elif menu_opcion == 6:
                    guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)
                    print("Regresando a la pantalla inicial.")
                    return "CAMBIAR_USUARIO"

                else:
                    print("Opcion invalida.")

        elif opcion == "C":
            print("\nCIERRE DE CAJA")

            mostrar_reporte_caja(
                usuario, nickname, caja,
                ventas, ventasPep, ventasHaw,
                folio, total_caja
            )

            estado_caja["ventas"] = ventas
            estado_caja["ventasPep"] = ventasPep
            estado_caja["ventasHaw"] = ventasHaw
            estado_caja["folio"] = folio
            estado_caja["total_caja"] = total_caja

            guardar_inventario(inventario, harina, queso, salsa, pep, jamon, pina)

            guardar_reporte_caja(
                usuario, nickname, caja,
                ventas, ventasPep, ventasHaw,
                folio, total_caja
            )

            print("\nCaja cerrada correctamente.")
            return "CERRAR_CAJA"

        else:
            print("Opcion invalida. Use V, M o C.")


# Funcion principal del programa
def sistema_pizzeria():
    inventario = {
        "harina": 5000.0,
        "queso": 3000.0,
        "salsa": 2000.0,
        "pep": 1000.0,
        "jamon": 1000.0,
        "pina": 1000.0
    }

    cajas = {
        1: {
            "ventas": 0,
            "ventasPep": 0,
            "ventasHaw": 0,
            "folio": 0,
            "total_caja": 0.0
        },
        2: {
            "ventas": 0,
            "ventasPep": 0,
            "ventasHaw": 0,
            "folio": 0,
            "total_caja": 0.0
        }
    }

    crear_archivos_iniciales()
    cargar_programa()

    while True:
        print("\nPIZZERIA")
        print("1. Iniciar sesion")
        print("2. Salir del programa")

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            usuario, nickname = iniciar_sesion()

            caja = seleccionar_caja()

            if caja is None:
                print("Programa finalizado.")
                break

            resultado = abrir_caja(
                usuario, nickname, caja,
                inventario, cajas[caja]
            )

            if resultado == "CAMBIAR_USUARIO":
                print("\nRegresando a la pantalla de inicio de sesion.")
                continue

            print("\nLa caja se cerro. Regresando al menu de inicio.")

        elif opcion == "2":
            print("\nGracias por visitar la pizzeria.")
            break

        else:
            print("Opcion invalida. Intente nuevamente.")


if __name__ == "__main__":
    sistema_pizzeria()