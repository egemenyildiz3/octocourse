from sys import stdout

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic.base import ContextMixin

from assignment_manager.forms import CommentForm
from assignment_manager.models import Comment, Event


class CommentMixin(ContextMixin):
    """
    Mixin for automatically adding comments to a view class.
    This class dynamically adds a receiver for post-requests, which are created by posting a comment on a page.

    For an example use, see AssignmentDetailView.

    Care should probably be taken in pages with other post request forms.
    """
    def post(self, request, *args, **kwargs):
        """
        This function handles post requests for comments.

        :param request: The HTTP request object.
        :type request: HttpRequest

        :returns: An HTTP response.
        :rtype: HttpResponse
        """

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.content_object = self.object
            new_comment.author = request.user
            new_comment.save()
            event = Event.objects.create(
                name="Comment: Created",
                user=request.user,
                text=f'added comment with text: "{new_comment.comment_text}"',
            )
            self.object.event_history.add(event)
            self.object.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/fallback-url/'))

        context['comment_form'] = comment_form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """
        This function adds comments to the context of the view.
        """
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]
        # obj = context['assignment']
        # Assuming 'comments' is the related name given in the ForeignKey in Comment model
        context['comments'] = obj.comments.all()
        context['comment_form'] = CommentForm()  # add the comment form to the context
        return context

def delete_comment(request, comment_id):
    """
    This function retrieves a comment using its unique ID and deletes it from the database.
    If the comment with the specified ID does not exist, a 404 error will be raised.
    After deletion, it redirects the user back to the same page the request came from.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param comment_id: The id of the comment to delete.
    :type comment_id: int
    :returns: An HTTP redirect response to the referer or a fallback URL.
    :rtype: HttpResponseRedirect

    """
    comment = get_object_or_404(Comment, id=comment_id)
    obj = comment.content_object
    event = Event.objects.create(
        name="Comment: Deleted",
        user=request.user,
        text=f'removed comment from {comment.author} with text: "{comment.comment_text}"',
    )
    obj.event_history.add(event)
    obj.save()
    comment.delete()
    # redirect back to the same page
    fallback = 'course_list'
    return redirect(request.META.get('HTTP_REFERER', fallback))