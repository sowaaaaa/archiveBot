from aiogram.fsm.state import State, StatesGroup


class ArchiveStates(StatesGroup):
    choosing_language = State()
    # Основной поток
    welcome = State()
    choosing_type = State()
    collecting_front_photo = State()
    collecting_profile_photo = State()
    asking_optional = State()
    collecting_fullbody = State()
    asking_age = State()
    asking_nationality = State()
    asking_origin = State()
    asking_anthropometry = State()
    analyzing = State()
    showing_results = State()
    expert_upsell = State()


class AdminStates(StatesGroup):
    panel = State()
    broadcast_compose = State()
    broadcast_confirm = State()
    edit_text_select = State()
    edit_text_input = State()
