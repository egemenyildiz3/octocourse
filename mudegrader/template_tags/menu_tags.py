from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, pattern):
    request_path = context['request'].path
    path_segments = request_path.strip('/').split('/')
    pattern_segments = pattern.strip('/').split('/')

    # Check if the initial segments of the current path match the pattern
    if path_segments[:len(pattern_segments)] == pattern_segments:
        return 'active'
    return ''
