from django.utils.crypto import get_random_string

def generate_unique_code(length):
    """
    Generate a unique code
    """
    chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ0123456789!@#$%&'
    return get_random_string(length, chars)


def generate_reference_code():
    return generate_unique_code(13)


def generate_bet_id():
    return generate_unique_code(6)
