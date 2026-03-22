#!/usr/bin/env python3
"""
generate_demo_pdf.py
--------------------
Creates realistic demo PDF schedule files for testing.
Requires: reportlab
    pip install reportlab
"""

from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("reportlab not installed. Run: pip install reportlab")

SCHEDULE_DATA = {
    1: {
        "groups": ["ЭК-11", "ЭК-12", "ЭК-13"],
        "subjects": [
            ("Математический анализ", "Иванов А.А.", "101", "Лекция"),
            ("Линейная алгебра", "Петрова Б.В.", "202", "Практика"),
            ("Информатика", "Сидоров В.Г.", "Лаб. 5", "Лаб. работа"),
            ("Философия", "Козлова Д.Е.", "Актовый зал", "Семинар"),
            ("Иностранный язык", "Михайлов Е.Ж.", "305", "Практика"),
        ]
    },
    2: {
        "groups": ["ЭК-21", "ЭК-22"],
        "subjects": [
            ("Теория вероятностей", "Новиков А.П.", "101", "Лекция"),
            ("Микроэкономика", "Волкова С.Р.", "203", "Семинар"),
            ("Статистика", "Зайцев К.М.", "Лаб. 3", "Лаб. работа"),
            ("Менеджмент", "Орлова Т.Н.", "Актовый зал", "Лекция"),
            ("Право", "Лебедев Ф.О.", "104", "Практика"),
        ]
    },
    3: {
        "groups": ["ЭК-31", "ЭК-32"],
        "subjects": [
            ("Макроэкономика", "Кузнецов Г.Д.", "202", "Лекция"),
            ("Финансы и кредит", "Морозова В.А.", "301", "Семинар"),
            ("Бухгалтерский учёт", "Попов И.С.", "Лаб. 2", "Практика"),
            ("Маркетинг", "Соколов Р.Е.", "Актовый зал", "Лекция"),
            ("Эконометрика", "Тихонова Л.В.", "205", "Лаб. работа"),
        ]
    },
    4: {
        "groups": ["ЭК-41"],
        "subjects": [
            ("Стратегический менеджмент", "Федоров П.К.", "301", "Лекция"),
            ("Международная экономика", "Белова Н.Ж.", "202", "Семинар"),
            ("Налогообложение", "Смирнов О.А.", "104", "Практика"),
            ("Аудит", "Волков Д.И.", "Лаб. 1", "Лаб. работа"),
            ("Преддипломная практика", "Кравцов Л.М.", "Деканат", "Другое"),
        ]
    },
}

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
TIME_SLOTS = ["08:30-10:00", "10:10-11:40", "12:10-13:40", "13:50-15:20", "15:30-17:00"]


def generate_pdf(course: int, output_dir: Path):
    if not HAS_REPORTLAB:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"economy_{course}.pdf"

    data = SCHEDULE_DATA[course]
    groups = data["groups"]
    subjects = data["subjects"]

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=1*cm,
        rightMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1*cm,
    )

    styles = getSampleStyleSheet()
    small = ParagraphStyle('small', fontSize=7, leading=9)
    header_style = ParagraphStyle('header', fontSize=14, leading=18, spaceAfter=6)

    story = []
    story.append(Paragraph(f"Расписание занятий — {course} курс", header_style))
    story.append(Paragraph(f"Экономический факультет | Группы: {', '.join(groups)}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    import random
    random.seed(course * 42)

    # Build table: rows = time slots, cols = days × groups
    # Header row 1: days (spanning groups count)
    # Header row 2: groups under each day
    # Data rows: lessons

    n_groups = len(groups)
    n_days = len(DAYS)

    # Header
    header1 = ["Время"]
    for day in DAYS:
        header1.extend([day] + [""] * (n_groups - 1))

    header2 = [""]
    for _ in DAYS:
        header2.extend(groups)

    table_data = [header1, header2]

    for slot in TIME_SLOTS:
        row = [slot]
        for day_idx in range(n_days):
            for g_idx, group in enumerate(groups):
                # Randomly assign lessons (70% chance of having a lesson)
                if random.random() < 0.7:
                    subj, teacher, room, ltype = random.choice(subjects)
                    cell = f"{subj}\n{teacher}\nауд. {room}\n({ltype})"
                else:
                    cell = ""
                row.append(cell)
        table_data.append(row)

    # Column widths
    time_col_w = 2.2 * cm
    day_col_w = (landscape(A4)[0] - 2*cm - time_col_w) / (n_days * n_groups)

    col_widths = [time_col_w] + [day_col_w] * (n_days * n_groups)

    # Convert cells to Paragraphs for wrapping
    formatted = []
    for r_idx, row in enumerate(table_data):
        frow = []
        for c_idx, cell in enumerate(row):
            if r_idx == 0:
                frow.append(Paragraph(str(cell), ParagraphStyle('h1', fontSize=8, fontName='Helvetica-Bold')))
            elif r_idx == 1:
                frow.append(Paragraph(str(cell), ParagraphStyle('h2', fontSize=7, fontName='Helvetica-Bold')))
            else:
                frow.append(Paragraph(str(cell), small))
        formatted.append(frow)

    t = Table(formatted, colWidths=col_widths, repeatRows=2)

    # Styling
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#2b5282')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
        # Merge day header cells
    ]

    # Add span for day headers
    for d_idx in range(n_days):
        start_col = 1 + d_idx * n_groups
        end_col = start_col + n_groups - 1
        if n_groups > 1:
            style_cmds.append(('SPAN', (start_col, 0), (end_col, 0)))

    t.setStyle(TableStyle(style_cmds))

    story.append(t)
    doc.build(story)
    print(f"✅ Generated: {output_path}")


if __name__ == "__main__":
    base = Path("data/schedule")
    for course in range(1, 5):
        generate_pdf(course, base / str(course))
    print("Done! All demo PDFs generated.")
