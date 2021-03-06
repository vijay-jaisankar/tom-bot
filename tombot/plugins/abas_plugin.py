'''
ABAS: Automated Birthday Announcement System
'''
from apscheduler.jobstores.base import JobLookupError
from tombot.registry import get_easy_logger, Subscribe, BOT_START, BOT_SHUTDOWN
from tombot.rpc import remote_send


LOGGER = get_easy_logger('plugins.abas')

def announce_bday(name, recipient):
    ''' Send a congratulation for name to recipient. '''
    LOGGER.info('Congratulating %s', name)
    body = 'Gefeliciteerd, {}!'.format(name)
    remote_send(body, recipient)

@Subscribe(BOT_START)
def abas_register_cb(bot, *args, **kwargs):
    ''' Add jobs to the scheduler for all birthdays. '''
    LOGGER.info('Registering ABAs.')
    try:
        bot.cursor.execute('SELECT primary_nick,bday FROM users WHERE bday IS NOT NULL')
    except TypeError:
        LOGGER.error('Invalid date found, fix your database!')
        return
    results = bot.cursor.fetchall()
    for person in results:
        LOGGER.info('Scheduling ABA for %s', person[0])
        bot.scheduler.add_job(
            announce_bday,
            'cron', month=person[1].month, day=person[1].day,
            hour=0, minute=0, second=45,
            id='abas.{}'.format(person[0]),
            args=(person[0], bot.config['Jids']['announce-group']),
            replace_existing=True, misfire_grace_time=86400
            )

@Subscribe(BOT_SHUTDOWN)
def abas_deregister_cb(bot, *args, **kwargs):
    '''
    Remove jobs for birthday-announcing from scheduler.

    This is necessary because we cannot predict whether the plugin will remain
    enabled, and removing jobs manually or having jobs referring to non-existent
    functions leads to Fun.
    '''
    LOGGER.info('Deregistering ABAs.')
    bot.cursor.execute('SELECT primary_nick FROM users WHERE bday IS NOT NULL')
    results = bot.cursor.fetchall()
    for person in results:
        try:
            bot.scheduler.remove_job('abas.{}'.format(person[0]))
        except JobLookupError:
            pass
    LOGGER.info('Done.')
