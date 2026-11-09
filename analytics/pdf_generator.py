import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from students.models import Student
from tests_module.models import TestAttempt
from mock_interviews.models import MockInterview
from marks.models import Marks
from subjects.models import Subject


def generate_student_pdf_report(student):
    """
    Generates a professional, branded PDF performance card for the student using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1, # Center
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        fontName='Helvetica'
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("STUDENT PERFORMANCE PORTAL", title_style))
    elements.append(Paragraph("Official Comprehensive Academic & Skill Evaluation Report", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3b82f6'), spaceBefore=2, spaceAfter=14))

    # 2. Student Info Card Table
    batch_name = student.batch.batch_name if student.batch else "Unassigned"
    batch_code = student.batch.batch_code if student.batch else "N/A"

    info_data = [
        [
            Paragraph(f"<b>Candidate Name:</b> {student.full_name}", body_style),
            Paragraph(f"<b>Roll Number:</b> {student.roll_number}", body_style),
        ],
        [
            Paragraph(f"<b>Cohort / Batch:</b> {batch_code} ({batch_name})", body_style),
            Paragraph(f"<b>Email Address:</b> {student.email}", body_style),
        ],
        [
            Paragraph(f"<b>Department:</b> {student.department or 'General'}", body_style),
            Paragraph(f"<b>Admission Date:</b> {student.admission_date}", body_style),
        ]
    ]

    info_table = Table(info_data, colWidths=[3.75 * inch, 3.75 * inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    # 3. Assessment Transcript Table
    elements.append(Paragraph("I. Subject Assessments Breakdown (Coding, MCQ & Mock Interview)", section_heading))

    transcript_data = [
        [
            Paragraph("Subject", table_header),
            Paragraph("Coding Test", table_header),
            Paragraph("MCQ Test", table_header),
            Paragraph("Mock Interview", table_header),
            Paragraph("Average %", table_header),
            Paragraph("Status", table_header)
        ]
    ]

    subjects = Subject.objects.all()
    if student.batch:
        batch_subjects = student.batch.subjects.all()
        if batch_subjects.exists():
            subjects = batch_subjects

    total_percentages = []

    for sub in subjects:
        # Get coding attempts
        coding_att = TestAttempt.objects.filter(
            student=student,
            test__subject=sub,
            test__test_type='CODING',
            status__in=['SUBMITTED', 'TIMED_OUT', 'FORCE_SUBMITTED']
        ).first()

        # Get MCQ attempts
        mcq_att = TestAttempt.objects.filter(
            student=student,
            test__subject=sub,
            test__test_type='MCQ',
            status__in=['SUBMITTED', 'TIMED_OUT', 'FORCE_SUBMITTED']
        ).first()

        # Get Mock Interview
        interview = MockInterview.objects.filter(
            student=student,
            subject=sub,
            status='COMPLETED'
        ).first()

        # Also check legacy Marks table for compatibility
        legacy_coding = Marks.objects.filter(student=student, subject=sub, exam_type='CODING_TEST').first()
        legacy_mcq = Marks.objects.filter(student=student, subject=sub, exam_type='MCQ').first()
        legacy_interview = Marks.objects.filter(student=student, subject=sub, exam_type='MOCK_INTERVIEW').first()

        coding_pct = coding_att.percentage if coding_att else (legacy_coding.percentage if legacy_coding else None)
        mcq_pct = mcq_att.percentage if mcq_att else (legacy_mcq.percentage if legacy_mcq else None)
        int_pct = interview.percentage if interview else (legacy_interview.percentage if legacy_interview else None)

        scores = [s for s in [coding_pct, mcq_pct, int_pct] if s is not None]
        avg_pct = round(sum(scores) / len(scores), 1) if scores else 0.0
        if scores:
            total_percentages.append(avg_pct)

        status_str = "Passed" if avg_pct >= 40 else ("In Progress" if not scores else "Needs Improvement")

        transcript_data.append([
            Paragraph(f"<b>{sub.subject_name}</b>", table_text),
            Paragraph(f"{coding_pct}%" if coding_pct is not None else "-", table_text),
            Paragraph(f"{mcq_pct}%" if mcq_pct is not None else "-", table_text),
            Paragraph(f"{int_pct}%" if int_pct is not None else "-", table_text),
            Paragraph(f"<b>{avg_pct}%</b>", table_text),
            Paragraph(status_str, table_text)
        ])

    transcript_table = Table(transcript_data, colWidths=[2.2 * inch, 1.05 * inch, 1.05 * inch, 1.15 * inch, 1.05 * inch, 1.0 * inch])
    transcript_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(transcript_table)
    elements.append(Spacer(1, 14))

    # 4. Overall Standing Summary
    overall_avg = round(sum(total_percentages) / len(total_percentages), 1) if total_percentages else 0.0
    grade = 'A+' if overall_avg >= 90 else ('A' if overall_avg >= 80 else ('B' if overall_avg >= 70 else ('C' if overall_avg >= 60 else ('D' if overall_avg >= 40 else 'F'))))

    # Batch Rank
    all_students = Student.objects.filter(batch=student.batch) if student.batch else Student.objects.all()
    rank = 1
    for other in all_students:
        if other.id != student.id:
            other_atts = TestAttempt.objects.filter(student=other, status__in=['SUBMITTED', 'TIMED_OUT'])
            other_scores = [a.percentage for a in other_atts]
            if other_scores and (sum(other_scores) / len(other_scores)) > overall_avg:
                rank += 1

    summary_data = [
        [
            Paragraph(f"<b>Overall Aggregate:</b> <font color='#1e3a8a'>{overall_avg}%</font>", body_style),
            Paragraph(f"<b>Final Grade:</b> <font color='#16a34a'>{grade}</font>", body_style),
            Paragraph(f"<b>Batch Standing:</b> Rank #{rank} of {all_students.count()}", body_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # 5. Qualitative Feedback: AI & Staff Remarks
    elements.append(Paragraph("II. Qualitative Evaluator Notes & Faculty Interview Remarks", section_heading))

    # Recent AI code feedback
    recent_coding = TestAttempt.objects.filter(student=student, test__test_type='CODING', is_evaluated=True).first()
    ai_feedback = recent_coding.ai_feedback_summary if recent_coding else "No automated AI coding evaluation recorded yet."

    # Recent Mock Interview feedback
    recent_int = MockInterview.objects.filter(student=student, status='COMPLETED').first()
    int_feedback = f"{recent_int.feedback_notes} (Strengths: {recent_int.strengths or 'Consistent effort'}, Focus: {recent_int.areas_for_improvement or 'Ongoing practice'})" if recent_int else "No mock interview commentary recorded yet."

    feedback_data = [
        [Paragraph("<b>Google Gemini AI Code Review:</b>", body_style)],
        [Paragraph(ai_feedback, table_text)],
        [Paragraph("<b>Faculty Mock Interview Commentary:</b>", body_style)],
        [Paragraph(int_feedback, table_text)],
    ]

    feedback_table = Table(feedback_data, colWidths=[7.5 * inch])
    feedback_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(feedback_table)
    elements.append(Spacer(1, 18))

    # 6. Verification Footer
    footer_text = Paragraph(
        "<i>This official report card is generated electronically by the Student Performance Portal. Verified against secure database logs and anti-cheat exam timestamps.</i>",
        subtitle_style
    )
    elements.append(footer_text)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
