from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

register = template.Library()

@register.filter
def no_dash(value):
    """Remplace les tirets par des espaces"""
    return value.replace('-', ' ')
