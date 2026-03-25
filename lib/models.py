import unicodedata
from collections import defaultdict


def strip_accents_ponct(s):
    """Remove accents and punctuation from a string."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) not in ('Mn', 'Po'))


EA_NAME = "Adh\u00e9sion \u00e0 l'ACS avec acc\u00e8s \u00e0 la salle Emile Allais"


def parse_member(item):
    """Extract member information from a HelloAsso API item."""
    member = {
        'ea': item['name'] == EA_NAME,
        'firstname': item['user']['firstName'].strip().title(),
        'lastname': item['user']['lastName'].strip().title(),
        'email': item['payer']['email'],
        'activities': [o['name'] for o in item.get('options', []) if "oubliez pas" not in o['name']],
    }
    for field in item.get('customFields', []):
        if field['name'] == "Soci\u00e9t\u00e9":
            member['company'] = field['answer'].upper()
        elif field['name'] == "T\u00e9l\u00e9phone":
            member['phone'] = field['answer']
    return member


def get_member_filename(item):
    """Produce normalized filename: firstname_lastname_orderdate_id.json"""
    firstname = strip_accents_ponct(item['user']['firstName'].lower().replace(" ", ""))
    lastname = strip_accents_ponct(item['user']['lastName'].lower().replace(" ", ""))
    orderdate = item['order']['date'].split('T')[0]
    return f"{firstname}_{lastname}_{orderdate}_{item['id']}.json"


def build_summary(items_and_members):
    """Group members by activity, sorted by member count descending.

    Args:
        items_and_members: list of (item, member) tuples

    Returns:
        list of (activity_name, [members]) tuples sorted by count desc.
        Members with no activities go into "[Aucune activite]".
    """
    summary = defaultdict(list)
    summary_none = []

    for item, member in items_and_members:
        options = item.get('options', [])
        if len(options) > 0:
            for o in options:
                if "oubliez pas" not in o['name']:
                    summary[o['name']].append(member)
        else:
            summary_none.append(member)

    sorted_summary = sorted(summary.items(), key=lambda x: len(x[1]), reverse=True)
    if len(summary_none) > 0:
        sorted_summary.append(("[Aucune activit\u00e9]", summary_none))

    return sorted_summary
