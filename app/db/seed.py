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


@dataclass(frozen=True)
class QuestionDraft:
    text: str
    options: list[str]
    correct_index: int
    explanation: str


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


def _topic_seed(title: str, grade: int, kind: Literal["theory", "practice"]) -> int:
    return sum(ord(ch) for ch in f"{title}:{kind}") + grade * 101


def _pick(seed: int, low: int, high: int) -> int:
    return low + (seed % (high - low + 1))


def _topic_category(title: str) -> str:
    lowered = title.lower()

    if "тригонометр" in lowered:
        return "trigonometry"
    if any(token in lowered for token in ("туынды", "интеграл", "шек")):
        return "calculus"
    if any(token in lowered for token in ("логарифм", "көрсеткіш")):
        return "log_exp"
    if "вектор" in lowered:
        return "vector"
    if any(token in lowered for token in ("ықтималдық", "статистика", "комбинатор")):
        return "probability"
    if any(token in lowered for token in ("функция", "график", "прогрессия")):
        return "function"
    if any(token in lowered for token in ("теңдеу", "теңсіздік", "өрнек")):
        return "equation"
    if any(token in lowered for token in ("бөлшек", "пайыз", "пропорц", "қатынас", "ондық", "үлес", "рационал")):
        return "fraction_percent"
    if any(
        token in lowered
        for token in ("геометр", "периметр", "аудан", "көлем", "бұрыш", "үшбұрыш", "шеңбер", "дөңгелек", "пифагор", "стереометр", "жанама")
    ):
        return "geometry"
    if any(token in lowered for token in ("мәтіндік", "құрама", "модельдеу", "қозғалыс")):
        return "word_problem"
    return "arithmetic"


def _format_tenths(value_tenths: int) -> str:
    return f"{value_tenths / 10:.1f}"


def _generic_drafts(
    title: str,
    grade: int,
    kind: Literal["theory", "practice"],
    seed: int,
) -> list[QuestionDraft]:
    a = _pick(seed + 1, 18, 70)
    b = _pick(seed + 2, 9, 45)
    c = _pick(seed + 3, 4, 20)
    correct = a + b - c

    start = _pick(seed + 4, 50, 150)
    used = _pick(seed + 5, 15, 40)
    added = _pick(seed + 6, 8, 30)
    if used >= start:
        used = start - 5
    remain = start - used + added

    strategy_text = (
        "Күрделі есепті шағын қадамдарға бөліп, әр қадамда аралық нәтижені тексеру."
        if kind == "practice"
        else "Есепті шығармай тұрып, қандай формула мен шарт қолданылатынын негіздеу."
    )

    return [
        QuestionDraft(
            text=f"«{title}» тақырыбы бойынша есепті бастау үшін ең дұрыс әрекет қайсы?",
            options=[
                "Ең ұзын формуланы бірден таңдау.",
                "Берілген шамаларды, бірліктерді және сұралғанды белгілеу.",
                "Жауап нұсқаларын шамалап таңдау.",
                "Тексеруді соңында емес, мүлде өткізбеу.",
            ],
            correct_index=1,
            explanation="Дұрыс бастау - шартты талдау және берілгендерді нақты жазу.",
        ),
        QuestionDraft(
            text=f"{a} + {b} - {c} өрнегінің мәнін табыңыз.",
            options=[str(correct + 3), str(correct), str(correct - 4), str(correct + 10)],
            correct_index=1,
            explanation="Алдымен қосып, кейін азайтамыз.",
        ),
        QuestionDraft(
            text=f"Қоймада {start} дәптер болды. {used}-і сатылды, кейін {added} дәптер келді. Қанша дәптер қалды?",
            options=[str(remain), str(remain - added), str(remain + used), str(remain - 7)],
            correct_index=0,
            explanation="Қалғаны = бастапқы - сатылған + жаңадан келген.",
        ),
        QuestionDraft(
            text=f"Шешім соңында нәтижені тексерудің ең сенімді жолы қайсы?",
            options=[
                "Жауапты орнына қойып немесе кері амалмен тексеру.",
                "Жауап нұсқасының ең әдемісін таңдау.",
                "Тек соңғы санды қайта жазу.",
                "Аралық қадамдарды алып тастау.",
            ],
            correct_index=0,
            explanation="Тексеру есептің шартқа сай екенін дәлелдейді.",
        ),
        QuestionDraft(
            text=f"«{title}» тақырыбында тұрақты дұрыс нәтиже беретін стратегияны таңдаңыз.",
            options=[
                "Күрделі жерде бірден жауапты болжау.",
                "Бір ғана дайын мысалды жаттап, бәріне соны қолдану.",
                strategy_text,
                "Ереже шарттарын елемеу.",
            ],
            correct_index=2,
            explanation="Тұрақты нәтиже алгоритм мен тексеруге сүйенгенде ғана шығады.",
        ),
    ]


def _arithmetic_drafts(
    title: str,
    grade: int,
    kind: Literal["theory", "practice"],
    seed: int,
) -> list[QuestionDraft]:
    _ = kind
    a = _pick(seed + 1, 24, 86)
    b = _pick(seed + 2, 12, 48)
    c = _pick(seed + 3, 5, 22)
    total = a + b - c

    start = _pick(seed + 4, 60, 180)
    used = _pick(seed + 5, 18, 45)
    add = _pick(seed + 6, 10, 34)
    if used >= start:
        used = start - 8
    remain = start - used + add

    m = _pick(seed + 7, 3, 9)
    n = _pick(seed + 8, 4, 11)
    p = _pick(seed + 9, 18, 70)
    mixed = p + m * n

    div_base = _pick(seed + 10, 3, 9)
    divisible = div_base * _pick(seed + 11, 4, 11)

    bracket = a - (c - b)

    third_question = QuestionDraft(
        text=f"{p} + {m} × {n} өрнегінің мәнін табыңыз.",
        options=[str(mixed), str((p + m) * n), str(p * m + n), str(p + m + n)],
        correct_index=0,
        explanation="Көбейту амалы қосудан бұрын орындалады.",
    )
    if grade < 3:
        simple = p + m + n
        third_question = QuestionDraft(
            text=f"{p} + {m} + {n} қосындысын табыңыз.",
            options=[str(simple - 2), str(simple), str(simple + 3), str(simple + 8)],
            correct_index=1,
            explanation="Сандарды ретімен қосамыз.",
        )

    return [
        QuestionDraft(
            text=f"«{title}» тақырыбы: {a} + {b} - {c} = ?",
            options=[str(total + 4), str(total - 3), str(total), str(total + 9)],
            correct_index=2,
            explanation="Алдымен қосу, кейін азайту орындалады.",
        ),
        QuestionDraft(
            text=f"Сөреде {start} кітап болды. {used} кітап алынды, тағы {add} кітап қойылды. Соңында неше кітап болды?",
            options=[str(remain), str(remain + used), str(remain - add), str(start + used + add)],
            correct_index=0,
            explanation="Қалған саны = бастапқы - алынған + қосылған.",
        ),
        third_question,
        QuestionDraft(
            text=f"{div_base} санына қалдықсыз бөлінетін санды табыңыз.",
            options=[str(divisible + 1), str(divisible), str(divisible + div_base - 1), str(divisible + 2)],
            correct_index=1,
            explanation=f"{divisible} саны {div_base}-ке дәл бөлінеді.",
        ),
        QuestionDraft(
            text=f"{a} - ({c} - {b}) өрнегінің дұрыс мәні қайсы?",
            options=[str(bracket), str(bracket + 4), str(bracket - 3), str(bracket + 9)],
            correct_index=0,
            explanation="Жақша ішін бірінші есептейміз: a - (c - b) = a - c + b.",
        ),
    ]


def _fraction_percent_drafts(title: str, seed: int) -> list[QuestionDraft]:
    d1 = _pick(seed + 1, 12, 39)
    d2 = _pick(seed + 2, 11, 37)
    d_sum = d1 + d2

    den = _pick(seed + 3, 6, 12)
    n1 = _pick(seed + 4, 1, den - 2)
    n2 = _pick(seed + 5, 1, den - n1 - 1)
    frac_sum = n1 + n2

    base = 20 * _pick(seed + 6, 5, 12)
    pct = 5 * _pick(seed + 7, 2, 10)
    part = base * pct // 100

    right = 5 * _pick(seed + 8, 4, 12)
    left = right * 3 // 5

    return [
        QuestionDraft(
            text=f"{_format_tenths(d1)} + {_format_tenths(d2)} мәнін табыңыз.",
            options=[
                _format_tenths(d_sum - 3),
                _format_tenths(d_sum),
                _format_tenths(d_sum + 2),
                _format_tenths(d_sum - 6),
            ],
            correct_index=1,
            explanation="Ондық бөлшектерді разряд бойынша қосамыз.",
        ),
        QuestionDraft(
            text=f"{n1}/{den} + {n2}/{den} қосындысы неге тең?",
            options=[f"{frac_sum}/{den}", f"{frac_sum + 1}/{den}", f"{frac_sum - 1}/{den}", f"{frac_sum}/{den + 1}"],
            correct_index=0,
            explanation="Бөлімдері бірдей бөлшектерде алымдар қосылады.",
        ),
        QuestionDraft(
            text=f"{base} санының {pct}% мәнін табыңыз.",
            options=[str(part), str(part + 10), str(part - 10), str(base // 10)],
            correct_index=0,
            explanation="Пайызды табу: base × pct / 100.",
        ),
        QuestionDraft(
            text=f"3 : 5 = x : {right} болса, x неге тең?",
            options=[str(left - 3), str(left), str(left + 5), str(right - left)],
            correct_index=1,
            explanation="Пропорция бойынша x = 3 × right / 5.",
        ),
        QuestionDraft(
            text="Қайсысы үлкен мән?",
            options=["0.6", "5/8", "Екеуі тең", "Салыстыру мүмкін емес"],
            correct_index=1,
            explanation="5/8 = 0.625, ол 0.6-дан үлкен.",
        ),
    ]


def _equation_drafts(title: str, seed: int) -> list[QuestionDraft]:
    lowered = title.lower()
    x = _pick(seed + 1, 2, 9)
    k = _pick(seed + 2, 2, 7)
    b = _pick(seed + 3, 3, 14)
    rhs = k * x + b

    p = _pick(seed + 4, 1, 6)
    x2 = _pick(seed + 5, 4, 12)
    rhs2 = 2 * (x2 - p)

    good = _pick(seed + 6, 3, 11)
    check_rhs = 3 * good - 7

    item1 = QuestionDraft(
        text=f"{k}x + {b} = {rhs} теңдеуін шешіңіз.",
        options=[str(x + 1), str(x), str(x - 1), str(rhs)],
        correct_index=1,
        explanation="Айнымалыны жеке қалдырып, коэффициентке бөлеміз.",
    )

    if "жүйе" in lowered:
        sx = _pick(seed + 7, 2, 8)
        sy = _pick(seed + 8, 1, 7)
        s1 = sx + sy
        s2 = sx - sy
        item2 = QuestionDraft(
            text=f"Жүйені шешіңіз: x + y = {s1}, x - y = {s2}.",
            options=[f"x={sx}, y={sy}", f"x={s1}, y={s2}", f"x={sy}, y={sx}", f"x={sx + 1}, y={sy - 1}"],
            correct_index=0,
            explanation="Қосу/азайту әдісімен x және y мәндерін табамыз.",
        )
    elif "теңсіздік" in lowered:
        boundary = _pick(seed + 7, 2, 9)
        c = _pick(seed + 8, 1, 6)
        r = k * boundary - c
        item2 = QuestionDraft(
            text=f"{k}x - {c} > {r} теңсіздігінің шешімі қайсы?",
            options=[f"x < {boundary}", f"x > {boundary}", f"x = {boundary}", f"x >= {boundary}"],
            correct_index=1,
            explanation="k оң болғандықтан, жақтарды бөлгенде таңба өзгермейді: x > boundary.",
        )
    elif "квадрат" in lowered:
        r1 = _pick(seed + 7, 1, 5)
        r2 = r1 + _pick(seed + 8, 1, 4)
        item2 = QuestionDraft(
            text=f"(x - {r1})(x - {r2}) = 0 теңдеуінің түбірлерін табыңыз.",
            options=[f"x={r1} немесе x={r2}", f"x={r1 + r2}", f"x={r1 * r2}", "Түбір жоқ"],
            correct_index=0,
            explanation="Көбейтінді нөл болса, көбейткіштердің бірі нөлге тең.",
        )
    else:
        item2 = QuestionDraft(
            text=f"2(x - {p}) = {rhs2} теңдеуін шешіңіз.",
            options=[str(x2), str(x2 + p), str(rhs2), str(x2 - 2)],
            correct_index=0,
            explanation="Алдымен 2-ге бөліп, содан кейін p-ны қосамыз.",
        )

    price = _pick(seed + 9, 60, 140)
    total = 2 * price + 30

    return [
        item1,
        item2,
        QuestionDraft(
            text=f"Қай x мәні 3x - 7 = {check_rhs} теңдеуін қанағаттандырады?",
            options=[str(good - 2), str(good + 1), str(good), str(good + 3)],
            correct_index=2,
            explanation="x-ті орнына қойып тексереміз.",
        ),
        QuestionDraft(
            text=f"Екі бірдей дәптер және 30 тг қалам бірге {total} тг тұрса, бір дәптердің бағасы қанша?",
            options=[str(price), str(price + 30), str(total // 2), str(price - 15)],
            correct_index=0,
            explanation="Теңдеу: 2x + 30 = total.",
        ),
        QuestionDraft(
            text="Қай теңдеу «санды 5-ке көбейтіп, 12 қосты, нәтиже 47 болды» мәтініне сәйкес?",
            options=["5x + 12 = 47", "5 + 12x = 47", "x + 5 = 12 + 47", "47x = 5 + 12"],
            correct_index=0,
            explanation="Мәтіндік сипаттаманы тура алгебралық түрге аударамыз.",
        ),
    ]


def _geometry_drafts(title: str, seed: int) -> list[QuestionDraft]:
    lowered = title.lower()
    a = _pick(seed + 1, 4, 14)
    b = _pick(seed + 2, 5, 15)
    per = 2 * (a + b)
    area = a * b

    alpha = _pick(seed + 3, 35, 80)
    beta = _pick(seed + 4, 25, 60)
    if alpha + beta >= 170:
        beta = 160 - alpha
    gamma = 180 - alpha - beta

    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
    t = triples[seed % len(triples)]
    t_a, t_b, t_c = t

    r = _pick(seed + 5, 3, 9)
    circle = 2 * 3.14 * r

    second_item = QuestionDraft(
        text=f"Қабырғалары {a} см және {b} см тіктөртбұрыштың ауданын табыңыз.",
        options=[str(area), str(per), str(area + a), str(area - b)],
        correct_index=0,
        explanation="Тіктөртбұрыш ауданы: S = a × b.",
    )
    if "көлем" in lowered or "стереометр" in lowered:
        x = _pick(seed + 6, 3, 8)
        y = _pick(seed + 7, 4, 9)
        z = _pick(seed + 8, 2, 7)
        volume = x * y * z
        second_item = QuestionDraft(
            text=f"Өлшемдері {x} см, {y} см, {z} см тікбұрышты параллелепипедтің көлемі қанша?",
            options=[str(volume), str(x * y + z), str(2 * (x + y + z)), str(volume - z)],
            correct_index=0,
            explanation="Көлем формуласы: V = a × b × c.",
        )

    return [
        QuestionDraft(
            text=f"Қабырғалары {a} см және {b} см тіктөртбұрыштың периметрін табыңыз.",
            options=[str(per), str(a + b), str(2 * a + b), str(per + 2)],
            correct_index=0,
            explanation="Периметр формуласы: P = 2(a + b).",
        ),
        second_item,
        QuestionDraft(
            text=f"Үшбұрыштың екі бұрышы {alpha}° және {beta}°. Үшінші бұрыш қанша?",
            options=[str(gamma), str(alpha + beta), str(180 - alpha), str(beta + 10)],
            correct_index=0,
            explanation="Үшбұрыш бұрыштарының қосындысы 180°.",
        ),
        QuestionDraft(
            text=f"Тікбұрышты үшбұрыштың катеттері {t_a} және {t_b}. Гипотенузаны табыңыз.",
            options=[str(t_c), str(t_a + t_b), str(t_c - 1), str(t_c + 2)],
            correct_index=0,
            explanation="Пифагор теоремасы: c² = a² + b².",
        ),
        QuestionDraft(
            text=f"Радиусы {r} см шеңбер ұзындығын табыңыз (π = 3.14).",
            options=[f"{circle:.2f}", f"{(3.14 * r * r):.2f}", f"{(2 * r):.2f}", f"{(circle - 3.14):.2f}"],
            correct_index=0,
            explanation="Шеңбер ұзындығы: L = 2πr.",
        ),
    ]


def _function_drafts(title: str, seed: int) -> list[QuestionDraft]:
    lowered = title.lower()
    x = _pick(seed + 1, 2, 7)
    val = 2 * x - 3

    px1 = _pick(seed + 2, 0, 3)
    px2 = px1 + _pick(seed + 3, 2, 5)
    py1 = _pick(seed + 4, 1, 5)
    slope = _pick(seed + 5, 1, 4)
    py2 = py1 + slope * (px2 - px1)

    a1 = _pick(seed + 6, 2, 9)
    d = _pick(seed + 7, 2, 6)
    n = _pick(seed + 8, 4, 8)
    an = a1 + (n - 1) * d

    item3 = QuestionDraft(
        text=f"Арифметикалық прогрессияда a₁ = {a1}, d = {d}. a{n} мүшесін табыңыз.",
        options=[str(an), str(a1 + n * d), str(an - d), str(an + 2)],
        correct_index=0,
        explanation="aₙ = a₁ + (n-1)d формуласы қолданылады.",
    )
    if "прогрессия" not in lowered:
        gx = _pick(seed + 9, 2, 5)
        item3 = QuestionDraft(
            text=f"y = x² функциясында x = {gx} кезінде y неге тең?",
            options=[str(gx * gx), str(2 * gx), str(gx + 2), str(gx * gx - 1)],
            correct_index=0,
            explanation="Функция мәніне x орнына сан қоямыз.",
        )

    return [
        QuestionDraft(
            text=f"y = 2x - 3 функциясында x = {x} болса, y неге тең?",
            options=[str(val), str(val + 2), str(2 * x + 3), str(x - 3)],
            correct_index=0,
            explanation="Айнымалыны орнына қойып есептейміз.",
        ),
        QuestionDraft(
            text=f"({px1}, {py1}) және ({px2}, {py2}) нүктелері арқылы өтетін түзу үшін көлбеулік коэффициенті (k) неге тең?",
            options=[str(slope), str(py2 - py1), str(px2 - px1), str(slope + 1)],
            correct_index=0,
            explanation="k = (y2 - y1) / (x2 - x1).",
        ),
        item3,
        QuestionDraft(
            text="Қай нүкте y = 2x + 1 графигіне жатады?",
            options=["(2, 5)", "(2, 3)", "(1, 1)", "(0, 2)"],
            correct_index=0,
            explanation="x=2 болса, y=2·2+1=5.",
        ),
        QuestionDraft(
            text="y = f(x - 2) + 1 түрлендіруі графикті қалай жылжытады?",
            options=["2 бірлік солға, 1 бірлік төмен", "2 бірлік оңға, 1 бірлік жоғары", "1 бірлік оңға, 2 бірлік жоғары", "График өзгермейді"],
            correct_index=1,
            explanation="x-тің ішінде (x-2) болса оңға, сыртында +1 болса жоғары жылжиды.",
        ),
    ]


def _probability_drafts(seed: int) -> list[QuestionDraft]:
    red = _pick(seed + 1, 3, 8)
    blue = _pick(seed + 2, 2, 7)
    total = red + blue

    a = _pick(seed + 3, 4, 12)
    b = _pick(seed + 4, 5, 13)
    c = _pick(seed + 5, 6, 14)
    mean = (a + b + c) / 3

    m1 = _pick(seed + 6, 6, 14)
    m2 = m1 + _pick(seed + 7, 1, 4)
    m3 = m2 + _pick(seed + 8, 1, 4)

    return [
        QuestionDraft(
            text=f"Қорапта {red} қызыл және {blue} көк шар бар. Кездейсоқ бір шар алғанда қызыл шығу ықтималдығы қанша?",
            options=[f"{red}/{total}", f"{blue}/{total}", f"{total}/{red}", "1/2"],
            correct_index=0,
            explanation="Қолайлы жағдай саны / барлық жағдай саны.",
        ),
        QuestionDraft(
            text=f"{a}, {b}, {c} сандарының арифметикалық ортасын табыңыз.",
            options=[f"{mean:.2f}", str(a + b + c), str((a + b) // 2), f"{(mean + 1):.2f}"],
            correct_index=0,
            explanation="Орташа мән: (a+b+c)/3.",
        ),
        QuestionDraft(
            text=f"{m1}, {m2}, {m3} деректер жиынының медианасы қандай?",
            options=[str(m1), str(m2), str(m3), str((m1 + m3) // 2)],
            correct_index=1,
            explanation="Өсу ретімен тұрған үш санның медианасы - ортасындағы сан.",
        ),
        QuestionDraft(
            text="4 оқушыны бір қатарға неше түрлі тәсілмен орналастыруға болады?",
            options=["24", "16", "12", "8"],
            correct_index=0,
            explanation="Пермутация саны: 4! = 24.",
        ),
        QuestionDraft(
            text="5 оқушыдан 2 оқушыны кезекші етіп таңдаудың саны қанша?",
            options=["10", "20", "7", "25"],
            correct_index=0,
            explanation="Комбинация: C(5,2)=10.",
        ),
    ]


def _trigonometry_drafts() -> list[QuestionDraft]:
    return [
        QuestionDraft(
            text="sin 30° мәнін табыңыз.",
            options=["1/2", "√3/2", "0", "1"],
            correct_index=0,
            explanation="Негізгі тригонометриялық мән: sin 30° = 1/2.",
        ),
        QuestionDraft(
            text="0° пен 180° аралығында cos x = 0 теңдеуінің шешімі қайсы?",
            options=["x = 0°", "x = 90°", "x = 180°", "Шешімі жоқ"],
            correct_index=1,
            explanation="cos x осьте нөлге 90°-та тең.",
        ),
        QuestionDraft(
            text="Гипотенузасы 10, бір сүйір бұрышы 30° болатын тікбұрышты үшбұрышта осы бұрышқа қарсы катет қанша?",
            options=["5", "10", "5√3", "2"],
            correct_index=0,
            explanation="Қарсы катет = гипотенуза × sin30° = 10 × 1/2.",
        ),
        QuestionDraft(
            text="sin²α + cos²α өрнегінің мәні неге тең?",
            options=["0", "1", "sin α", "cos α"],
            correct_index=1,
            explanation="Негізгі тепе-теңдік: sin²α + cos²α = 1.",
        ),
        QuestionDraft(
            text="0° пен 180° аралығында 2sin x = 1 теңдеуінің шешімдері қайсы?",
            options=["x = 30°", "x = 150°", "x = 30° және x = 150°", "x = 60°"],
            correct_index=2,
            explanation="sin x = 1/2 болғанда екі бұрыш бар: 30° және 150°.",
        ),
    ]


def _calculus_drafts(title: str) -> list[QuestionDraft]:
    lowered = title.lower()
    if "интеграл" in lowered or "алғашқы функция" in lowered:
        return [
            QuestionDraft(
                text="∫(2x + 3)dx интегралын табыңыз.",
                options=["x² + 3x + C", "2x + 3 + C", "x² + C", "2x² + 3x + C"],
                correct_index=0,
                explanation="Қосындының интегралы жеке интегралдар қосындысына тең.",
            ),
            QuestionDraft(
                text="∫₀² x dx мәнін есептеңіз.",
                options=["2", "4", "1", "8"],
                correct_index=0,
                explanation="Алғашқы функция x²/2, сонда (4/2)-0=2.",
            ),
            QuestionDraft(
                text="y = x түзуі мен Ox осі арасындағы [0;4] кесіндісіндегі аудан қанша?",
                options=["8", "16", "4", "6"],
                correct_index=0,
                explanation="Бұл негізі 4, биіктігі 4 болатын үшбұрыш: S=1/2·4·4=8.",
            ),
            QuestionDraft(
                text="d/dx (x² + 3x) туындысы неге тең?",
                options=["2x + 3", "x + 3", "2x", "x² + 3"],
                correct_index=0,
                explanation="Интеграл мен туынды тақырыптары байланысқан: стандарт туынды ережесі.",
            ),
            QuestionDraft(
                text="∫(1/x)dx (x>0) нәтижесін табыңыз.",
                options=["ln x + C", "1/x² + C", "x + C", "eˣ + C"],
                correct_index=0,
                explanation="1/x функциясының алғашқы функциясы ln x.",
            ),
        ]

    return [
        QuestionDraft(
            text="f(x)=x³-4x болса, f'(x) неге тең?",
            options=["3x²-4", "x²-4", "3x-4", "x³-4"],
            correct_index=0,
            explanation="Қуат ережесі: (x^n)' = n*x^(n-1).",
        ),
        QuestionDraft(
            text="f(x)=x² функциясы үшін x=3 нүктесіндегі жанаманың көлбеулігі қандай?",
            options=["6", "3", "9", "2"],
            correct_index=0,
            explanation="f'(x)=2x, сонда f'(3)=6.",
        ),
        QuestionDraft(
            text="y = -x² + 4x - 1 функциясының экстремумы x-тің қай мәнінде болады?",
            options=["x = 2", "x = -2", "x = 4", "x = 1"],
            correct_index=0,
            explanation="Туындысы -2x+4, оны нөлге теңестірсек x=2.",
        ),
        QuestionDraft(
            text="lim x→1 (x²-1)/(x-1) шегін табыңыз.",
            options=["2", "1", "0", "Шегі жоқ"],
            correct_index=0,
            explanation="Қысқарту: (x-1)(x+1)/(x-1)=x+1, x=1 болса 2.",
        ),
        QuestionDraft(
            text="Туындыны қолданудың дұрыс мысалын таңдаңыз.",
            options=["Функцияның өсу/кему аралықтарын анықтау", "Тек бөлшек қысқарту", "Тек пайыз табу", "Тек пропорция құру"],
            correct_index=0,
            explanation="Туынды функцияның өзгеру жылдамдығын сипаттайды.",
        ),
    ]


def _log_exp_drafts() -> list[QuestionDraft]:
    return [
        QuestionDraft(
            text="2^x = 32 теңдеуін шешіңіз.",
            options=["x = 5", "x = 4", "x = 6", "x = 3"],
            correct_index=0,
            explanation="32 = 2^5.",
        ),
        QuestionDraft(
            text="log₂(8) мәнін табыңыз.",
            options=["3", "2", "4", "8"],
            correct_index=0,
            explanation="2^3=8 болғандықтан, log₂8=3.",
        ),
        QuestionDraft(
            text="ln(e^3) неге тең?",
            options=["3", "e", "1", "0"],
            correct_index=0,
            explanation="ln мен e^x өзара кері функциялар.",
        ),
        QuestionDraft(
            text="10^(log10 7) өрнегінің мәні қандай?",
            options=["7", "10", "70", "1"],
            correct_index=0,
            explanation="a^(log_a b)=b қасиеті қолданылады.",
        ),
        QuestionDraft(
            text="Қайсысы үлкен?",
            options=["2^6", "3^4", "Екеуі тең", "Салыстыру мүмкін емес"],
            correct_index=1,
            explanation="2^6=64, 3^4=81, сондықтан 3^4 үлкен.",
        ),
    ]


def _vector_drafts() -> list[QuestionDraft]:
    return [
        QuestionDraft(
            text="a = (2, -1), b = (3, 4). a + b қосындысын табыңыз.",
            options=["(5, 3)", "(6, 4)", "(1, -5)", "(-1, 3)"],
            correct_index=0,
            explanation="Координаталар бойынша қосамыз.",
        ),
        QuestionDraft(
            text="v = (3,4) векторының ұзындығы неге тең?",
            options=["5", "7", "12", "1"],
            correct_index=0,
            explanation="|v| = √(3²+4²)=5.",
        ),
        QuestionDraft(
            text="(1,2) және (3,-1) векторларының скаляр көбейтіндісін табыңыз.",
            options=["1", "5", "-1", "6"],
            correct_index=0,
            explanation="1·3 + 2·(-1) = 3 - 2 = 1.",
        ),
        QuestionDraft(
            text="Қай жұп векторлар коллинеар?",
            options=["(2,4) және (1,2)", "(1,3) және (2,5)", "(2,1) және (1,2)", "(3,0) және (0,3)"],
            correct_index=0,
            explanation="(2,4)=2·(1,2), яғни параллель.",
        ),
        QuestionDraft(
            text="A(1,2), B(4,7) болса, AB векторы қандай?",
            options=["(3,5)", "(5,9)", "(-3,-5)", "(4,7)"],
            correct_index=0,
            explanation="AB = (xB-xA, yB-yA) = (3,5).",
        ),
    ]


def _word_problem_drafts(seed: int) -> list[QuestionDraft]:
    speed = _pick(seed + 1, 40, 90)
    time = _pick(seed + 2, 2, 5)
    distance = speed * time

    kg = _pick(seed + 3, 12, 36)
    price = _pick(seed + 4, 180, 420)
    cost = kg * price

    return [
        QuestionDraft(
            text=f"Көлік {speed} км/сағ жылдамдықпен {time} сағат жүрді. Жүрген қашықтықты табыңыз.",
            options=[str(distance), str(speed + time), str(distance - speed), str(speed * (time - 1))],
            correct_index=0,
            explanation="Қашықтық = жылдамдық × уақыт.",
        ),
        QuestionDraft(
            text=f"{kg} кг өнімнің 1 кг бағасы {price} тг. Жалпы құнын есептеңіз.",
            options=[str(cost), str(kg + price), str(cost - price), str(kg * (price // 10))],
            correct_index=0,
            explanation="Жалпы құн = масса × бірлік бағасы.",
        ),
        QuestionDraft(
            text="Мәтіндік есепте теңдеу құрудың бірінші қадамы қайсы?",
            options=[
                "Белгісіз шаманы белгілеу және шартты қысқаша жазу",
                "Дайын жауапты таңдау",
                "Кері тексеруді алып тастау",
                "Тек соңғы санды пайдалану",
            ],
            correct_index=0,
            explanation="Белгісізді дұрыс белгілеу шешімнің негізі.",
        ),
        QuestionDraft(
            text="Бірдей 3 заттың бағасы 750 тг. Бір зат қанша тұрады?",
            options=["250", "150", "300", "225"],
            correct_index=0,
            explanation="750/3 = 250.",
        ),
        QuestionDraft(
            text="Екі кезеңді есепте дұрыс тексеру қалай жасалады?",
            options=[
                "Әр кезең нәтижесін шартпен салыстырып, соңында толық кері тексеру жасау",
                "Тек бірінші кезеңді жазу",
                "Соңғы жауапты өзгертпей қалдыру",
                "Өлшем бірліктерін елемеу",
            ],
            correct_index=0,
            explanation="Кезеңдік тексеру қате жиналуын болдырмайды.",
        ),
    ]


def _topic_question_drafts(
    title: str,
    grade: int,
    kind: Literal["theory", "practice"],
) -> list[QuestionDraft]:
    category = _topic_category(title)
    seed = _topic_seed(title, grade, kind)

    if category == "trigonometry":
        return _trigonometry_drafts()
    if category == "calculus":
        return _calculus_drafts(title)
    if category == "log_exp":
        return _log_exp_drafts()
    if category == "vector":
        return _vector_drafts()
    if category == "probability":
        return _probability_drafts(seed)
    if category == "function":
        return _function_drafts(title, seed)
    if category == "equation":
        return _equation_drafts(title, seed)
    if category == "fraction_percent":
        return _fraction_percent_drafts(title, seed)
    if category == "geometry":
        return _geometry_drafts(title, seed)
    if category == "word_problem":
        return _word_problem_drafts(seed)
    if category == "arithmetic":
        return _arithmetic_drafts(title, grade, kind, seed)
    return _generic_drafts(title, grade, kind, seed)


def _build_hard_questions_for_lesson(
    lesson_id: str,
    title: str,
    grade: int,
    kind: Literal["theory", "practice"],
) -> list[QuizQuestion]:
    drafts = _topic_question_drafts(title, grade, kind)
    if len(drafts) < 5:
        drafts.extend(_generic_drafts(title, grade, kind, _topic_seed(title, grade, kind) + 17))
    drafts = drafts[:5]

    questions: list[QuizQuestion] = []
    for idx, draft in enumerate(drafts, start=1):
        questions.append(
            QuizQuestion(
                id=f"q5-{lesson_id}-{idx}",
                lesson_id=lesson_id,
                text=draft.text,
                options=draft.options,
                correct_index=draft.correct_index,
                explanation=draft.explanation,
            )
        )
    return questions

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
    active_topic_ids: set[str] = set()

    for grade, topic_list in CURRICULUM_TOPICS.items():
        for order_index, title in enumerate(topic_list, start=1):
            # Keep distance from legacy topics to avoid grade+order uniqueness conflicts.
            safe_order_index = 100 + order_index
            bundle = _topic_bundle(grade, safe_order_index, title)
            active_topic_ids.add(bundle.topic.id)

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

    # Only curriculum topics stay visible; legacy/temporary topics are hidden.
    all_topics = (await session.execute(select(Topic))).scalars().all()
    for topic in all_topics:
        topic.is_published = topic.id in active_topic_ids


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
    math_book_urls = {
        1: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/1класс.pdf",
        2: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/2класс.pdf",
        3: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/3класс.pdf",
        4: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/4класс.pdf",
        5: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/5класс.pdf",
        6: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/6класс.pdf",
        7: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/7класс.pdf",
        8: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/8класс.pdf",
        9: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/9класс.pdf",
        10: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/10класс.pdf",
        11: "https://3b8f33e25e2e7f341b25a3fef543a0d1.r2.cloudflarestorage.com/math/books/11класс.pdf",
    }

    def _math_book_payload(grade: int) -> dict:
        return {
            "id": f"book-grade-{grade}",
            "title": f"Математика {grade}-сынып",
            "grade": grade,
            "cover_url": None,
            "file_url": math_book_urls[grade],
            "author": "Мектеп бағдарламасы",
            "published_year": 2025,
            "chapters": [
                "Қайталау",
                "Жаңа тақырып",
                "Практикалық тапсырмалар",
                "Бақылау сұрақтары",
                ],
        }

    desired_books: list[dict] = [_math_book_payload(grade) for grade in range(1, 12)]
    desired_ids = {book["id"] for book in desired_books}

    existing_books = (await session.execute(select(Book))).scalars().all()
    existing_by_id = {book.id: book for book in existing_books}

    for payload in desired_books:
        existing = existing_by_id.get(payload["id"])
        if existing:
            existing.title = payload["title"]
            existing.grade = payload["grade"]
            existing.cover_url = payload["cover_url"]
            existing.file_url = payload["file_url"]
            existing.author = payload["author"]
            existing.published_year = payload["published_year"]
            existing.chapters = payload["chapters"]
            continue
        session.add(Book(**payload))

    await session.execute(delete(Book).where(Book.id.not_in(desired_ids)))


async def seed_all(session: AsyncSession) -> None:
    await seed_reference_data(session)
    await seed_topics_lessons_and_quizzes(session)
    await enrich_legacy_lessons(session)
    await sync_hard_quiz_questions(session)
    await seed_books(session)
    await session.commit()


