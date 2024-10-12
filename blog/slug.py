import random
import string

from django.utils.text import slugify


def generate_unique_slug(instance, base_title, new_slug=None, update=False):
    slug = new_slug or slugify(base_title)
    model = instance.__class__

    # Determine the queryset for checking if the slug exists
    if update:
        slug_exists = model.objects.filter(slug__icontains=slug).exclude(pk=instance.pk).exists()
    else:
        slug_exists = model.objects.filter(slug__icontains=slug).exists()

    # If the slug exists, generate a new one with a random string appended
    if slug_exists:
        random_string = "".join(random.choices(string.ascii_lowercase, k=4))
        new_slug = f"{slug}-{random_string}"
        return generate_unique_slug(instance, base_title, new_slug=new_slug, update=update)

    return slug
