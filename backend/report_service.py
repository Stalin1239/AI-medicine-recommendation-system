from fpdf import FPDF
import pandas as pd
import os
from datetime import datetime


def ensure_report_dirs():
    os.makedirs("reports", exist_ok=True)
    os.makedirs("exports", exist_ok=True)


class HealthReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'HealthOS - Diagnostic Summary', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | Medical Disclaimer: Not a Substitute for Professional Diagnosis.', 0, 0, 'C')

def generate_pdf_report(data):
    pdf = HealthReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)
    pdf.set_font("Arial", size=12)

    page_width = pdf.w - 2 * pdf.l_margin

    # Futuristic Header Accent
    pdf.set_fill_color(18, 69, 148)
    pdf.rect(pdf.l_margin, pdf.t_margin - 4, page_width, 28, style='F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(page_width, 10, "HEALTHOS REPORT", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(page_width, 6, "FUTURISTIC CARE SUMMARY | AI-informed diagnostics", ln=True, align='C')
    pdf.ln(8)

    pdf.set_text_color(32, 58, 122)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"Patient: {data['name']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Condition: {data['disease']}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_fill_color(242, 247, 255)
    pdf.set_draw_color(18, 69, 148)
    pdf.set_line_width(0.5)
    pdf.rect(pdf.l_margin, pdf.get_y(), page_width, 18, style='DF')
    pdf.set_xy(pdf.l_margin + 4, pdf.get_y() + 4)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(18, 69, 148)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Report ID: {datetime.now().strftime('%H%M%S')}", ln=True)
    pdf.ln(12)

    pdf.set_draw_color(18, 69, 148)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)

    # Dosage Recommendation
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(18, 69, 148)
    pdf.cell(page_width, 8, "Dosage Recommendation", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(page_width, 8, data['dosage'])
    pdf.ln(6)

    # Safe Tip
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(page_width, 8, "Safe Traditional Tip", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(page_width, 8, data['safe_tip'])
    pdf.ln(6)

    # Warning / Myth
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(page_width, 8, "Warning / Myth", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.set_fill_color(255, 230, 230)
    pdf.multi_cell(page_width, 8, data['myth'], border=1, fill=True)
    pdf.ln(6)

    # Dietary Plan
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(page_width, 8, "Dietary Plan", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(page_width, 8, f"Eat: {data['diet_eat']}\nAvoid: {data['diet_avoid']}")
    pdf.ln(8)

    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(page_width, 6, "Note: This report is for informational purposes only and does not replace professional medical advice.")

    ensure_report_dirs()
    filename = f"reports/Report_{data['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename


def export_research_data(db_engine):
    ensure_report_dirs()
    # Anonymized Export: We strip out patient PII and only export trends
    query = "SELECT disease_name, severity, location, created_at FROM triage_history"
    df = pd.read_sql(query, db_engine)
    export_path = "exports/research_anonymized_data.csv"
    df.to_csv(export_path, index=False)
    return export_path


def export_anonymized_json(db_engine):
    ensure_report_dirs()
    query = "SELECT disease_name, severity, location, created_at FROM triage_history"
    df = pd.read_sql(query, db_engine)
    export_path = "exports/anonymized_research_data.json"
    df.to_json(export_path, orient='records', date_format='iso')
    return export_path

def generate_prescription_pdf(data):
    ensure_report_dirs()
    pdf = FPDF()
    pdf.add_page()
    
    # Setup fonts
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(18, 69, 148)
    
    # Header: Hospital Name
    pdf.cell(0, 10, "FedMedFlow Healthcare", align='C', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "123 Health Ave, Medical District | Contact: +1 800-FED-MED | Email: care@fedmedflow.com", align='C', ln=True)
    pdf.ln(10)
    
    # Divider
    pdf.set_draw_color(18, 69, 148)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Doctor Details (Left) and Date (Right)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, f"Dr. {data.get('doctor_name', 'Unknown')}")
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%d %b %Y')}", align='R', ln=True)
    
    pdf.cell(100, 6, f"Specialty: {data.get('doctor_specialty', 'General Practice')}", ln=True)
    pdf.ln(5)
    
    # Patient Details Box
    pdf.set_fill_color(240, 245, 255)
    pdf.rect(10, pdf.get_y(), 190, 25, style='F')
    
    pdf.set_xy(15, pdf.get_y() + 3)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(90, 6, f"Patient Name: {data.get('patient_name', 'Unknown')}")
    pdf.cell(90, 6, f"Patient ID: #{data.get('patient_id', 'N/A')}", ln=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(90, 6, f"Age: {data.get('patient_age', 'Unknown')} | Gender: {data.get('patient_gender', 'Not specified')}")
    pdf.cell(90, 6, f"Diagnosis: {data.get('diagnosis', 'Pending')}", ln=True)
    
    pdf.set_xy(10, pdf.get_y() + 10)
    
    # Rx Symbol
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(18, 69, 148)
    pdf.cell(0, 15, "Rx", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Medicines Table
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(18, 69, 148)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(60, 8, "Medicine", border=1, fill=True)
    pdf.cell(30, 8, "Dosage", border=1, fill=True)
    pdf.cell(40, 8, "Timing", border=1, fill=True)
    pdf.cell(20, 8, "Duration", border=1, fill=True)
    pdf.cell(40, 8, "Instructions", border=1, fill=True, ln=True)
    
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)
    
    medicines = data.get('medicines', [])
    for med in medicines:
        name = f"{med.get('name', '')} ({med.get('type', '')})"
        dosage = med.get('dosage', '')
        timing = ", ".join(med.get('timings', []))
        duration = med.get('duration', '')
        instructions = med.get('instructions', '')
        
        pdf.cell(60, 8, name[:35], border=1)
        pdf.cell(30, 8, dosage[:15], border=1)
        pdf.cell(40, 8, timing[:20], border=1)
        pdf.cell(20, 8, duration[:10], border=1)
        pdf.cell(40, 8, instructions[:20], border=1, ln=True)
        
    pdf.ln(10)
    
    # Additional Directives
    if data.get('lab_tests'):
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, "Lab Tests Required:", ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, data['lab_tests'])
        pdf.ln(4)
        
    if data.get('diet_plan') or data.get('exercise'):
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, "Diet & Lifestyle Recommendations:", ln=True)
        pdf.set_font('Arial', '', 10)
        rec = f"Diet: {data.get('diet_plan', 'N/A')}\nExercise: {data.get('exercise', 'N/A')}"
        pdf.multi_cell(0, 6, rec)
        pdf.ln(4)
        
    # Signature Section
    pdf.set_y(-50)
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 6, "")
    pdf.cell(90, 6, "_________________________", align='C', ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(90, 6, f"Dr. {data.get('doctor_name', '')}", align='C', ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(90, 6, "Digital Signature", align='C', ln=True)
    
    # Verification Footer
    pdf.set_y(-25)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    verify_id = data.get('prescription_id', datetime.now().strftime('%Y%m%d%H%M%S'))
    pdf.cell(0, 5, f"Prescription ID: {verify_id} | Valid only with Doctor's Digital Signature", align='C', ln=True)
    pdf.cell(0, 5, "Use ID to verify at fedmedflow.com/verify", align='C', ln=True)

    filename = f"reports/Prescription_{verify_id}.pdf"
    pdf.output(filename)
    return filename

