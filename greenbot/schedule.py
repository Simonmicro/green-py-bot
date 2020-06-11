import schedule
import logging
import greenbot.repos

class Schedule:
    __days = set([0, 1, 2, 3, 4, 5, 6]) # 0-6 are the weekdays
    __times = set(['00:00'])
    __interval = 10
    __useInterval = False
    __jobs = []
    __forSkriptIdentifier = None
    __forUser = None
    __lastRunResult = 1 # 0 = Success, 1 = Warning, 2 = Failed

    # Simple class to wrap the different parameters
    def __init__(self, obj = None):
        if obj is not None:
            self.load(obj)
        return

    def load(self, obj):
        self.__days = set(obj['days'])
        self.__interval = obj['interval']
        self.__useInterval = obj['useInterval']
        self.__times = set(obj['times'])

    def save(self):
        return {
            'days': list(self.__days),
            'interval': self.__interval,
            'useInterval': self.__useInterval,
            'times': list(self.__times),
        }

    def __str__(self):
        return self.toString()

    def toString(self):
        if self.__useInterval:
            return 'every ' + str(self.__interval) + ' minutes'
        return self.daysToString() + ' ' + self.timeToString()

    def daysToString(self):
        if len(self.__days) == 7:
            return 'every day'
        return ', '.join(self.dayToString(x) for x in self.__days)

    def timeToString(self):
            return 'at ' + ', '.join(self.__times)

    @staticmethod
    def dayToString(dayId):
        if dayId == 0:
            return 'Monday'
        if dayId == 1:
            return 'Tuesday'
        if dayId == 2:
            return 'Wednesday'
        if dayId == 3:
            return 'Thursday'
        if dayId == 4:
            return 'Friday'
        if dayId == 5:
            return 'Saturday'
        if dayId == 6:
            return 'Sunday'
        return 'Unknown'

    def setInterval(self, interval):
        self.__interval = interval
        self.__apply()

    def getDays(self):
        return self.__days

    def toggleDay(self, dayId):
        if dayId in self.__days:
            self.__days.remove(dayId)
        else:
            self.__days.add(dayId)
        self.__apply()

    def addTime(self, time):
        self.__times.add(time)
        self.__apply()

    def removeTime(self, time):
        self.__times.remove(time)
        self.__apply()

    def getInterval(self):
        return self.__interval

    def enableInterval(self):
        self.__useInterval = True

    def enableDayTime(self):
        self.__useInterval = False

    def usesInterval(self):
        return self.__useInterval

    def __apply(self):
        self.deactivate()

        # Create new job...
        if self.__forUser is not None and self.__forSkriptIdentifier is not None:
            if self.__useInterval:
                self.__jobs.append(schedule.every(self.__interval).minutes.do(Schedule.run, self))
            else:
                for dayId in self.__days:
                    print('Activating for day id ' + str(dayId))
                    for time in self.__times:
                        print('for time ' + time)
                        self.__jobs.append(schedule.every().monday.at(time).do(Schedule.run, self))
            logging.debug('Activated schedule for user id ' + str(self.__forUser.getUID()) + ', script ' + self.__forSkriptIdentifier)

    def activate(self, user, skriptIdentifier):
        # Store data for next run
        self.__forSkriptIdentifier = skriptIdentifier
        self.__forUser = user

        # Apply new info
        self.__apply()

    def deactivate(self):
        # Remove old job (if existent)
        if len(self.__jobs) != 0:
            for job in self.__jobs:
                schedule.cancel_job(job)
            self.__jobs = []
            logging.debug('Deactivated schedule for user id ' + str(self.__forUser.getUID()) + ', script ' + self.__forSkriptIdentifier)

    def getLastRunEmoji(self):
        if self.__lastRunResult == 0:
            return '✅'
        elif self.__lastRunResult == 1:
            return '⚠️'
        elif self.__lastRunResult == 2:
            return '❌'
        else:
            return '🔥'

    def run(self):
        logging.debug('Running schedule for user id ' + str(self.__forUser.getUID()) + ', script ' + self.__forSkriptIdentifier)
        try:
            # Load the module
            module = greenbot.repos.getModule(self.__forSkriptIdentifier)

            # And call the scheduled function (if available)
            if hasattr(module, 'scheduledRun'):
                module.scheduledRun(self.__forUser)
                self.__lastRunResult = 0
            else:
                logging.error('Ooops, the script ' + self.__forSkriptIdentifier + ' has no scheduledRun(user) method!')
        except:
            self.__lastRunResult = 2
            pass
