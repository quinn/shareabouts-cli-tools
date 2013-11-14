from collections import defaultdict
from datetime import datetime
from pybars import strlist
from pybars._compiler import resolve, _if, _each


# Handlebars helpers
def _title(this, string):
    return string.title()

def _underline(this, string, char='-'):
    return char*len(string)

def _first_of(this, *values):
    for value in values:
        if value:
            return value

def _if_changed(this, options, var, val=None):
    if not hasattr(this.context, '_memo'):
        this.context._memo = {}

    val = val or resolve(this, *var.split('.'))
    if var not in this.context._memo:
        this.context._memo[var] = val
        changed = True
    else:
        changed = (this.context._memo[var] == val)
        this._memo[var] = val

    if changed:
        return options['fn'](this)
    else:
        return options['inverse'](this)

def _if_datetime_changed(this, options, var, format):
    val = resolve(this, *var.split('.'))
    dt_formatted = _format(this, val, format)
    return _if_changed(this, options, var + '_formatted_' + format, dt_formatted)

def _quoted(this, value):
    if value:
        return strlist(['"', value.replace('\\', '\\\\').replace('"', '\\"'), '"'])

def _format(this, value, format):
    if value:
        try:
            dt = datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
            return dt.strftime(format)
        except ValueError:
            pass
    return value

def _sort_by(this, options, *args):
    # If there's one argument, it's the sorting attribute name, and this will
    # be used as the context (iterable).
    if len(args) == 1:
        attr_name = args[0]
        iterable = this

    # If there are two arguments, the first is the context, the second if the
    # sorting argument.
    else:
        iterable, attr_name = args

    # Check the options for the function that generates an sort key. The
    # function should take two parameters (an element and the name of an
    # attribute) and generate a sort key.
    sort_key_maker = options.get(
        'sort_key_maker',
        lambda elem, attr: resolve(elem, *attr.split('.'))
    )

    sorted_context = sorted(iterable, key=lambda elem: sort_key_maker(elem, attr_name))
    return options['fn'](sorted_context)

def _group_by(this, options, *args):
    # If there's one argument, it's the grouping attribute name, and this will
    # be used as the context (iterable).
    if len(args) == 1:
        attr_name = args[0]
        iterable = this

    # If there are two arguments, the first is the context, the second if the
    # grouping argument.
    else:
        iterable, attr_name = args

    # Check the options for the function that generates an group key. The
    # function should take two parameters (an element and the name of an
    # attribute) and generate a group key.
    group_key_maker = options.get(
        'group_key_maker',
        lambda elem, attr: resolve(elem, *attr.split('.'))
    )

    grouped_context = defaultdict(list)
    for elem in iterable:
        group_key = group_key_maker(elem, attr_name)
        grouped_context[group_key].append(elem)

    return _each(this, options, grouped_context)

def _group_by_date(this, options, *args):
    # The group key should only take in to accound the first 10 characters of
    # the given attribute, as the first 10 characters in an ISO8601 formatted
    # date/time string represent the date portion.
    options['group_key_maker'] = lambda elem, attr: resolve(elem, *attr.split('.'))[:10]
    return _group_by(this, options, *args)

def _if_gte(this, options, val1, val2):
    return _if(this, options, lambda _: val1 >= val2)

def _if_lte(this, options, val1, val2):
    return _if(this, options, lambda _: val1 <= val2)

def _if_equal(this, options, val1, val2):
    return _if(this, options, lambda _: val1 == val2)

def _if_any(this, options, *values):
    return _if(this, options, any(values))

def _if_all(this, options, *values):
    return _if(this, options, all(values))

def _with(this, options, local_context):
    return options['fn'](local_context)

def _length(this, *args):
    if len(args) == 1:
        context = args[0]
    else:
        context = this

    try:
        return len(context)
    except TypeError:
        return len(context.context)

helpers = {
    'title': _title,
    'underline': _underline,
    'first_of': _first_of,
    'if_changed': _if_changed,
    'if_datetime_changed': _if_datetime_changed,
    'quoted': _quoted,
    'format': _format,
    'sort_by': _sort_by,
    'group_by': _group_by,
    'group_by_date': _group_by_date,
    'if_lte': _if_lte,
    'if_gte': _if_gte,
    'if_equal': _if_equal,
    'if_any': _if_any,
    'if_all': _if_all,
    'with': _with,
    'length': _length
}

