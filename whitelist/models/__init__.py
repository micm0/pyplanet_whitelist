from peewee import *
from pyplanet.core.db import TimedModel

class WhiteListPlayer(TimedModel):
  """
	Player login
	"""
  login = CharField(
		max_length=50,
		null=False,
	)