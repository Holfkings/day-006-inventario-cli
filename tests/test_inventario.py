"""Tests para el gestor de inventario."""

import os
import sys
import tempfile
import pytest

# Asegurar que el directorio del proyecto está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Producto, Venta, MovimientoStock
import db


@pytest.fixture
def test_db():
    """Crea una base de datos temporal para cada test."""
    # Cerrar conexiones existentes
    import importlib
    importlib.reload(db)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    db.DB_PATH = db_path
    db.init_db()
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


# ---- Tests de Modelos ----

class TestProducto:
    def test_creacion_basica(self):
        p = Producto(nombre="Test", precio=100.0, stock=10)
        assert p.nombre == "Test"
        assert p.precio == 100.0
        assert p.stock == 10
        assert p.stock_minimo == 5
        assert p.categoria == "General"

    def test_stock_bajo(self):
        p = Producto(nombre="Test", stock=3, stock_minimo=5)
        assert p.stock_bajo is True

    def test_stock_ok(self):
        p = Producto(nombre="Test", stock=10, stock_minimo=5)
        assert p.stock_bajo is False

    def test_valor_inventario(self):
        p = Producto(nombre="Test", precio=150.0, stock=4)
        assert p.valor_inventario == 600.0

    def test_to_dict(self):
        p = Producto(id=1, nombre="Test", precio=100.0, stock=10)
        d = p.to_dict()
        assert d['id'] == 1
        assert d['nombre'] == "Test"
        assert d['precio'] == 100.0

    def test_from_row(self):
        row = (1, "Test", "Desc", 100.0, 10, 5, "General", "2024-01-01", "2024-01-01")
        p = Producto.from_row(row)
        assert p.id == 1
        assert p.nombre == "Test"
        assert p.descripcion == "Desc"


class TestVenta:
    def test_creacion_basica(self):
        v = Venta(producto_id=1, cantidad=2, precio_unitario=50.0)
        assert v.total == 100.0

    def test_total_manual(self):
        v = Venta(producto_id=1, cantidad=2, precio_unitario=50.0, total=999.0)
        assert v.total == 999.0

    def test_from_row(self):
        row = (1, 1, 2, 50.0, 100.0, "Cliente", "Notas", "2024-01-01")
        v = Venta.from_row(row)
        assert v.id == 1
        assert v.producto_id == 1
        assert v.cantidad == 2
        assert v.total == 100.0


# ---- Tests de Base de Datos ----

class TestDB:
    def test_init_db(self, test_db):
        productos = db.listar_productos()
        assert productos == []

    def test_crear_producto(self, test_db):
        p = Producto(nombre="Laptop", precio=2000000.0, stock=10)
        pid = db.crear_producto(p)
        assert pid > 0

        recuperado = db.obtener_producto(pid)
        assert recuperado.nombre == "Laptop"
        assert recuperado.precio == 2000000.0

    def test_listar_productos(self, test_db):
        db.crear_producto(Producto(nombre="A", precio=100.0, stock=5))
        db.crear_producto(Producto(nombre="B", precio=200.0, stock=3))
        productos = db.listar_productos()
        assert len(productos) == 2

    def test_buscar_productos(self, test_db):
        db.crear_producto(Producto(nombre="Laptop Gaming", precio=2000000.0))
        db.crear_producto(Producto(nombre="Mouse", precio=50000.0))
        resultados = db.buscar_productos("Laptop")
        assert len(resultados) == 1
        assert resultados[0].nombre == "Laptop Gaming"

    def test_actualizar_producto(self, test_db):
        p = Producto(nombre="Viejo", precio=100.0)
        pid = db.crear_producto(p)
        p.id = pid
        p.nombre = "Nuevo"
        p.precio = 200.0
        assert db.actualizar_producto(p) is True
        actualizado = db.obtener_producto(pid)
        assert actualizado.nombre == "Nuevo"
        assert actualizado.precio == 200.0

    def test_eliminar_producto(self, test_db):
        p = Producto(nombre="Test", precio=100.0)
        pid = db.crear_producto(p)
        assert db.eliminar_producto(pid) is True
        assert db.obtener_producto(pid) is None

    def test_productos_con_stock_bajo(self, test_db):
        db.crear_producto(Producto(nombre="OK", precio=100.0, stock=10, stock_minimo=5))
        db.crear_producto(Producto(nombre="Bajo", precio=100.0, stock=2, stock_minimo=5))
        bajos = db.productos_con_stock_bajo()
        assert len(bajos) == 1
        assert bajos[0].nombre == "Bajo"


class TestVentas:
    def test_registrar_venta(self, test_db):
        p = Producto(nombre="Test", precio=100.0, stock=10)
        pid = db.crear_producto(p)

        v = Venta(producto_id=pid, cantidad=3, precio_unitario=100.0)
        vid = db.registrar_venta(v)
        assert vid > 0

        # Verificar stock actualizado
        producto = db.obtener_producto(pid)
        assert producto.stock == 7

    def test_venta_stock_insuficiente(self, test_db):
        p = Producto(nombre="Test", precio=100.0, stock=2)
        pid = db.crear_producto(p)

        v = Venta(producto_id=pid, cantidad=5, precio_unitario=100.0)
        with pytest.raises(ValueError, match="Stock insuficiente"):
            db.registrar_venta(v)

    def test_listar_ventas(self, test_db):
        p = Producto(nombre="Test", precio=100.0, stock=10)
        pid = db.crear_producto(p)
        db.registrar_venta(Venta(producto_id=pid, cantidad=1, precio_unitario=100.0))
        db.registrar_venta(Venta(producto_id=pid, cantidad=2, precio_unitario=100.0))
        ventas = db.listar_ventas()
        assert len(ventas) == 2


class TestMovimientosStock:
    def test_entrada_stock(self, test_db):
        p = Producto(nombre="Test", precio=100.0, stock=5)
        pid = db.crear_producto(p)

        mid = db.registrar_entrada_stock(pid, 10, "Compra proveedor")
        assert mid > 0

        producto = db.obtener_producto(pid)
        assert producto.stock == 15

    def test_listar_movimientos(self, test_db):
        p = Producto(nombre="Test", precio=100.0, stock=5)
        pid = db.crear_producto(p)
        db.registrar_entrada_stock(pid, 10)
        db.registrar_entrada_stock(pid, 5)
        movimientos = db.listar_movimientos(pid)
        assert len(movimientos) == 2


class TestReportes:
    def test_resumen_inventario(self, test_db):
        db.crear_producto(Producto(nombre="A", precio=100.0, stock=10))
        db.crear_producto(Producto(nombre="B", precio=200.0, stock=5))
        resumen = db.resumen_inventario()
        assert resumen['total_productos'] == 2
        assert resumen['total_unidades'] == 15
        assert resumen['valor_total_inventario'] == 2000.0

    def test_top_productos_vendidos(self, test_db):
        p1 = Producto(nombre="Popular", precio=100.0, stock=100)
        p2 = Producto(nombre="Menos", precio=100.0, stock=100)
        pid1 = db.crear_producto(p1)
        pid2 = db.crear_producto(p2)

        db.registrar_venta(Venta(producto_id=pid1, cantidad=10, precio_unitario=100.0))
        db.registrar_venta(Venta(producto_id=pid2, cantidad=2, precio_unitario=100.0))

        top = db.top_productos_vendidos()
        assert len(top) == 2
        assert top[0]['nombre'] == "Popular"
        assert top[0]['total_vendido'] == 10
