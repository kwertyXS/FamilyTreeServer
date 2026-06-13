import re
from typing import Optional

from lxml import etree
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session_factory
from db.models import Person, Place, Event, Family, person_event_table, person_relation_table


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
    """Извлечь год из строки даты для сортировки."""
    if not date_str:
        return None
    m = re.search(r"\b(\d{4})\b", date_str)
    if m:
        return int(m.group(1))
    return None


def _parse_sex(raw: str | None) -> bool | None:
    """М → True (муж), Ж → False (жен), остальное → None."""
    if raw == "М":
        return True
    if raw == "Ж":
        return False
    return None


async def parse_and_save(xml_bytes: bytes):
    """Парсит XML и сохраняет всё в БД. Если данные уже есть — перезаписывает."""
    root = etree.fromstring(xml_bytes)

    async with async_session_factory() as session:
        async with session.begin():
            for table in (person_relation_table, person_event_table):
                await session.execute(table.delete())
            for model in (Person, Event, Place, Family):
                await session.execute(model.__table__.delete())

            # --- Places (два прохода: сначала создаём, потом parent_id) ---
            places_root = root.find("places")
            place_map: dict[str, Place] = {}
            if places_root is not None:
                all_place_els = list(places_root.findall("place"))

                # 1-й проход: создаём Place без parent_id
                for el in all_place_els:
                    pid = el.get("id")
                    lat, lon = _parse_coords(el.get("coords"))
                    place = Place(
                        id=pid,
                        full_name=el.get("fullname", ""),
                        name=el.get("name"),
                        short_name=el.get("nameshort"),
                        latitude=lat,
                        longitude=lon,
                    )
                    session.add(place)
                    place_map[pid] = place

                await session.flush()

                # 2-й проход: проставляем parent_id
                for el in all_place_els:
                    pid = el.get("id")
                    parent_el = el.find("parent_id")
                    parent_id = parent_el.get("id") if parent_el is not None else None
                    if parent_id and parent_id in place_map:
                        place_map[pid].parent_id = parent_id

                await session.flush()

            # --- Families ---
            families_root = root.find("families")
            family_map: dict[str, Family] = {}
            if families_root is not None:
                for el in families_root.findall("family"):
                    fid = el.get("id")
                    family = Family(
                        id=fid,
                        name=el.get("name", ""),
                        male_surname=el.get("ms"),
                        female_surname=el.get("fs"),
                    )
                    session.add(family)
                    family_map[fid] = family

                await session.flush()

            # --- Events ---
            events_root = root.find("events")
            event_map: dict[str, Event] = {}
            if events_root is not None:
                for el in events_root.findall("event"):
                    eid = el.get("id")
                    place_el = el.find("place")
                    place_id = place_el.get("id") if place_el is not None else None
                    event = Event(
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
                    session.add(event)
                    event_map[eid] = event

                await session.flush()

            # --- Persons ---
            persons_root = root.find("persons")
            if persons_root is None:
                return

            person_elements = persons_root.findall("person")
            persons_in_xml: dict[str, etree._Element] = {}

            # 1-й проход: создаём Person
            for el in person_elements:
                pid = el.get("id")
                persons_in_xml[pid] = el

                family_el = el.find("family")
                family_id = family_el.get("id") if family_el is not None else None

                biography = el.findtext("comment") or None

                # места
                place_el = el.find("place")          # основное
                bplace_el = el.find("bplace")        # место рождения
                dplace_el = el.find("dplace")        # место смерти

                person = Person(
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
                )
                session.add(person)

            # сбросить pending-объекты в БД, чтобы FK работали
            await session.flush()

            # --- Documents (фото) ---
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
                        if pid and pid in persons_in_xml:
                            person = await session.get(Person, pid)
                            if person is not None:
                                person.photo = photo_path

            # 2-й проход: events (person_event) и relations (nearest)
            for pid, el in persons_in_xml.items():
                # --- events ---
                events_el = el.find("events")
                if events_el is not None:
                    for event_el in events_el.findall("event"):
                        eid = event_el.get("id")
                        role = event_el.get("role", "")
                        if eid and eid in event_map:
                            await session.execute(
                                person_event_table.insert().values(
                                    person_id=pid, event_id=eid, role=role
                                )
                            )

                # --- nearest / relations ---
                nearest_el = el.find("nearest")
                if nearest_el is not None:
                    await _process_nearest(session, pid, nearest_el, persons_in_xml)


async def _process_nearest(
    session: AsyncSession,
    person_id: str,
    nearest_el: etree._Element,
    persons_in_xml: dict[str, etree._Element],
):
    """Обрабатывает <nearest> — строит связи person_relations."""

    async def _add_relation(pid_a: str, pid_b: str, relcode: str, label: str):
        """Добавляет двунаправленную связь."""
        if pid_a == pid_b:
            return
        for p1, p2, rcode, rlabel in [
            (pid_a, pid_b, relcode, label),
        ]:
            exists = await session.execute(
                select(person_relation_table).where(
                    person_relation_table.c.person_id == p1,
                    person_relation_table.c.related_person_id == p2,
                )
            )
            if not exists.first():
                await session.execute(
                    person_relation_table.insert().values(
                        person_id=p1, related_person_id=p2,
                        relation_type=rcode, relation_label=rlabel,
                    )
                )

    for rel_person_el in nearest_el.findall("person"):
        rel_person_id = rel_person_el.get("id")
        if not rel_person_id or rel_person_id not in persons_in_xml:
            continue

        relcode = rel_person_el.get("relcode", "")
        label = rel_person_el.get("rel", "")

        # Прямая связь
        await _add_relation(person_id, rel_person_id, relcode, label)

        # Родительские relcode: F (отец), M (мать) — у потомка relcode будет S (сын) или D (дочь)
        if relcode in ("F", "M"):
            child_sex = persons_in_xml[person_id].get("sex")
            child_relcode = "S" if _parse_sex(child_sex) is True else "D"
            child_label = "Сын" if child_relcode == "S" else "Дочь"
            await _add_relation(rel_person_id, person_id, child_relcode, child_label)

        # Супружеские relcode: B (жена), A (муж)
        elif relcode in ("B", "A"):
            spouse_relcode = "A" if relcode == "B" else "B"
            spouse_label = "Муж" if spouse_relcode == "A" else "Жена"
            await _add_relation(rel_person_id, person_id, spouse_relcode, spouse_label)

            # --- Дети внутри супружеской пары ---
            for child_el in rel_person_el.findall("person"):
                child_id = child_el.get("id")
                if not child_id or child_id not in persons_in_xml:
                    continue
                child_sex = persons_in_xml[child_id].get("sex")
                child_relcode = "S" if _parse_sex(child_sex) is True else "D"
                child_label = "Сын" if child_relcode == "S" else "Дочь"

                # связь: отец -> ребёнок
                await _add_relation(person_id, child_id, child_relcode, child_label)
                # связь: мать -> ребёнок
                await _add_relation(rel_person_id, child_id, child_relcode, child_label)
                # связь: ребёнок -> отец
                await _add_relation(child_id, person_id, "F", "Отец")
                # связь: ребёнок -> мать
                await _add_relation(child_id, rel_person_id, "M", "Мать")
