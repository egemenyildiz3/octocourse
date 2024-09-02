import pypandoc
from django.template import Context, Template

def generate_html_from_markdown_template(template_string: str, context_dict: dict) -> str:
    """
    Generate HTML from a Markdown template string and a context dictionary.
    
    :param template_string: The Markdown template string.
    :type template_string: str
    
    :param context_dict: The context dictionary.
    :type context_dict: dict
    
    :returns: The generated HTML.
    :rtype: str
    """
    result_markdown = apply_template(template_string, context_dict)
    html = markdown_to_html(result_markdown)
    return html


def apply_template(template_string: str, context_dict: dict) -> str:
    """
    Apply a template string to a context dictionary.

    :param template_string: The template string.
    :type template_string: str

    :param context_dict: The context dictionary.
    :type context_dict: dict

    :returns: The rendered template string.
    :rtype: str
    """
    template = Template(template_string)
    context = Context(context_dict)
    return template.render(context)

def markdown_to_html(markdown_text):
    """
    Convert Markdown text to HTML using pypandoc.convert.

    :param markdown_text: The Markdown text.
    :type markdown_text: str

    :returns: The HTML text.
    :rtype: str
    """
    return pypandoc.convert_text(markdown_text, 'html', format='md')