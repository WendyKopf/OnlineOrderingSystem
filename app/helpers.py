def add_error(form, key, value):
    if key not in form.errors:
        form.errors[key] = []
    form.errors[key].append(value)

def flatten_hierarchy(employee, f):
    """Walks the managements hierarchy from top to bottom and returns
    a flat list of the values returned by calling f on an Employee
    instance."""
    acc = f(employee)
    if employee.direct_reports == []:
        return acc
    for report in employee.direct_reports:
        acc += flatten_hierarchy(report, f)
    return acc

