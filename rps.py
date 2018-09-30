from evennia import CmdSet
from evennia import Command


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
		"paper": "cuts",
		"lizard": "decapitates",
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
	"""Attack with the weapon of choice."""
	key = "attack"

	def func(self):
		# are we wielding a weapon
		# do we have a target
		# is the target defending itself
		# evaluate attack kind vs defense kind
		pass


class CmdRPS(Command):
	"""Displays a reminder of the rules of combat."""
	key = "rps"
	aliases = ["combat", "rules"]

	def func(self):
		self.msg("These are the rules of combat:")
		for a, b in BEATS.items():
			for d, v in b.items():
				self.msg('  %s %s %s' % (a, v, d))


class RPSCmdSet(CmdSet):
	"""Commands related to RPS combat."""
	key = "rpscmdset"

	def at_cmdset_creation(self):
		self.add(CmdAttack())
		self.add(CmdRPS())
