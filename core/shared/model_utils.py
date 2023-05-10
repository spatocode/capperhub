import sys
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.crypto import get_random_string

def optimize_image(model):
    name = model.image.name.split('.')[0]
    image = model.image
    output = BytesIO()

    img = Image.open(image)

    basewidth = 800
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    img.save(output, format='JPEG', quality=90)
    output.seek(0)

    optimized_file = InMemoryUploadedFile(output, 'FileField', name, 'image/jpeg', sys.getsizeof(output), None)
    return optimized_file

def generate_unique_code(length):
    """
    Generate a unique code
    """
    chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ0123456789!@#$%&'
    return get_random_string(length, chars)


def generate_reference_code():
    return generate_unique_code(16)


def generate_wager_id():
    return generate_unique_code(10)
