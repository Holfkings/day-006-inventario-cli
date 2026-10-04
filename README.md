# Gestor de Inventario CLI

Herramienta de línea de comandos para gestionar inventarios de pequeños negocios. Control de productos, stock, ventas y reportes en una interfaz simple y directa.

## Características

- **Gestión completa de productos**: alta, baja, edición y búsqueda
- **Control de stock**: entradas, salidas y alertas de stock bajo
- **Registro de ventas**: con actualización automática de inventario
- **Reportes**: resumen general, productos más vendidos, ventas por período
- **Base de datos SQLite**: portable, sin servidor, sin configuración
- **Interfaz CLI intuitiva**: menú interactivo o comandos directos

## Requisitos

- Python 3.8+
- Sin dependencias externas (solo biblioteca estándar)

## Instalación

```bash
git clone https://github.com/Holfkings/day-006-inventario-cli.git
cd day-006-inventario-cli
```

## Uso

### Menú interactivo

```bash
python app.py
```

### Comandos directos

```bash
# Agregar producto
python app.py agregar

# Listar productos
python app.py listar

# Buscar producto
python app.py buscar

# Ver detalle
python app.py ver

# Registrar venta
python app.py vender

# Ver alertas de stock bajo
python app.py stock-bajo

# Resumen del inventario
python app.py resumen

# Productos más vendidos
python app.py top
```

### Base de datos personalizada

```bash
python app.py --db /ruta/mi_inventario.db
```

## Estructura del proyecto

```
inventario-cli/
├── app.py              # Aplicación principal (CLI)
├── models.py           # Modelos de datos (Producto, Venta, Movimiento)
├── db.py               # Capa de acceso a datos (SQLite)
├── tests/              # Tests unitarios
│   └── test_inventario.py
└── README.md
```

## Tests

```bash
python -m pytest tests/ -v
```

## Licencia

MIT
