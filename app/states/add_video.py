"""FSM states for the admin "add video" flow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddVideoStates(StatesGroup):
    waiting_for_forward = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_series_choice = State()
    waiting_for_episode_number = State()
