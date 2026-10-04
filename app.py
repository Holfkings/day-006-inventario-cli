#!/usr/bin/env python3
"""
Gestor de Inventario CLI — aplicación principal.

Interfaz de línea de comandos para gestionar productos, ventas y stock.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Asegurar que el directorio actual está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Producto, Venta, MovimientoStock
import db


# ---- Utilidades de presentación ----

def print_header(titulo: str):
    """Imprime un encabezado formateado."""
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}\n")


def print_table(headers: list, rows: list, widths: Optional[list] = None):
    """Imprime una tabla con columnas alineadas."""
    if not rows:
        print("  (sin datos)")
        return

    if widths is None:
        widths = [max(len(str(h)), max(len(str(row[i])) for row in rows)) for i, h in enumerate(headers)]

    header_line = "  " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    separator = "  " + "-+-".join("-" * w for w in widths)

    print(header_line)
    print(separator)
    for row in rows:
        print("  " + " | ".join(str(v).ljust(w) for v, w in zip(row, widths)))
    print()


def format_currency(valor: float) -> str:
    """Formatea un valor como moneda colombiana."""
    return f"${valor:,.0f} COP"


def input_required(prompt: str) -> str:
    """Solicita un valor obligatorio."""
    while True:
        valor = input(f"  {prompt}: ").strip()
        if valor:
            return valor
        print("    ⚠ Este campo es obligatorio.")


def input_float(prompt: str, min_val: float = 0) -> float:
    """Solicita un valor flotante."""
    while True:
        try:
            valor = float(input(f"  {prompt}: ").strip())
            if valor >= min_val:
                return valor
            print(f"    ⚠ Debe ser >= {min_val}")
        except ValueError:
            print("    ⚠ Ingrese un número válido.")


def input_int(prompt: str, min_val: int = 0) -> int:
    """Solicita un valor entero."""
    while True:
        try:
            valor = int(input(f"  {prompt}: ").strip())
            if valor >= min_val:
                return valor
            print(f"    ⚠ Debe ser >= {min_val}")
        except ValueError:
            print("    ⚠ Ingrese un número entero válido.")


def confirmar(mensaje: str) -> bool:
    """Solicita confirmación al usuario."""
    respuesta = input(f"  {mensaje} (s/n): ").strip().lower()
    return respuesta in ('s', 'si', 'sí', 'y', 'yes')


# ---- Comandos de Productos ----

def cmd_agregar_producto(args):
    """Agrega un nuevo producto al inventario."""
    print_header("AGREGAR PRODUCTO")

    nombre = input_required("Nombre del producto")
    descripcion = input("  Descripción (opcional): ").strip()
    precio = input_float("Precio de venta", 0.01)
    stock = input_int("Stock inicial", 0)
    stock_minimo = input_int("Stock mínimo (alerta)", 0)
    categoria = input("  Categoría [General]: ").strip() or "General"

    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        stock_minimo=stock_minimo,
        categoria=categoria,
    )

    producto_id = db.crear_producto(producto)
    print(f"\n  ✓ Producto agregado con ID: {producto_id}")
    print(f"    Nombre: {nombre}")
    print(f"    Precio: {format_currency(precio)}")
    print(f"    Stock: {stock} unidades")


def cmd_listar_productos(args):
    """Lista todos los productos."""
    print_header("INVENTARIO DE PRODUCTOS")

    productos = db.listar_productos()
    if not productos:
        print("  No hay productos registrados.")
        return

    headers = ["ID", "Nombre", "Categoría", "Precio", "Stock", "Mínimo", "Estado"]
    rows = []
    for p in productos:
        estado = "⚠ BAJO" if p.stock_bajo else "OK"
        rows.append([
            p.id, p.nombre[:25], p.categoria[:15],
            format_currency(p.precio), p.stock, p.stock_minimo, estado
        ])

    print_table(headers, rows, [4, 27, 17, 14, 8, 8, 8])
    print(f"  Total: {len(productos)} productos")


def cmd_buscar_producto(args):
    """Busca productos por término."""
    print_header("BUSCAR PRODUCTO")

    termino = input_required("Término de búsqueda")
    productos = db.buscar_productos(termino)

    if not productos:
        print(f"  No se encontraron productos con '{termino}'")
        return

    headers = ["ID", "Nombre", "Categoría", "Precio", "Stock"]
    rows = [[p.id, p.nombre[:30], p.categoria[:15], format_currency(p.precio), p.stock] for p in productos]
    print_table(headers, rows, [4, 32, 17, 14, 8])
    print(f"  {len(productos)} resultado(s)")


def cmd_ver_producto(args):
    """Muestra detalle de un producto."""
    print_header("DETALLE DE PRODUCTO")

    producto_id = input_int("ID del producto", 1)
    producto = db.obtener_producto(producto_id)

    if not producto:
        print(f"  ✗ Producto {producto_id} no encontrado")
        return

    print(f"  ID:          {producto.id}")
    print(f"  Nombre:      {producto.nombre}")
    print(f"  Descripción: {producto.descripcion or '(sin descripción)'}")
    print(f"  Categoría:   {producto.categoria}")
    print(f"  Precio:      {format_currency(producto.precio)}")
    print(f"  Stock:       {producto.stock} unidades")
    print(f"  Stock mín:   {producto.stock_minimo} unidades")
    print(f"  Valor inv.:  {format_currency(producto.valor_inventario)}")
    print(f"  Estado:      {'⚠ STOCK BAJO' if producto.stock_bajo else '✓ OK'}")
    print(f"  Creado:      {producto.creado_en[:19]}")
    print(f"  Actualizado: {producto.actualizado_en[:19]}")


def cmd_editar_producto(args):
    """Edita un producto existente."""
    print_header("EDITAR PRODUCTO")

    producto_id = input_int("ID del producto", 1)
    producto = db.obtener_producto(producto_id)

    if not producto:
        print(f"  ✗ Producto {producto_id} no encontrado")
        return

    print(f"  Editando: {producto.nombre}")
    print("  (Enter para mantener valor actual)\n")

    nombre = input(f"  Nombre [{producto.nombre}]: ").strip() or producto.nombre
    descripcion = input(f"  Descripción [{producto.descripcion}]: ").strip() or producto.descripcion
    precio_str = input(f"  Precio [{producto.precio}]: ").strip()
    precio = float(precio_str) if precio_str else producto.precio
    stock_str = input(f"  Stock [{producto.stock}]: ").strip()
    stock = int(stock_str) if stock_str else producto.stock
    stock_min_str = input(f"  Stock mínimo [{producto.stock_minimo}]: ").strip()
    stock_minimo = int(stock_min_str) if stock_min_str else producto.stock_minimo
    categoria = input(f"  Categoría [{producto.categoria}]: ").strip() or producto.categoria

    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.stock = stock
    producto.stock_minimo = stock_minimo
    producto.categoria = categoria

    if db.actualizar_producto(producto):
        print(f"\n  ✓ Producto actualizado correctamente")
    else:
        print(f"\n  ✗ Error al actualizar el producto")


def cmd_eliminar_producto(args):
    """Elimina un producto."""
    print_header("ELIMINAR PRODUCTO")

    producto_id = input_int("ID del producto", 1)
    producto = db.obtener_producto(producto_id)

    if not producto:
        print(f"  ✗ Producto {producto_id} no encontrado")
        return

    print(f"  Producto: {producto.nombre}")
    print(f"  Stock actual: {producto.stock} unidades")

    if not confirmar("¿Está seguro de eliminar este producto?"):
        print("  Operación cancelada.")
        return

    if db.eliminar_producto(producto_id):
        print(f"  ✓ Producto eliminado")
    else:
        print(f"  ✗ Error al eliminar")


# ---- Comandos de Stock ----

def cmd_entrada_stock(args):
    """Registra entrada de stock."""
    print_header("ENTRADA DE STOCK")

    producto_id = input_int("ID del producto", 1)
    producto = db.obtener_producto(producto_id)

    if not producto:
        print(f"  ✗ Producto {producto_id} no encontrado")
        return

    print(f"  Producto: {producto.nombre}")
    print(f"  Stock actual: {producto.stock} unidades\n")

    cantidad = input_int("Cantidad a ingresar", 1)
    motivo = input("  Motivo (opcional): ").strip()

    movimiento_id = db.registrar_entrada_stock(producto_id, cantidad, motivo)
    nuevo_stock = db.obtener_producto(producto_id).stock

    print(f"\n  ✓ Entrada registrada (movimiento #{movimiento_id})")
    print(f"    Cantidad: +{cantidad}")
    print(f"    Nuevo stock: {nuevo_stock} unidades")


def cmd_stock_bajo(args):
    """Muestra productos con stock bajo."""
    print_header("ALERTAS DE STOCK BAJO")

    productos = db.productos_con_stock_bajo()

    if not productos:
        print("  ✓ No hay productos con stock bajo")
        return

    headers = ["ID", "Nombre", "Stock", "Mínimo", "Faltante"]
    rows = []
    for p in productos:
        faltante = p.stock_minimo - p.stock
        rows.append([p.id, p.nombre[:30], p.stock, p.stock_minimo, f"+{faltante}"])

    print_table(headers, rows, [4, 32, 8, 8, 10])
    print(f"  ⚠ {len(productos)} producto(s) necesitan reposición")


# ---- Comandos de Ventas ----

def cmd_registrar_venta(args):
    """Registra una nueva venta."""
    print_header("REGISTRAR VENTA")

    producto_id = input_int("ID del producto", 1)
    producto = db.obtener_producto(producto_id)

    if not producto:
        print(f"  ✗ Producto {producto_id} no encontrado")
        return

    print(f"  Producto: {producto.nombre}")
    print(f"  Precio: {format_currency(producto.precio)}")
    print(f"  Stock disponible: {producto.stock} unidades\n")

    cantidad = input_int("Cantidad vendida", 1)
    if cantidad > producto.stock:
        print(f"  ✗ Stock insuficiente (disponible: {producto.stock})")
        return

    precio_str = input(f"  Precio unitario [{producto.precio}]: ").strip()
    precio_unitario = float(precio_str) if precio_str else producto.precio

    cliente = input("  Cliente (opcional): ").strip()
    notas = input("  Notas (opcional): ").strip()

    venta = Venta(
        producto_id=producto_id,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        cliente=cliente,
        notas=notas,
    )

    try:
        venta_id = db.registrar_venta(venta)
        print(f"\n  ✓ Venta registrada (ID: {venta_id})")
        print(f"    Producto: {producto.nombre}")
        print(f"    Cantidad: {cantidad}")
        print(f"    Total: {format_currency(venta.total)}")
        print(f"    Stock restante: {producto.stock - cantidad} unidades")
    except ValueError as e:
        print(f"\n  ✗ Error: {e}")


def cmd_listar_ventas(args):
    """Lista las ventas recientes."""
    print_header("VENTAS RECIENTES")

    ventas = db.listar_ventas(limit=50)

    if not ventas:
        print("  No hay ventas registradas.")
        return

    headers = ["ID", "Fecha", "Producto", "Cant.", "Total"]
    rows = []
    for v in ventas:
        producto = db.obtener_producto(v.producto_id)
        nombre_prod = producto.nombre[:20] if producto else "?"
        fecha = v.fecha[:16] if v.fecha else "?"
        rows.append([v.id, fecha, nombre_prod, v.cantidad, format_currency(v.total)])

    print_table(headers, rows, [4, 18, 22, 6, 14])
    print(f"  Mostrando {len(ventas)} venta(s)")


# ---- Comandos de Reportes ----

def cmd_resumen(args):
    """Muestra resumen del inventario."""
    print_header("RESUMEN DE INVENTARIO")

    resumen = db.resumen_inventario()

    print(f"  Total de productos:        {resumen['total_productos']}")
    print(f"  Unidades en stock:         {resumen['total_unidades']}")
    print(f"  Valor total inventario:    {format_currency(resumen['valor_total_inventario'])}")
    print(f"  Productos stock bajo:      {resumen['productos_con_stock_bajo']}")
    print(f"  Total ventas:              {format_currency(resumen['total_ventas'])}")
    print(f"  Cantidad de ventas:        {resumen['cantidad_ventas']}")


def cmd_top_ventas(args):
    """Muestra productos más vendidos."""
    print_header("PRODUCTOS MÁS VENDIDOS")

    top = db.top_productos_vendidos(limit=10)

    if not top:
        print("  No hay ventas registradas.")
        return

    headers = ["#", "Producto", "Unidades", "Ingresos"]
    rows = [[i+1, p['nombre'][:30], p['total_vendido'], format_currency(p['ingresos'])] for i, p in enumerate(top)]

    print_table(headers, rows, [4, 32, 10, 14])


def cmd_ventas_periodo(args):
    """Muestra ventas en un período."""
    print_header("VENTAS POR PERÍODO")

    print("  Formato de fecha: YYYY-MM-DD")
    fecha_inicio = input_required("Fecha inicio")
    fecha_fin = input_required("Fecha fin")

    try:
        datetime.strptime(fecha_inicio, "%Y-%m-%d")
        datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        print("  ✗ Formato de fecha inválido")
        return

    ventas = db.ventas_por_periodo(fecha_inicio, fecha_fin)

    if not ventas:
        print(f"  No hay ventas entre {fecha_inicio} y {fecha_fin}")
        return

    total = sum(v.total for v in ventas)
    headers = ["Fecha", "Producto", "Cant.", "Total"]
    rows = []
    for v in ventas:
        producto = db.obtener_producto(v.producto_id)
        nombre_prod = producto.nombre[:20] if producto else "?"
        rows.append([v.fecha[:16], nombre_prod, v.cantidad, format_currency(v.total)])

    print_table(headers, rows, [18, 22, 6, 14])
    print(f"  Total del período: {format_currency(total)}")


# ---- Menú interactivo ----

def menu_interactivo():
    """Ejecuta el menú interactivo."""
    db.init_db()

    while True:
        print_header("GESTOR DE INVENTARIO — MENÚ PRINCIPAL")
        print("  PRODUCTOS:")
        print("    1. Agregar producto")
        print("    2. Listar productos")
        print("    3. Buscar producto")
        print("    4. Ver detalle de producto")
        print("    5. Editar producto")
        print("    6. Eliminar producto")
        print("\n  STOCK:")
        print("    7. Entrada de stock")
        print("    8. Alertas de stock bajo")
        print("\n  VENTAS:")
        print("    9. Registrar venta")
        print("   10. Listar ventas")
        print("\n  REPORTES:")
        print("   11. Resumen de inventario")
        print("   12. Productos más vendidos")
        print("   13. Ventas por período")
        print("\n   0. Salir")
        print()

        opcion = input("  Seleccione opción: ").strip()

        acciones = {
            '1': cmd_agregar_producto,
            '2': cmd_listar_productos,
            '3': cmd_buscar_producto,
            '4': cmd_ver_producto,
            '5': cmd_editar_producto,
            '6': cmd_eliminar_producto,
            '7': cmd_entrada_stock,
            '8': cmd_stock_bajo,
            '9': cmd_registrar_venta,
            '10': cmd_listar_ventas,
            '11': cmd_resumen,
            '12': cmd_top_ventas,
            '13': cmd_ventas_periodo,
        }

        if opcion == '0':
            print("\n  ¡Hasta luego!\n")
            break
        elif opcion in acciones:
            try:
                acciones[opcion](None)
            except KeyboardInterrupt:
                print("\n  Operación cancelada.")
            except Exception as e:
                print(f"\n  ✗ Error: {e}")
        else:
            print("  Opción no válida.")

        input("\n  Presione Enter para continuar...")


# ---- Punto de entrada ----

def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Gestor de Inventario CLI — control de productos, stock y ventas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--db', default='inventario.db',
        help='Ruta de la base de datos (default: inventario.db)'
    )

    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')

    # Comandos directos (sin subcomando, abre menú interactivo)
    p_agregar = subparsers.add_parser('agregar', help='Agregar producto')
    p_agregar.set_defaults(func=cmd_agregar_producto)

    p_listar = subparsers.add_parser('listar', help='Listar productos')
    p_listar.set_defaults(func=cmd_listar_productos)

    p_buscar = subparsers.add_parser('buscar', help='Buscar productos')
    p_buscar.set_defaults(func=cmd_buscar_producto)

    p_ver = subparsers.add_parser('ver', help='Ver detalle de producto')
    p_ver.set_defaults(func=cmd_ver_producto)

    p_editar = subparsers.add_parser('editar', help='Editar producto')
    p_editar.set_defaults(func=cmd_editar_producto)

    p_eliminar = subparsers.add_parser('eliminar', help='Eliminar producto')
    p_eliminar.set_defaults(func=cmd_eliminar_producto)

    p_entrada = subparsers.add_parser('entrada', help='Entrada de stock')
    p_entrada.set_defaults(func=cmd_entrada_stock)

    p_bajo = subparsers.add_parser('stock-bajo', help='Alertas de stock bajo')
    p_bajo.set_defaults(func=cmd_stock_bajo)

    p_venta = subparsers.add_parser('vender', help='Registrar venta')
    p_venta.set_defaults(func=cmd_registrar_venta)

    p_ventas = subparsers.add_parser('ventas', help='Listar ventas')
    p_ventas.set_defaults(func=cmd_listar_ventas)

    p_resumen = subparsers.add_parser('resumen', help='Resumen de inventario')
    p_resumen.set_defaults(func=cmd_resumen)

    p_top = subparsers.add_parser('top', help='Productos más vendidos')
    p_top.set_defaults(func=cmd_top_ventas)

    args = parser.parse_args()

    # Configurar ruta de BD
    db.DB_PATH = args.db

    # Inicializar BD
    db.init_db()

    if hasattr(args, 'func'):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n  Operación cancelada.")
        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            sys.exit(1)
    else:
        # Sin subcomando → menú interactivo
        try:
            menu_interactivo()
        except KeyboardInterrupt:
            print("\n\n  ¡Hasta luego!")
            sys.exit(0)


if __name__ == '__main__':
    main()
