from django import template
from django.template.defaultfilters import stringfilter
from django.utils import timezone
from datetime import timedelta
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)

@register.filter(name='get_attribute')
def get_attribute(obj, attr_name):
    return getattr(obj, attr_name, None)

@register.filter(name='filter_document_type')
def filter_document_type(documents, doc_type):
    """Filter documents by document type."""
    if documents is None:
        return []
    return [doc for doc in documents if doc.document_type == doc_type]

@register.filter(name='filter_documents_by_type')
def filter_documents_by_type(documents, doc_type):
    """Filter documents by document type and return a queryset."""
    if documents is None:
        return documents
    return documents.filter(document_type=doc_type)

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def subtract_hours(value, hours):
    """Subtract hours from a datetime value."""
    if not value:
        return None
    try:
        hours = int(hours)
        return value - timedelta(hours=hours)
    except (ValueError, TypeError):
        return None

@register.filter
def time_until(value):
    """Calculate time until a given datetime."""
    now = timezone.now()
    if value > now:
        delta = value - now
        hours = delta.total_seconds() / 3600
        return int(hours)
    return 0

@register.filter
def filter_by_university(payments, university_name):
    """Filter payments by university name"""
    return payments.filter(university=university_name).first()

@register.filter
def filter_documents_by_university(documents, university_name):
    """Filter documents by university name"""
    return documents.filter(university__name=university_name).first()

@register.filter(name='count_notifications')
def count_notifications(notifications):
    if notifications is None:
        return 0
    return notifications.filter(is_read=False).count()

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_elided_page_range(paginator, number, on_each_side=3, on_ends=2):
    return paginator.get_elided_page_range(number=number, 
                                           on_each_side=on_each_side, 
                                           on_ends=on_ends)

@register.filter
def filter_documents_by_university_id(documents, university_id):
    """Filter documents by university ID."""
    for doc in documents:
        if doc.university_id == university_id and doc.document_type == 'payment_proof':
            return doc
    return None

@register.filter
def filter_by_university(documents, university_name):
    """Filter documents by university name."""
    return [doc for doc in documents if doc.university.name == university_name]

@register.filter
def json_encode(value):
    """Convert a Python value to a JSON string."""
    return mark_safe(json.dumps(value)) 