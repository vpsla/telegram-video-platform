"""FSM states for the admin "create series" flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CreateSeriesStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_category = State()
    waiting_for_author = State()
    waiting_for_description = State()
    waiting_for_tags = State()
