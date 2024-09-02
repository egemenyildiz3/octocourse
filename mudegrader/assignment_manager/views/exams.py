from django.shortcuts import render, get_object_or_404
from assignment_manager.models import Student
from analytics.models import StudentExams

def exam_list(request, student_id):
    """Render a list of exams for a specific student."""
    student = get_object_or_404(Student, id=student_id)
    exams = StudentExams.objects.filter(student=student).select_related('exam_metadata')

    return render(request, 'exams/exam_list.html', {'student': student, 'exams': exams})
