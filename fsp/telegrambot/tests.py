import datetime as dt
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from telegrambot import bot


class TelegramBotCallbackTests(IsolatedAsyncioTestCase):
    async def test_start_sends_single_welcome_message(self):
        reply_text = AsyncMock()
        update = SimpleNamespace(
            message=SimpleNamespace(reply_text=reply_text),
            effective_message=SimpleNamespace(reply_text=reply_text),
            effective_chat=SimpleNamespace(id=123),
            effective_user=SimpleNamespace(id=777),
        )
        context = SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()))

        await bot.start(update, context)

        reply_text.assert_awaited_once()
        first_call_text = reply_text.await_args_list[0].args[0]
        self.assertIn('Добро пожаловать', first_call_text)

    async def test_send_current_info_uses_effective_message_when_update_message_is_none(self):
        reply_text = AsyncMock()
        effective_message = SimpleNamespace(reply_text=reply_text)
        update = SimpleNamespace(
            message=None,
            effective_message=effective_message,
            effective_chat=SimpleNamespace(id=123),
            effective_user=SimpleNamespace(id=777),
        )
        context = SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()))

        data = {
            'moex_price': 300.12,
            'fair_price': 340.89,
            'fair_price_20_percent': 409.07,
            'pb_ratio': 0.88,
            'price_score': 'дешево',
            'timestamp': __import__('datetime').datetime(2026, 1, 1, 10, 30),
        }

        def fake_sync_to_async(_func):
            async def runner():
                return data
            return runner

        with patch('telegrambot.bot.sync_to_async', side_effect=fake_sync_to_async):
            await bot.send_current_info(update, context)

        self.assertTrue(reply_text.await_count >= 1)
        first_call_text = reply_text.await_args_list[0].args[0]
        self.assertIn('📊 Данные по акции Сбербанка', first_call_text)

    async def test_send_current_info_uses_local_server_time_in_updated_line(self):
        reply_text = AsyncMock()
        effective_message = SimpleNamespace(reply_text=reply_text)
        update = SimpleNamespace(
            message=None,
            effective_message=effective_message,
            effective_chat=SimpleNamespace(id=123),
            effective_user=SimpleNamespace(id=777),
        )
        context = SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()))

        data = {
            'moex_price': 300.12,
            'fair_price': 340.89,
            'fair_price_20_percent': 409.07,
            'pb_ratio': 0.88,
            'price_score': 'дешево',
            'timestamp': dt.datetime(2026, 1, 1, 10, 30, tzinfo=dt.timezone.utc),
        }
        server_now = dt.datetime(2026, 2, 14, 20, 45, tzinfo=dt.timezone.utc)
        local_server_now = dt.datetime(2026, 2, 14, 23, 45, tzinfo=dt.timezone.utc)

        def fake_sync_to_async(_func):
            async def runner():
                return data
            return runner

        with patch('telegrambot.bot.sync_to_async', side_effect=fake_sync_to_async):
            with patch('telegrambot.bot.timezone.now', return_value=server_now):
                with patch('telegrambot.bot.timezone.localtime', return_value=local_server_now):
                    await bot.send_current_info(update, context)

        text = reply_text.await_args_list[0].args[0]
        self.assertIn('🕐 Обновлено: 14.02.2026 23:45', text)

    async def test_handle_menu_action_current_works_for_callback_update(self):
        reply_text = AsyncMock()
        query = SimpleNamespace(
            data='current',
            answer=AsyncMock(),
            message=SimpleNamespace(reply_text=reply_text),
        )
        update = SimpleNamespace(
            message=None,
            callback_query=query,
            effective_message=SimpleNamespace(reply_text=reply_text),
            effective_chat=SimpleNamespace(id=123),
            effective_user=SimpleNamespace(id=888),
        )
        context = SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()))

        data = {
            'moex_price': 301.11,
            'fair_price': 340.89,
            'fair_price_20_percent': 409.07,
            'pb_ratio': 0.88,
            'price_score': 'дешево',
            'timestamp': __import__('datetime').datetime(2026, 1, 1, 10, 30),
        }

        def fake_sync_to_async(_func):
            async def runner():
                return data
            return runner

        with patch('telegrambot.bot.sync_to_async', side_effect=fake_sync_to_async):
            await bot.handle_menu_action(update, context)

        query.answer.assert_awaited_once()
        self.assertTrue(reply_text.await_count >= 1)
