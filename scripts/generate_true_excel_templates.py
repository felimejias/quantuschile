import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

base_static = "/Users/felipe/proyectos/quantuschile.cl/do/static"

# Estilos profesionales de Quantus (Azul Ejecutivo, Bordes limpios, Fuentes visibles)
header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid") # Dark Slate / Navy

data_font = Font(name="Segoe UI", size=10, color="000000")
example_font = Font(name="Segoe UI", size=10, italic=True, color="475569")
example_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

thin_border = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

alignment_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
alignment_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

# ---------------------------------------------------------
# 1. PLANTILLA EXCEL OFICIAL RAT (Ley N° 21.719)
# ---------------------------------------------------------
wb_rat = openpyxl.Workbook()
ws_rat = wb_rat.active
ws_rat.title = "Registro_RAT_Oficial"

headers_rat = [
    "N° Correlativo",
    "Nombre de la Lista / Base de Datos",
    "Soporte (Digital o Papel)",
    "Categorías de Datos Guardados",
    "Finalidad del Uso (¿Para qué se usan?)",
    "Base Legal (Consentimiento / Contrato / Ley)",
    "Quiénes Tienen Acceso (Cargos)",
    "Plazo de Retención / Borrado",
    "Medidas de Seguridad Aplicadas"
]

ws_rat.append(headers_rat)

# Fichas de ejemplo listas para que el usuario borre o use de guía
examples_rat = [
    [1, "Lista de Clientes y Facturación", "Digital (Excel / Software PC)", "Nombres, RUT, Teléfono, Dirección, Email", "Cobranza, emisión de facturas y despacho", "Cumplimiento Contractual y Tributario", "Gerente Comercial y Contador", "6 Años (Exigencia Código Tributario SII)", "PC con clave personal y disco cifrado"],
    [2, "Archivadores de Contratos 2026", "Físico (Papel en Bodega)", "Nombres, RUT, Firma en Papel", "Respaldo legal de contratos de arriendo", "Cumplimiento Contractual", "Custodio de Llaves autorizado", "5 Años (Prescripción Civil)", "Mueble con chapa bajo llave"],
    [3, "Suscriptores Formulario Web", "Digital (Base de Datos Web)", "Nombres y Correo Electrónico", "Envío de boletín mensual de noticias", "Consentimiento Libre en Formulario", "Encargado de Marketing", "Borrado Inmediato al solicitar baja", "Hash SHA-256 e IP registrada"]
]

for row in examples_rat:
    ws_rat.append(row)

# Formatear filas vacías para llenar (Filas 5 a 25)
for r in range(5, 26):
    ws_rat.append([r - 1, "", "Digital (Excel / Papel)", "", "", "", "", "", ""])

# Estilar cabecera y celdas
for col_num, header in enumerate(headers_rat, 1):
    cell = ws_rat.cell(row=1, column=col_num)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = alignment_center
    cell.border = thin_border

for row in range(2, ws_rat.max_row + 1):
    for col in range(1, len(headers_rat) + 1):
        cell = ws_rat.cell(row=row, column=col)
        cell.border = thin_border
        if row in [2, 3, 4]:
            cell.font = example_font
            cell.fill = example_fill
        else:
            cell.font = data_font
        
        if col in [1, 3]:
            cell.alignment = alignment_center
        else:
            cell.alignment = alignment_left

# Ajustar ancho de columnas automáticamente
for col in ws_rat.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws_rat.column_dimensions[col_letter].width = max(max_len + 4, 18)

wb_rat.save(f"{base_static}/Plantilla_Oficial_RAT_Ley21719_Quantus.xlsx")

# ---------------------------------------------------------
# 2. PLANTILLA EXCEL EVALUACIÓN PIA (Ley N° 21.719)
# ---------------------------------------------------------
wb_pia = openpyxl.Workbook()
ws_pia = wb_pia.active
ws_pia.title = "Matriz_PIA_Riesgos"

headers_pia = [
    "ID Riesgo",
    "Sistema / Proceso Evaluado",
    "Peligro o Riesgo Identificado",
    "Nivel de Impacto (Alto / Medio / Bajo)",
    "Medida de Mitigación / Solución Técnica",
    "Estado de Implementación",
    "Fecha de Revisión"
]

ws_pia.append(headers_pia)

examples_pia = [
    ["R-01", "Base de datos en Excel local", "Robo o extravío de computador de ventas", "Alto", "Cifrar disco con BitLocker y clave de 12 dígitos", "Implementado", "2026-08-01"],
    ["R-02", "Formulario Web de Contacto", "Interceptación de datos por cibercriminales", "Medio", "Instalar certificado SSL HTTPS y cifrado AES-256", "Implementado", "2026-08-01"],
    ["R-03", "Archivadores físicos en oficina", "Acceso no autorizado de personal de aseo", "Medio", "Instalar cerradura con llave y designar custodio", "En Proceso", "2026-08-01"]
]

for row in examples_pia:
    ws_pia.append(row)

for r in range(5, 20):
    ws_pia.append([f"R-0{r-1}", "", "", "Medio", "", "Pendiente", ""])

for col_num, header in enumerate(headers_pia, 1):
    cell = ws_pia.cell(row=1, column=col_num)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = alignment_center
    cell.border = thin_border

for row in range(2, ws_pia.max_row + 1):
    for col in range(1, len(headers_pia) + 1):
        cell = ws_pia.cell(row=row, column=col)
        cell.border = thin_border
        if row in [2, 3, 4]:
            cell.font = example_font
            cell.fill = example_fill
        else:
            cell.font = data_font
        cell.alignment = alignment_left

for col in ws_pia.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws_pia.column_dimensions[col_letter].width = max(max_len + 4, 18)

wb_pia.save(f"{base_static}/Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.xlsx")

print("GENIAL: ARCHIVOS EXCEL VERDADEROS (.XLSX) GENERADOS CON ÉXITO Y FORMATO PROFESIONAL LISTO PARA LLENAR Y CARGAR")
