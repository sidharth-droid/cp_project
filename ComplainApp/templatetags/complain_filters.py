from django import template

register = template.Library()

@register.filter(name='is_image')
def is_image(file_url):
    return file_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))

@register.filter(name='is_pdf')
def is_pdf(file_url):
    return file_url.lower().endswith('.pdf')

@register.filter(name='is_video')
def is_video(file_url):
    return file_url.lower().endswith(('.mp4', '.mov', '.avi'))
