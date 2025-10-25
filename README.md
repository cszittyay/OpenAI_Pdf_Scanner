# OpenAI PDF Invoice Scanner

Aplicación de consola en Python que parsea archivos PDF de facturas y genera una salida JSON estructurada utilizando la API de OpenAI.

## Características

- 📄 Extrae texto de archivos PDF
- 🤖 Utiliza OpenAI GPT para analizar y estructurar datos de facturas
- 📊 Genera salida JSON con información estructurada de la factura
- 🌍 Soporte para facturas en español
- 💾 Guarda resultados en archivos o imprime en consola

## Requisitos

- Python 3.7 o superior
- Cuenta de OpenAI con API key
- Dependencias Python (ver `requirements.txt`)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/cszittyay/OpenAI_Pdf_Scanner.git
cd OpenAI_Pdf_Scanner
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar la API key de OpenAI:

Crear un archivo `.env` en el directorio raíz:
```bash
OPENAI_API_KEY=tu-api-key-aqui
```

O exportar como variable de entorno:
```bash
export OPENAI_API_KEY=tu-api-key-aqui
```

## Uso

### Sintaxis básica

```bash
python pdf_invoice_scanner.py <archivo_pdf>
```

### Ejemplos

1. Parsear una factura y mostrar el resultado en consola:
```bash
python pdf_invoice_scanner.py factura.pdf
```

2. Guardar el resultado en un archivo JSON:
```bash
python pdf_invoice_scanner.py factura.pdf -o resultado.json
```

3. Mostrar resultado con formato pretty-print:
```bash
python pdf_invoice_scanner.py factura.pdf --pretty
```

4. Proporcionar API key directamente (sin archivo .env):
```bash
python pdf_invoice_scanner.py factura.pdf --api-key sk-...
```

### Opciones

- `pdf_file` - (Requerido) Ruta al archivo PDF de la factura
- `-o, --output` - Archivo de salida JSON (opcional, imprime en stdout si no se especifica)
- `--pretty` - Formato de salida JSON con indentación
- `--api-key` - API key de OpenAI (alternativa a la variable de entorno)

## Formato de salida JSON

La aplicación extrae y estructura la siguiente información de las facturas:

```json
{
  "numero_factura": "FACT-2024-001",
  "fecha": "2024-01-15",
  "vendedor": {
    "nombre": "Empresa S.L.",
    "direccion": "Calle Principal 123",
    "cif": "B12345678"
  },
  "cliente": {
    "nombre": "Cliente SA",
    "direccion": "Avenida Secundaria 456",
    "cif": "A87654321"
  },
  "items": [
    {
      "descripcion": "Servicio de consultoría",
      "cantidad": 10,
      "precio_unitario": 100.00,
      "total": 1000.00
    }
  ],
  "subtotal": 1000.00,
  "impuestos": {
    "tipo": "IVA",
    "porcentaje": 21,
    "monto": 210.00
  },
  "total": 1210.00,
  "metodo_pago": "Transferencia bancaria",
  "notas": "Pago a 30 días"
}
```

## Estructura del proyecto

```
OpenAI_Pdf_Scanner/
├── pdf_invoice_scanner.py  # Aplicación principal
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla de configuración
├── .gitignore            # Archivos ignorados por git
├── example_output.json   # Ejemplo de salida JSON
└── README.md             # Documentación
```

## Dependencias

- `openai` - Cliente de la API de OpenAI
- `PyPDF2` - Extracción de texto de archivos PDF
- `python-dotenv` - Gestión de variables de entorno

## Solución de problemas

### Error: "OpenAI API key not found"
Asegúrate de haber configurado la variable de entorno `OPENAI_API_KEY` o proporcionar la API key con el parámetro `--api-key`.

### Error: "No text could be extracted from the PDF file"
El PDF podría estar escaneado como imagen. Asegúrate de que el PDF contenga texto seleccionable.

### Error de importación de módulos
Instala las dependencias: `pip install -r requirements.txt`

## Limitaciones

- El PDF debe contener texto seleccionable (no solo imágenes)
- La calidad de la extracción depende del formato del PDF
- Requiere conexión a Internet para usar la API de OpenAI
- Consumo de tokens de OpenAI según el tamaño de la factura

## Licencia

Este proyecto es de código abierto.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.