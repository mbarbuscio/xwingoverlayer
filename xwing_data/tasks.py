import json
from collections import OrderedDict

import os

from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from xwing_data.models import *


@shared_task(bind=True, max_retries=3)
def process_pilot_data(self, pilot_entry, delay=True):
    ship = Ship.objects.get(name=pilot_entry['ship'])
    if not ship:
        print("MISSING SHIP: {}".format(pilot_entry['ship']))
        process_pilot_data.delay(pilot_entry)
        return False

    faction, created = Faction.objects.update_or_create(name=pilot_entry['faction'], defaults={})

    pilot, created_pilot = Pilot.objects.update_or_create(
        xws=pilot_entry['xws'],
        id=pilot_entry['id'],
        defaults={
            "name": pilot_entry['name'],
            "is_unique": pilot_entry.get('unique', False),
            "ship": ship,
            "skill": pilot_entry['skill'] if pilot_entry['skill'] != "?" else 99,
            "points": pilot_entry['points'] if pilot_entry['points'] != "?" else 99,
            "ability": pilot_entry.get('text', None),
            "faction": faction,
            "image": pilot_entry['image'] if pilot_entry.get('image', None) else None,
        }
    )

    if pilot_entry.get('ship_override', None):
        stats = StatisticSet()
        for field in ["attack", "agility", "hull", "shields"]:
            setattr(stats, field, pilot_entry['ship_override'].get(field, 0))

        stats.save()
        pilot.ship_override = stats
        pilot.save()

    pilot.slot_set.all().delete()

    for slot_name in pilot_entry.get('slots', []):
        slot_type, created = SlotType.objects.update_or_create(
            name=slot_name,
            defaults={},
        )
        slot = Slot(
            slot_type=slot_type,
            pilot=pilot
        )
        slot.save()

    print("{} {} ({}) to system".format(
        "Added" if created_pilot else "Updated",
        pilot.name,
        pilot.faction
    ))
    return True


@shared_task(bind=True, max_retries=3)
def process_ship_data(self, ship_entry, delay=True):
    stats = StatisticSet()

    for field in ["attack", "agility", "hull", "shields"]:
        setattr(stats, field, ship_entry.get(field, 0))
    stats.save()

    base_size, created = BaseSize.objects.update_or_create(name=ship_entry['size'], defaults={})

    ship, created_ship = Ship.objects.update_or_create(
        xws=ship_entry['xws'],
        id=ship_entry['id'],
        defaults={
            "size": base_size,
            "stats": stats,
            "name": ship_entry['name'],
        }
    )

    for faction_name in ship_entry['faction']:
        faction, created = Faction.objects.update_or_create(name=faction_name, defaults={})
        ship.faction.add(faction)

    for action_name in ship_entry['actions']:
        action, created = Action.objects.update_or_create(name=action_name, defaults={})
        ship.actions.add(action)

    print("{} {} to system".format(
        "Added" if created_ship else "Updated",
        ship.name
    ))
    return True


@shared_task(bind=True, max_retries=3)
def process_upgrade_data(self, upgrade_entry, delay=True):
    ships = []
    for ship in upgrade_entry.get('ship', []):
        ship_object = Ship.objects.get(name=ship)
        if not ship_object:
            print("MISSING SHIP: {}".format(ship))
            process_upgrade_data.delay(upgrade_entry)
            return False
        ships.append(ship_object)

    bases = []
    for size in upgrade_entry.get('size', []):
        base = BaseSize.objects.get(name=size)
        if not base:
            print("MISSING BASE SIZE: {}".format(size))
            process_upgrade_data.delay(upgrade_entry)
            return False
        bases.append(base)

    slot_type, created = SlotType.objects.update_or_create(
        name=upgrade_entry['slot'],
        defaults={},
    )
    faction = None
    if upgrade_entry.get('faction', False):
        faction, created = Faction.objects.update_or_create(name=upgrade_entry['faction'], defaults={})

    upgrade, created_upgrade = Upgrade.objects.update_or_create(
        xws=upgrade_entry['xws'],
        id=upgrade_entry['id'],
        defaults={
            "is_unique": upgrade_entry.get('unique', False),
            "is_limited": upgrade_entry.get('limited', False),
            "text": upgrade_entry.get('text', ""),
            "slot": slot_type,
            "image": upgrade_entry['image'] if upgrade_entry.get('image', None) else None,
            "points": upgrade_entry.get('points', 0),
            "energy": upgrade_entry.get('energy', 0),
            "range": upgrade_entry.get('range', ""),
            "attack": upgrade_entry.get('attack', 0),
            "name": upgrade_entry.get('name', "")
        }
    )

    if faction:
        upgrade.faction.add(faction)

    for ship in ships:
        upgrade.ships.add(ship)

    for base in bases:
        upgrade.size.add(base)

    for grant in upgrade_entry.get('grants', []):
        if grant['type'] == "stats":
            object = StatisticSet(
                skill=0,
                attack=0,
                agility=0,
                hull=0,
                shields=0
            )
            setattr(object, grant['name'], grant['value'])
            object.save()
        if grant['type'] == "action":
            object, created = Action.objects.update_or_create(
                name=grant['name'], defaults={}
            )
        if grant['type'] == "slot":
            object, created = SlotType.objects.update_or_create(
                name=grant['name'],
                defaults={},
            )

        related_object_type = ContentType.objects.get_for_model(object)
        grant_object = Grant(
            content_type=related_object_type,
            object_id=object.id
        )
        grant_object.save()
        upgrade.grants.add(grant_object)

    print("{} {} {} to system".format(
        "Added" if created_upgrade else "Updated",
        upgrade.slot,
        upgrade.name
    ))
    return True


@shared_task(bind=True, max_retries=3)
def process_damage_deck(self, damage_entry, deck_type, delay=True):
    damage_deck, created = DamageDeck.objects.update_or_create(
        name=deck_type
    )

    damage_type, create = DamageType.objects.update_or_create(
        name=damage_entry.get('type')
    )

    card, created = DamageCard.objects.update_or_create(
        name=damage_entry.get('name'),
        defaults={
            "text": damage_entry.get('text', ""),
            "type": damage_type,
            "amount": damage_entry.get('amount'),
            "deck": damage_deck,
            "image": damage_entry['image'] if damage_entry.get('image', None) else None,
        }
    )
    print("Added {} ({}) to system".format(
        card.name,
        damage_deck.name
    ))
    return True


@shared_task(bind=True, max_retries=3)
def process_damage_deck_tfa(self, damage_entry, delay=True):
    return process_damage_deck(damage_entry, "TFA", delay)


@shared_task(bind=True, max_retries=3)
def process_damage_deck_core(self, damage_entry, delay=True):
    return process_damage_deck(damage_entry, "Core", delay)


FUNCTIONS = OrderedDict(
    [
        ('ships', process_ship_data),
        ('pilots', process_pilot_data),
        ('upgrades', process_upgrade_data),
        ('damage-deck-core', process_damage_deck_core),
        ('damage-deck-core-tfa', process_damage_deck_tfa),
    ]
)


@shared_task(bind=True, max_retries=3)
def import_data(self, source, delay=True):
    with open(os.path.join(settings.XWING_DATA, 'data', '{}.js'.format(source)), encoding='utf8') as raw_data:
        data = json.load(raw_data)
    count = 0
    if source == 'upgrades':
        Grant.objects.all().delete()
    for entry in data:
        result = FUNCTIONS[source](entry) if not delay else FUNCTIONS[source].delay(entry)
        if result:
            count += 1
    return count


@shared_task(bind=True, max_retries=3)
def delete_all_xwing_data(self):
    Faction.objects.all().delete()
    Action.objects.all().delete()
    BaseSize.objects.all().delete()
    SlotType.objects.all().delete()
    StatisticSet.objects.all().delete()
    Ship.objects.all().delete()
    Pilot.objects.all().delete()
    Slot.objects.all().delete()
    GrantType.objects.all().delete()
    Grant.objects.all().delete()
    Upgrade.objects.all().delete()
    DamageDeck.objects.all().delete()
    DamageType.objects.all().delete()
    DamageCard.objects.all().delete()