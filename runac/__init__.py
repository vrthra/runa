from . import (
	parser, blocks, liveness, typer, specialize,
	escapes, destructor, codegen, util, pretty
)
import os, subprocess, collections

PASSES = collections.OrderedDict((
	('liveness', liveness.liveness),
	('typer', typer.typer),
	('specialize', specialize.specialize),
	('escapes', escapes.escapes),
	('destruct', destructor.destruct),
))

def lex(src):
	'''Takes a string containing source code, returns list of token tuples'''
	return parser.lex(src)

def parse(fn):
	'''Takes a string containing file name, returns an AST Module node'''
	return parser.parse(fn)

def merge(mod):
	'''Merge AST Modules for core library files into the given Module'''
	for fn in os.listdir(util.CORE_DIR):
		if not fn.endswith('.rns'): continue
		fn = os.path.join(util.CORE_DIR, fn)
		mod.merge(blocks.module(parser.parse(fn)))

def show(fn, last):
	'''Show Runa high-level intermediate representation for the source code
	in the given file name (`fn`). `last` contains the last pass from
	PASSES to apply to the module before generating the IR.
	
	Returns a dict with function names (string or tuple) -> IR (string).
	Functions from modules other than the given module are ignored.'''
	mod = blocks.module(parser.parse(fn))
	names = [name for (name, code) in mod.code]
	
	merge(mod)
	for name, fun in PASSES.iteritems():
		fun(mod)
		if name == last:
			break
	
	data = {}
	for name, code in mod.code:
		if name not in names:
			continue
		data[name] = pretty.prettify(name, code)
	
	return data

def ir(fn):
	'''Generate LLVM IR for the given module. Takes a string file name and
	returns a string of LLVM IR, for the host architecture.'''
	mod = blocks.module(parser.parse(fn))
	merge(mod)
	for name, fun in PASSES.iteritems():
		fun(mod)
	return codegen.generate(mod)

def compile(ir, outfn):
	'''Compiles LLVM IR into a binary. Takes a string file name and a string
	output file name. Writes the IR to a temporary file, then calls clang on
	it. (Shelling out to clang is pretty inefficient.)'''
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
