from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Returns a list of strings, split by the given delimiter.
    
    Example:
        {{ "a,b,c"|split:"," }}
        Returns: ['a', 'b', 'c']
    """
    return value.split(delimiter)

@register.filter
def is_in_list(value, arg):
    """
    Check if a value is in a list.
    """
    return value in arg