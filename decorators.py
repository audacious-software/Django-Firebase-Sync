# pylint: disable=pointless-string-statement, line-too-long

import time
import logging
import tempfile
import traceback

import fasteners

from django.conf import settings
from django.utils.text import slugify
"""
A decorator for management commands (or any class method) to ensure that there is
only ever one process running the method at any one time.
Requires lockfile - (pip install lockfile)
Author: Ross Lawley
Via: http://rosslawley.co.uk/archive/old/2010/10/18/locking-django-management-commands/
"""

# Lock timeout value - how long to wait for the lock to become available.
# Default behavior is to never wait for the lock to be available (fail fast)
LOCK_WAIT_TIMEOUT = getattr(settings, "DEFAULT_LOCK_WAIT_TIMEOUT", -1)

def handle_lock(handle):
    """
    Decorate the handle method with a file lock to ensure there is only ever
    one process running at any one time.
    """

    def wrapper(self, *args, **options):
        lock_prefix = ''

        try:
            lock_prefix = settings.SITE_URL.split('//')[1].replace('/', '').replace('.', '-')
        except AttributeError:
            try:
                lock_prefix = settings.ALLOWED_HOSTS[0].replace('.', '-')
            except IndexError:
                lock_prefix = 'pdk_lock'

        lock_prefix = slugify(lock_prefix)

        start_time = time.time()
        verbosity = options.get('verbosity', 0)
        if verbosity == 0:
            level = logging.ERROR
        elif verbosity == 1:
            level = logging.WARN
        elif verbosity == 2:
            level = logging.INFO
        else:
            level = logging.DEBUG

        logging.basicConfig(level=level, format="%(message)s")
        logging.debug("-" * 72)

        lock_name = self.__module__.split('.').pop()
        lock = fasteners.InterProcessLock('%s/%s__%s' % (tempfile.gettempdir(), lock_prefix, lock_name))

        logging.debug("%s - acquiring lock...", lock_name)

        locked = False

        if LOCK_WAIT_TIMEOUT > 0:
            locked = lock.acquire(timeout=LOCK_WAIT_TIMEOUT)
        else:
            locked = lock.acquire()

        if locked is False:
            logging.debug("waiting for the lock timed out. quitting.")
            return

        logging.debug("acquired.")

        try:
            handle(self, *args, **options)
        except: # pylint: disable=bare-except
            logging.error("Command Failed")
            logging.error('==' * 72)
            logging.error(traceback.format_exc())
            logging.error('==' * 72)

        logging.debug("releasing lock...")
        lock.release()
        logging.debug("released.")

        logging.info("done in %.2f seconds", (time.time() - start_time))
        return

    return wrapper
