from atc.models import DetectionRule, DataNeeded
from yaml import load_all, FullLoader
from django.core.exceptions import ObjectDoesNotExist

mitre_tactics_list = [
    'initial_access',
    'execution',
    'persistence',
    'privilege_escalation',
    'defense_evasion',
    'credential_access',
    'discovery',
    'lateral_movement',
    'collection',
    'command_and_control',
    'exfiltration',
    'impact',
]

mitre_techniques_regex = 'attack\.t\d{4}'


def fill_DN(detection_rule: DetectionRule) -> DetectionRule:

    rule = load_all(detection_rule.raw_rule, Loader=FullLoader)
    [rule] = [x for x in rule]

    field_list = []
    event_ids = []

    ########################
    # Fill two above lists #
    ########################

    for item in rule:
        for condition in item.get("detection").keys():
            if condition == "condition":
                # this does not contain any fields from logs so skip
                continue

            if not isinstance(item["detection"].get(condition), dict):
                # something unexpected or just straight list of values
                # so skip
                continue

            for fieldname in item["detection"][condition].keys():
                # add a fieldname to field_list
                field_list.append(fieldname)

                # check if maybe the field holds event IDs
                if fieldname.lower() in [
                    "event_id",
                    "event_ids",
                    "eventid",
                    "eventids"
                ]:
                    print(type(item["detection"][condition][fieldname]))
                    # if this is a list of values..
                    if isinstance(item["detection"][condition][fieldname],
                                  list):
                        for value in item["detection"][condition][fieldname]:
                            try:
                                event_ids.append(int(value))
                            except ValueError:
                                pass

                    # if this is a single value..
                    elif isinstance(item["detection"][condition][fieldname],
                                    str):
                        try:
                            event_ids.append(
                                int(item["detection"][condition][fieldname])
                            )
                        except ValueError:
                            pass
                    # or maybe it's natively an int..
                    elif isinstance(item["detection"][condition][fieldname],
                                    int):
                        try:
                            event_ids.append(
                                item["detection"][condition][fieldname]
                            )
                        except ValueError:
                            pass

    ########################
    # Find according DNs   #
    ########################

    print(event_ids)
    print(field_list)

    # find by EventID (easy)
    for event_id in event_ids:
        try:
            data_needed = DataNeeded.objects.get(eventID=event_id)
        except ObjectDoesNotExist:
            data_needed = None

        if data_needed:
            # we do not have to care about duplicates
            # django will handle that
            detection_rule.data_needed.add(data_needed.id)
