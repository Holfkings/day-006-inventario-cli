"""Capa de acceso a datos — SQLite."""

import sqlite3
import os
from typing import List, Optional
from models import Producto, Venta, MovimientoStock


DB_PATH = os.environ.get("INVENTARIO_DB", "inventario.db")


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Crea una conexión a la base de datos."""
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = None) -> None:
    """Inicializa el esquema de la base de datos."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                precio REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER NOT NULL DEFAULT 5,
                categoria TEXT DEFAULT 'General',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                total REAL NOT NULL,
                cliente TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                fecha TEXT NOT NULL,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS movimientos_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida')),
                cantidad INTEGER NOT NULL,
                motivo TEXT DEFAULT '',
                fecha TEXT NOT NULL,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre);
            CREATE INDEX IF NOT EXISTS idx_ventas_producto ON ventas(producto_id);
            CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
            CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_stock(producto_id);
        """)
        conn.commit()
    finally:
        conn.close()


# ---- Operaciones con Productos ----

def crear_producto(producto: Producto, db_path: str = None) -> int:
    """Inserta un nuevo producto y retorna su ID."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO productos (nombre, descripcion, precio, stock, stock_minimo, categoria, creado_en, actualizado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (producto.nombre, producto.descripcion, producto.precio,
             producto.stock, producto.stock_minimo, producto.categoria,
             producto.creado_en, producto.actualizado_en)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def obtener_producto(producto_id: int, db_path: str = None) -> Optional[Producto]:
    """Obtiene un producto por su ID."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        return Producto.from_row(tuple(row)) if row else None
    finally:
        conn.close()


def listar_productos(db_path: str = None) -> List[Producto]:
    """Lista todos los productos ordenados por nombre."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM productos ORDER BY nombre"
        ).fetchall()
        return [Producto.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


def buscar_productos(termino: str, db_path: str = None) -> List[Producto]:
    """Busca productos por nombre o descripción."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR descripcion LIKE ? ORDER BY nombre",
            (f"%{termino}%", f"%{termino}%")
        ).fetchall()
        return [Producto.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


def actualizar_producto(producto: Producto, db_path: str = None) -> bool:
    """Actualiza un producto existente."""
    from datetime import datetime
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """UPDATE productos SET nombre=?, descripcion=?, precio=?, stock=?,
               stock_minimo=?, categoria=?, actualizado_en=? WHERE id=?""",
            (producto.nombre, producto.descripcion, producto.precio,
             producto.stock, producto.stock_minimo, producto.categoria,
             datetime.now().isoformat(), producto.id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def eliminar_producto(producto_id: int, db_path: str = None) -> bool:
    """Elimina un producto por su ID."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        cursor = conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def productos_con_stock_bajo(db_path: str = None) -> List[Producto]:
    """Retorna productos con stock por debajo del mínimo."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM productos WHERE stock <= stock_minimo ORDER BY stock ASC"
        ).fetchall()
        return [Producto.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


# ---- Operaciones con Ventas ----

def registrar_venta(venta: Venta, db_path: str = None) -> int:
    """Registra una venta y actualiza el stock del producto."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        # Verificar stock disponible
        producto = obtener_producto(venta.producto_id, db_path)
        if not producto:
            raise ValueError(f"Producto {venta.producto_id} no existe")
        if producto.stock < venta.cantidad:
            raise ValueError(
                f"Stock insuficiente: disponible {producto.stock}, solicitado {venta.cantidad}"
            )

        # Calcular total
        venta.total = venta.cantidad * venta.precio_unitario

        # Insertar venta
        cursor = conn.execute(
            """INSERT INTO ventas (producto_id, cantidad, precio_unitario, total, cliente, notas, fecha)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (venta.producto_id, venta.cantidad, venta.precio_unitario,
             venta.total, venta.cliente, venta.notas, venta.fecha)
        )
        venta_id = cursor.lastrowid

        # Actualizar stock
        nuevo_stock = producto.stock - venta.cantidad
        conn.execute(
            "UPDATE productos SET stock = ?, actualizado_en = ? WHERE id = ?",
            (nuevo_stock, venta.fecha, venta.producto_id)
        )

        # Registrar movimiento
        conn.execute(
            """INSERT INTO movimientos_stock (producto_id, tipo, cantidad, motivo, fecha)
               VALUES (?, 'salida', ?, 'Venta registrada', ?)""",
            (venta.producto_id, venta.cantidad, venta.fecha)
        )

        conn.commit()
        return venta_id
    finally:
        conn.close()


def listar_ventas(limit: int = 100, db_path: str = None) -> List[Venta]:
    """Lista las ventas más recientes."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM ventas ORDER BY fecha DESC LIMIT ?", (limit,)
        ).fetchall()
        return [Venta.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


def ventas_por_producto(producto_id: int, db_path: str = None) -> List[Venta]:
    """Lista las ventas de un producto específico."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM ventas WHERE producto_id = ? ORDER BY fecha DESC",
            (producto_id,)
        ).fetchall()
        return [Venta.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


# ---- Operaciones con Movimientos de Stock ----

def registrar_entrada_stock(producto_id: int, cantidad: int, motivo: str = "",
                            db_path: str = None) -> int:
    """Registra una entrada de stock."""
    from datetime import datetime
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        fecha = datetime.now().isoformat()
        cursor = conn.execute(
            """INSERT INTO movimientos_stock (producto_id, tipo, cantidad, motivo, fecha)
               VALUES (?, 'entrada', ?, ?, ?)""",
            (producto_id, cantidad, motivo, fecha)
        )
        # Actualizar stock
        conn.execute(
            "UPDATE productos SET stock = stock + ?, actualizado_en = ? WHERE id = ?",
            (cantidad, fecha, producto_id)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def listar_movimientos(producto_id: Optional[int] = None, db_path: str = None) -> List[MovimientoStock]:
    """Lista movimientos de stock, opcionalmente filtrados por producto."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        if producto_id:
            rows = conn.execute(
                "SELECT * FROM movimientos_stock WHERE producto_id = ? ORDER BY fecha DESC",
                (producto_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM movimientos_stock ORDER BY fecha DESC LIMIT 200"
            ).fetchall()
        return [MovimientoStock.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


# ---- Estadísticas y Reportes ----

def resumen_inventario(db_path: str = None) -> dict:
    """Genera un resumen del inventario."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        total_productos = conn.execute(
            "SELECT COUNT(*) FROM productos"
        ).fetchone()[0]

        valor_total = conn.execute(
            "SELECT COALESCE(SUM(precio * stock), 0) FROM productos"
        ).fetchone()[0]

        total_stock = conn.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM productos"
        ).fetchone()[0]

        productos_bajo_stock = conn.execute(
            "SELECT COUNT(*) FROM productos WHERE stock <= stock_minimo"
        ).fetchone()[0]

        total_ventas = conn.execute(
            "SELECT COALESCE(SUM(total), 0) FROM ventas"
        ).fetchone()[0]

        cantidad_ventas = conn.execute(
            "SELECT COUNT(*) FROM ventas"
        ).fetchone()[0]

        return {
            "total_productos": total_productos,
            "valor_total_inventario": round(valor_total, 2),
            "total_unidades": total_stock,
            "productos_con_stock_bajo": productos_bajo_stock,
            "total_ventas": round(total_ventas, 2),
            "cantidad_ventas": cantidad_ventas,
        }
    finally:
        conn.close()


def top_productos_vendidos(limit: int = 10, db_path: str = None) -> List[dict]:
    """Retorna los productos más vendidos."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT p.id, p.nombre, SUM(v.cantidad) as total_vendido,
                      SUM(v.total) as ingresos
               FROM ventas v
               JOIN productos p ON v.producto_id = p.id
               GROUP BY p.id
               ORDER BY total_vendido DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
        return [
            {
                "id": r[0],
                "nombre": r[1],
                "total_vendido": r[2],
                "ingresos": round(r[3], 2),
            }
            for r in rows
        ]
    finally:
        conn.close()


def ventas_por_periodo(fecha_inicio: str, fecha_fin: str, db_path: str = None) -> List[Venta]:
    """Lista ventas en un rango de fechas."""
    if db_path is None:
        db_path = DB_PATH
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM ventas WHERE fecha >= ? AND fecha <= ? ORDER BY fecha DESC",
            (fecha_inicio, fecha_fin)
        ).fetchall()
        return [Venta.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()
