from django.contrib import admin
from .models import Marks


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'subject',
        'exam_type',
        'marks_obtained',
        'max_marks',
        'exam_date',
    )

    list_filter = ('exam_type', 'subject', 'exam_date')

    search_fields = (
        'student__full_name',
        'student__roll_number',
        'subject__subject_name',
    )

    ordering = ('-exam_date',)