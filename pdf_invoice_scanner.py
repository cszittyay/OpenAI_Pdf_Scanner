#!/usr/bin/env python3
"""
PDF Invoice Scanner - Console Application
Parses a PDF invoice file and outputs structured JSON data using OpenAI.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import PyPDF2
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


class PDFInvoiceScanner:
    """Scanner for extracting structured data from PDF invoices using OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the PDF Invoice Scanner.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY environment variable.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Please set OPENAI_API_KEY environment variable or provide it as argument."
            )
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Extracted text content from all pages.
        """
        text_content = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            
            return "\n\n".join(text_content)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {e}")
    
    def parse_invoice_to_json(self, pdf_text: str) -> Dict[str, Any]:
        """
        Parse invoice text using OpenAI to extract structured data.
        
        Args:
            pdf_text: Text content extracted from the PDF invoice.
            
        Returns:
            Dictionary containing structured invoice data.
        """
        prompt = f"""Analiza la siguiente factura y extrae la información estructurada en formato JSON.
Incluye los siguientes campos si están disponibles:
- numero_factura: número de la factura
- fecha: fecha de emisión
- vendedor: información del vendedor (nombre, dirección, CIF/NIF)
- cliente: información del cliente (nombre, dirección, CIF/NIF)
- items: lista de productos/servicios con descripción, cantidad, precio_unitario, y total
- subtotal: subtotal antes de impuestos
- impuestos: información de impuestos (tipo, porcentaje, monto)
- total: monto total de la factura
- metodo_pago: método de pago si está disponible
- notas: cualquier nota o información adicional

Texto de la factura:
{pdf_text}

Responde ÚNICAMENTE con el JSON estructurado, sin texto adicional."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en procesar facturas y extraer datos estructurados. Respondes únicamente con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Extract JSON from response
            json_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split('\n')
                json_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_text
                if json_text.startswith("json"):
                    json_text = json_text[4:].strip()
            
            return json.loads(json_text)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON from OpenAI response: {e}")
        except Exception as e:
            raise Exception(f"Error calling OpenAI API: {e}")
    
    def scan_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete workflow to scan a PDF invoice and return structured JSON.
        
        Args:
            pdf_path: Path to the PDF invoice file.
            
        Returns:
            Dictionary containing structured invoice data.
        """
        print(f"Extracting text from PDF: {pdf_path}")
        pdf_text = self.extract_text_from_pdf(pdf_path)
        
        if not pdf_text.strip():
            raise ValueError("No text could be extracted from the PDF file")
        
        print("Parsing invoice with OpenAI...")
        invoice_data = self.parse_invoice_to_json(pdf_text)
        
        return invoice_data


def main():
    """Main console application entry point."""
    parser = argparse.ArgumentParser(
        description="PDF Invoice Scanner - Parse PDF invoices to JSON using OpenAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_invoice_scanner.py invoice.pdf
  python pdf_invoice_scanner.py invoice.pdf -o output.json
  python pdf_invoice_scanner.py invoice.pdf --pretty

Environment:
  OPENAI_API_KEY    OpenAI API key (required)
        """
    )
    
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF invoice file"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output JSON file path (if not specified, prints to stdout)"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (alternatively set OPENAI_API_KEY env variable)"
    )
    
    args = parser.parse_args()
    
    # Validate PDF file exists
    if not os.path.isfile(args.pdf_file):
        print(f"Error: PDF file not found: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize scanner
        scanner = PDFInvoiceScanner(api_key=args.api_key)
        
        # Scan the invoice
        invoice_data = scanner.scan_invoice(args.pdf_file)
        
        # Format output
        indent = 2 if args.pretty else None
        json_output = json.dumps(invoice_data, indent=indent, ensure_ascii=False)
        
        # Save or print output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"\nSuccess! Invoice data saved to: {args.output}")
        else:
            print("\n" + "="*50)
            print("INVOICE DATA (JSON)")
            print("="*50)
            print(json_output)
        
        return 0
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
