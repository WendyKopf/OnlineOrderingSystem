from flask import flash

def add_error(form, key, value):
    if key not in form.errors:
        form.errors[key] = []
    form.errors[key].append(value)

def flash_errors(errors):
    for field, error_list in errors.items():
        for error in error_list:
            flash('Error - %s : %s' % (field, error))

def flash_form_errors(form):
    flash_errors(form.errors)

def flatten_hierarchy(employee, f):
    """Walks the managements hierarchy from top to bottom and returns
    a flat list of the values returned by calling f on an Employee
    instance."""
    acc = [item for item in f(employee)]
    if employee.direct_reports == []:
        return acc
    for report in employee.direct_reports:
        acc += flatten_hierarchy(report, f)
    return acc

