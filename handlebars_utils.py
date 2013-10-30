from datetime import datetime
from pybars import strlist
from pybars._compiler import resolve, Scope, _if, _each


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

def _group_by(this, options, *args):
    if len(args) == 1:
        attr_name = args[0]
        iterable = this
    else:
        iterable, attr_name = args

    grouped_context = {}

    for elem in iterable:
        value = elem[attr_name]
        if value not in grouped_context:
            grouped_context[value] = [elem]
        else:
            grouped_context[value].append(elem)

    return _each(this, options, grouped_context)

def _group_by_date(this, options, *args):
    if len(args) == 1:
        attr_name = args[0]
        iterable = this
    else:
        iterable, attr_name = args

    grouped_context = {}

    for elem in iterable:
        # Assume an ISO8601 String
        value = elem[attr_name][:10]
        if value not in grouped_context:
            grouped_context[value] = [elem]
        else:
            grouped_context[value].append(elem)

    return _each(this, options, grouped_context)

def _if_gte(this, options, val1, val2):
    return _if(this, options, lambda _: val1 >= val2)

def _if_lte(this, options, val1, val2):
    return _if(this, options, lambda _: val1 <= val2)

def _if_equal(this, options, val1, val2):
    return _if(this, options, lambda _: val1 == val2)

def _with(this, options, local_context):
    scope = Scope(local_context, this)
    return options['fn'](scope)

def _length(this, *args):
    if len(args) == 1:
        return len(args[0])
    else:
        return len(this.context)

helpers = {
    'title': _title,
    'underline': _underline,
    'first_of': _first_of,
    'if_changed': _if_changed,
    'if_datetime_changed': _if_datetime_changed,
    'quoted': _quoted,
    'format': _format,
    'group_by': _group_by,
    'group_by_date': _group_by_date,
    'if_lte': _if_lte,
    'if_gte': _if_gte,
    'if_equal': _if_equal,
    'with': _with,
    'length': _length
}

