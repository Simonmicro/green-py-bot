import random
import greenbot.repos
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def updateOrReply(update, *args, **kwargs):
    # Detect if we are inside a callback (in that case we will update the msg) or just inside a handler
    if update.callback_query is not None:
        # Triggered by callback -> edit last msg
        return update.callback_query.edit_message_text(*args, **kwargs)
    else:
        # Okay, no callback -> reply with new msg
        return update.effective_message.reply_text(*args, **kwargs)

def getGlobalSkriptIdentifier(update, context, commandName):
    # Are we missing the identifier or is it invalid?
    if len(context.args) < 1 or not greenbot.repos.resolveIdentifier(context.args[0])[0] in greenbot.repos.getRepos():
        keyboard = []
        for repoName in greenbot.repos.getRepos():
            keyboard.append([InlineKeyboardButton(repoName, callback_data='{"cmd":"' + commandName + '", "params": ["' + greenbot.repos.makeIdentifier(repoName) + '"]}')])
        greenbot.util.updateOrReply(update, 'Okay, now tell me in which repository I should look 🤔', reply_markup=InlineKeyboardMarkup(keyboard))
        return False
    # ...or the script part? (Intended, if we are showing the keyboard)
    elif not greenbot.repos.resolveIdentifier(context.args[0])[1] in greenbot.repos.getScripts(greenbot.repos.resolveIdentifier(context.args[0])[0]):
        # Show keyboard with key for every script
        keyboard = []
        for scriptName in greenbot.repos.getScripts(greenbot.repos.resolveIdentifier(context.args[0])[0]):
            keyboard.append([InlineKeyboardButton(scriptName, callback_data='{"cmd":"' + commandName + '", "params": ["' + greenbot.repos.makeIdentifier(context.args[0], scriptName) + '"]}')])
        greenbot.util.updateOrReply(update, 'And which script do you wish to activate ' + random.choice(['🧐', '🤨']) + '?', reply_markup=InlineKeyboardMarkup(keyboard))
        return False

    return context.args[0]

def getUserSkriptIdentifier(update, context, commandName):
    # Show keyboard for active scripts
    if len(context.args) < 1 or not greenbot.repos.validateIdentifier(context.args[0]):
        # Show keyboard with key for every active script
        keyboard = []
        for scriptIdentifier in greenbot.user.get(update.effective_chat.id).getScripts():
            keyboard.append([InlineKeyboardButton(scriptIdentifier, callback_data='{"cmd":"' + commandName + '", "params": ["' + scriptIdentifier + '"]}')])
        greenbot.util.updateOrReply(update, 'Yes, yes - I see. Which script should I ' + random.choice(['fire 😎', 'disable', 'remove']) + '?', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    return context.args[0]
