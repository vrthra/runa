Basics
======

Goal: a Python-like static language, i.e. doing away with much of the C noise.
To do this, I'd like to get rid of explicit pointer syntax; all mutable types
whose size is larger than a word will be passed by reference. To make that
possible, I need to get rid of outparams. To enable that, I need multiple
return values.

More C noise elimination: return on errors by default, i.e. exception flow.
Also, limit the amount of explicit types. Use local type inference for most
declarations, with types for function signatures (and possibly generics).


Secondary goals
===============

 * Definitely want operator overloading
 * Deterministic (RAII-like) memory management, no GC
 * Minimal generics rather then templates
 * Error propagation by default, light-weight exceptions
 * Optional, but inclusive standard library
 * Easy FFI would be nice


Implementation notes
====================

Standard streams:

 - stdin: 0 (unistd.h: STDIN_FILENO)
 - stdout: 1 (unistd.h: STDOUT_FILENO)
 - stderr: 2 (unistd.h: STDERR_FILENO)

Context managers:

 - def __enter__(self)
 - def __exit__(self, type, value, traceback)

Generics:

Can we prevent keeping a pointer to the class inside every object? Only if
the compiler knows all of the types in advance. Alternative: keep a pointer to
the type of the contained type in containers. Simple first problem: str()
should accept any type and call its __str__() method.

Covariance and contravariance:

If B is a subtype of A, then all member functions of B must return the same or
a narrower set of types as A; the return type is said to be covariant. On the
other hand, if the member functions of B take the same or broader set of
arguments compared with the member functions of A, the argument type is said
to be contravariant. The problem for instances of B is how to be perfectly
substitutable for instances of A. The only way to guarantee type safety and
substitutability is to be equally or more liberal than A on inputs, and to
be equally or more strict than A on outputs.


How a Pratt parser works
========================

nud: null denotation, used when token appears at beginning of construct
led: left denotation, used when it appears inside the construct (left of rest)
lbp: left binding power, controls operator precedence; higher binds to right

- start by looking at first token, calling nud() on it
- if lbp of next is >= given rbp, call led for next


Memory model
============

Goals:

- Should not leak memory or double-free (d0h!)
- Should be easy to use, not much of a distraction in the code
- Should be deterministic; no separate garbage collection
- Should support the language's semantics
- Should be efficient/performant


Ideas
-----

Allocate statically-sized variables on the caller's stack. Ignoring global
variables for now, memory references can only flow up the stack in (a) return
variables (which got allocated on the upstream stack in the first place) and
(b) as part of a larger structure that gets returned up the stack.

Dynamically-sized variables must be allocated on the heap. They are always
wrapped in a stack-allocated variable to keep a reference around. Multiple
wrappers are allowed to reference to the same block of heap-allocated
memory (because these blocks may be large and copying them would be expensive
in both memory and CPU time). The memory must be freed once all wrappers
get cleaned up; reference counting seems like a good fit for this.
