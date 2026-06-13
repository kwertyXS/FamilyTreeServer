# Схема базы данных

PostgreSQL, ORM — SQLAlchemy.

## Таблицы

### `persons`

| Поле | Тип | XML-атрибут | Описание |
|------|-----|-------------|----------|
| `id` | `String PK` | `id` | Уникальный ID из XML |
| `sex` | `Boolean?` | `sex` | `true` — мужчина, `false` — женщина, `null` — не указан |
| `surname` | `String?` | `sn` | Фамилия |
| `maiden_surname` | `String?` | `msn` | Девичья фамилия |
| `first_name` | `String?` | `fn` | Имя |
| `middle_name` | `String?` | `mn` | Отчество |
| `full_name` | `String` | `fullname` | Полное имя (обязательно) |
| `occupation` | `String?` | `occu` | Занятие / профессия |
| `birth_date` | `String?` | `bdate` | Дата рождения (сырая строка) |
| `death_date` | `String?` | `ddate` | Дата смерти |
| `death_reason` | `String?` | `dreason` | Причина смерти |
| `lifespan` | `String?` | `lifespan` | Срок жизни |
| `is_favorite` | `Boolean` | `fav` | Избранный (`"1"` — да) |
| `biography` | `Text?` | `comment` | Биография |
| `photo` | `String?` | `<document path>` | Путь к файлу фото |
| `birth_place_id` | `FK → places.id` | `bplace` / `place` | Место рождения |
| `death_place_id` | `FK → places.id` | `dplace` | Место смерти |
| `place_id` | `FK → places.id` | `place` | Основное место |
| `family_id` | `FK → families.id` | `family` | Семья |

### `places`

| Поле | Тип | XML-атрибут | Описание |
|------|-----|-------------|----------|
| `id` | `String PK` | `id` | Уникальный ID |
| `full_name` | `String` | `fullname` | Полное название |
| `name` | `String?` | `name` | Краткое название |
| `short_name` | `String?` | `nameshort` | Сокращение |
| `latitude` | `Float?` | `coords` | Широта |
| `longitude` | `Float?` | `coords` | Долгота |
| `parent_id` | `FK → places.id` | `parent_id` | Родительское место |

### `events`

| Поле | Тип | XML-атрибут | Описание |
|------|-----|-------------|----------|
| `id` | `String PK` | `id` | Уникальный ID |
| `type` | `String` | `type` | Тип (Рождение, Свадьба, Смерть…) |
| `date` | `String?` | `date` | Дата (сырая строка) |
| `date_sort` | `Integer?` | — | Год для сортировки (извлечён из `date`) |
| `description` | `Text?` | `comment` + `deathreason` | Описание |
| `place_id` | `FK → places.id` | `place` | Место события |

### `families`

| Поле | Тип | XML-атрибут | Описание |
|------|-----|-------------|----------|
| `id` | `String PK` | `id` | Уникальный ID |
| `name` | `String` | `name` | Название семьи |
| `male_surname` | `String?` | `ms` | Фамилия по мужской линии |
| `female_surname` | `String?` | `fs` | Фамилия по женской линии |

### `person_events` (связь M:N)

| Поле | Тип | Описание |
|------|-----|----------|
| `person_id` | `FK → persons.id` | Персона |
| `event_id` | `FK → events.id` | Событие |
| `role` | `String` | Роль персоны в событии |

### `person_relations` (связь M:N)

| Поле | Тип | Описание |
|------|-----|----------|
| `person_id` | `FK → persons.id` | Персона |
| `related_person_id` | `FK → persons.id` | Связанная персона |
| `relation_type` | `String` | relcode (F, M, S, D, A, B, FS, FD…) |
| `relation_label` | `String` | Человекочитаемая метка (Отец, Мать, Сын…) |

#### Коды связей (`relation_type`)

| Код | Значение |
|-----|----------|
| `F` | Отец |
| `M` | Мать |
| `S` | Сын |
| `D` | Дочь |
| `A` | Муж |
| `B` | Жена |
| `FS` | Сестра (по отцу) |
| `FD` | Брат (по отцу) |
| `MS` | Сестра (по матери) |
| `MD` | Брат (по матери) |
| `BS` | Сестра (полная) |
| `BD` | Брат (полный) |
| `L` | Бывший(ая) супруг(а) |
