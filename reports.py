import csv
from datetime import datetime
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ACCENT = colors.HexColor("#7c3aed")
TEXT = colors.HexColor("#1e293b")
CARD_BG = colors.HexColor("#f8fafc")
INCOME = colors.HexColor("#22c55e")
EXPENSE = colors.HexColor("#ef4444")


def currency(value):
    return f"${float(value or 0):,.2f}"


def month_title(month):
    return datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%B %Y")


def generate_csv(transactions, month):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([f"Expense Tracker Report - {month_title(month)}"])
    writer.writerow([])
    writer.writerow(["Date", "Type", "Category", "Amount", "Description"])

    for tx in transactions:
        writer.writerow(
            [
                tx["date"],
                tx["type"].title(),
                tx["category"],
                f"{float(tx['amount']):.2f}",
                tx["description"] or "",
            ]
        )

    buffer = BytesIO()
    buffer.write(output.getvalue().encode("utf-8-sig"))
    buffer.seek(0)
    return buffer


def generate_pdf(month, summary, category_breakdown, transactions):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"Expense Report - {month_title(month)}",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            textColor=TEXT,
            fontSize=22,
            leading=28,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["Normal"],
            textColor=colors.HexColor("#64748b"),
            fontSize=9,
            leading=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            textColor=TEXT,
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=8,
        )
    )

    elements = [
        Paragraph(f"Expense Report: {month_title(month)}", styles["ReportTitle"]),
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            styles["SmallMuted"],
        ),
        Spacer(1, 0.18 * inch),
    ]

    summary_table = Table(
        [
            ["Total Income", "Total Expenses", "Net Savings"],
            [
                currency(summary["income"]),
                currency(summary["expense"]),
                currency(summary["savings"]),
            ],
        ],
        colWidths=[2.15 * inch, 2.15 * inch, 2.15 * inch],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, 1), CARD_BG),
                ("TEXTCOLOR", (0, 1), (0, 1), INCOME),
                ("TEXTCOLOR", (1, 1), (1, 1), EXPENSE),
                ("TEXTCOLOR", (2, 1), (2, 1), TEXT),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    elements.append(summary_table)

    elements.append(Paragraph("Category Breakdown", styles["SectionTitle"]))
    category_rows = [["Category", "Expense Total"]]
    if category_breakdown:
        category_rows.extend(
            [[item["category"], currency(item["total"])] for item in category_breakdown]
        )
    else:
        category_rows.append(["No expenses recorded", currency(0)])

    category_table = Table(category_rows, colWidths=[4.3 * inch, 2.2 * inch])
    category_table.setStyle(default_table_style(header_bg=colors.HexColor("#312e81")))
    elements.append(category_table)

    elements.append(Paragraph("Transactions", styles["SectionTitle"]))
    transaction_rows = [["Date", "Type", "Category", "Amount", "Description"]]
    if transactions:
        for tx in transactions:
            transaction_rows.append(
                [
                    tx["date"],
                    tx["type"].title(),
                    tx["category"],
                    currency(tx["amount"]),
                    tx["description"] or "",
                ]
            )
    else:
        transaction_rows.append(["-", "-", "-", currency(0), "No transactions found"])

    transaction_table = Table(
        transaction_rows,
        colWidths=[0.9 * inch, 0.75 * inch, 1.05 * inch, 0.95 * inch, 2.8 * inch],
        repeatRows=1,
    )
    table_style = default_table_style(header_bg=ACCENT)
    for index, tx in enumerate(transactions, start=1):
        if tx["type"] == "income":
            table_style.add("TEXTCOLOR", (1, index), (1, index), INCOME)
        else:
            table_style.add("TEXTCOLOR", (1, index), (1, index), EXPENSE)
    transaction_table.setStyle(table_style)
    elements.append(transaction_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def default_table_style(header_bg):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
    )
