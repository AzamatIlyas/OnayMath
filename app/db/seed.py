from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.education import Book, City, Lesson, QuizQuestion, School, Topic


def _lesson_content(theory: str, example: str, tasks: list[str]) -> dict:
    return {
        "theory": theory,
        "example": example,
        "tasks": tasks,
    }


def _one_line(value: str) -> str:
    return " ".join(value.split())


BASE_CITIES = [
    {"id": "city-almaty", "name": "Алматы", "region": "Алматы"},
    {"id": "city-astana", "name": "Астана", "region": "Астана"},
    {"id": "city-shymkent", "name": "Шымкент", "region": "Шымкент"},
    {"id": "city-karaganda", "name": "Қарағанды", "region": "Қарағанды облысы"},
    {"id": "city-aktobe", "name": "Ақтөбе", "region": "Ақтөбе облысы"},
    {"id": "city-aktau", "name": "Ақтау", "region": "Маңғыстау облысы"},
]
BASE_SCHOOLS = [
    {"id": "school-almaty-12", "city_id": "city-almaty", "name": "№12 мектеп-гимназия", "address": "Алматы, Самал"},
    {"id": "school-almaty-56", "city_id": "city-almaty", "name": "№56 лицей", "address": "Алматы, Абай даңғылы"},
    {"id": "school-astana-77", "city_id": "city-astana", "name": "№77 мектеп", "address": "Астана, Түркістан көшесі"},
    {"id": "school-astana-31", "city_id": "city-astana", "name": "№31 лицей", "address": "Астана, Сығанақ көшесі"},
    {"id": "school-shymkent-8", "city_id": "city-shymkent", "name": "№8 мектеп", "address": "Шымкент, Тәуке хан көшесі"},
    {"id": "school-shymkent-45", "city_id": "city-shymkent", "name": "№45 гимназия", "address": "Шымкент, Республика даңғылы"},
    {"id": "school-karaganda-3", "city_id": "city-karaganda", "name": "№3 мектеп", "address": "Қарағанды, Ержанов көшесі"},
    {"id": "school-aktobe-21", "city_id": "city-aktobe", "name": "№21 мектеп", "address": "Ақтөбе, Маресьев көшесі"},
]

# Schools in Aktau from OpenStreetMap (amenity=school, fetched 2026-05-11).
AKTAU_SCHOOLS = [
    {"name": "№14 жалпы білім беретін мектеп", "address": None},
    {"name": "№20 жалпы білім беретін мектеп", "address": None},
    {"name": "№11 физика-математика мектебі", "address": None},
    {"name": "NIS Ақтау", "address": "33 шағын аудан, 16"},
    {"name": "№7 мектеп-лицей", "address": None},
    {"name": "№22 мектеп", "address": None},
]

CURRICULUM_TOPICS: dict[int, list[str]] = {
    1: [
        "20-ға дейін сандарды санау және салыстыру",
        "20-ға дейін қосу және азайту",
        "Бір амалмен мәтіндік есептер",
        "Геометриялық фигуралар мен сызықтар",
        "Ұзындық, масса және уақытты өлшеу",
        "Логикалық заңдылықтар",
    ],
    2: [
        "100-ге дейінгі сандар және разрядтық құрам",
        "100 шегінде қосу және азайту",
        "Көбейту кестесі (кіріспе)",
        "Бір белгісізі бар қарапайым теңдеулер",
        "Фигура периметрі",
        "Салыстыру және айырмаға есептер",
    ],
    3: [
        "Көбейту және бөлу",
        "Амалдардың орындалу реті",
        "Үлестер және қарапайым бөлшектер",
        "Тіктөртбұрыш ауданы",
        "Қозғалысқа есептер",
        "Теңдеулер және өрнектер",
    ],
    4: [
        "Көптаңбалы сандар және амалдар",
        "Жазбаша бөлу және көбейту",
        "Жай бөлшектер",
        "Өлшем бірліктері және түрлендіру",
        "Аудан және көлем",
        "Құрама есептер",
    ],
    5: [
        "Натурал сандар және амал қасиеттері",
        "Ондық бөлшектер",
        "Пайыздар (кіріспе)",
        "Теңдеулер және теңсіздіктер",
        "Геометриялық салулар",
        "Бұрыштар және көпбұрыштар",
    ],
    6: [
        "Сандардың бөлінгіштігі",
        "Қатынастар және пропорциялар",
        "Оң және теріс сандар",
        "Рационал сандар",
        "Координаталық жазықтық",
        "Шеңбер және дөңгелек",
    ],
    7: [
        "Рационал сандар және амалдар",
        "Сызықтық теңдеулер",
        "Сызықтық функция",
        "Натурал көрсеткішті дәреже",
        "Қысқаша көбейту формулалары",
        "Геометрия: үшбұрыштар және бұрыштар",
        "Статистика және диаграммалар",
    ],
    8: [
        "Квадрат теңдеулер",
        "Квадрат функция",
        "Теңдеулер жүйесі",
        "Теңсіздіктер және жүйелері",
        "Үшбұрыштардың ұқсастығы",
        "Пифагор теоремасы",
        "Комбинаторика элементтері",
    ],
    9: [
        "Арифметикалық және геометриялық прогрессия",
        "Функциялар және графиктер",
        "Теңсіздіктер жүйесі",
        "Ықтималдық және статистика",
        "Шеңбер және жанама",
        "Жазықтықтағы векторлар",
        "Қорытынды аттестацияға дайындық",
    ],
    10: [
        "Тригонометриялық функциялар",
        "Тригонометриялық теңдеулер",
        "Функция туындысы",
        "Туындыны қолдану",
        "Стереометрия: түзулер мен жазықтықтар",
        "Комбинаторика және ықтималдық",
        "Математикалық модельдеу",
    ],
    11: [
        "Алғашқы функция және интеграл",
        "Шек және үздіксіздік",
        "Логарифмдік және көрсеткіштік функция",
        "Алгебрадан күрделі есептер",
        "Стереометрия: көлемдер және аудандар",
        "ҰБТ-ға дайындық",
        "Қорытынды практикум",
    ],
}

@dataclass
class TopicBundle:
    topic: Topic
    lessons: list[Lesson]
    questions: list[QuizQuestion]


@dataclass(frozen=True)
class TopicProfile:
    focus: str
    formula: str
    algorithm: list[str]
    example: str
    example_steps: list[str]
    check: str
    mistakes: list[str]


def _default_profile(title: str, grade: int) -> TopicProfile:
    return TopicProfile(
        focus=f"«{title}» тақырыбының негізгі ережесін түсініп, оны {grade}-сынып деңгейіндегі стандарт есептерде қолдану.",
        formula=f"Тірек ереже: «{title}» тақырыбының анықтамалары мен қасиеттерін қолданыңыз.",
        algorithm=[
            "Есеп шартын мұқият жазып, берілген мен табылатын шамаларды белгілеңіз.",
            "Тақырыпқа сәйкес формула немесе ережені таңдаңыз.",
            "Есептеуді қадамдап орындап, әр өтуді негіздеңіз.",
            "Жауапты тексеріңіз: таңбасы, мағынасы және шартқа сәйкестігі.",
        ],
        example=f"«{title}» тақырыбы бойынша типтік есепті талдаңыз: белгісізді тауып, әр қадамды түсіндіріңіз.",
        example_steps=[
            "Берілгендерді жазып, белгісіз шаманы белгілеңіз.",
            "Шарт бойынша өрнек/теңдеу/сызба құрыңыз.",
            "Түрлендірулерді ретімен орындаңыз.",
            "Жауапты есеп мәтініне сай тұжырымдаңыз.",
        ],
        check="Нәтижені кері амалмен немесе орнына қою арқылы тексеріңіз.",
        mistakes=[
            "Шешу қадамдары арасында негіздеуді өткізіп жіберу.",
            "Таңбалар мен ережені қолдану шарттарына мұқият болмау.",
            "Соңғы жауапты тексермеу.",
        ],
    )

def _topic_profile(title: str, grade: int) -> TopicProfile:
    return _default_profile(title, grade)

def _build_lesson_content(title: str, grade: int, kind: Literal["theory", "practice"]) -> dict:
    profile = _topic_profile(title, grade)
    is_theory = kind == "theory"

    overview = (
        f"{grade}-сыныптың «{title}» тақырыбы. Бұл сабақта негізгі идеяны, "
        f"қадамдық алгоритмді және типтік есептерді қарастырамыз."
    )
    objectives = [
        f"«{title}» тақырыбының мағынасын және қолданылуын түсіну.",
        "Шығару алгоритмін қадамдарды өткізіп алмай орындау.",
        "Жауапты тексеріп, жиі қателерді таба алу.",
    ]
    theory = (
        f"{profile.focus} {profile.formula} "
        "Тек жауап алу емес, әр қадамды дәлелдеп жазу маңызды."
    )
    if not is_theory:
        theory = (
            f"«{title}» тақырыбы бойынша практикалық бөлім: әртүрлі деңгейдегі есептерде ережені бекітеміз "
            "және шешуді сауатты рәсімдеуді машықтаймыз."
        )

    tasks = {
        "basic": [
            f"«{title}» тақырыбының негізгі ережесін жазып, өз сөзіңізбен түсіндіріңіз.",
            "Сабақ алгоритмі бойынша 2 базалық есеп шығарыңыз.",
        ],
        "medium": [
            "Аралас амалдары бар есеп шығарып, әр қадамды негіздеңіз.",
            "Өз мысалыңызды құрып, толық шешімін жазыңыз.",
        ],
        "advanced": [
            "Күрделі есепті екі тәсілмен шығарып, нәтижесін салыстырыңыз.",
            "Дайын шешімдегі қателікті тауып, дұрыс нұсқасын түсіндіріңіз.",
        ],
    }

    if not is_theory:
        tasks["basic"].append("Өзін-өзі тексеру парағын қолданыңыз: шарт, формула, есептеу, жауап.")
        tasks["medium"].append("Екі түрлі шешу жолын салыстырып, тиімдісін таңдаңыз.")

    return {
        "overview": _one_line(overview),
        "objectives": objectives,
        "theory": _one_line(theory),
        "formula": profile.formula,
        "algorithm": profile.algorithm,
        "example": profile.example,
        "exampleSteps": profile.example_steps,
        "check": profile.check,
        "commonMistakes": profile.mistakes,
        "tasks": tasks,
        "summary": f"Сабақ соңында оқушы «{title}» тақырыбының базалық есептерін сенімді шығара алуы керек.",
    }

def _detect_lesson_kind(title: str, order_index: int) -> Literal["theory", "practice"]:
    lowered = title.lower()
    if "теория" in lowered:
        return "theory"
    if "практика" in lowered or "тәжірибе" in lowered:
        return "practice"
    return "theory" if order_index == 1 else "practice"


def _build_hard_questions_for_lesson(
    lesson_id: str,
    title: str,
    grade: int,
    kind: Literal["theory", "practice"],
) -> list[QuizQuestion]:
    profile = _topic_profile(title, grade)
    a0 = profile.algorithm[0] if profile.algorithm else "Есеп шартын талдаңыз."
    a1 = profile.algorithm[1] if len(profile.algorithm) > 1 else "Тиісті ережені таңдаңыз."
    a2 = profile.algorithm[2] if len(profile.algorithm) > 2 else "Есептеуді қадамдап орындаңыз."
    a3 = profile.algorithm[3] if len(profile.algorithm) > 3 else "Нәтижені тексеріңіз."

    m0 = profile.mistakes[0] if profile.mistakes else "Жауапты тексермеу."
    m1 = profile.mistakes[1] if len(profile.mistakes) > 1 else "Формуланы қолдану шартын ескермеу."

    q1 = QuizQuestion(
        id=f"q5-{lesson_id}-1",
        lesson_id=lesson_id,
        text=f"«{title}» тақырыбындағы негізгі ережені қолданар алдында алдымен не істеу керек?",
        options=[
            "Шартты тексермей бірден сандарды қою.",
            "Ең таныс жауапты таңдау.",
            "Есеп шартын және әдістің жарамдылығын тексеру.",
            "Шартты жазбай, бірден жауапқа көшу.",
        ],
        correct_index=2,
        explanation="Ереже дұрыс болса да, қолдану шарты сақталмаса нәтиже қате болады.",
    )

    q2 = QuizQuestion(
        id=f"q5-{lesson_id}-2",
        lesson_id=lesson_id,
        text="Төмендегі қай реттілік әдістемелік тұрғыдан дұрыс?",
        options=[
            f"1) {a0} 2) {a2} 3) {a1} 4) {a3}",
            f"1) {a0} 2) {a1} 3) {a2} 4) {a3}",
            f"1) {a3} 2) {a1} 3) {a2} 4) {a0}",
            f"1) {a2} 2) {a0} 3) {a3} 4) {a1}",
        ],
        correct_index=1,
        explanation="Алдымен талдау, одан кейін ереже таңдау, сосын есептеу, ең соңында тексеру орындалады.",
    )

    q3 = QuizQuestion(
        id=f"q5-{lesson_id}-3",
        lesson_id=lesson_id,
        text="Қай әрекет қате шешімге жиі әкеледі?",
        options=[
            "Аралық қадамдарды толық жазу.",
            "Шектеулер мен таңбаларды тексеру.",
            "Жауапты жуық бағамен салыстыру.",
            m0,
        ],
        correct_index=3,
        explanation=f"Бұл тақырыптағы жиі қате: {m0}",
    )

    q4 = QuizQuestion(
        id=f"q5-{lesson_id}-4",
        lesson_id=lesson_id,
        text="Тексеру кезінде шартқа қайшы нәтиже шықты. Не істеу дұрыс?",
        options=[
            "Ереже бұзылған алғашқы қадамды тауып, сол жерден қайта есептеу.",
            "Жуық нәтиже болса, сол күйі қалдыру.",
            "Нәтижені үлгіге сәйкестендіріп өзгерту.",
            "Аралық қадамдарды алып тастау.",
        ],
        correct_index=0,
        explanation="Қайшылық туындаса, қате шыққан қадамды тауып, алгоритм бойынша қайта шығару керек.",
    )

    if kind == "theory":
        q5 = QuizQuestion(
            id=f"q5-{lesson_id}-5",
            lesson_id=lesson_id,
            text="Тақырыпты терең түсінгенді не жақсы көрсетеді?",
            options=[
                "Бір дайын мысалды ғана жаттап алу.",
                "Ережені өз сөзімен түсіндіріп, балама тәсілмен шығарып тексеру.",
                "Шектеулерді қарамай, тек формуланы жаттау.",
                m1,
            ],
            correct_index=1,
            explanation="Терең түсіну - білімді жаңа жағдайға қолдану және нәтижені дәлелді тексеру.",
        )
    else:
        q5 = QuizQuestion(
            id=f"q5-{lesson_id}-5",
            lesson_id=lesson_id,
            text="Күрделі есепті шығаруда ең тиімді стратегия қайсы?",
            options=[
                "Таныс түр шыққанша кездейсоқ түрлендіру.",
                "Уақыт үнемдеу үшін тексеруді өткізіп жіберу.",
                "Есепті алгоритм қадамдарына бөліп, әр өтуді бақылау.",
                "Шартты тексермей ең ұзын формуланы таңдау.",
            ],
            correct_index=2,
            explanation="Күрделі есептер кезең-кезеңмен шешіліп, әр қадам міндетті түрде тексеріледі.",
        )

    return [q1, q2, q3, q4, q5]

def _build_quiz_questions(grade: int, order_index: int, title: str, lesson1_id: str, lesson2_id: str) -> list[QuizQuestion]:
    _ = order_index
    return [
        *_build_hard_questions_for_lesson(lesson1_id, title, grade, "theory"),
        *_build_hard_questions_for_lesson(lesson2_id, title, grade, "practice"),
    ]


def _normalize_name(value: str) -> str:
    return " ".join(value.replace("\u200b", "").split())

async def _upsert_city(session: AsyncSession, city_data: dict) -> None:
    city = await session.get(City, city_data["id"])
    if city:
        city.name = city_data["name"]
        city.region = city_data["region"]
        return
    session.add(City(**city_data))


async def _upsert_school(session: AsyncSession, school_data: dict) -> None:
    school = await session.get(School, school_data["id"])
    if school:
        school.city_id = school_data["city_id"]
        school.name = school_data["name"]
        school.address = school_data.get("address")
        return
    session.add(School(**school_data))


def _topic_bundle(grade: int, order_index: int, title: str) -> TopicBundle:
    topic_id = f"topic-g{grade:02d}-{order_index:02d}"
    lesson1_id = f"lesson-g{grade:02d}-{order_index:02d}-1"
    lesson2_id = f"lesson-g{grade:02d}-{order_index:02d}-2"
    profile = _topic_profile(title, grade)

    topic = Topic(
        id=topic_id,
        title=title,
        description=f"{profile.focus} Сынып: {grade}.",
        grade=grade,
        order_index=order_index,
        is_published=True,
    )

    lesson1 = Lesson(
        id=lesson1_id,
        topic_id=topic_id,
        title=f"{title}: теория",
        order_index=1,
        duration_minutes=18,
        xp_reward=45,
        content=_build_lesson_content(title, grade, "theory"),
    )

    lesson2 = Lesson(
        id=lesson2_id,
        topic_id=topic_id,
        title=f"{title}: тәжірибе",
        order_index=2,
        duration_minutes=22,
        xp_reward=55,
        content=_build_lesson_content(title, grade, "practice"),
    )

    questions = _build_quiz_questions(grade, order_index, title, lesson1_id, lesson2_id)

    return TopicBundle(topic=topic, lessons=[lesson1, lesson2], questions=questions)


async def seed_reference_data(session: AsyncSession) -> None:
    for city_data in BASE_CITIES:
        await _upsert_city(session, city_data)

    for school_data in BASE_SCHOOLS:
        await _upsert_school(session, school_data)

    for idx, item in enumerate(AKTAU_SCHOOLS, start=1):
        school_id = f"school-aktau-{idx:03d}"
        await _upsert_school(
            session,
            {
                "id": school_id,
                "city_id": "city-aktau",
                "name": _normalize_name(item["name"]),
                "address": _normalize_name(item["address"]) if item.get("address") else None,
            },
        )


async def seed_topics_lessons_and_quizzes(session: AsyncSession) -> None:
    for grade, topic_list in CURRICULUM_TOPICS.items():
        for order_index, title in enumerate(topic_list, start=1):
            # Keep distance from legacy topics to avoid grade+order uniqueness conflicts.
            safe_order_index = 100 + order_index
            bundle = _topic_bundle(grade, safe_order_index, title)

            topic = await session.get(Topic, bundle.topic.id)
            if topic:
                topic.title = bundle.topic.title
                topic.description = bundle.topic.description
                topic.grade = bundle.topic.grade
                topic.order_index = bundle.topic.order_index
                topic.is_published = True
            else:
                session.add(bundle.topic)

            for lesson in bundle.lessons:
                existing_lesson = await session.get(Lesson, lesson.id)
                if existing_lesson:
                    existing_lesson.topic_id = lesson.topic_id
                    existing_lesson.title = lesson.title
                    existing_lesson.content = lesson.content
                    existing_lesson.order_index = lesson.order_index
                    existing_lesson.duration_minutes = lesson.duration_minutes
                    existing_lesson.xp_reward = lesson.xp_reward
                else:
                    session.add(lesson)

            # Quiz questions are synchronized in a single pass by sync_hard_quiz_questions.


def _is_placeholder_content(content: dict | None) -> bool:
    if not isinstance(content, dict):
        return True

    theory = str(content.get("theory", ""))
    example = str(content.get("example", ""))
    formula = str(content.get("formula", ""))
    has_objectives = bool(content.get("objectives"))
    has_algorithm = bool(content.get("algorithm"))

    return (
        "Базовая теория по теме" in theory
        or "Практические задачи по теме" in theory
        or "Разберем типовой пример" in example
        or formula.startswith("Опорное правило: используйте определения и свойства темы")
        or "Бұл сабақта негізгі идеяны" in str(content.get("overview", ""))
        or not has_objectives
        or not has_algorithm
    )


async def enrich_legacy_lessons(session: AsyncSession) -> None:
    lesson_rows = (
        await session.execute(
            select(Lesson, Topic).join(Topic, Topic.id == Lesson.topic_id)
        )
    ).all()

    for lesson, topic in lesson_rows:
        if not _is_placeholder_content(lesson.content):
            continue

        kind: Literal["theory", "practice"] = "theory" if lesson.order_index == 1 else "practice"
        lesson.content = _build_lesson_content(topic.title, topic.grade, kind)


async def sync_hard_quiz_questions(session: AsyncSession) -> None:
    lesson_rows = (await session.execute(select(Lesson, Topic).join(Topic, Topic.id == Lesson.topic_id))).all()

    await session.execute(delete(QuizQuestion))

    all_questions: list[QuizQuestion] = []
    for lesson, topic in lesson_rows:
        kind = _detect_lesson_kind(lesson.title, lesson.order_index)
        all_questions.extend(_build_hard_questions_for_lesson(lesson.id, topic.title, topic.grade, kind))

    session.add_all(all_questions)


async def seed_books(session: AsyncSession) -> None:
    existing_books = (await session.execute(select(Book))).scalars().all()
    if existing_books:
        for book in existing_books:
            if book.file_url.startswith("http://") or book.file_url.startswith("https://"):
                book.file_url = f"grade-{book.grade}/math-grade-{book.grade}.pdf"
        return

    books = []
    for grade in range(1, 12):
        books.append(
            Book(
                id=f"book-grade-{grade}",
                title=f"Математика {grade}-сынып",
                grade=grade,
                cover_url=None,
                file_url=f"grade-{grade}/math-grade-{grade}.pdf",
                author="Мектеп бағдарламасы",
                published_year=2025,
                chapters=[
                    "Қайталау",
                    "Жаңа тақырып",
                    "Практикалық тапсырмалар",
                    "Бақылау сұрақтары",
                ],
            )
        )
    session.add_all(books)


async def seed_all(session: AsyncSession) -> None:
    await seed_reference_data(session)
    await seed_topics_lessons_and_quizzes(session)
    await enrich_legacy_lessons(session)
    await sync_hard_quiz_questions(session)
    await seed_books(session)
    await session.commit()


