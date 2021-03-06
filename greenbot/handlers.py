import logging
import random
import greenbot.config
import greenbot.repos
import greenbot.util
import greenbot.user
import greenbot.schedule
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton
logger = logging.getLogger('greenbot.handlers')

## Show the user the welcome sentence and send over the keyboard
# @param update
# @param context
def start(update, context):
    logger.debug('Command: start')
    keyboard = [
        [KeyboardButton('/info')],
        [KeyboardButton('/activate'), KeyboardButton('/store'), KeyboardButton('/deactivate')],
        [KeyboardButton('/schedule'), KeyboardButton('/run')]
    ]
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hi! I am a bot ' + random.choice(['😏', '🤪']) + ', programmed to execute scripts by your schedule!\n' +
        'To begin you should take a look into the store with /store. Note you can also use /info to see all currently active scripts and their latest execution result. If you don\'t ' + 
        'find what you are looking for, maybe consider to program it yourself and contribute to https://github.com/Simonmicro/green-py-bot!', reply_markup=ReplyKeyboardMarkup(keyboard))

## Stop the main loop (useage not recommended)
# @param update
# @param context
def stop(update, context):
    logger.debug('Command: stop')
    if not greenbot.util.isGroupAdminOrDirectChat(update):
        return

    context.bot.send_message(chat_id=update.effective_chat.id, text='🆘 Initiating bot shutdown...')
    from greenbot.bot import stop
    stop()

## Show the user the store, with the scripts and some contextual buttons
# @param update
# @param context
def store(update, context):
    logger.debug('Command: store')

    scriptIdentifier = greenbot.util.getGlobalSkriptIdentifier(update, context, 'store', 'Welcome to the store, stranger ' + random.choice(['🖖', '😜']) + '! Before I can show you any of my beautiful scripts, please tell me in which repository you want to take a look with me' + random.choice(['', ' 🤔']) + '...',
        random.choice(['Good', 'Excellent', '🤩 Perfect']) + ' choice! Here you can see all the scripts inside that one particular repository. In which one are you more interested in ' + random.choice(['😊', '😇', '😁']) + '?')
    if not scriptIdentifier:
        return

    scriptInfo = greenbot.repos.getModule(scriptIdentifier).getScriptInfo()
    response = random.choice(['😊 As you wish.', '😏 Here you go...', '😁 All right!']) + ' Thats is everything i know:\n\n' + \
        'Name: ' + scriptInfo['name'] + ' (' + scriptIdentifier + ')\n' + \
        'Author: ' + scriptInfo['author'] + '\n' + \
        'Description: ' + scriptInfo['description'] + '\n' + \
        'Version: ' + scriptInfo['version']
    keyboard = []
    if not greenbot.user.get(update.effective_chat.id).hasScript(scriptIdentifier):
        keyboard.append([InlineKeyboardButton('Activate', callback_data='activate ' + scriptIdentifier)])
    else:
        keyboard.append([InlineKeyboardButton('Schedule', callback_data='schedule ' + scriptIdentifier)])
        keyboard.append([InlineKeyboardButton('Deactivate', callback_data='deactivate ' + scriptIdentifier)])
    keyboard.append([InlineKeyboardButton('Back', callback_data='store ' + greenbot.repos.resolveIdentifier(scriptIdentifier)[0])])
    greenbot.util.updateOrReply(update, response, reply_markup=InlineKeyboardMarkup(keyboard))

## Show the user a little hello from the current bot version and his active scripts
# @param update
# @param context
def info(update, context):
    logger.debug('Command: info')
    user = greenbot.user.get(update.message.chat.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hi, I am The Green Bot #' + greenbot.config.version + ' - at your service!')
    if len(user.getScripts()) > 0:
        scriptsStr = 'Your currently active scripts are:\n\n'
        for identifier in greenbot.user.get(update.message.chat.id).getScripts():
            scriptsStr = scriptsStr + user.getLastRunEmoji(identifier) + ' ' + identifier + ' \(' + str(user.getScriptSchedule(identifier)) + '\)\n'
        context.bot.send_message(chat_id=update.effective_chat.id, text=scriptsStr, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='You have currently no scripts activated ' + random.choice(['😢', '😱', '🥺']) + '. Use /store to view for some.')

## Execute the requested script manually
# @param update
# @param context
def run(update, context):
    logger.debug('Command: run')
    if not greenbot.util.isGroupAdminOrDirectChat(update):
        return

    scriptIdentifier = greenbot.util.getUserSkriptIdentifier(update, context, 'run', 'Which script do you want to execute manually 🤔?')
    if not scriptIdentifier:
        return

    greenbot.util.updateOrReply(update, 'Executing ' + scriptIdentifier + '...')
    greenbot.user.get(update.effective_chat.id).runManually(scriptIdentifier, update, context)

## Activate the requested script identifier for the user
# @param update
# @param context
def activate(update, context):
    logger.debug('Command: activate')
    if not greenbot.util.isGroupAdminOrDirectChat(update):
        return

    scriptIdentifier = greenbot.util.getGlobalSkriptIdentifier(update, context, 'activate')
    if not scriptIdentifier:
        return

    # Okay, activate the script
    greenbot.user.get(update.effective_chat.id).activateScript(scriptIdentifier)
    greenbot.util.updateOrReply(update, random.choice(['👻', '🥳', '😁']) + ' Yay, the script is now active! Now use 👉 /schedule ' + scriptIdentifier + ' 👈 to execute it whenever you need (its currently scheduled ' + str(greenbot.user.get(update.effective_chat.id).getScriptSchedule(scriptIdentifier)) + ')...')

## Enable/disable the schedule for the scripts identifier for the user (its quite complex)
# @param update
# @param context
def schedule(update, context):
    logger.debug('Command: schedule')
    if not greenbot.util.isGroupAdminOrDirectChat(update):
        return

    scriptIdentifier = greenbot.util.getUserSkriptIdentifier(update, context, 'schedule', 'Which from your scripts did you mean ' + random.choice(['🤔', '🤨']) + '?')
    if not scriptIdentifier:
        return

    user = greenbot.user.get(update.effective_chat.id)
    scriptSchedule = user.getScriptSchedule(scriptIdentifier)

    # Show the current schedule if no params are given
    if len(context.args) >= 2:
        if context.args[1] == 'useInterval':
            scriptSchedule.enableInterval()
            user.write()
        elif context.args[1] == 'useDayTime':
            scriptSchedule.enableDayTime()
            user.write()
        elif context.args[1] == 'enable':
            scriptSchedule.enable()
            user.write()
        elif context.args[1] == 'disable':
            scriptSchedule.disable()
            user.write()
        elif context.args[1] == 'setInterval':
            # Did the user already appended his new interval?
            if len(context.args) == 3:
                try:
                    scriptSchedule.setInterval(int(context.args[2]))
                    user.write()
                except ValueError:
                    user.setCommandContext('schedule ' + context.args[0] + ' setInterval')
                    context.bot.send_message(chat_id=update.effective_chat.id, text='🤨 Thats not a number. Try again.')
                    return
            else:
                # No -> update the command context so the user can send his input into this command
                user.setCommandContext('schedule ' + context.args[0] + ' setInterval')
                context.bot.send_message(chat_id=update.effective_chat.id, text='Okay, send me now the new interval in minutes!')
                return

    if len(context.args) < 2 or context.args[1] == 'useInterval' or context.args[1] == 'useDayTime' or context.args[1] == 'setInterval' or context.args[1] == 'enable' or context.args[1] == 'disable':
        keyboard = []
        if scriptSchedule.isEnabled():
            if scriptSchedule.usesInterval():
                keyboard.append([InlineKeyboardButton('Change interval', callback_data='schedule ' + context.args[0] + ' setInterval')])
                keyboard.append([InlineKeyboardButton('Switch to day/time', callback_data='schedule ' + context.args[0] + ' useDayTime'),
                    InlineKeyboardButton('Disable schedule', callback_data='schedule ' + context.args[0] + ' disable')])
            else:
                keyboard.append([InlineKeyboardButton('Edit days', callback_data='schedule ' + context.args[0] + ' editDays'),
                    InlineKeyboardButton('Edit times', callback_data='schedule ' + context.args[0] + ' editTime')])
                keyboard.append([InlineKeyboardButton('Switch to interval', callback_data='schedule ' + context.args[0] + ' useInterval'),
                    InlineKeyboardButton('Disable schedule', callback_data='schedule ' + context.args[0] + ' disable')])
            greenbot.util.updateOrReply(update, '🕒 The current schedule is ' + str(scriptSchedule), reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard.append([InlineKeyboardButton('Enable schedule', callback_data='schedule ' + context.args[0] + ' enable')])
            greenbot.util.updateOrReply(update, '🕒 This schedule is currently inactive. You can always execute the script by using 👉 /run ' + scriptIdentifier + ' 👈.', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Toggle the day as requested
    if context.args[1] == 'toggleDay':
        scriptSchedule.toggleDay(int(context.args[2]))
        user.write()

    # Show menu for setting day(s) if called with editDays
    if context.args[1] == 'editDays' or context.args[1] == 'toggleDay':
        keyboard = []
        for dayId in range(0, 7):
            sign = ''
            if dayId in scriptSchedule.getDays():
                sign = '✅'
            else:
                sign = '❌'
            keyboard.append([InlineKeyboardButton(sign + ' ' + greenbot.schedule.Schedule.dayToString(dayId) + ' ' + sign, callback_data='schedule ' + context.args[0] + ' toggleDay ' + str(dayId))])
        keyboard.append([InlineKeyboardButton('Back', callback_data='schedule ' + context.args[0])])
        greenbot.util.updateOrReply(update, 'Select your active days...', reply_markup=InlineKeyboardMarkup(keyboard))

    # Apply the requested time change
    if context.args[1] == 'addTime':
        if len(context.args) == 3:
            try:
                scriptSchedule.addTime(context.args[2])
                user.write()
            except ValueError:
                user.setCommandContext('schedule ' + context.args[0] + ' addTime')
                context.bot.send_message(chat_id=update.effective_chat.id, text='🤨 Thats not a valid time. Try again.')
                return
        else:
            # No time given... Ask for one...
            user.setCommandContext('schedule ' + context.args[0] + ' addTime')
            context.bot.send_message(chat_id=update.effective_chat.id, text='Okay, send me the new time formatted like 11:42! But please note, that my timezone is currently +00:00.')
            return
    if context.args[1] == 'delTime':
        if len(context.args) == 3:
            scriptSchedule.removeTime(context.args[2])
            user.write()
        else:
            # No time given... Show list of available ones...
            if len(scriptSchedule.getTimes()) > 1:
                keyboard = []
                for time in scriptSchedule.getTimes():
                    keyboard.append([InlineKeyboardButton(time, callback_data='schedule ' + context.args[0] + ' delTime ' + time)])
                keyboard.append([InlineKeyboardButton('Back', callback_data='schedule ' + context.args[0] + ' editTime')])
                greenbot.util.updateOrReply(update, 'Which time do you want to remove?', reply_markup=InlineKeyboardMarkup(keyboard))
                return
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='🤨 At least one execution time is needed (otherwise just disable the schedule)!')          
                return      

    # Show menu for setting time/interval if called with editTime
    if context.args[1] == 'editTime' or context.args[1] == 'addTime' or context.args[1] == 'delTime' or context.args[1] == 'setInterval':
        keyboard = []
        keyboard.append([InlineKeyboardButton('Add', callback_data='schedule ' + context.args[0] + ' addTime'),
            InlineKeyboardButton('Remove', callback_data='schedule ' + context.args[0] + ' delTime')])
        keyboard.append([InlineKeyboardButton('Back', callback_data='schedule ' + context.args[0])])
        greenbot.util.updateOrReply(update, '🕒 The current schedule is ' + str(scriptSchedule), reply_markup=InlineKeyboardMarkup(keyboard))
        return

## Disable the script of the user
# @param update
# @param context
def deactivate(update, context):
    logger.debug('Command: deactivate')
    if not greenbot.util.isGroupAdminOrDirectChat(update):
        return

    scriptIdentifier = greenbot.util.getUserSkriptIdentifier(update, context, 'deactivate', 'Yes, yes - I see. Which script should I ' + random.choice(['fire 😎', 'disable 😬', 'remove 😬']) + '?')
    if not scriptIdentifier:
        return

    # Okay, activate the script
    greenbot.user.get(update.effective_chat.id).deactivateScript(context.args[0])
    greenbot.util.updateOrReply(update, random.choice(['💀', '👮‍♂️', '😵']) + ' Bye ' + context.args[0] + '. You have been deactivated.')

## Callback on exceptions - just shows the `I am broken...`-msg
# @param update
# @param context
def onError(update, context):
    if update is not None:
        greenbot.util.updateOrReply(update, random.choice(['🤯', '🤬', '😬', '🥴']) + ' I am broken...')
    raise context.error

## Callback on inline keyboard buttons (executes their internal command)
# @param update
# @param context
def onButton(update, context):
    query = update.callback_query
    logger.debug('Callback: Keyboard button pressed ' + str(query.data))
    query.answer()
    greenbot.util.executeVirtualCommand(update, context, query.data)

## Callback on messages, will only be executed, if the users command context is set
# @param update
# @param context
def onMessage(update, context):
    if update.message is not None and greenbot.user.get(update.message.chat.id).getCommandContext() is not None:
        # Always reset the context before executing the virtual command with the context
        cmdContext = greenbot.user.get(update.message.chat.id).getCommandContext()
        greenbot.user.get(update.message.chat.id).setCommandContext(None)
        greenbot.util.executeVirtualCommand(update, context, cmdContext + ' ' + update.message.text)
    # Otherwise we will just ignore the msg of the user...
