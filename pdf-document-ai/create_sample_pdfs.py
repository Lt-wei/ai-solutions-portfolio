"""
Generate sample contract PDFs for demonstration
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_contracts():
    """Create sample contract PDFs with realistic text"""
    
    samples_dir = Path("sample_pdfs")
    samples_dir.mkdir(exist_ok=True)
    
    contracts = [
        {
            "filename": "contract_001_software_services.pdf",
            "content": {
                "title": "SOFTWARE SERVICES AGREEMENT",
                "contract_no": "SSA-2024-0451",
                "date": "2024-03-15",
                "party_a": "TechSolutions Inc.",
                "party_b": "Global Retail Corp.",
                "amount": "125,000.00",
                "description": "Cloud infrastructure consulting and implementation services"
            }
        },
        {
            "filename": "contract_002_consulting.pdf",
            "content": {
                "title": "CONSULTING AGREEMENT",
                "contract_no": "CA-2024-0892",
                "date": "2024-05-22",
                "party_a": "Strategy Partners LLC",
                "party_b": "Manufacturing Systems Ltd.",
                "amount": "75,500.00",
                "description": "Business process optimization and digital transformation"
            }
        },
        {
            "filename": "contract_003_equipment_lease.pdf",
            "content": {
                "title": "EQUIPMENT LEASE AGREEMENT",
                "contract_no": "ELA-2024-1123",
                "date": "2024-08-10",
                "party_a": "Enterprise Equipment Corp.",
                "party_b": "StartupTech Ventures Inc.",
                "amount": "45,000.00",
                "description": "Server equipment lease for data center operations"
            }
        }
    ]
    
    for contract in contracts:
        pdf_path = samples_dir / contract["filename"]
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        content = contract["content"]
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, content["title"])
        
        # Contract details
        c.setFont("Helvetica", 12)
        y_position = 700
        
        c.drawString(100, y_position, f"Contract Number: {content['contract_no']}")
        y_position -= 30
        
        c.drawString(100, y_position, f"Date: {content['date']}")
        y_position -= 30
        
        c.drawString(100, y_position, f"BETWEEN:")
        y_position -= 25
        c.drawString(120, y_position, f"Party A: {content['party_a']}")
        y_position -= 20
        c.drawString(120, y_position, f"(hereinafter referred to as 'Provider')")
        y_position -= 40
        
        c.drawString(100, y_position, f"AND:")
        y_position -= 25
        c.drawString(120, y_position, f"Party B: {content['party_b']}")
        y_position -= 20
        c.drawString(120, y_position, f"(hereinafter referred to as 'Client')")
        y_position -= 40
        
        c.drawString(100, y_position, f"AGREEMENT TERMS:")
        y_position -= 30
        
        c.drawString(100, y_position, f"1. Scope of Services:")
        y_position -= 20
        c.drawString(120, y_position, content['description'])
        y_position -= 40
        
        c.drawString(100, y_position, f"2. Contract Value:")
        y_position -= 20
        c.drawString(120, y_position, f"Total Amount: ${content['amount']}")
        y_position -= 40
        
        c.drawString(100, y_position, f"3. Terms and Conditions:")
        y_position -= 20
        c.drawString(120, y_position, "This agreement is valid for a period of twelve (12) months")
        y_position -= 20
        c.drawString(120, y_position, "from the date of execution. Payment terms: Net 30 days.")
        y_position -= 40
        
        c.drawString(100, y_position, "SIGNATURES:")
        y_position -= 40
        c.drawString(100, y_position, f"_______________________          _______________________")
        y_position -= 20
        c.drawString(100, y_position, f"{content['party_a']}                {content['party_b']}")
        
        c.save()
        print(f"Created: {pdf_path}")
    
    print(f"\nGenerated {len(contracts)} sample contract PDFs in {samples_dir}/")
    print("\nThese PDFs contain realistic contract text for testing the extraction system.")


if __name__ == "__main__":
    try:
        create_sample_contracts()
    except ImportError:
        print("Note: reportlab not installed. Creating text-based sample instead...")
        print("Run: pip install reportlab  (for PDF generation)")
        print("\nFor now, sample text files will work with the main app.")
