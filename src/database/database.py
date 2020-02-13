import logging
import os
import sys

import psycopg2
import psycopg2.extras

from database.queries import (
    menu_query,
    settings_query,
    settings_insert,
    settings_update,
    settings_broadcast_subscribers_query
)
from util.const import (
    HIDE_CUISINE,
    BROADCAST_SUBSCRIPTION
)

# global connection
_connection = None


def connect_database():
    """ Connect to the PostgreSQL database server"""
    global _connection
    # if connection is already formed, return connection
    if _connection:
        return _connection

    try:
        # connect to the PostgreSQL server
        logging.info("Connecting to the PostgreSQL database...")
        _connection = psycopg2.connect(host=os.getenv("RC_DINING_BOT_HOST"),
                                       database=os.getenv("RC_DINING_BOT_DATABASE"),
                                       user=os.getenv("RC_DINING_BOT_DB_USER"),
                                       password=os.getenv("RC_DINING_BOT_DB_PASSWORD"),
                                       connect_timeout=10
                                       )

        # create a cursor
        cursor = _connection.cursor()

        # display the PostgreSQL database server version
        logging.info("PostgreSQL database version:")
        cursor.execute("SELECT version()")
        db_version = cursor.fetchone()
        logging.info(db_version)

        cursor.close()
    except Exception as error:
        logging.fatal(error)
        sys.exit(1)


def get_raw_menu(meal, date):
    # get menu from database
    conn = connect_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(menu_query(meal), (date,))
    menu = cursor.fetchone()
    cursor.close()
    return menu


def insert_default_user_pref(chat_id):
    conn = connect_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(settings_insert(), (chat_id, '{}', '{}'))
    conn.commit()
    cursor.close()


def get_hidden_cuisines(chat_id):
    conn = connect_database()
    # get hidden cuisines of a user from database
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(settings_query(HIDE_CUISINE), (chat_id,))
    data = cursor.fetchone()

    if data is None:
        # insert default settings
        insert_default_user_pref(chat_id)
        hidden = []
    else:
        hidden = data[HIDE_CUISINE]

    cursor.close()
    return hidden  # returns hidden cuisines in user_pref


def get_broadcast_subscribers(meal):
    # get broadcast subscribers from database based on meal
    conn = connect_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(settings_broadcast_subscribers_query(meal), ('true',))
    data = cursor.fetchall()

    return data


def get_subscribe_setting(meal, chat_id):
    # get user's subscribe setting from database based on meal
    conn = connect_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(settings_query(meal + BROADCAST_SUBSCRIPTION), (chat_id,))
    [data] = cursor.fetchone()

    return data


def update_hidden_cuisine(chat_id, cuisine_to_hide):
    # updates hidden cuisine of a user
    hidden_cuisines = get_hidden_cuisines(chat_id)

    if cuisine_to_hide in hidden_cuisines:
        hidden_cuisines.remove(cuisine_to_hide)
    else:
        hidden_cuisines.append(cuisine_to_hide)

    # update database
    conn = connect_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(settings_update(HIDE_CUISINE), (hidden_cuisines, chat_id))
    conn.commit()
    cursor.close()

    return hidden_cuisines


def update_subscribe_setting(chat_id, meal):
    # update database
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    field = meal + BROADCAST_SUBSCRIPTION
    cursor.execute(settings_query(field), (chat_id,))
    [subscribed] = cursor.fetchone()
    subscribed = not subscribed
    cursor.execute(settings_update(field), (subscribed, chat_id))
    cursor.close()

    return subscribed
