import re
from typing import Any

from lxml import etree
from lxml.etree import _Element
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import *

from src.repositories.SQLAlchemyRepositories import (
    EventRepository,
    FamilyRepository,
    PersonEventRepository,
    PersonRelationRepository,
    PersonRepository,
    PlaceRepository,
)


class XMLParser:
    async def parse_and_save(self, session: AsyncSession, xml_bytes: bytes) -> None:
        """Парсит XML и сохраняет всё в БД. Если данные уже есть — перезаписывает."""
        root = etree.fromstring(xml_bytes)

        places_list = self.__places_list_parse(root)
        families_list = self.__family_list_parse(root)
        event_list, event_map = self.__event_list_parse(root)
        persons_list, persons_in_xml = self.__person_list_parse(root)
        person_event_list, relations_list = (
            self.__person_events_and_relation_list_parse(event_map, persons_in_xml)
        )
        async with session.begin():
            await PlaceRepository(session).rewrite(places_list)
            await FamilyRepository(session).rewrite(families_list)
            await PersonRepository(session).rewrite(persons_list)
            await EventRepository(session).rewrite(event_list)
            await PersonEventRepository(session).rewrite(person_event_list)
            await PersonRelationRepository(session).rewrite(relations_list)

    def __person_events_and_relation_list_parse(
        self, event_map: dict[str, EventTable], persons_in_xml: dict[str, _Element]
    ) -> tuple[list[PersonEventTable], list[PersonRelationTable]]:
        person_event_list: list[PersonEventTable] = []
        relations_list: list[PersonRelationTable] = []
        relations_seen: set[tuple[str, str]] = set()

        for pid, el in persons_in_xml.items():
            events_el = el.find("events")
            if events_el is not None:
                for event_el in events_el.findall("event"):
                    eid = event_el.get("id")
                    role = event_el.get("role", "")
                    if eid and eid in event_map:
                        event_map[eid].person_id = pid
                        person_event_list.append(
                            PersonEventTable(person_id=pid, event_id=eid, role=role)
                        )

            nearest_el = el.find("nearest")
            if nearest_el is not None:
                self.__collect_relations(
                    relations_list, relations_seen, pid, nearest_el, persons_in_xml
                )
        return person_event_list, relations_list

    def __person_list_parse(
        self, root: type[_Element] | None | Any
    ) -> tuple[list[Any], dict[str, _Element]]:
        persons_in_xml: dict[str, _Element] = {}
        persons_root = root.find("persons")
        person_elements = persons_root.findall("person")
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
                sex=self.__parse_sex(el.get("sex")),
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
                birth_place_id=bplace_el.get("id")
                if bplace_el is not None
                else (place_el.get("id") if place_el is not None else None),
                death_place_id=dplace_el.get("id") if dplace_el is not None else None,
                family_id=family_id,
                photo=photo_map.get(pid),
            )
            persons_list.append(person)
        return persons_list, persons_in_xml

    def __event_list_parse(
        self, root: _Element
    ) -> tuple[list[EventTable], dict[str, EventTable]]:
        event_list: list[EventTable] = []
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
                date_sort=self.__extract_year(el.get("date")),
                description=(
                    (el.findtext("comment") or "")
                    + (" " + el.get("deathreason", "") if el.get("deathreason") else "")
                ).strip()
                or None,
                place_id=place_id,
            )
            event_map[eid] = event
            event_list.append(event)
        return event_list, event_map

    def __family_list_parse(self, root: _Element) -> list[FamilyTable]:
        families_list: list[FamilyTable] = []
        families_root = root.find("families")
        for el in families_root.findall("family"):
            fid = el.get("id")
            families_list.append(
                FamilyTable(
                    id=fid,
                    name=el.get("name", ""),
                    male_surname=el.get("ms"),
                    female_surname=el.get("fs"),
                )
            )
        return families_list

    def __places_list_parse(self, root: _Element) -> list[PlaceTable]:
        places_list: list[PlaceTable] = []
        all_place_els = list(root.find("places").findall("place"))
        for el in all_place_els:
            pid = el.get("id")
            lat, lon = self.__parse_coords(el.get("coords"))
            places_list.append(
                PlaceTable(
                    id=pid,
                    full_name=el.get("fullname", ""),
                    name=el.get("name"),
                    short_name=el.get("nameshort"),
                    latitude=lat,
                    longitude=lon,
                )
            )
        return places_list

    @staticmethod
    def __parse_coords(coords: str | None) -> tuple[float | None, float | None]:
        if not coords:
            return None, None
        try:
            parts = list(map(float, coords.split(",")))
            return parts[0], parts[1]
        except (ValueError, IndexError):
            return None, None

    @staticmethod
    def __extract_year(date_str: str | None) -> int | None:
        if not date_str:
            return None
        m = re.search(r"\b(\d{4})\b", date_str)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def __parse_sex(raw: str | None) -> bool | None:
        if raw == "М":
            return True
        if raw == "Ж":
            return False
        return None

    def __collect_relations(
        self,
        relations_list: list[PersonRelationTable],
        seen: set[tuple[str, str]],
        person_id: str,
        nearest_el: _Element,
        persons_in_xml: dict[str, _Element],
    ) -> None:
        """Собирает связи из <nearest> в общий список (без проверок БД)."""

        def _add_relation(pid_a: str, pid_b: str, relcode: str, label: str) -> None:
            if pid_a == pid_b:
                return
            key = (pid_a, pid_b)
            if key in seen:
                return
            seen.add(key)
            relations_list.append(
                PersonRelationTable(
                    person_id=pid_a,
                    related_person_id=pid_b,
                    relation_type=relcode,
                    relation_label=label,
                )
            )

        for rel_person_el in nearest_el.findall("person"):
            rel_person_id = rel_person_el.get("id")
            if not rel_person_id or rel_person_id not in persons_in_xml:
                continue

            relcode = rel_person_el.get("relcode", "")
            label = rel_person_el.get("rel", "")

            _add_relation(person_id, rel_person_id, relcode, label)

            if relcode in ("F", "M"):
                child_sex = persons_in_xml[person_id].get("sex")
                child_relcode = "S" if self.__parse_sex(child_sex) is True else "D"
                child_label = "Сын" if child_relcode == "S" else "Дочь"
                _add_relation(rel_person_id, person_id, child_relcode, child_label)

            elif relcode in ("B", "A"):
                spouse_relcode = "A" if relcode == "B" else "B"
                spouse_label = "Муж" if spouse_relcode == "A" else "Жена"
                _add_relation(rel_person_id, person_id, spouse_relcode, spouse_label)

                for child_el in rel_person_el.findall("person"):
                    child_id = child_el.get("id")
                    if not child_id or child_id not in persons_in_xml:
                        continue
                    child_sex = persons_in_xml[child_id].get("sex")
                    child_relcode = "S" if self.__parse_sex(child_sex) is True else "D"
                    child_label = "Сын" if child_relcode == "S" else "Дочь"

                    _add_relation(person_id, child_id, child_relcode, child_label)
                    _add_relation(rel_person_id, child_id, child_relcode, child_label)
                    _add_relation(child_id, person_id, "F", "Отец")
                    _add_relation(child_id, rel_person_id, "M", "Мать")
