from typeclasses.objects import Object


class RPSNPC(Object):
	"""An RPS-combat-capable NPC."""

	def at_object_creation(self):
		"""Configure appropriate locks."""

		# NPCs can't be picked up
		self.locks.add("get:false()")
		self.db.get_err_msg = "You can't pick %s up. You aren't their type." % self

	def at_init(self):
		self.ndb.weapon = "sword"
		self.ndb.defend = ["Spock"]
