from util import Error, ParseError
from . import (
	parser, blocks, liveness, typer, specialize, escapes, destructor, codegen,
)
import os, subprocess, collections

BASE = os.path.dirname(__path__[0])
CORE_DIR = os.path.join(BASE, 'core')

PASSES = collections.OrderedDict((
	('liveness', liveness.liveness),
	('typer', typer.typer),
	('specialize', specialize.specialize),
	('escapes', escapes.escapes),
	('destruct', destructor.destruct),
))

def merge(mod):
	for fn in os.listdir(CORE_DIR):
		if not fn.endswith('.rns'): continue
		fn = os.path.join(CORE_DIR, fn)
		mod.merge(blocks.module(parser.parse(fn)))

def ir(fn):
	mod = blocks.module(parser.parse(fn))
	merge(mod)
	for name, fun in PASSES.iteritems():
		fun(mod)
	return codegen.generate(mod)

def compile(ir, outfn):
	
	name = outfn + '.ll'
	with open(name, 'wb') as f:
		f.write(ir)
	
	try:
		subprocess.check_call(('clang', '-o', outfn, name))
	except OSError as e:
		if e.errno == 2:
			print 'error: clang not found'
	except subprocess.CalledProcessError:
		pass
	finally:
		os.unlink(name)
