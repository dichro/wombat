"""RPS Combat for Wombat.

RPS (Rock-Paper-Scissors(-Lizard-Spock, in this case)) is used to determine the outcome of combat.

The sequence of commands to engage in combat with a dagger that is on the floor:
get dagger (this unlocks all of the following commands)
defend Spock (this selects the defensive stance that will be used if the player is attacked)
attack robin scissors (this attacks an object named robin using the scissors stance - this is unrelated to the player's own defense stance)

Now, if:
robin is present, and
robin has acquired a weapon, wielded it, and set a defensive stance

Then combat will be decided by matching the attacker's attack stance against the defender's defensive stances according to the rules of RPS.
The loser will be forced to drop their weapon.

Things to fix:
* all weapons add attack/defend to their holder's command sets. This makes commands awkward when carrying multiple weapons. Best
fix may be to have a "wield" in default_commands, and only the wielded object activates its combat commands.
* having multiple weapons named the same thing does the wrong thing with forced drops when losing combat
* add armor! Armor gets dropped in preference to the wielded weapon.
"""

from evennia import CmdSet
from evennia import Command
from typeclasses.objects import Object


# Each value in BEATS describes that the stances that the corresponding key beats.
# The value in the sub-dictionary provides the verb that describes the victory.
BEATS = {
	"rock": {
		"scissors": "blunts",
		"lizard": "crushes",
	},
	"paper": {
		"rock": "covers",
		"Spock": "disproves",
	},
	"scissors": {
		"paper": "cut",
		"lizard": "decapitate",
	},
	"lizard": {
		"paper": "eats",
		"Spock": "poisons",
	},
	"Spock": {
		"scissors": "disassembles",
		"rock": "vaporizes",
	},
}


class CmdAttack(Command):
	"""Attack with your weapon.

	Usage: attack <target> <stance>

	Examples:
		attack Miki scissors              -- attack Miki using the scissors stance

	Try typing "rules" to learn more about stances.
	"""
	key = "attack"

	def func(self):
		args = self.args.strip().split()
		if len(args) < 2:
			self.msg('Attack whom, and how? Try typing "help attack"')
			self.caller.location.msg_contents('%s fumbles with their weapon' % self.caller, exclude=self.caller)
			return
		if not self.caller.ndb.defend:
			self.msg('You must first be defending before you can attack! Try "help defend"')
			self.caller.location.msg_contents('%s fumbles with their weapon' % self.caller, exclude=self.caller)
			return
		attacks = args[1:]
		invalid = set(a for a in attacks if a not in BEATS)
		if invalid:
			self.msg('These are not attacks (%s)! Try "rules"' % ', '.join(invalid))
			self.caller.location.msg_contents('%s fumbles with their weapon' % self.caller, exclude=self.caller)
			return
		target = self.caller.search(args[0])
		if not target:
			return
		if target == self.caller:
			self.msg('Why would you do that?')
			self.caller.location.msg_contents('%s fumbles with their weapon' % self.caller, exclude=self.caller)
			return
		if not target.ndb.defend:
			self.msg('%s is defenseless, you cad!' % target)
			self.caller.location.msg_contents('%s waves their weapon at %s threateningly' % (self.caller, target), exclude=self.caller)
			return

		# OK, now we're actually attacking
		for attack in attacks:
			defense = target.ndb.defend[0]
			if len(target.ndb.defend) > 1:
				# rotate defensive stances for the next attack
				target.ndb.defend = target.ndb.defend[1:] + target.ndb.defend[0:0]
			if defense in BEATS[attack]:
				# attacker wins
				self.caller.msg("Your %s %s %s's %s!" % (
					attack, BEATS[attack][defense], target, defense))
				self.caller.location.msg_contents("%s's %s %s %s's %s!" % (
					self.caller, attack, BEATS[attack][defense], target, defense),
					exclude=self.caller)
				try:
					target.at_defeat(self.caller)
				except AttributeError, e:
					target.execute_cmd('drop 1-%s' % target.ndb.weapon)
				return
			elif attack in BEATS[defense]:
				# defender wins
				# TODO(dichro): make the verb passive? I need a grammar engine.
				self.caller.location.msg_contents("%s's %s %s %s's %s!" % (target, defense, BEATS[defense][attack], self.caller, attack))
				self.caller.execute_cmd('drop 1-%s' % self.caller.ndb.weapon)
				return
			else:
				# tie
				self.caller.location.msg_contents('%s attacks %s but neither prevails!' % (self.caller, target))


class CmdDefend(Command):
	"""Selects a defensive stance for combat.

	Usage: defend <stance>

	Examples:
		defend         -- shows current stance
		defend Spock   -- sets a defensive stance of "Spock"
		defend none    -- stop defending

	Try typing "rules" to learn more about stances.
	"""
	key = "defend"
	aliases = ["block"]

	def func(self):
		stances = self.args.strip().split()
		if len(stances) == 1 and stances[0] == "none":
			del self.caller.ndb.defend
			stances = None # fallthrough to the next block for caller feedback
		if not stances:
			if self.caller.ndb.defend:
				self.msg('Your defensive status is: %s' % ', '.join(self.caller.ndb.defend))
			else:
				self.msg('You are not in a defensive stance at present')
			return
		invalid = set(s for s in stances if s not in BEATS)
		if len(invalid):
			self.msg("Usage: defend <stance> [<stance>...]\nTry 'combat' for more information")
			return
		self.caller.ndb.defend = stances
		self.caller.ndb.weapon = self.obj
		self.caller.location.msg_contents('%s waves their %s around threateningly' % (self.caller, self.obj), exclude=self.caller)
		self.msg('You adopt a defensive stance.')


class CmdRPS(Command):
	"""Displays a reminder of the rules of combat."""
	key = "rps"
	aliases = ["combat", "rules"]

	def func(self):
		self.msg("These are the rules of combat:")
		for attack, beats in BEATS.items():
			for defeats, verb in beats.items():
				self.msg('  %s %s %s' % (attack, verb, defeats))


class RPSCmdSet(CmdSet):
	"""Commands related to RPS combat."""
	key = "rpscmdset"

	def at_cmdset_creation(self):
		self.add(CmdAttack())
		self.add(CmdDefend())
		self.add(CmdRPS())


class RPSWeapon(Object):
	"""Base typeclass for RPS weapons."""

	def at_object_creation(self):
		self.cmdset.add_default(RPSCmdSet, permanent=True)
		self.locks.add("call:holds(%i)" % self.id)

	def move_to(self, *args, **kwargs):
		"""Unwields this weapon before dropping."""
		wielder = self.location
		ret = super(RPSWeapon, self).move_to(*args, **kwargs)
		if ret and wielder and wielder.ndb.weapon == self:
			# we've lost the object
			del wielder.ndb.defend
			del wielder.ndb.weapon
		return ret
