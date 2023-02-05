from django.utils.crypto import get_random_string

def generate_unique_code():
    """
    Generate a unique code
    """
    chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ123456789!@#$%&'
    return get_random_string(8, chars)
