# -*- coding: utf8 -*-

import json
import logging

import telepot
import telepot.helper
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from .utils import parse_football_sportru_rss, parse_hockey_sportru_rss


TelegramBot = telepot.Bot(settings.TELEGRAM_BOT_TOKEN)

logger = logging.getLogger('telegram.bot')


def _display_help(chat_id):
    #TelegramBot.sendMessage(chat_id, render_to_string('help.md'), parse_mode='Markdown')
    TelegramBot.sendMessage(chat_id, render_to_string('help.md'),
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Новости футбола',
        callback_data='football_feed'),
        InlineKeyboardButton(text='Новости хоккея', callback_data='hockey_feed')]]))
    return chat_id

def _display_football_feed(chat_id):
    football_items = parse_football_sportru_rss()
    for news in football_items:
        fmsg = render_to_string('feed.md', news)
        TelegramBot.sendMessage(chat_id, fmsg, parse_mode='Markdown')

    return chat_id


def _display_hockey_feed(chat_id):
    hockey_items = parse_hockey_sportru_rss()
    for news in hockey_items:
        hmsg = render_to_string('feed.md', news)
        TelegramBot.sendMessage(chat_id, hmsg, parse_mode='Markdown')

    return chat_id


class CommandReceiveView(View):


    def post(self, request, bot_token):
        if bot_token != settings.TELEGRAM_BOT_TOKEN:
            return HttpResponseForbidden('Invalid token')

        commands = {
            '/start': _display_help,
            'help': _display_help,
            'football_feed': _display_football_feed,
            'hockey_feed': _display_hockey_feed,
        }

        raw = request.body.decode('utf-8')
        logger.info(raw)

        try:
            payload = json.loads(raw)
        except ValueError:
            return HttpResponseBadRequest('Invalid request body')
        else:


            #flavor = telepot.flavor(payload['message'])
            if 'callback_query' in payload:
                query_id, from_id, query_data = telepot.glance(payload['callback_query'], flavor='callback_query')
                TelegramBot.sendMessage(chat_id, query_data, parse_mode='Markdown')
                cmd = query_data
                #chat_id = from_id
            elif 'message' in payload:
                chat_id = payload['message']['chat']['id']
                cmd = payload['message'].get('text')  # command
                #TelegramBot.sendMessage(chat_id, flavor, parse_mode='Markdown')



            func = commands.get(cmd.split()[0].lower())

            if func:
                func(chat_id)
            else:
                TelegramBot.sendMessage(chat_id, 'I do not understand you, Sir!')

        return JsonResponse({}, status=200)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CommandReceiveView, self).dispatch(request, *args, **kwargs)
