# -*- coding: utf8 -*-

import json
import logging

import telepot
import telepot.helper
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, ShippingOption
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
        InlineKeyboardButton(text='Новости хоккея', callback_data='hockey_feed'), InlineKeyboardButton(text='Что сегодня в продаже?',
        callback_data='buy')]]))
    return None

def _display_football_feed(chat_id):
    football_items = parse_football_sportru_rss()
    for news in football_items:
        fmsg = render_to_string('feed.md', news)
        TelegramBot.sendMessage(chat_id, fmsg, parse_mode='Markdown')
    TelegramBot.sendMessage(chat_id, text='другие новости?',
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Новости футбола',
        callback_data='football_feed'),
        InlineKeyboardButton(text='Новости хоккея', callback_data='hockey_feed')]]))


    return None


def _display_hockey_feed(chat_id):
    hockey_items = parse_hockey_sportru_rss()
    for news in hockey_items:
        hmsg = render_to_string('feed.md', news)
        TelegramBot.sendMessage(chat_id, hmsg, parse_mode='Markdown')
    TelegramBot.sendMessage(chat_id, text='другие новости?',
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Новости футбола',
        callback_data='football_feed'),
        InlineKeyboardButton(text='Новости хоккея', callback_data='hockey_feed')]]))

    return None

def _send_invoice(chat_id):
    TelegramBot.sendInvoice(chat_id, "Gaming console PS4(USED)", "Greates gaming console in the world",
                payload='a-string-identifying-related-payment-messages-tuvwxyz',
                provider_token=settings.PAYMENT_PROVIDER_TOKEN,
                start_parameter='abc',
                currency='RUB', prices=[LabeledPrice(label='One Case', amount=320000),],
                need_shipping_address=True, is_flexible=True)  # required for shipping query
    return None

def _payment_succes(chat_id):

    TelegramBot.sendMessage(chat_id, render_to_string('On_succes_payment.md'),
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Новости футбола',
        callback_data='football_feed'),
        InlineKeyboardButton(text='Новости хоккея', callback_data='hockey_feed')]]))

    return None

class CommandReceiveView(View):


    def post(self, request, bot_token):
        if bot_token != settings.TELEGRAM_BOT_TOKEN:
            return HttpResponseForbidden('Invalid token')

        commands = {
            '/start': _display_help,
            'help': _display_help,
            'football_feed': _display_football_feed,
            'hockey_feed': _display_hockey_feed,
            'buy': _send_invoice,
            'successful_payment': _payment_succes,
        }

        raw = request.body.decode('utf-8')
        logger.info(raw)

        try:
            pload = json.loads(raw)
        except ValueError:
            return HttpResponseBadRequest('Invalid request body')
        else:
            if 'callback_query' in pload:
                query_id, from_id, query_data = telepot.glance(pload['callback_query'], flavor='callback_query')
                #TelegramBot.sendMessage(chat_id, query_data, parse_mode='Markdown')
                cmd = query_data
                chat_id = from_id
            elif 'message' in pload:
                content_type, chat_type, chat_id = telepot.glance(pload['message'])
                if content_type == 'successful_payment':
                    cmd = 'successful_payment'
                else:
                    #chat_id = pload['message']['chat']['id']
                    cmd = pload['message'].get('text')  # command
                #TelegramBot.sendMessage(chat_id, flavor, parse_mode='Markdown')
            elif 'shipping_query' in pload:
                query_id, from_id, invoice_payload = telepot.glance(pload['shipping_query'], flavor='shipping_query')
                chat_id = from_id
                TelegramBot.answerShippingQuery(query_id, True, shipping_options=[
                        ShippingOption(id='fedex', title='FedEx', prices=[
                            LabeledPrice(label='Local', amount=345),
                            LabeledPrice(label='International', amount=2345)]),
                        ShippingOption(id='dhl', title='DHL', prices=[
                            LabeledPrice(label='Local', amount=342),
                            LabeledPrice(label='International', amount=1234)])])
            elif 'pre_checkout_query' in pload:
                query_id, from_id, invoice_payload = telepot.glance(pload['pre_checkout_query'], flavor='pre_checkout_query')
                chat_id = from_id
                TelegramBot.answerPreCheckoutQuery(query_id, True)

            func = commands.get(cmd.split()[0].lower())

            if func:
                func(chat_id)
            else:
                TelegramBot.sendMessage(chat_id, 'I do not understand you, Sir!')

        return JsonResponse({}, status=200)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CommandReceiveView, self).dispatch(request, *args, **kwargs)
