import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_mock_interview_invitation_email(mock_interview):
    """
    Sends a formatted HTML email to the student with interview details and Google Meet/Zoom link.
    """
    student = mock_interview.student
    subject = mock_interview.subject
    staff = mock_interview.staff
    datetime_str = mock_interview.scheduled_datetime.strftime("%B %d, %Y at %I:%M %p")

    subject_line = f"Mock Interview Invitation: {subject.subject_name} with {staff.get_full_name() or staff.username}"

    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #ffffff;">
        <h2 style="color: #1e3a8a; margin-top: 0;">Mock Interview Scheduled</h2>
        <p>Dear <strong>{student.full_name}</strong>,</p>
        <p>Your mock interview for <strong>{subject.subject_name}</strong> has been scheduled by faculty member <strong>{staff.get_full_name() or staff.username}</strong>.</p>
        
        <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 6px 0;"><strong>Cohort:</strong> {mock_interview.batch.batch_code} ({mock_interview.batch.batch_name})</p>
            <p style="margin: 6px 0;"><strong>Date & Time:</strong> {datetime_str}</p>
            <p style="margin: 6px 0;"><strong>Duration:</strong> {mock_interview.duration_minutes} minutes</p>
            <p style="margin: 6px 0;"><strong>Platform:</strong> {mock_interview.get_meeting_platform_display()}</p>
        </div>

        <div style="text-align: center; margin: 28px 0;">
            <a href="{mock_interview.meeting_url}" style="background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
                Join {mock_interview.get_meeting_platform_display()} Meeting
            </a>
        </div>

        {f'<div style="background: #f1f5f9; padding: 12px; border-radius: 6px; margin-bottom: 20px;"><strong>Instructions:</strong> {mock_interview.instructions}</div>' if mock_interview.instructions else ''}

        <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 16px;">
            Please ensure you join on time with your microphone and camera ready. If you cannot attend, notify your instructor immediately.
            <br><br>
            <em>Student Performance Portal &middot; Academic Excellence Team</em>
        </p>
    </div>
    """

    plain_message = strip_tags(html_message)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studentperformanceportal.edu')

    try:
        sent_count = send_mail(
            subject=subject_line,
            message=plain_message,
            from_email=from_email,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=False
        )
        if sent_count > 0:
            mock_interview.email_sent = True
            mock_interview.save(update_fields=['email_sent'])
            return True
    except Exception as e:
        logger.error(f"Failed to dispatch mock interview email to {student.email}: {e}")
        return False

    return False
