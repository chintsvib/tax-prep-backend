import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

class DraftingAgent:
    def __init__(self, template_path: str):
        self.template_path = template_path

    def create_overlay(self, data: dict):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # --- Watermark (Psychological Value) ---
        can.setFont("Helvetica-Bold", 60)
        can.setStrokeColorRGB(0.8, 0.8, 0.8)
        can.setFillColorRGB(0.9, 0.9, 0.9)
        can.saveState()
        can.translate(300, 450)
        can.rotate(45)
        can.drawCentredString(0, 0, "DRAFT - NOT FOR FILING")
        can.restoreState()

        # --- Mapping Data to 1040 Coordinates ---
        # Note: These coordinates (x, y) require some fine-tuning 
        # based on your specific 1040 PDF template.
        can.setFont("Helvetica", 10)
        can.setFillColorRGB(0, 0, 0)
        
        # Example: Filing Status (Checkboxes)
        if data.get("filing_status") == "Single":
            can.drawString(65, 715, "X")
        elif data.get("filing_status") == "Married filing jointly":
            can.drawString(135, 715, "X")

        # Example: Income Lines
        can.drawString(440, 560, f"{data.get('wages', 0):,.0f}") # Line 1z
        can.drawString(440, 435, f"{data.get('agi', 0):,.0f}")   # Line 11
        
        can.showPage()
        can.save()
        packet.seek(0)
        return packet

    def generate(self, data: dict, output_path: str):
        overlay_packet = self.create_overlay(data)
        overlay_pdf = PdfReader(overlay_packet)
        template_pdf = PdfReader(open(self.template_path, "rb"))
        
        output = PdfWriter()
        
        # Merge overlay with the first page of the template
        page = template_pdf.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        output.add_page(page)
        
        # Add remaining pages from template if they exist
        for i in range(1, len(template_pdf.pages)):
            output.add_page(template_pdf.pages[i])

        with open(output_path, "wb") as f:
            output.write(f)