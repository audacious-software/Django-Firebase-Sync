# pylint: disable=line-too-long
# -*- coding: utf-8 -*-

from __future__ import print_function

import importlib

import firebase_admin
import firebase_admin.db

from django.conf import settings
from django.core.management.base import BaseCommand

from ...decorators import handle_lock

def firebase_listener(event):
    for app in settings.INSTALLED_APPS:
        try:
            firebase_sync_api = importlib.import_module(app + '.firebase_sync_api')

            firebase_sync_api.process_event(event.event_type, event.path, event.data)

            print(app + '[3]: ' + event.event_type + ' -- ' + event.path)
        except ImportError:
            pass
        except AttributeError:
            pass # traceback.print_exc()
        except NotImplementedError:
            pass # traceback.print_exc()

class Command(BaseCommand):
    help = 'Sets up a persistent listener for Firebase database changes.'

    def add_arguments(self, parser):
        pass

    @handle_lock
    def handle(self, *args, **options):
        credentials = firebase_admin.credentials.Certificate(settings.FIREBASE_SYNC_SERVICE_ACCOUNT_KEY)

        app = firebase_admin.initialize_app(credentials, {
            'databaseURL': settings.FIREBASE_SYNC_SERVICE_DATABASE_URL,
            'databaseAuthVariableOverride': None
        })

        print('Setting up listener for ' + app.name + '...')

        firebase_admin.db.reference('/').listen(firebase_listener)
