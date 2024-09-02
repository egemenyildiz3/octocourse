from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from assignment_manager.models import Course
from assignment_manager.forms import TagForm
from assignment_manager.tag_model import Tag


def edit_tags(request, course_id):
    """
    Render a page to edit tags for a course.
    
    :param request: The HTTP request object.
    :type request: HttpRequest
    
    :param course_id: The ID of the course to edit tags for.
    :type course_id: int

    :returns: An HTTP response.
    :rtype: HttpResponse
    """
    course = get_object_or_404(Course, id=course_id)
    tags = course.tags.all()  # Assuming 'tags' is a related name in a ManyToMany field relation

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_tag = form.save(commit=False)
            new_tag.course = course  # Assuming the Tag model has a foreign key to Course
            new_tag.save()
            course.tags.add(new_tag)  # Link the tag to the course
            return redirect('edit_tags', course_id=course_id)  # Redirect to the same page to show the updated tag list
    else:
        form = TagForm()
    return render(request, 'tags/edit_tags.html', {'form': form, 'course': course, 'tags': tags})

@require_POST  # Ensures this view can only be accessed via POST method
def delete_tag(request, course_id, tag_id):
    """
    Delete a tag from a course.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course.
    :type course_id: int
    :param tag_id: The ID of the tag to delete.
    :type tag_id: int

    :returns: An HTTP redirect response to the referer or a fallback URL.
    :rtype: HttpResponseRedirect
    """
    tag = get_object_or_404(Tag, id=tag_id)
    tag.delete()
    return redirect(request.META.get('HTTP_REFERER', reverse('edit_tags', args=[course_id])))