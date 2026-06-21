import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from src.db.tables import *
from src.repositories.SQLAlchemyRepositories import *


# ─── GEDCOM record types ────────────────────────────────────────────────


@dataclass
class GedLine:
    level: int
    xref: str | None
    tag: str
    value: str


@dataclass
class GedRecord:
    xref: str | None
    tag: str
    value: str = ""
    children: list["GedRecord"] = field(default_factory=list)

    def find(self, tag: str) -> Optional["GedRecord"]:
        for c in self.children:
            if c.tag == tag:
                return c
        return None

    def find_all(self, tag: str) -> list["GedRecord"]:
        return [c for c in self.children if c.tag == tag]

    def find_value(self, tag: str) -> str | None:
        r = self.find(tag)
        return r.value.strip() if r and r.value else None

    def collect_text(self, tag: str) -> str | None:
        """Собирает текст тэга вместе с CONT / CONC строками."""
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


# ─── Парсинг текста GEDCOM ──────────────────────────────────────────────

GEDCOM_LINE_RE = re.compile(
    r"^(\d+)\s+(?:@([^@]+)@\s+)?(\w+)\s*(.*)"
)


def _parse_gedcom(text: str) -> list[GedRecord]:
    lines = text.splitlines()
    parsed_lines: list[GedLine] = []
    for line in lines:
        m = GEDCOM_LINE_RE.match(line)
        if not m:
            continue
        level = int(m.group(1))
        xref = m.group(2)
        tag = m.group(3)
        value = m.group(4)
        parsed_lines.append(GedLine(level, xref, tag, value))

    # Stack-based tree building
    stack: list[GedRecord] = []
    top_records: list[GedRecord] = []
    for gl in parsed_lines:
        rec = GedRecord(xref=gl.xref, tag=gl.tag, value=gl.value)
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
            # keep stack at correct depth for subsequent sibling lines
            while len(stack) > gl.level + 1:
                stack.pop()

    return top_records


# ─── Утилиты ────────────────────────────────────────────────────────────


def _place_id(name: str) -> str:
    return "P" + hashlib.md5(name.encode()).hexdigest()[:12]


def _parse_sex(raw: str | None) -> bool | None:
    if raw == "M":
        return True
    if raw == "F":
        return False
    return None


def _parse_year(date_str: str | None) -> int | None:
    if not date_str:
        return None
    m = re.search(r"\b(\d{4})\b", date_str)
    return int(m.group(1)) if m else None


def _clean_ged_date(raw: str | None) -> str | None:
    """Убирает @#DJULIAN@ и т.п. префиксы из даты."""
    if not raw:
        return None
    cleaned = re.sub(r"@#\w+@\s*", "", raw).strip()
    return cleaned or None


def _parse_name(name_line: str) -> tuple[str, str, str, str]:
    """Парсит NAME: 'John William /Smith/' -> (surname, first_name, middle_name, full_name)"""
    m = re.search(r"/([^/]*)/", name_line)
    surname = m.group(1).strip() if m else ""

    given = re.sub(r"/\s*[^/]*\s*/", "", name_line).strip()
    parts = given.split()
    first_name = parts[0] if parts else ""
    middle_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    full_name = f"{given} {surname}".strip() if surname else given
    return surname, first_name, middle_name, full_name


def _get_photo(indi: GedRecord) -> str | None:
    """Выбирает основное фото (с _PRIM Y или первое)."""
    obje_list = indi.find_all("OBJE")
    if not obje_list:
        return None
    # Сначала ищем с _PRIM Y
    for obje in obje_list:
        if obje.find("_PRIM") and obje.find("_PRIM").value.strip().upper() == "Y":
            file_rec = obje.find("FILE")
            if file_rec and file_rec.value:
                return os.path.basename(file_rec.value.strip())
    # fallback — первое
    file_rec = obje_list[0].find("FILE")
    return os.path.basename(file_rec.value.strip()) if file_rec and file_rec.value else None


# ─── Основной парсер ────────────────────────────────────────────────────


async def parse_and_save_gedcom(ged_text: str) -> str:
    """Парсит GEDCOM-текст и перезаписывает данные в БД."""
    records = _parse_gedcom(ged_text)

    # Разделяем на INDI, FAM и т.д.
    indis: dict[str, GedRecord] = {}
    fams: dict[str, GedRecord] = {}
    for rec in records:
        if rec.tag == "INDI" and rec.xref:
            indis[rec.xref] = rec
        elif rec.tag == "FAM" and rec.xref:
            fams[rec.xref] = rec

    # ─── Places ───
    places_set: dict[str, str] = {}  # id -> full_name
    collect_places(indis, fams, places_set)

    places_list = [
        PlaceTable(id=pid, full_name=name, name=name)
        for pid, name in places_set.items()
    ]

    # ─── Families ───
    families_list = []
    for fid, fam_rec in fams.items():
        husb_ref = strip_xref(fam_rec.find_value("HUSB"))
        wife_ref = strip_xref(fam_rec.find_value("WIFE"))
        ms = ""
        fs = ""
        if husb_ref and husb_ref in indis:
            ms = extract_surname(indis[husb_ref])
        if wife_ref and wife_ref in indis:
            fs = extract_surname(indis[wife_ref])
        name = f"{ms} / {fs}".strip(" /") or f"Семья {fid}"
        families_list.append(FamilyTable(
            id=fid,
            name=name,
            male_surname=ms or None,
            female_surname=fs or None,
        ))

    # ─── Events ───
    event_list = []
    event_map: dict[str, EventTable] = {}
    event_counter = 0

    def _make_event(typ: str, date_raw: str | None, plac: str | None,
                    desc: str | None = None, role: str = "") -> EventTable:
        nonlocal event_counter
        event_counter += 1
        eid = f"GE{event_counter}"
        dt = _clean_ged_date(date_raw)
        pl_id = _place_id(plac) if plac else None
        ev = EventTable(
            id=eid,
            type=typ,
            date=dt,
            date_sort=_parse_year(dt),
            description=desc,
            place_id=pl_id,
        )
        event_list.append(ev)
        # Дополнительно сохраняем роль для привязки к человеку
        ev._role = role  # type: ignore[attr-defined]
        event_map[eid] = ev
        return ev

    for pid, indi in indis.items():
        # BIRT
        birt = indi.find("BIRT")
        if birt:
            bp = place_from_children(birt)
            _make_event("Рождение", birt.find_value("DATE"), bp)

        # DEAT
        deat = indi.find("DEAT")
        if deat:
            dp = place_from_children(deat)
            cause = deat.find_value("CAUS")
            _make_event("Смерть", deat.find_value("DATE"), dp, cause)

    # События брака из FAM
    for fid, fam in fams.items():
        marr = fam.find("MARR")
        if marr:
            mp = place_from_children(marr)
            _make_event("Брак", marr.find_value("DATE"), mp)

    # ─── Persons ───
    persons_list = []
    person_event_list = []

    for pid, indi in indis.items():
        surname, first_name, middle_name, full_name = _parse_name(
            indi.find_value("NAME") or ""
        )
        maiden = indi.find_value("_MARNM") or ""
        biography = indi.collect_text("NOTE")
        photo = _get_photo(indi)

        # Places
        place_id = place_from_children(indi.find("RESI"))
        bplace_id = place_from_children(indi.find("BIRT"))
        dplace_id = place_from_children(indi.find("DEAT"))

        # Family (as spouse — FAMS)
        fams_list = indi.find_all("FAMS")
        family_id = strip_xref(fams_list[0].value) if fams_list else None

        # Dates
        birt = indi.find("BIRT")
        deat = indi.find("DEAT")
        bdate = _clean_ged_date(birt.find_value("DATE")) if birt else None
        ddate = _clean_ged_date(deat.find_value("DATE")) if deat else None
        dreason = deat.find_value("CAUS") if deat else None

        person = PersonTable(
            id=pid,
            sex=_parse_sex(indi.find_value("SEX")),
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

        # Person-Events
        if birt:
            dt = _clean_ged_date(birt.find_value("DATE"))
            bp = place_from_children(birt)
            ev = find_event(event_list, "Рождение", dt, bp)
            if ev:
                person_event_list.append(PersonEventTable(
                    person_id=pid, event_id=ev.id, role="Родился" if person.sex is True else "Родилась"
                ))
        if deat:
            dt = _clean_ged_date(deat.find_value("DATE"))
            dp = place_from_children(deat)
            ev = find_event(event_list, "Смерть", dt, dp)
            if ev:
                person_event_list.append(PersonEventTable(
                    person_id=pid, event_id=ev.id, role="Умер" if person.sex is True else "Умерла"
                ))

    # --- Гарантируем, что все place_id из событий и персон есть в places_set ---
    for ev in event_list:
        if ev.place_id and ev.place_id not in places_set:
            places_set[ev.place_id] = f"Место {ev.place_id}"
    for p in persons_list:
        for pid_attr in ("place_id", "birth_place_id", "death_place_id"):
            pid = getattr(p, pid_attr, None)
            if pid and pid not in places_set:
                places_set[pid] = f"Место {pid}"

    # Пересоздаём places_list с учётом добавленных
    places_list = [
        PlaceTable(id=pid, full_name=name, name=name)
        for pid, name in places_set.items()
    ]

    # ─── Relations ───
    relations_list = []
    relations_seen: set[tuple[str, str]] = set()

    def _add_rel(a: str, b: str, rtype: str, rlabel: str):
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
        husb = strip_xref(fam.find_value("HUSB"))
        wife = strip_xref(fam.find_value("WIFE"))
        children = [strip_xref(c.value) for c in fam.find_all("CHIL")]

        # Супруги
        if husb and wife:
            _add_rel(husb, wife, "A", "Муж")
            _add_rel(wife, husb, "B", "Жена")

        # Родители → дети
        for child in children:
            if not child or child not in indis:
                continue
            child_sex = _parse_sex(indis[child].find_value("SEX"))
            if husb:
                _add_rel(husb, child, "S" if child_sex is True else "D",
                         "Сын" if child_sex is True else "Дочь")
                _add_rel(child, husb, "F", "Отец")
            if wife:
                _add_rel(wife, child, "S" if child_sex is True else "D",
                         "Сын" if child_sex is True else "Дочь")
                _add_rel(child, wife, "M", "Мать")

    # ─── Запись в БД ───
    await PlaceRepository().rewrite(places_list)
    await FamilyRepository().rewrite(families_list)
    await EventRepository().rewrite(event_list)
    await PersonRepository().rewrite(persons_list)
    await PersonEventRepository().rewrite(person_event_list)
    await PersonRelationRepository().rewrite(relations_list)

    return f"GEDCOM: {len(indis)} человек, {len(fams)} семей"


# ─── Вспомогательные функции ────────────────────────────────────────────


def strip_xref(val: str | None) -> str | None:
    if not val:
        return None
    val = val.strip()
    if val.startswith("@") and val.endswith("@"):
        return val[1:-1]
    return val if val else None


def extract_surname(indi: GedRecord) -> str:
    name_val = indi.find_value("NAME")
    if not name_val:
        return ""
    m = re.search(r"/([^/]*)/", name_val)
    return m.group(1).strip() if m else ""


def collect_places(indis: dict[str, GedRecord], fams: dict[str, GedRecord], out: dict[str, str]):
    """Собирает уникальные места из INDI и FAM записей."""
    for indi in indis.values():
        for tag in ("BIRT", "DEAT", "RESI"):
            rec = indi.find(tag)
            if rec is None:
                continue
            plac = rec.find("PLAC")
            if plac and plac.value:
                name = plac.value.strip()
                pid = _place_id(name)
                if pid not in out:
                    out[pid] = name
    for fam in fams.values():
        marr = fam.find("MARR")
        if marr is None:
            continue
        plac = marr.find("PLAC")
        if plac and plac.value:
            name = plac.value.strip()
            pid = _place_id(name)
            if pid not in out:
                out[pid] = name


def place_from_children(rec: GedRecord | None) -> str | None:
    """Достаёт place_id из PLAC внутри события."""
    if rec is None:
        return None
    plac = rec.find("PLAC")
    if plac and plac.value:
        name = plac.value.strip()
        return _place_id(name)
    return None


def find_event(events: list[EventTable], typ: str, date: str | None,
               place_id: str | None) -> EventTable | None:
    """Ищет событие по типу, дате и месту."""
    for ev in events:
        if ev.type == typ and ev.date == date and ev.place_id == place_id:
            return ev
    return None
