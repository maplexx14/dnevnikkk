from aiogram.dispatcher.filters.state import StatesGroup, State

class Register_states(StatesGroup):
    get_email = State()
    get_password = State()
    get_name = State()
    get_surname = State()
    get_class = State()
class GPT_states(StatesGroup):
    s_question = State()