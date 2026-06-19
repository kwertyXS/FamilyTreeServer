import re
from typing import Optional

from lxml import etree

from src.db.tables import *
from src.repositories.FamilyRepository import *


def _parse_coords(coords: str | None) -> tuple[Optional[float], Optional[float]]:
    if not coords:
        return None, None
    parts = coords.split(",")
    if len(parts) == 2:
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            pass
    return None, None


def _extract_year(date_str: str | None) -> int | None:
    if not date_str:
        return None
    m = re.search(r"\b(\d{4})\b", date_str)
    if m:
        return int(m.group(1))
    return None


def _parse_sex(raw: str | None) -> bool | None:
    if raw == "М":
        return True
    if raw == "Ж":
        return False
    return None


async def parse_and_save(xml_bytes: bytes):
    """Парсит XML и сохраняет всё в БД. Если данные уже есть — перезаписывает."""
    root = etree.fromstring(xml_bytes)

    # --- Places ---
    places_list = []
    all_place_els = list(root.find("places").findall("place"))
    for el in all_place_els:
        pid = el.get("id")
        lat, lon = _parse_coords(el.get("coords"))
        places_list.append(PlaceTable(
            id=pid,
            full_name=el.get("fullname", ""),
            name=el.get("name"),
            short_name=el.get("nameshort"),
            latitude=lat,
            longitude=lon,
        ))

    # --- Families ---
    families_list = []
    families_root = root.find("families")
    for el in families_root.findall("family"):
        fid = el.get("id")
        families_list.append(FamilyTable(
            id=fid,
            name=el.get("name", ""),
            male_surname=el.get("ms"),
            female_surname=el.get("fs"),
        ))

    # --- Events ---
    event_list = []
    event_map: dict[str, EventTable] = {}
    events_root = root.find("events")
    for el in events_root.findall("event"):
        eid = el.get("id")
        place_el = el.find("place")
        place_id = place_el.get("id") if place_el is not None else None
        event = EventTable(
            id=eid,
            type=el.get("type", ""),
            date=el.get("date"),
            date_sort=_extract_year(el.get("date")),
            description=(
                (el.findtext("comment") or "")
                + (" " + el.get("deathreason", "") if el.get("deathreason") else "")
            ).strip() or None,
            place_id=place_id,
        )
        event_list.append(event)
        event_map[eid] = event

    # --- Persons (сбор + photo из documents) ---
    persons_root = root.find("persons")
    if persons_root is None:
        await PlaceRepository().rewrite(places_list)
        await FamilyRepository().rewrite(families_list)
        await EventRepository().rewrite(event_list)
        return

    person_elements = persons_root.findall("person")
    persons_in_xml: dict[str, etree._Element] = {}

    # Собираем photo наперёд из documents
    photo_map: dict[str, str] = {}
    documents_root = root.find("documents")
    if documents_root is not None:
        for doc_el in documents_root.findall("document"):
            photo_path = doc_el.get("path")
            if not photo_path:
                continue
            details_el = doc_el.find("details")
            if details_el is None:
                continue
            for detail_el in details_el.findall("detail"):
                person_el = detail_el.find("person")
                if person_el is None:
                    continue
                pid = person_el.get("id")
                if pid:
                    photo_map[pid] = photo_path

    persons_list = []
    for el in person_elements:
        pid = el.get("id")
        persons_in_xml[pid] = el

        family_el = el.find("family")
        family_id = family_el.get("id") if family_el is not None else None

        biography = el.findtext("comment") or None

        place_el = el.find("place")
        bplace_el = el.find("bplace")
        dplace_el = el.find("dplace")

        person = PersonTable(
            id=pid,
            sex=_parse_sex(el.get("sex")),
            surname=el.get("sn"),
            maiden_surname=el.get("msn"),
            first_name=el.get("fn"),
            middle_name=el.get("mn"),
            full_name=el.get("fullname", ""),
            occupation=el.get("occu"),
            birth_date=el.get("bdate"),
            death_date=el.get("ddate"),
            death_reason=el.get("dreason"),
            lifespan=el.get("lifespan"),
            is_favorite=el.get("fav") == "1",
            biography=biography,
            place_id=place_el.get("id") if place_el is not None else None,
            birth_place_id=bplace_el.get("id") if bplace_el is not None else (
                place_el.get("id") if place_el is not None else None
            ),
            death_place_id=dplace_el.get("id") if dplace_el is not None else None,
            family_id=family_id,
            photo=photo_map.get(pid),
        )
        persons_list.append(person)

    # --- Сбор person_events и relations ---
    person_event_list = []
    relations_list = []
    relations_seen: set[tuple[str, str]] = set()

    for pid, el in persons_in_xml.items():
        # events
        events_el = el.find("events")
        if events_el is not None:
            for event_el in events_el.findall("event"):
                eid = event_el.get("id")
                role = event_el.get("role", "")
                if eid and eid in event_map:
                    person_event_list.append(PersonEventTable(
                        person_id=pid, event_id=eid, role=role
                    ))

        # nearest / relations
        nearest_el = el.find("nearest")
        if nearest_el is not None:
            _collect_relations(relations_list, relations_seen, pid, nearest_el, persons_in_xml)

    # --- Запись в БД (двухфазно: удаление снизу вверх, вставка сверху вниз) ---
    # Фаза 1: очистка (от зависимых к независимым)
    # await PersonEventRepository().rewrite([])
    # await PersonRelationRepository().rewrite([])
    # await PersonRepository().rewrite([])
    # await EventRepository().rewrite([])
    # await FamilyRepository().rewrite([])
    # await PlaceRepository().rewrite([])

    # Фаза 2: вставка (от независимых к зависимым)
    await PlaceRepository().rewrite(places_list)
    await FamilyRepository().rewrite(families_list)
    await EventRepository().rewrite(event_list)
    await PersonRepository().rewrite(persons_list)
    await PersonEventRepository().rewrite(person_event_list)
    await PersonRelationRepository().rewrite(relations_list)


def _collect_relations(
    relations_list: list,
    seen: set[tuple[str, str]],
    person_id: str,
    nearest_el: etree._Element,
    persons_in_xml: dict[str, etree._Element],
):
    """Собирает связи из <nearest> в общий список (без проверок БД)."""

    def _add_relation(pid_a: str, pid_b: str, relcode: str, label: str):
        if pid_a == pid_b:
            return
        key = (pid_a, pid_b)
        if key in seen:
            return
        seen.add(key)
        relations_list.append(PersonRelationTable(
            person_id=pid_a, related_person_id=pid_b,
            relation_type=relcode, relation_label=label,
        ))

    for rel_person_el in nearest_el.findall("person"):
        rel_person_id = rel_person_el.get("id")
        if not rel_person_id or rel_person_id not in persons_in_xml:
            continue

        relcode = rel_person_el.get("relcode", "")
        label = rel_person_el.get("rel", "")

        # Прямая связь
        _add_relation(person_id, rel_person_id, relcode, label)

        # Родительские relcode: F (отец), M (мать) — у потомка relcode будет S (сын) или D (дочь)
        if relcode in ("F", "M"):
            child_sex = persons_in_xml[person_id].get("sex")
            child_relcode = "S" if _parse_sex(child_sex) is True else "D"
            child_label = "Сын" if child_relcode == "S" else "Дочь"
            _add_relation(rel_person_id, person_id, child_relcode, child_label)

        # Супружеские relcode: B (жена), A (муж)
        elif relcode in ("B", "A"):
            spouse_relcode = "A" if relcode == "B" else "B"
            spouse_label = "Муж" if spouse_relcode == "A" else "Жена"
            _add_relation(rel_person_id, person_id, spouse_relcode, spouse_label)

            # --- Дети внутри супружеской пары ---
            for child_el in rel_person_el.findall("person"):
                child_id = child_el.get("id")
                if not child_id or child_id not in persons_in_xml:
                    continue
                child_sex = persons_in_xml[child_id].get("sex")
                child_relcode = "S" if _parse_sex(child_sex) is True else "D"
                child_label = "Сын" if child_relcode == "S" else "Дочь"

                # связь: отец -> ребёнок
                _add_relation(person_id, child_id, child_relcode, child_label)
                # связь: мать -> ребёнок
                _add_relation(rel_person_id, child_id, child_relcode, child_label)
                # связь: ребёнок -> отец
                _add_relation(child_id, person_id, "F", "Отец")
                # связь: ребёнок -> мать
                _add_relation(child_id, rel_person_id, "M", "Мать")
