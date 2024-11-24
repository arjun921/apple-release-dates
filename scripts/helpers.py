import re
def generate_tags(data):
    tags = []
    tags.append(data.family)
    # tags.append(data.model)
    tags.append(data.released.strftime('%Y'))
    return tags

def generate_categories(data):
    categories = []
    categories.append(data.family)
    # categories.append(data.model)
    categories.append(data.released.strftime('%Y'))
    if 'accessories' in data.family.lower():
        categories.append('Accessories')
    
    for folder in data.destination.parts:
        if folder in ['content', 'posts']:
            continue
        categories.append(folder)
    return categories

def make_path_safe(string):
    # Replace any character that is not alphanumeric, space, hyphen, or underscore with an underscore
    return re.sub(r'[^\w\s\-\(\)\"]', '_', string).strip()
