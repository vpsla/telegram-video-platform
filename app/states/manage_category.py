"""FSM states for admin category management."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ManageCategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_icon = State()
