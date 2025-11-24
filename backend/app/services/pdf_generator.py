"""
PDF generation utilities for exporting user data.
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List

# ReportLab imports (ignore stub warnings - library doesn't provide full type stubs)
from reportlab.lib.pagesizes import letter, A4  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.lib.colors import HexColor, black, blue, white  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak  # type: ignore


class PDFGenerator:
    """Generate PDF reports for user data."""
    
    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1e40af'),
            alignment=1  # Center
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=HexColor('#1e40af'),
        )
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=black,
        )

    def generate_dashboard_report(self, dashboard_data: Dict[str, Any]) -> BytesIO:
        """Generate a comprehensive dashboard report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title Page
        story.append(Paragraph("MedFin Dashboard Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # User Info
        user_info = dashboard_data['user_info']
        story.append(Paragraph("User Information", self.heading_style))
        
        user_data = [
            ['Name:', user_info.get('full_name') or user_info['username']],
            ['Email:', user_info['email']],
            ['Username:', user_info['username']],
            ['Member Since:', datetime.fromisoformat(user_info['created_at']).strftime('%B %d, %Y')],
            ['Account Status:', 'Active' if user_info['is_active'] else 'Inactive']
        ]
        
        user_table = Table(user_data, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
        ]))
        story.append(user_table)
        story.append(Spacer(1, 20))
        
        # Insurance Information
        if dashboard_data.get('insurance_info'):
            story.append(Paragraph("Insurance Information", self.heading_style))
            insurance = dashboard_data['insurance_info']
            
            insurance_data = [
                ['Insurance Type:', insurance['insurance_type'].title()],
                ['Plan Name:', insurance.get('plan_name', 'Not specified')],
                ['Deductible:', f"${insurance['deductible']:,.2f}"],
                ['Deductible Remaining:', f"${insurance['deductible_remaining']:,.2f}"],
                ['Out-of-Pocket Max:', f"${insurance['out_of_pocket_max']:,.2f}"],
                ['Coverage Percentage:', f"{insurance['coverage_percentage']*100:.0f}%"]
            ]
            
            insurance_table = Table(insurance_data, colWidths=[2*inch, 4*inch])
            insurance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
            ]))
            story.append(insurance_table)
            story.append(Spacer(1, 20))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", self.heading_style))
        summary = dashboard_data['summary']
        
        summary_data = [
            ['Total Bills:', str(summary['total_bills'])],
            ['Total Bill Amount:', f"${summary['total_bill_amount']:,.2f}"],
            ['Navigation Plans:', str(summary['total_plans'])],
            ['Projected Savings:', f"${summary['total_projected_savings']:,.2f}"],
            ['Cost Estimates:', str(summary['total_estimates'])],
            ['Insurance on File:', 'Yes' if summary['has_insurance'] else 'No']
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Recent Bills
        if dashboard_data['recent_bills']:
            story.append(Paragraph("Recent Bills", self.heading_style))
            
            bills_data = [['Provider', 'Service Date', 'Amount', 'Status']]
            for bill in dashboard_data['recent_bills']:
                bills_data.append([
                    bill['provider_name'],
                    datetime.fromisoformat(bill['service_date']).strftime('%m/%d/%Y'),
                    f"${bill['patient_responsibility']:,.2f}",
                    bill['status'].title()
                ])
            
            bills_table = Table(bills_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            bills_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9fafb')])
            ]))
            story.append(bills_table)
            story.append(Spacer(1, 20))
        
        # Recent Navigation Plans
        if dashboard_data['recent_plans']:
            story.append(Paragraph("Recent Navigation Plans", self.heading_style))
            
            plans_data = [['Plan ID', 'Created', 'Projected Savings', 'Status']]
            for plan in dashboard_data['recent_plans']:
                plans_data.append([
                    f"#{plan['id']}",
                    datetime.fromisoformat(plan['created_at']).strftime('%m/%d/%Y'),
                    f"${plan['projected_savings']:,.2f}",
                    plan['status'].title()
                ])
            
            plans_table = Table(plans_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
            plans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9fafb')])
            ]))
            story.append(plans_table)
            story.append(Spacer(1, 20))
        
        # Recent Cost Estimates
        if dashboard_data['recent_estimates']:
            story.append(Paragraph("Recent Cost Estimates", self.heading_style))
            
            estimates_data = [['Service Type', 'Est. Cost', 'Your Cost', 'Date']]
            for estimate in dashboard_data['recent_estimates']:
                estimates_data.append([
                    estimate['service_type'],
                    f"${estimate['estimated_cost']:,.2f}",
                    f"${estimate['patient_responsibility']:,.2f}",
                    datetime.fromisoformat(estimate['created_at']).strftime('%m/%d/%Y')
                ])
            
            estimates_table = Table(estimates_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            estimates_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9fafb')])
            ]))
            story.append(estimates_table)
        
        # Footer
        story.append(PageBreak())
        story.append(Paragraph("Report Information", self.heading_style))
        story.append(Paragraph(f"""
        This report was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} 
        using the MedFin Healthcare Financial Navigator system. 
        
        For questions about this report or to update your information, 
        please contact support or log in to your MedFin account.
        
        © 2024 MedFin - All rights reserved.
        """, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_navigation_plan_report(self, plan_data: Dict[str, Any]) -> BytesIO:
        """Generate a detailed navigation plan report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        story.append(Paragraph("Healthcare Navigation Plan", self.title_style))
        story.append(Spacer(1, 20))
        
        # Plan Overview
        story.append(Paragraph("Plan Overview", self.heading_style))
        
        overview_data = [
            ['Plan ID:', f"#{plan_data.get('id', 'N/A')}"],
            ['Created:', datetime.fromisoformat(plan_data['created_at']).strftime('%B %d, %Y')],
            ['Status:', plan_data.get('status', 'active').title()],
            ['Projected Savings:', f"${plan_data['projected_savings']:,.2f}"]
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Financial Situation
        financial = plan_data.get('current_financial_situation', {})
        if financial:
            story.append(Paragraph("Current Financial Situation", self.heading_style))
            
            financial_data = [
                ['Annual Income:', f"${financial.get('annual_income', 0):,.2f}"],
                ['Monthly Income:', f"${financial.get('monthly_income', 0):,.2f}"],
                ['Monthly Expenses:', f"${financial.get('monthly_expenses', 0):,.2f}"],
                ['Available for Medical:', f"${financial.get('available_for_medical', 0):,.2f}"],
                ['Household Size:', str(financial.get('household_size', 1))],
                ['Has Insurance:', 'Yes' if financial.get('has_insurance') else 'No']
            ]
            
            financial_table = Table(financial_data, colWidths=[2.5*inch, 3.5*inch])
            financial_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
            ]))
            story.append(financial_table)
            story.append(Spacer(1, 20))
        
        # Navigation Steps
        plan_details = plan_data.get('plan_data', {})
        if 'navigation_steps' in plan_details:
            story.append(Paragraph("Recommended Action Steps", self.heading_style))
            
            steps = plan_details['navigation_steps']
            for i, step in enumerate(steps, 1):
                story.append(Paragraph(f"Step {i}: {step.get('title', 'Untitled Step')}", self.subheading_style))
                story.append(Paragraph(step.get('description', ''), self.styles['Normal']))
                
                if 'priority' in step:
                    priority_color = {
                        'high': HexColor('#dc2626'),
                        'medium': HexColor('#f59e0b'),
                        'low': HexColor('#10b981')
                    }.get(step['priority'], black)
                    story.append(Paragraph(f"Priority: {step['priority'].title()}", ParagraphStyle(
                        'Priority', parent=self.styles['Normal'], textColor=priority_color
                    )))
                
                if 'timeline' in step:
                    story.append(Paragraph(f"Timeline: {step['timeline']}", self.styles['Normal']))
                
                story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
