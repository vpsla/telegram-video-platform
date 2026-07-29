"""FSM states for the admin broadcast flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_confirmation = State()
