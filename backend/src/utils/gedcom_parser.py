import hashlib
import os
import re

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import *
from src.repositories.SQLAlchemyRepositories import *


class GedcomParser:
    MONTHS_GENITIVE = {
        "JAN": "января", "FEB": "февраля", "MAR": "марта",
        "APR": "апреля", "MAY": "мая", "JUN": "июня",
        "JUL": "июля", "AUG": "августа", "SEP": "сентября",
        "OCT": "октября", "NOV": "ноября", "DEC": "декабря",
    }
    MONTHS_NOMINATIVE = {
        "JAN": "январь", "FEB": "февраль", "MAR": "март",
        "APR": "апрель", "MAY": "май", "JUN": "июнь",
        "JUL": "июль", "AUG": "август", "SEP": "сентябрь",
        "OCT": "октябрь", "NOV": "ноябрь", "DEC": "декабрь",
    }

    __GEDCOM_LINE_RE = re.compile(
        r"^(\d+)\s+(?:@([^@]+)@\s+)?(\w+)\s*(.*)"
    )

    class __GedLine:
        def __init__(self, level: int, xref: str | None, tag: str, value: str):
            self.level = level
            self.xref = xref
            self.tag = tag
            self.value = value

    class __GedRecord:
        def __init__(self, xref: str | None, tag: str, value: str = ""):
            self.xref = xref
            self.tag = tag
            self.value = value
            self.children: list = []

        def find(self, tag: str):
            for c in self.children:
                if c.tag == tag:
                    return c
            return None

        def find_all(self, tag: str) -> list:
            return [c for c in self.children if c.tag == tag]

        def find_value(self, tag: str) -> str | None:
            r = self.find(tag)
            return r.value.strip() if r and r.value else None

        def collect_text(self, tag: str) -> str | None:
            parts = []
            main = self.find(tag)
            if main is None:
                return None
            parts.append(main.value or "")
            for c in main.children:
                if c.tag == "CONT":
                    parts.append("\n" + (c.value or ""))
                elif c.tag == "CONC":
                    if parts:
                        parts[-1] += c.value or ""
                    else:
                        parts.append(c.value or "")
            return "".join(parts).strip() or None

    async def parse_and_save(self, session: AsyncSession, ged_text: str) -> str:
        records = self.__parse_gedcom(ged_text)

        indis: dict = {}
        fams: dict = {}
        for rec in records:
            if rec.tag == "INDI" and rec.xref:
                indis[rec.xref] = rec
            elif rec.tag == "FAM" and rec.xref:
                fams[rec.xref] = rec

        places_set: dict[str, str] = {}
        self.__collect_places(indis, fams, places_set)

        places_list = [
            PlaceTable(id=pid, full_name=name, name=name)
            for pid, name in places_set.items()
        ]

        families_list = []
        for fid, fam_rec in fams.items():
            husb_ref = self.__strip_xref(fam_rec.find_value("HUSB"))
            wife_ref = self.__strip_xref(fam_rec.find_value("WIFE"))
            ms = ""
            fs = ""
            if husb_ref and husb_ref in indis:
                ms = self.__extract_surname(indis[husb_ref])
            if wife_ref and wife_ref in indis:
                fs = self.__extract_surname(indis[wife_ref])
            name = f"{ms} / {fs}".strip(" /") or f"Семья {fid}"
            families_list.append(FamilyTable(
                id=fid,
                name=name,
                male_surname=ms or None,
                female_surname=fs or None,
            ))

        event_list: list[EventTable] = []
        event_map: dict[str, EventTable] = {}
        event_counter = 0

        def __make_event(
            typ: str, date_raw: str | None, plac: str | None,
            desc: str | None = None,
        ) -> EventTable:
            nonlocal event_counter
            event_counter += 1
            eid = f"GE{event_counter}"
            dt = self.__convert_date(date_raw)
            pl_id = self.__place_id(plac) if plac else None
            ev = EventTable(
                id=eid,
                type=typ,
                date=dt,
                date_sort=self.__parse_year(dt),
                description=desc,
                place_id=pl_id,
            )
            event_list.append(ev)
            event_map[eid] = ev
            return ev

        for pid, indi in indis.items():
            birt = indi.find("BIRT")
            if birt:
                bp = self.__place_from_children(birt)
                __make_event("Рождение", birt.find_value("DATE"), bp)

            deat = indi.find("DEAT")
            if deat:
                dp = self.__place_from_children(deat)
                cause = deat.find_value("CAUS")
                __make_event("Смерть", deat.find_value("DATE"), dp, cause)

        for fid, fam in fams.items():
            marr = fam.find("MARR")
            if marr:
                mp = self.__place_from_children(marr)
                __make_event("Брак", marr.find_value("DATE"), mp)

        persons_list = []
        person_event_list = []

        for pid, indi in indis.items():
            surname, first_name, middle_name, full_name = self.__parse_name(
                indi.find_value("NAME") or ""
            )
            maiden = indi.find_value("_MARNM") or ""
            biography = indi.collect_text("NOTE")
            photo = self.__get_photo(indi)

            place_id = self.__place_from_children(indi.find("RESI"))
            bplace_id = self.__place_from_children(indi.find("BIRT"))
            dplace_id = self.__place_from_children(indi.find("DEAT"))

            fams_list = indi.find_all("FAMS")
            family_id = self.__strip_xref(fams_list[0].value) if fams_list else None

            birt = indi.find("BIRT")
            deat = indi.find("DEAT")
            bdate = self.__convert_date(birt.find_value("DATE")) if birt else None
            ddate = self.__convert_date(deat.find_value("DATE")) if deat else None
            dreason = deat.find_value("CAUS") if deat else None

            person = PersonTable(
                id=pid,
                sex=self.__parse_sex(indi.find_value("SEX")),
                surname=surname or None,
                maiden_surname=maiden or None,
                first_name=first_name or None,
                middle_name=middle_name or None,
                full_name=full_name,
                occupation=indi.find_value("OCCU") or None,
                birth_date=bdate,
                death_date=ddate,
                death_reason=dreason,
                lifespan=indi.find_value("AGE") or None,
                is_favorite=False,
                biography=biography,
                photo=photo,
                place_id=places_set.get(place_id) and place_id or None,
                birth_place_id=places_set.get(bplace_id) and bplace_id or None,
                death_place_id=places_set.get(dplace_id) and dplace_id or None,
                family_id=family_id,
            )
            persons_list.append(person)

            if birt:
                dt = self.__convert_date(birt.find_value("DATE"))
                bp = self.__place_from_children(birt)
                ev = self.__find_event(event_list, "Рождение", dt, bp)
                if ev:
                    ev.person_id = pid
                    person_event_list.append(PersonEventTable(
                        person_id=pid, event_id=ev.id,
                        role="Родился" if person.sex is True else "Родилась",
                    ))
            if deat:
                dt = self.__convert_date(deat.find_value("DATE"))
                dp = self.__place_from_children(deat)
                ev = self.__find_event(event_list, "Смерть", dt, dp)
                if ev:
                    ev.person_id = pid
                    person_event_list.append(PersonEventTable(
                        person_id=pid, event_id=ev.id,
                        role="Умер" if person.sex is True else "Умерла",
                    ))

        for ev in event_list:
            if ev.place_id and ev.place_id not in places_set:
                places_set[ev.place_id] = f"Место {ev.place_id}"
        for p in persons_list:
            for pid_attr in ("place_id", "birth_place_id", "death_place_id"):
                val = getattr(p, pid_attr, None)
                if val and val not in places_set:
                    places_set[val] = f"Место {val}"

        places_list = [
            PlaceTable(id=pid, full_name=name, name=name)
            for pid, name in places_set.items()
        ]

        relations_list: list[PersonRelationTable] = []
        relations_seen: set[tuple[str, str]] = set()

        def __add_rel(a: str, b: str, rtype: str, rlabel: str) -> None:
            if a == b:
                return
            key = (a, b)
            if key in relations_seen:
                return
            relations_seen.add(key)
            relations_list.append(PersonRelationTable(
                person_id=a, related_person_id=b,
                relation_type=rtype, relation_label=rlabel,
            ))

        for fid, fam in fams.items():
            husb = self.__strip_xref(fam.find_value("HUSB"))
            wife = self.__strip_xref(fam.find_value("WIFE"))
            children = [self.__strip_xref(c.value) for c in fam.find_all("CHIL")]

            if husb and wife:
                __add_rel(husb, wife, "A", "Муж")
                __add_rel(wife, husb, "B", "Жена")

            for child in children:
                if not child or child not in indis:
                    continue
                child_sex = self.__parse_sex(indis[child].find_value("SEX"))
                if husb:
                    __add_rel(husb, child, "S" if child_sex is True else "D",
                              "Сын" if child_sex is True else "Дочь")
                    __add_rel(child, husb, "F", "Отец")
                if wife:
                    __add_rel(wife, child, "S" if child_sex is True else "D",
                              "Сын" if child_sex is True else "Дочь")
                    __add_rel(child, wife, "M", "Мать")

        async with session.begin():
            await PlaceRepository(session).rewrite(places_list)
            await FamilyRepository(session).rewrite(families_list)
            await PersonRepository(session).rewrite(persons_list)
            await EventRepository(session).rewrite(event_list)
            await PersonEventRepository(session).rewrite(person_event_list)
            await PersonRelationRepository(session).rewrite(relations_list)

        return f"GEDCOM: {len(indis)} человек, {len(fams)} семей"

    def __parse_gedcom(self, text: str) -> list:
        lines = text.splitlines()
        parsed_lines = []
        for line in lines:
            m = self.__GEDCOM_LINE_RE.match(line)
            if not m:
                continue
            level = int(m.group(1))
            xref = m.group(2)
            tag = m.group(3)
            value = m.group(4)
            parsed_lines.append(self.__GedLine(level, xref, tag, value))

        stack = []
        top_records = []
        for gl in parsed_lines:
            rec = self.__GedRecord(xref=gl.xref, tag=gl.tag, value=gl.value)
            if gl.level == 0:
                top_records.append(rec)
                stack = [rec]
            else:
                while len(stack) > gl.level:
                    stack.pop()
                if stack:
                    stack[-1].children.append(rec)
                else:
                    top_records.append(rec)
                stack.append(rec)
                while len(stack) > gl.level + 1:
                    stack.pop()
        return top_records

    def __convert_date(self, raw: str | None) -> str | None:
        if not raw:
            return None
        date = re.sub(r"@#\w+@\s*", "", raw).strip()
        if not date:
            return None

        m = re.match(r"FROM\s+(.+)\s+TO\s+(.+)", date, re.IGNORECASE)
        if m:
            start = self.__convert_single_date(m.group(1).strip())
            end = self.__convert_single_date(m.group(2).strip())
            return f"с {start} по {end}"

        m = re.match(r"BET\s+(.+)\s+AND\s+(.+)", date, re.IGNORECASE)
        if m:
            start = self.__convert_single_date(m.group(1).strip())
            end = self.__convert_single_date(m.group(2).strip())
            return f"между {start} и {end}"

        prefix_map = {
            "BEF": "до", "AFT": "после", "ABT": "около",
            "EST": "примерно", "CAL": "ориентировочно",
            "INT": "интерпретировано",
        }
        for prefix, ru_prefix in prefix_map.items():
            if date.upper().startswith(prefix):
                rest = date[len(prefix):].strip()
                return f"{ru_prefix} {self.__convert_single_date(rest)}"

        return self.__convert_single_date(date)

    def __convert_single_date(self, date_part: str) -> str:
        parts = date_part.split()
        if len(parts) == 3:
            day, month, year = parts
            ru_month = self.MONTHS_GENITIVE.get(month.upper(), month)
            return f"{day} {ru_month} {year}"
        if len(parts) == 2:
            month, year = parts
            ru_month = self.MONTHS_NOMINATIVE.get(month.upper(), month)
            return f"{ru_month} {year}"
        return date_part

    @staticmethod
    def __place_id(name: str) -> str:
        return "P" + hashlib.md5(name.encode()).hexdigest()[:12]

    @staticmethod
    def __parse_sex(raw: str | None) -> bool | None:
        if raw == "M":
            return True
        if raw == "F":
            return False
        return None

    @staticmethod
    def __parse_year(date_str: str | None) -> int | None:
        if not date_str:
            return None
        m = re.search(r"\b(\d{4})\b", date_str)
        return int(m.group(1)) if m else None

    @staticmethod
    def __parse_name(name_line: str) -> tuple[str, str, str, str]:
        m = re.search(r"/([^/]*)/", name_line)
        surname = m.group(1).strip() if m else ""

        given = re.sub(r"/\s*[^/]*\s*/", "", name_line).strip()
        parts = given.split()
        first_name = parts[0] if parts else ""
        middle_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        full_name = f"{given} {surname}".strip() if surname else given
        return surname, first_name, middle_name, full_name

    @staticmethod
    def __get_photo(indi) -> str | None:
        obje_list = indi.find_all("OBJE")
        if not obje_list:
            return None
        for obje in obje_list:
            if obje.find("_PRIM") and obje.find("_PRIM").value.strip().upper() == "Y":
                file_rec = obje.find("FILE")
                if file_rec and file_rec.value:
                    return os.path.basename(file_rec.value.strip())
        file_rec = obje_list[0].find("FILE")
        return os.path.basename(file_rec.value.strip()) if file_rec and file_rec.value else None

    @staticmethod
    def __strip_xref(val: str | None) -> str | None:
        if not val:
            return None
        val = val.strip()
        if val.startswith("@") and val.endswith("@"):
            return val[1:-1]
        return val if val else None

    @staticmethod
    def __extract_surname(indi) -> str:
        name_val = indi.find_value("NAME")
        if not name_val:
            return ""
        m = re.search(r"/([^/]*)/", name_val)
        return m.group(1).strip() if m else ""

    def __collect_places(self, indis: dict, fams: dict, out: dict[str, str]) -> None:
        for indi in indis.values():
            for tag in ("BIRT", "DEAT", "RESI"):
                rec = indi.find(tag)
                if rec is None:
                    continue
                plac = rec.find("PLAC")
                if plac and plac.value:
                    name = plac.value.strip()
                    pid = self.__place_id(name)
                    if pid not in out:
                        out[pid] = name
        for fam in fams.values():
            marr = fam.find("MARR")
            if marr is None:
                continue
            plac = marr.find("PLAC")
            if plac and plac.value:
                name = plac.value.strip()
                pid = self.__place_id(name)
                if pid not in out:
                    out[pid] = name

    def __place_from_children(self, rec) -> str | None:
        if rec is None:
            return None
        plac = rec.find("PLAC")
        if plac and plac.value:
            name = plac.value.strip()
            return self.__place_id(name)
        return None

    @staticmethod
    def __find_event(
        events: list[EventTable], typ: str, date: str | None,
        place_id: str | None,
    ) -> EventTable | None:
        for ev in events:
            if ev.type == typ and ev.date == date and ev.place_id == place_id:
                return ev
        return None
