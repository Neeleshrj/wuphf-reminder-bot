import datetime
import re
from discord.ext import commands
from utilities.timing import diff_timestamp

class parse:

	def parse_reminder(self,desc,date,time):
		regex_date = r'^[0-3][0-9]-[0-1][0-9]-[0-9][0-9]$'
		regex_time = r'^[0-2][0-9]:[0-6][0-9]$'

		if re.match(regex_date,date)==None or re.match(regex_time,time)==None:
			raise commands.BadArgument('Date or Time format not quite right, type ">helpme" to know the required format')	
		
		else:
			diff = diff_timestamp(date,time)
			if diff <= 0:
				raise commands.BadArgument("This Date and Time is already past, hope you didn't miss something important")
			elif diff > 7889238:
				raise commands.BadArgument("Sorry! reminders can only be set for dates atmost 3 months apart from now.")				