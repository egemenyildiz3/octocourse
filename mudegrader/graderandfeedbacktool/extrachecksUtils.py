import os
import re


def validate_submission(submission_path, extra_checks):
    """
    Validate the submission based on the extra checks provided.

    :param submission_path: Path to the submission directory.
    :type submission_path: str
    
    :param extra_checks: List of extra checks to perform.
    :type extra_checks: list
    
    :returns: Dictionary containing the results of the extra checks.
    :rtype: dict
    """
    results = {}
    submission_path = os.path.join("app/project_files/submissions/courso/1")
    for check in extra_checks:
        check_type = check['type']
        check_value = check['value']
        check_extra = check.get('extra', None)
        result = False
        
        if check_type == 'naming_convention':
            result = check_naming_convention(submission_path, check_value)
        elif check_type == 'file_existence':
            result = check_file_existence(submission_path, check_value, check_extra)
        elif check_type == 'file_type':
            result = check_file_type(submission_path, check_value, check_extra)
        elif check_type == 'file_location':
            result = check_file_location(submission_path, check_value, check_extra)
        
        results[f'{check_type}: {check_value}'] = 'Passed' if result else 'Failed'
    
    return results


def check_naming_convention(submission_path, regex_pattern):
    """
    Check if the files in the submission directory match the specified naming convention.

    :param submission_path: Path to the submission directory.
    :type submission_path: str

    :param regex_pattern: Regular expression pattern to match the file names.
    :type regex_pattern: str
    """
    pattern = re.compile(regex_pattern)
    print(f"Regex Pattern: {regex_pattern}")
    for root, dirs, files in os.walk(submission_path):
        print(f"Checking directory: {root}")
        for file in files:
            print(f"Checking file: {file}")
            if pattern.match(file):
                print(f"File {file} matches the pattern.")
            else:
                print(f"File {file} does not match the pattern.")
                return False
    return True

def check_file_existence(submission_path, filename, filetype):
    """
    Check if the specified file exists in the submission directory.
    
    :param submission_path: Path to the submission directory.
    :type submission_path: str
    
    :param filename: Name of the file.
    :type filename: str
    
    :param filetype: Type of the file.
    :type filetype: str
    
    :returns: True if the file exists, False otherwise.
    :rtype: bool
    """
    for root, dirs, files in os.walk(submission_path):
        if f"{filename}.{filetype}" in files:
            print(files)
            return True
    return False

def check_file_type(submission_path, filename, expected_filetype):
    """
    Check if the specified file exists in the submission directory with the expected file type.

    :param submission_path: Path to the submission directory.
    :type submission_path: str

    :param filename: Name of the file.
    :type filename: str

    :param expected_filetype: Expected file type.
    :type expected_filetype: str

    :returns: True if the file exists with the expected file type, False otherwise.
    :rtype: bool
    """

    filename_with_extension = f"{filename}.{expected_filetype}"
    print(filename_with_extension)
    for root, dirs, files in os.walk(submission_path):
        print(files)
        if filename_with_extension in files:
            return True
    return False

def check_file_location(submission_path, filename, relative_path):
    """
    Check if the specified file exists in the correct location in the submission directory.

    :param submission_path: Path to the submission directory.
    :type submission_path: str

    :param filename: Name of the file.
    :type filename: str

    :param relative_path: Relative path of the file within the submission directory.
    :type relative_path: str

    :returns: True if the file exists in the correct location, False otherwise.
    :rtype: bool
    """
    print(f"Submission Path: {submission_path}")
    cleaned_filename = filename.strip()
    cleaned_relative_path = relative_path.strip().lstrip('/')  # Remove leading slash if any
    
    expected_path = os.path.join(submission_path, cleaned_relative_path, cleaned_filename)
    print(f"Checking file location for: {expected_path}")
    exists = os.path.exists(expected_path)
    print(f"File location exists: {exists}")
    return exists