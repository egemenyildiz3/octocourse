from django.urls import reverse
from django.views.generic import DetailView
import json
from assignment_manager.views.comments import CommentMixin
from assignment_manager.forms import GroupForm
from assignment_manager.models import Group, Course, Assignment, Student, GroupMember, Event
from assignment_manager.services.url_params import add_query_params
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from services.gitlab_services import GitlabService



class GroupDetailView(CommentMixin, DetailView):
    """Render details of a specific group."""
    model = Group
    template_name = 'groups/group_details.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # adds to context the list of group email addresses for email compose button
        group_email_addresses = []
        for member in context['group'].group_members.all():
            # student_id is actually a foreign key, so what we actually get is the student object
            group_email_addresses.append(member.student_id.email)
        context['group_email_addresses'] = group_email_addresses
        return context


def group_list(request):
    """Render a list of all groups."""
    current_course = request.session['selected_course_id']
    groups = Group.objects.filter(course=current_course)
    return render(request, 'groups/groups_list.html', {'groups': groups})


def delete_group(request, group_id):
    """Delete a group from the system."""
    group = get_object_or_404(Group, id=group_id)
    group.delete()
    fallback = 'group_list'
    return redirect(request.META.get('HTTP_REFERER', fallback))


def search_groups(request):
    """Search for groups by their name."""
    query = request.GET.get('search_query')
    groups = Group.objects.filter(name__icontains=query) if query else Group.objects.all()
    return render(request, 'groups/groups_list.html', {'groups': groups})


def filter_groups(request):
    """
    Filter groups based on a selected attribute and value.

    This function allows filtering groups based on various attributes such as name, creation date, etc.
    """
    filter_by = request.GET.get('filter')
    value = request.GET.get('value')

    if filter_by and value:
        if filter_by == 'name':
            groups = Group.objects.filter(name__icontains=value)
        elif filter_by == 'creation_date':
            groups = Group.objects.filter(creation_date=value)
        elif filter_by == 'assignment_id':
            course = get_object_or_404(Course, id=request.session['selected_course_id'])
            assignments = Assignment.objects.filter(course=course).filter(title__icontains=value)
            groups = Group.objects.filter(assignments__in=assignments)
    else:
        groups = Group.objects.all()

    return render(request, 'groups/groups_list.html', {'groups': groups})


def edit_group(request, group_id):
    """Edit an existing group."""
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            referer_url = request.META.get('HTTP_REFERER', reverse('group_details', args=[group_id]))
            url = redirect(add_query_params(referer_url, {'saved': 'true'}))
            return url
    else:
        form = GroupForm(instance=group)
    return render(request, 'groups/edit_group.html', {'form': form, 'group': group})


def show_group_timeline(request, group_id):
    gs = GitlabService()
    group = get_object_or_404(Group, id=group_id)
    course_id = request.session['selected_course_id']
    course = get_object_or_404(Course, pk=course_id)
    list_of_commits = gs.get_group_commits(group)
    event_history = group.event_history.all()
    context = {
        'group': group,
        'list_of_commits': list_of_commits,
        'event_history': event_history,
    }
    return render(request, 'groups/group_timeline.html', context)

def add_group(request):
    """Render a form to add a new group to the system."""
    course_id = request.session["selected_course_id"]
    selected_course = get_object_or_404(Course, pk=course_id)
    
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.course = selected_course
            new_group.save()
            return redirect('group_list')
    else:
        form = GroupForm()

    return render(request, 'groups/add_group.html', {'form': form, 'course': selected_course})

@csrf_exempt
def find_student_for_group(request):
    """
    Searches for students based on a query parameter. 
    It gets teh serach query to filter students by their
    net_id and it returns back a JSON array of student objects 
    containing id, net_id, and name.

    """
    if 'q' in request.GET:
        query = request.GET['q']
        students = Student.objects.filter(net_id__icontains=query)
        results = [{'id': student.id, 'net_id': student.net_id, 'name': f"{student.first_name} {student.last_name}"} for student in students]
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'No query provided'}, status=400)



@csrf_exempt
def add_student_to_group(request):
    """
    Adds a student to a specified group.
    It gets the group_id and student_id from the request body, 
    checks if the student is already in the group, and if not, 
    adds the student to the group.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        group_id = data.get('group_id')
        student_id = data.get('student_id')
        group = get_object_or_404(Group, id=group_id)
        student = get_object_or_404(Student, id=student_id)
        
        # Check if the student is already in the group
        if GroupMember.objects.filter(group_id=group, student_id=student).exists():
            return JsonResponse({'status': 'error', 'message': 'Student is already a member of this group'})

        GroupMember.objects.create(group_id=group, student_id=student)
        event = Event.objects.create(
            name="Student: Added",
            user=request.user,
            text=f"Student {student.get_details_link_html()} was added to group {group.get_details_link_html()}",
        )
        group.event_history.add(event)
        group.save()
        student.event_history.add(event)
        student.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@require_POST
def remove_student_from_group(request):
    """
    Removes a student from a specified group.
    It gets the group_id and student_id from the request body, 
    retrieves the corresponding GroupMembers object, and deletes it.
    """
    data = json.loads(request.body)
    group_id = data.get('group_id')
    student_id = data.get('student_id')
    
    group_member = get_object_or_404(GroupMember, group_id=group_id, student_id=student_id)
    group_member.delete()
    student = get_object_or_404(Student, id=student_id)
    group = get_object_or_404(Group, id=group_id)
    event = Event.objects.create(
        name="Student: Removed",
        user=request.user,
        text=f"Student {student.get_details_link_html()} was removed from group {group.get_details_link_html()}",
    )
    group.event_history.add(event)
    group.save()
    student.event_history.add(event)
    student.save()
    return JsonResponse({'status': 'success'})
