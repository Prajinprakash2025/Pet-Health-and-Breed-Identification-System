from django import template

register = template.Library()

@register.filter(name='replace')
def replace_string(value, arg):
    """
    Django template filter 'replace' - replaces all occurrences of arg[0] with arg[1].
    Usage: {{ value|replace:"_":" " }}
    """
    if not isinstance(value, str) or not arg:
        return value
    
    if ':' not in arg:
        return value
    
    old_char, new_char = arg.split(':', 1)
    return str(value).replace(old_char, new_char)

