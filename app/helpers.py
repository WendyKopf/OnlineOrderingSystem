def add_error(form, key, value):
    if key not in form.errors:
        form.errors[key] = []
    form.errors[key].append(value)
