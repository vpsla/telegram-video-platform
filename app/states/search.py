"""FSM states for the user search flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_for_query = State()
