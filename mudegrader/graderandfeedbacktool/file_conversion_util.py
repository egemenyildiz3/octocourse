import os
import subprocess
import nbformat
from nbconvert import HTMLExporter



def list_files_with_extension(directory, extension):
    """
    List all files in the specified directory with the specified extension.

    :param directory: The directory to search for files.
    :type directory: str

    :param extension: The file extension to search for.
    :type extension: str

    :returns: A list of files with the specified extension.
    :rtype: list
    """
    files_with_extension = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filename.endswith(extension):
            files_with_extension.append(filename)
    return files_with_extension


def convert_notebook_to_pdf(notebook_file_path):
    """
    Convert a Jupyter notebook file to PDF.

    :param notebook_file_path: The path to the Jupyter notebook file.
    :type notebook_file_path: str

    :returns: The path to the converted PDF file.
    :rtype: str
    """
    print(f"-> -> converting notebook to pdf...")

    # get the name of the markdown file   
    file_name_with_extension = os.path.basename(notebook_file_path)
    file_name_without_extension, file_extension = os.path.splitext(file_name_with_extension)
    output_pdf_file = file_name_without_extension + ".pdf"
    try:
        # Run the nbconvert command
        subprocess.run(['jupyter', 'nbconvert', '--to', 'pdf', notebook_file_path])
    except Exception as e:
        print("Error:", e)

    pdf_file_path = os.path.join(os.path.dirname(notebook_file_path), output_pdf_file)
    print(f"file path of pdf converted from notebook : {pdf_file_path}")
    return pdf_file_path


def convert_notebook_to_html(notebook_file_path):
    """
    Convert a Jupyter notebook file to HTML.
    
    :param notebook_file_path: The path to the Jupyter notebook file.
    :type notebook_file_path: str
    
    :returns: The path to the converted HTML file.
    :rtype: str
    """

    print(f"-> -> converting notebook to html...")

    # get the name of the markdown file   
    file_name_with_extension = os.path.basename(notebook_file_path)
    file_name_without_extension, file_extension = os.path.splitext(file_name_with_extension)
    output_pdf_file = file_name_without_extension + ".html"
    try:
        # Run the nbconvert command
        subprocess.run(['jupyter', 'nbconvert', '--to', 'html', notebook_file_path])
    except Exception as e:
        print("Error:", e)

    html_file_path = os.path.join(os.path.dirname(notebook_file_path), output_pdf_file)
    print(f"file path of pdf converted from notebook : {html_file_path}")
    return html_file_path


def convert_mark_down_to_html(markdown_file_path):
    """
    Convert a markdown file to HTML.
    
    :param markdown_file_path: The path to the markdown file.
    :type markdown_file_path: str
    
    :returns: The path to the converted HTML file.
    :rtype: str
    """
    
    print("-> -> converting markdown to html")

    # get the name of the markdown file   
    file_name_with_extension = os.path.basename(markdown_file_path)
    file_name_without_extension, file_extension = os.path.splitext(file_name_with_extension)
    output_html_file_name = file_name_without_extension + ".html"    
    output_html_file_path = os.path.join(os.path.dirname(markdown_file_path), output_html_file_name)
    
    convert_markdown_to_html_helper(markdown_file_path, output_html_file_path)
    print(f"file path of html converted from markdown : {output_html_file_path}")
    return output_html_file_path


def convert_markdown_to_html_helper(input_md_path, output_html_path):
    """
    Convert a markdown file to HTML.

    :param input_md_path: The path to the input markdown file.
    :type input_md_path: str

    :param output_html_path: The path to the output HTML file.  
    :type output_html_path: str
    """

    # Read the markdown file content
    with open(input_md_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # Create a new notebook object
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell(markdown_content))

    # Initialize the HTMLExporter
    html_exporter = HTMLExporter()
    
    # Convert the notebook to HTML
    (body, resources) = html_exporter.from_notebook_node(nb)

    # Write the HTML output to the specified file
    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(body)