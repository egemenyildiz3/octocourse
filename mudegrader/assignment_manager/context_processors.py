from .models import Course


def course_context(request):
    courses = Course.objects.all()
    selected_course = None

    # Check for selected course in GET parameters or session
    course_id = request.GET.get('course_id') or request.session.get('selected_course_id')
    if course_id:
        try:
            selected_course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            selected_course = None

    # Save selected course in session
    if selected_course:
        request.session['selected_course_id'] = selected_course.id

    return {
        'courses': courses,
        'selected_course': selected_course
    }
