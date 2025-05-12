from django import template

register = template.Library()

@register.filter
def index(lst, i):
    """
    Returns the item at the given index in the list.
    Usage: {{ list|index:i }}
    """
    try:
        return lst[int(i)]
    except (ValueError, TypeError, IndexError):
        return None 