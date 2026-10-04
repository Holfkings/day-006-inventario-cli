"""Modelos de datos para el gestor de inventario."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Producto:
    """Representa un producto en el inventario."""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    precio: float = 0.0
    stock: int = 0
    stock_minimo: int = 5
    categoria: str = "General"
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    def __post_init__(self):
        if self.creado_en is None:
            self.creado_en = datetime.now().isoformat()
        if self.actualizado_en is None:
            self.actualizado_en = self.creado_en

    @property
    def stock_bajo(self) -> bool:
        """Retorna True si el stock está por debajo del mínimo."""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self) -> float:
        """Valor total del producto en inventario."""
        return self.precio * self.stock

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "stock": self.stock,
            "stock_minimo": self.stock_minimo,
            "categoria": self.categoria,
            "creado_en": self.creado_en,
            "actualizado_en": self.actualizado_en,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Producto":
        """Crea un Producto desde una fila de SQLite."""
        return cls(
            id=row[0],
            nombre=row[1],
            descripcion=row[2],
            precio=row[3],
            stock=row[4],
            stock_minimo=row[5],
            categoria=row[6],
            creado_en=row[7],
            actualizado_en=row[8],
        )


@dataclass
class Venta:
    """Representa una venta registrada."""
    id: Optional[int] = None
    producto_id: int = 0
    cantidad: int = 0
    precio_unitario: float = 0.0
    total: float = 0.0
    cliente: str = ""
    notas: str = ""
    fecha: Optional[str] = None

    def __post_init__(self):
        if self.fecha is None:
            self.fecha = datetime.now().isoformat()
        if self.total == 0.0 and self.cantidad > 0:
            self.total = self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "total": self.total,
            "cliente": self.cliente,
            "notas": self.notas,
            "fecha": self.fecha,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Venta":
        """Crea una Venta desde una fila de SQLite."""
        return cls(
            id=row[0],
            producto_id=row[1],
            cantidad=row[2],
            precio_unitario=row[3],
            total=row[4],
            cliente=row[5],
            notas=row[6],
            fecha=row[7],
        )


@dataclass
class MovimientoStock:
    """Representa un movimiento de stock (entrada o salida)."""
    id: Optional[int] = None
    producto_id: int = 0
    tipo: str = "entrada"  # "entrada" o "salida"
    cantidad: int = 0
    motivo: str = ""
    fecha: Optional[str] = None

    def __post_init__(self):
        if self.fecha is None:
            self.fecha = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "motivo": self.motivo,
            "fecha": self.fecha,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "MovimientoStock":
        """Crea un MovimientoStock desde una fila de SQLite."""
        return cls(
            id=row[0],
            producto_id=row[1],
            tipo=row[2],
            cantidad=row[3],
            motivo=row[4],
            fecha=row[5],
        )
