# -*- coding: utf8 -*-

from xml.etree import cElementTree

import requests


def parse_football_sportru_rss():
    """Parses first 10 items from https://www.sport.ru/rssfeeds/football.rss

    """
    response = requests.get('https://www.sport.ru/rssfeeds/football.rss')
    parsed_xml = cElementTree.fromstring(response.content)
    items = []

    for node in parsed_xml.iter():
        if node.tag == 'item':
            item = {}
            for item_node in list(node):
                if item_node.tag == 'title':
                    item['title'] = item_node.text
                if item_node.tag == 'link':
                    item['link'] = item_node.text

            items.append(item)

    return items[:10]

def parse_hockey_sportru_rss():
    """Parses first 10 items from https://www.sport.ru/rssfeeds/hockey.rss

    """
    response = requests.get('https://www.sport.ru/rssfeeds/hockey.rss')
    parsed_xml = cElementTree.fromstring(response.content)
    items = []

    for node in parsed_xml.iter():
        if node.tag == 'item':
            item = {}
            for item_node in list(node):
                if item_node.tag == 'title':
                    item['title'] = item_node.text
                if item_node.tag == 'link':
                    item['link'] = item_node.text

            items.append(item)

    return items[:10]
