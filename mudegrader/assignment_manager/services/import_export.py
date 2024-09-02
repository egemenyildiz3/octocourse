import csv
from typing import List, Type

from django.apps import apps
from django.db import transaction
from django.db.models import QuerySet, Model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from assignment_manager.models import Course


def query_to_csv(objects: QuerySet) -> HttpResponse:
    """
    Returns a HttpResponse with a .csv file of the QuerySet
    A QuerySet is a django result of a query like Student.objects.all()
    """
    # TODO: Think of if it is possible to handle it in a way that
    #   every object is one row instead of a new row for every assignment that is related
    #   to an object
    response = HttpResponse(content_type='text/csv')
    model = objects.model
    model_name = model._meta.verbose_name
    date = timezone.now()
    formatted_datetime = date.strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"export_{model_name}_{formatted_datetime}.csv"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    # get all the field names of the object to use as .csv column names
    ys = model._meta.get_fields()
    field_names: List[str] = list(map(lambda x: x.name, ys))
    # filter out id
    field_names_no_id = [x for x in field_names if x != 'id']
    # start writing the file
    writer = csv.writer(response)
    # write column names
    writer.writerow(field_names_no_id)
    # write object rows
    for obj in objects.values_list(*field_names_no_id):
        writer.writerow(obj)

    return response

def import_any_model_csv(csv_file, model, remove_fields=None, defaults=None) -> List[Type[Model]]:
    # Initialize defaults
    if remove_fields is None:
        remove_fields = list()

    if defaults is None:
        defaults = dict()

    decoded_file = csv_file.read().decode('utf-8').splitlines()
    reader = csv.reader(decoded_file)

    # Get field names from the header row
    field_names = next(reader)
    objects = []
    with transaction.atomic():
        for row in reader:
            obj_zip = list(zip(field_names, row))
            # filter all empty rows out
            obj_no_empty_rows = list(filter(lambda x: x[1] !='', obj_zip))
            # filter all user-specified fields out
            obj_no_specified_fields = list(filter(lambda x: x[0] not in remove_fields, obj_no_empty_rows))
            obj_data = dict(obj_no_specified_fields)

            # TODO: add error catching
            # make model out of data
            try:
                created_object, success = model.objects.update_or_create(defaults=defaults, **obj_data)
                objects.append(created_object)
            except Exception as e:
                print("OOPS PROBLEM")
    return objects
