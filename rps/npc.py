from evennia import CmdSet
from evennia import Command
from typeclasses.objects import Object


class CmdGuard(Command):
	"""Asks this NPC to guard an exit.

	Syntax: guard <item or exit>
	"""
	key = "guard"

	def func(self):
		args = self.args.strip()
		if not args:
			self.msg('Guard what? Try typing "help guard".')
			return
		target = self.obj.location.search(args)
		if not target:
			self.msg("I don't see that here?")
			return
		if not target.access(self.caller, "control"):
			self.msg("That isn't yours to guard!")
			return
		guarding = False
		lock_str = "attr(defeated_%s)" % self.obj.id
		if target.locks.get("traverse") == "traverse:all()":
			guarding = True
			target.locks.add("traverse:%s" % lock_str)
			self.obj.db.guarding = target.id
		if target.locks.get("get") == "get:all()":
			guarding = True
			self.obj.db.guarding = target.id
			target.locks.add("get:%s" % lock_str)
		if not guarding:
			self.msg("I don't know how to guard that. Maybe it's already guarded?")


class RPSNPCCmdSet(CmdSet):
	"""Commands for interacting with an RPS NPC."""
	key = "rpsnpccmdset"

	def at_cmdset_creation(self):
		self.add(CmdGuard())


class RPSNPC(Object):
	"""An RPS-combat-capable NPC."""

	def at_object_creation(self):
		"""Configure appropriate locks."""

		# only accept commands from the creator of this NPC
		self.cmdset.add(RPSNPCCmdSet, permanent=True)
		self.locks.add("call:id(%s)" % self.location.id) # created in creator's inventory

		# NPCs can't be picked up
		self.locks.add("get:false()")
		self.db.get_err_msg = "You can't pick %s up. You aren't their type." % self

	def at_init(self):
		self.ndb.weapon = "sword"
		self.ndb.defend = ["Spock"]

	def at_defeat(self, opponent):
		"""Announces the defeat and marks the victor with an attribute."""

		msg = 'The instructor says: "%s"' % (
			self.db.defeat_cry or 'Lo, I am defeated!')
		self.location.msg_contents(msg)
		setattr(opponent.db, 'defeated_%s' % self.id, True)
