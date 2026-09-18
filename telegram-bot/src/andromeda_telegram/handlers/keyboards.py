"""Inline keyboard factories backed by opaque short-lived callback tokens."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..state.callbacks import CallbackPayload, CallbackStore


def resolver_choices(owner_key: str, programs: tuple[tuple[str, str], ...], store: CallbackStore) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for program_id, label in programs[:5]:
        builder.row(InlineKeyboardButton(text=label[:60], callback_data=store.issue(owner_key, CallbackPayload(action="details", program_ids=(program_id,)))))
    return builder.as_markup()


def program_actions(owner_key: str, program_id: str, store: CallbackStore) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Подробнее", callback_data=store.issue(owner_key, CallbackPayload(action="details", program_ids=(program_id,)))),
        InlineKeyboardButton(text="В shortlist", callback_data=store.issue(owner_key, CallbackPayload(action="shortlist_add", program_ids=(program_id,)))),
    )
    builder.row(
        InlineKeyboardButton(text="Сравнить", callback_data=store.issue(owner_key, CallbackPayload(action="compare", program_ids=(program_id,)))),
        InlineKeyboardButton(text="Учебный план", callback_data=store.issue(owner_key, CallbackPayload(action="curriculum", program_ids=(program_id,)))),
    )
    return builder.as_markup()


def refinement_choices(owner_key: str, question_id: str, revision: int, options: tuple[tuple[str, str], ...], store: CallbackStore) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option_id, label in options[:4]:
        builder.row(InlineKeyboardButton(text=label[:60], callback_data=store.issue(owner_key, CallbackPayload(action="refinement", question_id=question_id, option_id=option_id, revision=revision))))
    return builder.as_markup()


def image_actions(owner_key: str, program_ids: tuple[str, ...], store: CallbackStore, web_app_url: str, *, include_third: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if program_ids:
        builder.row(InlineKeyboardButton(text="Подробнее", callback_data=store.issue(owner_key, CallbackPayload(action="details", program_ids=(program_ids[0],)))))
    if program_ids:
        builder.row(InlineKeyboardButton(text="В shortlist", callback_data=store.issue(owner_key, CallbackPayload(action="shortlist_add", program_ids=(program_ids[0],)))))
    if len(program_ids) >= 2:
        builder.row(
            InlineKeyboardButton(text="Скрыть одинаковые ↺", callback_data=store.issue(owner_key, CallbackPayload(action="hide_identical", program_ids=program_ids))),
            InlineKeyboardButton(text="Добавить третью" if include_third else "Объяснить реалистичность", callback_data=store.issue(owner_key, CallbackPayload(action="add_third" if include_third else "realism", program_ids=program_ids))),
        )
        builder.row(InlineKeyboardButton(text="Профиль различий", callback_data=store.issue(owner_key, CallbackPayload(action="radar", program_ids=program_ids))))
    query = ",".join(program_ids)
    builder.row(InlineKeyboardButton(text="Открыть в приложении", url=f"{web_app_url.rstrip('/')}/?view=compare&ids={query}"))
    return builder.as_markup()


__all__ = ["image_actions", "program_actions", "refinement_choices", "resolver_choices"]
