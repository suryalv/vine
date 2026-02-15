#!/usr/bin/env python3
"""Generate complex underwriting PDF documents."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='DocTitle', fontSize=18, leading=22, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#00205B')))
styles.add(ParagraphStyle(name='DocSubtitle', fontSize=11, leading=14, spaceAfter=12, textColor=colors.HexColor('#475569')))
styles.add(ParagraphStyle(name='SectionHead', fontSize=13, leading=16, spaceBefore=18, spaceAfter=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f172a')))
styles.add(ParagraphStyle(name='SubSection', fontSize=11, leading=14, spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e293b')))
styles.add(ParagraphStyle(name='BodyText2', fontSize=9.5, leading=13, spaceAfter=6, textColor=colors.HexColor('#334155')))
styles.add(ParagraphStyle(name='SmallGray', fontSize=8, leading=10, textColor=colors.HexColor('#94a3b8')))
styles.add(ParagraphStyle(name='TableHeader', fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=colors.white))
styles.add(ParagraphStyle(name='CenterBold', fontSize=10, leading=13, fontName='Helvetica-Bold', alignment=TA_CENTER))
styles.add(ParagraphStyle(name='RightAligned', fontSize=9.5, leading=13, alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Footer', fontSize=7.5, leading=10, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER))

AIG_BLUE = colors.HexColor('#00205B')
LIGHT_BLUE = colors.HexColor('#e8edf5')
BORDER_GRAY = colors.HexColor('#cbd5e1')
ROW_ALT = colors.HexColor('#f8fafc')

def header_table(title_lines):
    """Create a standard AIG header block."""
    data = [
        ['AIG', title_lines[0]],
        ['', title_lines[1] if len(title_lines) > 1 else ''],
    ]
    t = Table(data, colWidths=[1.2*inch, 5.3*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (0,0), 20),
        ('TEXTCOLOR', (0,0), (0,0), AIG_BLUE),
        ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (1,0), (1,0), 14),
        ('TEXTCOLOR', (1,0), (1,0), AIG_BLUE),
        ('FONTSIZE', (1,1), (1,1), 9),
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#64748b')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    return t

def styled_table(headers, rows, col_widths=None):
    """Create a consistently styled data table."""
    data = [headers] + rows
    if not col_widths:
        col_widths = [6.5*inch / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0,0), (-1,0), AIG_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0,i), (-1,i), ROW_ALT))
    t.setStyle(TableStyle(style))
    return t

def kv_table(pairs, col_widths=None):
    """Key-value pair table."""
    if not col_widths:
        col_widths = [2.2*inch, 4.3*inch]
    t = Table(pairs, colWidths=col_widths)
    style = [
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#334155')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]
    t.setStyle(TableStyle(style))
    return t

def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#94a3b8'))
    canvas.drawCentredString(4.25*inch, 0.4*inch,
        f"AIG  |  Confidential  |  Page {doc.page}")
    canvas.restoreState()


# ============================================================
# 1. COMMERCIAL PROPERTY POLICY
# ============================================================
def generate_commercial_property_policy():
    path = os.path.join(OUT_DIR, 'Commercial_Property_Policy_Meridian_Steel.pdf')
    doc = SimpleDocTemplate(path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Header
    story.append(header_table([
        'Commercial Property Policy',
        'Policy No: AIG-CPP-2026-04871  |  Effective: 03/01/2026 - 03/01/2027'
    ]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=AIG_BLUE))
    story.append(Spacer(1, 16))

    # Declarations
    story.append(Paragraph('SECTION I — DECLARATIONS', styles['SectionHead']))
    story.append(kv_table([
        ['Named Insured:', 'Meridian Steel Corporation'],
        ['DBA:', 'Meridian Steel Manufacturing & Distribution'],
        ['Mailing Address:', '4200 Industrial Parkway, Suite 100\nHouston, TX 77041'],
        ['FEIN:', '74-3298156'],
        ['SIC Code:', '3312 — Steel Works, Blast Furnaces'],
        ['NAICS Code:', '331110 — Iron and Steel Mills and Ferroalloy Manufacturing'],
        ['Policy Period:', 'March 1, 2026, 12:01 AM to March 1, 2027, 12:01 AM\nStandard Time at the address shown above'],
        ['Producer:', 'Marsh & McLennan Companies\nAttn: David Chen, SVP\nLicense No: TX-7841205'],
        ['Premium:', '$287,500 (Annual)  |  Deposit: $143,750'],
        ['Policy Form:', 'AIG Advantage Property Premier (AIG-PP-2026)'],
    ]))
    story.append(Spacer(1, 12))

    # Coverage Summary
    story.append(Paragraph('SECTION II — SCHEDULE OF COVERAGES & LIMITS', styles['SectionHead']))
    story.append(styled_table(
        ['Coverage', 'Limit', 'Deductible', 'Coinsurance', 'Valuation'],
        [
            ['Building — Loc 1', '$42,500,000', '$25,000', '90%', 'Replacement Cost'],
            ['Building — Loc 2', '$18,750,000', '$25,000', '90%', 'Replacement Cost'],
            ['Business Personal Property — Loc 1', '$15,200,000', '$10,000', '80%', 'Replacement Cost'],
            ['Business Personal Property — Loc 2', '$8,400,000', '$10,000', '80%', 'Replacement Cost'],
            ['Business Income w/ Extra Expense', '$12,000,000', '72-hr waiting', 'N/A', '12-month ALS'],
            ['Equipment Breakdown', '$5,000,000', '$10,000', 'N/A', 'Replacement Cost'],
            ['Ordinance or Law — Coverage A', '$2,500,000', 'Per Building Ded', 'N/A', 'ACV'],
            ['Ordinance or Law — Coverage B', '$2,500,000', 'Per Building Ded', 'N/A', 'RC'],
            ['Ordinance or Law — Coverage C', '$5,000,000', 'Per Building Ded', 'N/A', 'RC'],
            ['Flood — Loc 1 (Zone X)', '$5,000,000', '$100,000', 'N/A', 'RC'],
            ['Flood — Loc 2 (Zone AE)', '$2,500,000', '$250,000', 'N/A', 'RC'],
            ['Named Storm — All Locations', '$10,000,000', '3% TIV / $500K min', 'N/A', 'RC'],
            ['Earthquake — All Locations', '$5,000,000', '5% TIV / $250K min', 'N/A', 'RC'],
            ['Transit / Inland Marine', '$2,000,000', '$5,000', 'N/A', 'RC'],
            ['Valuable Papers & Records', '$500,000', '$2,500', 'N/A', 'RC'],
            ['Accounts Receivable', '$1,000,000', '$2,500', 'N/A', 'N/A'],
        ],
        col_widths=[2.0*inch, 1.2*inch, 1.2*inch, 0.9*inch, 1.2*inch]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph('<b>Aggregate Policy Limit:</b> $85,000,000 per occurrence / $170,000,000 annual aggregate', styles['BodyText2']))

    story.append(PageBreak())

    # Locations
    story.append(Paragraph('SECTION III — SCHEDULE OF LOCATIONS', styles['SectionHead']))
    story.append(styled_table(
        ['Loc #', 'Address', 'Occupancy', 'Const.', 'Year Built', 'Sq Ft', 'Sprinkler', 'TIV'],
        [
            ['1', '4200 Industrial Pkwy\nHouston, TX 77041', 'Manufacturing\n& Warehouse', 'Fire\nResistive', '2008', '120,000', 'Full ESFR\nNFPA 13', '$57,700,000'],
            ['2', '8901 Port Arthur Rd\nBeaumont, TX 77705', 'Distribution\nCenter', 'Masonry\nNon-Comb', '2015', '65,000', 'Wet Pipe\nNFPA 13', '$27,150,000'],
        ],
        col_widths=[0.4*inch, 1.4*inch, 0.9*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.8*inch, 1.1*inch]
    ))
    story.append(Spacer(1, 12))

    # Endorsements
    story.append(Paragraph('SECTION IV — ENDORSEMENT SCHEDULE', styles['SectionHead']))
    story.append(styled_table(
        ['Form No.', 'Edition', 'Endorsement Title', 'Premium +/-'],
        [
            ['AIG-PP-001', '01/2026', 'Agreed Value Endorsement (Waiver of Coinsurance)', 'Included'],
            ['AIG-PP-002', '01/2026', 'Blanket Limits — Buildings & BPP', 'Included'],
            ['AIG-PP-003', '01/2026', 'Business Income — Extended Period of Indemnity (365 days)', '+$4,200'],
            ['AIG-PP-004', '01/2026', 'Utility Services — Direct Damage & Time Element', 'Included'],
            ['AIG-PP-005', '01/2026', 'Fungus, Wet Rot, Dry Rot — Limited Coverage ($100K)', 'Included'],
            ['AIG-PP-006', '01/2026', 'Electronic Data — Expanded Coverage ($250K)', '+$1,800'],
            ['AIG-PP-007', '01/2026', 'Ordinance or Law — Increased Coverage', 'Included'],
            ['AIG-PP-008', '01/2026', 'Protective Safeguards — P-1, P-2, P-9', 'Warranty'],
            ['AIG-PP-009', '01/2026', 'Water Exclusion — Amended (Storm Surge Buyback)', '+$12,500'],
            ['AIG-PP-010', '01/2026', 'Terrorism Risk Insurance Act (TRIA) — Certified Acts', '+$3,400'],
            ['CP 99 33', '10/2012', 'Exclusion of Loss Due to Virus or Bacteria', 'N/A'],
            ['IL 09 35', '07/2022', 'Exclusion of Certain Computer-Related Losses', 'N/A'],
        ],
        col_widths=[1.0*inch, 0.7*inch, 3.5*inch, 1.3*inch]
    ))

    story.append(PageBreak())

    # Loss History
    story.append(Paragraph('SECTION V — FIVE-YEAR LOSS HISTORY', styles['SectionHead']))
    story.append(Paragraph('Source: Meridian Steel Corp — verified via carrier loss runs and TPA reports.', styles['SmallGray']))
    story.append(Spacer(1, 6))
    story.append(styled_table(
        ['Policy Year', 'Carrier', 'Earned Premium', '# Claims', 'Incurred Losses', 'Loss Ratio', 'Status'],
        [
            ['2025-2026', 'AIG (Current)', '$287,500', '2', '$84,200', '29.3%', 'Open (1)'],
            ['2024-2025', 'Zurich', '$265,000', '4', '$312,450', '117.9%', 'All Closed'],
            ['2023-2024', 'Zurich', '$248,000', '1', '$18,700', '7.5%', 'All Closed'],
            ['2022-2023', 'Chubb', '$242,000', '3', '$156,800', '64.8%', 'All Closed'],
            ['2021-2022', 'Chubb', '$235,000', '0', '$0', '0.0%', 'All Closed'],
        ],
        col_widths=[0.9*inch, 0.9*inch, 1.1*inch, 0.7*inch, 1.1*inch, 0.8*inch, 1.0*inch]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph('<b>5-Year Combined Incurred:</b> $572,150  |  <b>Avg Loss Ratio:</b> 43.9%  |  <b>Large Loss ($50K+):</b> 2 claims', styles['BodyText2']))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Large Loss Detail:', styles['SubSection']))
    story.append(styled_table(
        ['Date of Loss', 'Location', 'Cause', 'Description', 'Incurred', 'Status'],
        [
            ['06/14/2024', 'Loc 1', 'Wind/Hail', 'Severe thunderstorm — roof membrane damage,\nHVAC unit destruction, 3-week production delay', '$248,000', 'Closed'],
            ['11/02/2022', 'Loc 2', 'Equipment\nBreakdown', 'Transformer failure — electrical surge damaged\nconveyor systems and control panels', '$142,300', 'Closed'],
        ],
        col_widths=[0.8*inch, 0.5*inch, 0.7*inch, 2.2*inch, 0.8*inch, 0.6*inch]
    ))

    story.append(PageBreak())

    # Underwriting Conditions
    story.append(Paragraph('SECTION VI — SPECIAL CONDITIONS & WARRANTIES', styles['SectionHead']))
    conditions = [
        '<b>1. Protective Safeguards Warranty:</b> The insured warrants that the following protective safeguards are maintained in working order at all times: (P-1) Automatic Sprinkler System per NFPA 13, (P-2) Automatic Fire Alarm connected to central station, (P-9) Operational security cameras with 30-day recording retention.',
        '<b>2. Vacancy Provision (Amended):</b> The standard 60-day vacancy provision is amended to 120 days. After 120 consecutive days of vacancy, coverage for vandalism, sprinkler leakage, and glass breakage is suspended. All other covered perils are subject to a 15% reduction in loss payment.',
        '<b>3. Roof Maintenance Warranty:</b> The insured shall maintain a written roof maintenance program with semi-annual inspections by a qualified roofing contractor. Inspection reports shall be retained and made available to AIG upon request. Failure to comply may result in exclusion of roof-related losses.',
        '<b>4. Hot Work Procedures:</b> All welding, cutting, and open flame operations shall comply with NFPA 51B. A designated fire watch shall be maintained for a minimum of 60 minutes following completion of hot work.',
        '<b>5. Business Continuity Plan:</b> The insured warrants that a documented Business Continuity Plan (BCP) is in effect, reviewed annually, and tested at least once every 24 months. The BCP shall include provisions for alternate production facilities.',
        '<b>6. Flood Zone AE — Location 2:</b> A flood elevation certificate (FEMA Form 086-0-33) is on file confirming the lowest floor elevation is 2.4 feet above Base Flood Elevation (BFE). The $250,000 flood deductible applies to Location 2 only.',
        '<b>7. Cyber Exclusion:</b> This policy does not cover loss or damage arising from any cyber incident, malicious code, hacking, ransomware, or denial of service attack. See endorsement IL 09 35 attached.',
    ]
    for c in conditions:
        story.append(Paragraph(c, styles['BodyText2']))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 20))
    story.append(Paragraph('SECTION VII — SIGNATURES', styles['SectionHead']))
    story.append(Spacer(1, 20))

    sig_data = [
        ['_' * 40, '', '_' * 40],
        ['Authorized Representative', '', 'Named Insured or Authorized Agent'],
        ['AIG Property Division', '', 'Meridian Steel Corporation'],
        ['Date: _______________', '', 'Date: _______________'],
    ]
    sig_table = Table(sig_data, colWidths=[2.8*inch, 0.9*inch, 2.8*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    story.append(sig_table)

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    print(f"  Created: {path}")


# ============================================================
# 2. ACORD 125 — COMMERCIAL INSURANCE APPLICATION
# ============================================================
def generate_acord_application():
    path = os.path.join(OUT_DIR, 'ACORD_125_Application_Pacific_Coast_Logistics.pdf')
    doc = SimpleDocTemplate(path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    story.append(header_table([
        'ACORD 125 — Commercial Insurance Application',
        'Date: 02/15/2026  |  Producer: Aon Risk Solutions'
    ]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=AIG_BLUE))
    story.append(Spacer(1, 14))

    # Applicant Info
    story.append(Paragraph('SECTION 1 — APPLICANT INFORMATION', styles['SectionHead']))
    story.append(kv_table([
        ['Applicant Name:', 'Pacific Coast Logistics, Inc.'],
        ['DBA:', 'PCL Freight Services'],
        ['Mailing Address:', '2750 Harbor Gateway Blvd\nLong Beach, CA 90810'],
        ['Phone:', '(562) 555-0147'],
        ['Website:', 'www.pacificcoastlogistics.com'],
        ['FEIN:', '95-4812903'],
        ['Entity Type:', 'S-Corporation — Incorporated in California (2011)'],
        ['SIC / NAICS:', '4731 / 488510 — Freight Transportation Arrangement'],
        ['Years in Business:', '15 years (est. 2011)'],
        ['Annual Revenue:', '$78,400,000 (FY 2025)'],
        ['Total Employees:', '342 (Full-Time: 298, Part-Time: 44)'],
    ]))
    story.append(Spacer(1, 10))

    # Lines of Business Requested
    story.append(Paragraph('SECTION 2 — COVERAGES REQUESTED', styles['SectionHead']))
    story.append(styled_table(
        ['Line of Business', 'Requested Limit', 'Current Carrier', 'Expiring Premium', 'Exp. Date'],
        [
            ['Commercial Property', '$45,000,000', 'Travelers', '$186,400', '04/01/2026'],
            ['General Liability', '$2M occ / $4M agg', 'Hartford', '$124,800', '04/01/2026'],
            ['Commercial Auto', '$1M CSL', 'Progressive Comm', '$287,600', '04/01/2026'],
            ['Umbrella / Excess', '$10,000,000', 'Chubb', '$42,000', '04/01/2026'],
            ['Workers Compensation', 'Statutory / $1M EL', 'SCIF', '$198,200', '04/01/2026'],
            ['Inland Marine', '$5,000,000', 'Travelers', '$18,900', '04/01/2026'],
            ['Cyber Liability', '$3,000,000', 'None (New)', 'N/A', 'N/A'],
        ],
        col_widths=[1.4*inch, 1.2*inch, 1.2*inch, 1.1*inch, 0.8*inch]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph('<b>Total Current Program Premium:</b> $857,900  |  <b>Reason for Marketing:</b> Rate increases at renewal; seeking competitive alternatives and expanded Cyber coverage.', styles['BodyText2']))

    story.append(PageBreak())

    # Operations
    story.append(Paragraph('SECTION 3 — DESCRIPTION OF OPERATIONS', styles['SectionHead']))
    ops_text = [
        'Pacific Coast Logistics (PCL) is a full-service third-party logistics (3PL) provider specializing in temperature-controlled freight, warehousing, and last-mile delivery for the food & beverage, pharmaceutical, and consumer goods industries.',
        '<b>Core Operations:</b>',
        '• <b>Freight Brokerage:</b> Arrangement of FTL/LTL shipments across 48 states. 85% of loads are temperature-sensitive (refrigerated/frozen). PCL does not own tractors — all freight is brokered to vetted motor carriers.',
        '• <b>Warehousing:</b> 3 cold-storage facilities (Long Beach, CA; Phoenix, AZ; Dallas, TX) totaling 380,000 sq ft. USDA-inspected. 24/7 temperature monitoring with automated alerting.',
        '• <b>Last-Mile Delivery:</b> Fleet of 47 owned refrigerated vans (2020-2024 model years) for final delivery within a 150-mile radius of warehouse locations. All drivers are W-2 employees.',
        '• <b>Customs Brokerage:</b> Licensed customs broker (CBP License #29847) handling import/export clearance for 120+ clients at the Port of Long Beach.',
        '<b>Key Clients:</b> Sysco Foods (22% of revenue), Albertsons Companies (14%), McKesson Pharmaceutical Distribution (11%), Amazon Fresh (9%).',
        '<b>Contracts:</b> All motor carrier agreements include minimum $1M auto liability, $1M cargo, and $100K environmental liability requirements. PCL is named as additional insured on all carrier policies.',
    ]
    for t in ops_text:
        story.append(Paragraph(t, styles['BodyText2']))

    story.append(Spacer(1, 10))

    # Premises
    story.append(Paragraph('SECTION 4 — PREMISES & LOCATIONS', styles['SectionHead']))
    story.append(styled_table(
        ['#', 'Location', 'Use', 'Sq Ft', 'Owned/Leased', 'Sprinkler', 'TIV'],
        [
            ['1', '2750 Harbor Gateway Blvd\nLong Beach, CA 90810', 'HQ + Cold Storage\nWarehouse', '145,000', 'Leased\n(10yr NNN)', 'Full Wet\nAMPP', '$28,400,000'],
            ['2', '4401 W Buckeye Rd\nPhoenix, AZ 85043', 'Cold Storage\nDistribution', '125,000', 'Leased\n(7yr NNN)', 'Full Wet\nEarly Sup', '$19,200,000'],
            ['3', '9800 Forney Rd\nDallas, TX 75227', 'Cold Storage\nCross-Dock', '110,000', 'Owned', 'Full Wet\nNFPA 13', '$22,600,000'],
        ],
        col_widths=[0.3*inch, 1.4*inch, 1.0*inch, 0.6*inch, 0.8*inch, 0.7*inch, 1.0*inch]
    ))

    story.append(PageBreak())

    # Loss History
    story.append(Paragraph('SECTION 5 — LOSS HISTORY (5 YEARS)', styles['SectionHead']))
    story.append(styled_table(
        ['Year', 'Line', '# Claims', 'Total Incurred', 'Largest Claim', 'Description'],
        [
            ['2025', 'Auto', '8', '$124,300', '$42,000', 'Rear-end collision — driver injury + cargo damage'],
            ['2025', 'GL', '2', '$18,500', '$14,200', 'Slip & fall at Long Beach facility'],
            ['2025', 'WC', '12', '$87,400', '$23,100', 'Repetitive stress injuries — warehouse workers'],
            ['2024', 'Auto', '6', '$78,200', '$31,500', 'Intersection accident — third-party BI claim'],
            ['2024', 'Property', '1', '$245,000', '$245,000', 'Refrigeration system failure — spoiled inventory'],
            ['2024', 'WC', '9', '$62,100', '$18,700', 'Forklift incident — ankle fracture'],
            ['2023', 'Auto', '5', '$56,800', '$28,400', 'Highway merge accident — vehicle totaled'],
            ['2023', 'GL', '1', '$8,200', '$8,200', 'Damaged customer goods during handling'],
            ['2023', 'WC', '7', '$48,900', '$15,300', 'Lower back injuries — lifting related'],
            ['2022', 'Auto', '4', '$34,100', '$18,600', 'Parking lot incident — property damage'],
            ['2022', 'Property', '0', '$0', 'N/A', 'No claims'],
            ['2021', 'Auto', '3', '$22,400', '$12,800', 'Minor fender benders — no injuries'],
            ['2021', 'WC', '5', '$31,200', '$11,400', 'Slip on wet warehouse floor'],
        ],
        col_widths=[0.5*inch, 0.6*inch, 0.6*inch, 0.9*inch, 0.9*inch, 3.0*inch]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph('<b>5-Year Total Incurred:</b> $817,100  |  <b>Total Claims:</b> 63  |  <b>Avg Claim:</b> $12,970', styles['BodyText2']))

    story.append(Spacer(1, 14))

    # Representations
    story.append(Paragraph('SECTION 6 — REPRESENTATIONS & SIGNATURES', styles['SectionHead']))
    rep_text = 'The undersigned authorized representative of the applicant declares that the statements set forth herein are true and correct to the best of their knowledge. The undersigned understands that the information provided is material to the acceptance of this risk and the issuance of a policy. Any material misrepresentation may void the policy. The signing of this application does not bind the applicant or the company to complete the insurance.'
    story.append(Paragraph(rep_text, styles['BodyText2']))
    story.append(Spacer(1, 24))

    sig_data = [
        ['_' * 40, '', '_' * 40],
        ['Applicant Signature', '', 'Producer Signature'],
        ['Name: Sarah Martinez, CFO', '', 'Name: Rachel Kim, Account Executive'],
        ['Date: _______________', '', 'Date: _______________'],
    ]
    sig_table = Table(sig_data, colWidths=[2.8*inch, 0.9*inch, 2.8*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(sig_table)

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    print(f"  Created: {path}")


# ============================================================
# 3. LOSS RUN REPORT
# ============================================================
def generate_loss_run_report():
    path = os.path.join(OUT_DIR, 'Loss_Run_Report_5Year_Acme_Manufacturing.pdf')
    doc = SimpleDocTemplate(path, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    story.append(header_table([
        'Loss Run Report — 5 Year History',
        'Prepared: 02/15/2026  |  Valued as of: 01/31/2026'
    ]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=AIG_BLUE))
    story.append(Spacer(1, 14))

    story.append(Paragraph('INSURED INFORMATION', styles['SectionHead']))
    story.append(kv_table([
        ['Named Insured:', 'Acme Manufacturing, Inc.'],
        ['Policy Numbers:', 'GL: AIG-GL-2025-31847  |  Property: AIG-CP-2025-31848'],
        ['Lines Covered:', 'General Liability, Products Liability, Commercial Property'],
        ['Report Period:', '02/01/2021 — 01/31/2026 (60 months)'],
        ['Prepared By:', 'AIG Claims Division — Loss Analytics Unit'],
    ]))
    story.append(Spacer(1, 12))

    # Summary by year
    story.append(Paragraph('LOSS SUMMARY BY POLICY YEAR', styles['SectionHead']))
    story.append(styled_table(
        ['Policy Year', 'Line', 'Earned\nPremium', 'Claims\nReported', 'Claims\nOpen', 'Paid\nLosses', 'Reserves', 'Total\nIncurred', 'Loss\nRatio'],
        [
            ['2025-26', 'GL', '$142,000', '3', '2', '$48,200', '$85,000', '$133,200', '93.8%'],
            ['2025-26', 'Prod Liab', '$96,000', '1', '1', '$0', '$175,000', '$175,000', '182.3%'],
            ['2025-26', 'Property', '$188,000', '1', '0', '$22,400', '$0', '$22,400', '11.9%'],
            ['2024-25', 'GL', '$135,000', '5', '0', '$124,600', '$0', '$124,600', '92.3%'],
            ['2024-25', 'Prod Liab', '$91,000', '2', '0', '$218,400', '$0', '$218,400', '239.1%'],
            ['2024-25', 'Property', '$178,000', '2', '0', '$67,800', '$0', '$67,800', '38.1%'],
            ['2023-24', 'GL', '$128,000', '2', '0', '$31,200', '$0', '$31,200', '24.4%'],
            ['2023-24', 'Prod Liab', '$86,000', '0', '0', '$0', '$0', '$0', '0.0%'],
            ['2023-24', 'Property', '$170,000', '1', '0', '$14,500', '$0', '$14,500', '8.5%'],
            ['2022-23', 'GL', '$122,000', '4', '0', '$89,700', '$0', '$89,700', '73.5%'],
            ['2022-23', 'Prod Liab', '$82,000', '1', '0', '$142,300', '$0', '$142,300', '173.5%'],
            ['2022-23', 'Property', '$164,000', '0', '0', '$0', '$0', '$0', '0.0%'],
            ['2021-22', 'GL', '$118,000', '2', '0', '$18,900', '$0', '$18,900', '16.0%'],
            ['2021-22', 'Prod Liab', '$78,000', '0', '0', '$0', '$0', '$0', '0.0%'],
            ['2021-22', 'Property', '$158,000', '1', '0', '$8,200', '$0', '$8,200', '5.2%'],
        ],
        col_widths=[0.7*inch, 0.65*inch, 0.7*inch, 0.55*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.55*inch]
    ))

    story.append(PageBreak())

    # Individual claim detail
    story.append(Paragraph('INDIVIDUAL CLAIM DETAIL — SIGNIFICANT CLAIMS (>$25,000)', styles['SectionHead']))
    claims = [
        {
            'num': 'CLM-2025-08841',
            'dol': '09/12/2025', 'dor': '09/14/2025',
            'line': 'Products Liability',
            'claimant': 'Johnson & Whitfield Distribution, LLC',
            'desc': 'Defective steel bracket assembly (Part #AM-4478) used in commercial shelving installation. Bracket failure caused collapse of loaded warehouse racking system at claimant\'s facility. 3 employees injured (2 soft tissue, 1 fracture). Property damage to stored inventory estimated at $95,000. Claimant alleging strict product liability and negligent manufacturing. Retained counsel: Baker & Associates. Litigation pending in Harris County District Court.',
            'paid': '$0',
            'reserve': '$175,000',
            'total': '$175,000',
            'status': 'OPEN — In Litigation'
        },
        {
            'num': 'CLM-2024-06234',
            'dol': '03/22/2024', 'dor': '03/24/2024',
            'line': 'Products Liability',
            'claimant': 'Southwest Industrial Supply Co.',
            'desc': 'Defective weld on custom fabricated steel beam (Order #22-7841). Beam installed in commercial construction project. Weld failure detected during load testing — no injuries but project delayed 6 weeks. Claimant seeking recovery of delay damages, re-fabrication costs, and engineering review fees.',
            'paid': '$186,400',
            'reserve': '$0',
            'total': '$186,400',
            'status': 'CLOSED — Settled 11/2024'
        },
        {
            'num': 'CLM-2024-05102',
            'dol': '11/08/2024', 'dor': '11/10/2024',
            'line': 'General Liability',
            'claimant': 'Maria Santos (Third-Party Visitor)',
            'desc': 'Slip and fall on oil-contaminated floor in visitor walkway adjacent to manufacturing line. Claimant suffered torn ACL and meniscus. Surgery required. Lost wages claim included. Settlement reached after mediation.',
            'paid': '$78,200',
            'reserve': '$0',
            'total': '$78,200',
            'status': 'CLOSED — Settled 08/2025'
        },
        {
            'num': 'CLM-2022-03891',
            'dol': '07/15/2022', 'dor': '07/18/2022',
            'line': 'Products Liability',
            'claimant': 'Great Plains Construction, Inc.',
            'desc': 'Lot of 200 steel connectors (Part #AM-2290) failed tensile strength testing per ASTM A307 Grade A specifications. Connectors had already been partially installed in bridge reinforcement project. Full recall and replacement required. OSHA investigation concluded — no citations issued against Acme.',
            'paid': '$142,300',
            'reserve': '$0',
            'total': '$142,300',
            'status': 'CLOSED — Settled 04/2023'
        },
    ]

    for cl in claims:
        story.append(Paragraph(f'Claim: {cl["num"]}', styles['SubSection']))
        story.append(kv_table([
            ['Date of Loss:', cl['dol']],
            ['Date Reported:', cl['dor']],
            ['Line of Business:', cl['line']],
            ['Claimant:', cl['claimant']],
            ['Status:', cl['status']],
        ], col_widths=[1.4*inch, 5.1*inch]))
        story.append(Paragraph(f'<b>Description:</b> {cl["desc"]}', styles['BodyText2']))
        fin_data = [
            ['Paid to Date', 'Outstanding Reserves', 'Total Incurred'],
            [cl['paid'], cl['reserve'], cl['total']],
        ]
        ft = Table(fin_data, colWidths=[2.1*inch, 2.2*inch, 2.2*inch])
        ft.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BLUE),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(ft)
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_GRAY))
    story.append(Spacer(1, 6))
    story.append(Paragraph('This loss run report is provided for informational purposes only and does not constitute a waiver of any policy terms, conditions, or exclusions. All figures are subject to change pending final claim adjudication.', styles['SmallGray']))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    print(f"  Created: {path}")


if __name__ == '__main__':
    print("Generating PDF documents...")
    generate_commercial_property_policy()
    generate_acord_application()
    generate_loss_run_report()
    print("Done — all PDFs generated.")
