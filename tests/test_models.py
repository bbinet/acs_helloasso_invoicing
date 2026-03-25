from lib.models import parse_member, get_member_filename, build_summary


def test_parse_member_extracts_basic_fields(sample_helloasso_item):
    member = parse_member(sample_helloasso_item)
    assert member['firstname'] == "Jean-Pierre"
    assert member['lastname'] == "De La Fontaine"
    assert member['email'] == "jp.fontaine@example.com"
    # ea is False because the item name doesn't match the exact EA string
    assert member['ea'] is False


def test_parse_member_extracts_company_and_phone(sample_helloasso_item):
    member = parse_member(sample_helloasso_item)
    assert member['company'] == "MA PETITE ENTREPRISE"
    assert member['phone'] == "06 12 34 56 78"


def test_parse_member_filters_oubliez_pas_from_activities(sample_helloasso_item):
    member = parse_member(sample_helloasso_item)
    # "N'oubliez pas de venir" should be filtered out
    assert member['activities'] == ["Football", "Tennis"]
    assert not any("oubliez pas" in a for a in member['activities'])


def test_get_member_filename(sample_helloasso_item):
    filename = get_member_filename(sample_helloasso_item)
    # Jean-Pierre -> jean-pierre (lowered, spaces removed, hyphens kept)
    # De La Fontaine -> delafontaine
    assert filename == "jean-pierre_delafontaine_2024-09-15_12345.json"


def test_build_summary_groups_by_activity_sorted_by_count():
    member_a = {'firstname': 'Alice', 'activities': ['Football', 'Tennis']}
    member_b = {'firstname': 'Bob', 'activities': ['Football']}
    member_c = {'firstname': 'Charlie', 'activities': ['Tennis', 'Basketball']}

    items_and_members = [
        ({'options': [{'name': 'Football'}, {'name': 'Tennis'}]}, member_a),
        ({'options': [{'name': 'Football'}]}, member_b),
        ({'options': [{'name': 'Tennis'}, {'name': 'Basketball'}]}, member_c),
    ]

    result = build_summary(items_and_members)
    # Football: 2 members (Alice, Bob), Tennis: 2 (Alice, Charlie), Basketball: 1 (Charlie)
    # Sorted by count desc: Football and Tennis tied (both 2), then Basketball (1)
    activities = [activity for activity, members in result]
    assert activities[0] in ("Football", "Tennis")  # both have 2
    assert activities[1] in ("Football", "Tennis")
    assert activities[2] == "Basketball"
    assert len(result[0][1]) == 2
    assert len(result[2][1]) == 1


def test_build_summary_no_activities_goes_to_aucune():
    member_a = {'firstname': 'Alice', 'activities': []}
    member_b = {'firstname': 'Bob', 'activities': ['Football']}

    items_and_members = [
        ({}, member_a),  # no 'options' key
        ({'options': [{'name': 'Football'}]}, member_b),
    ]

    result = build_summary(items_and_members)
    activities = [activity for activity, members in result]
    assert "[Aucune activit\u00e9]" in activities
    # Football first (1 member), then Aucune activite (1 member)
    assert result[0] == ("Football", [member_b])
    assert result[1] == ("[Aucune activit\u00e9]", [member_a])
