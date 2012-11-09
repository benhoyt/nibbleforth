Nibbleforth - A very compact stack machine (Forth) bytecode
-----------------------------------------------------------

This is just an idea at this point. I don't have time to work on it further at
this point. Posting my notes on GitHub for the record.

We'd been struggling with code size issues on one of our projects. We're using
one microcontroller with 32KB of flash (program memory), only 15KB of which we
have allocated to code size. So it was pretty tight, and gcc even with `-Os`
wasn't producing very tight code.

So I started thinking about the smallest possible instruction set. I'm pretty
familiar with
[Forth](http://en.wikipedia.org/wiki/Forth_(programming_language)) and stack-
based virtual machines, so that's where my thoughts went. My basic ideas were:

Use **variable-length instruction opcodes**, and assign the most frequently-
used opcodes the lowest numbers so they can be encoded in the smallest
instructions. Kind of like
[UTF-8](http://en.wikipedia.org/wiki/UTF-8#Description), or the [base 128
varints](https://developers.google.com/protocol-buffers/docs/encoding#varints)
used in Google protocol buffers -- but using nibbles instead of bytes.

Taken to the extreme, this is [Huffman
coding](http://en.wikipedia.org/wiki/Huffman_coding), which uses a variable
number of *bits* to encode each symbol, with the most frequently-used symbols
getting the shortest bit codes. However, I suspect Huffman decoding would be
too slow for an embedded virtual machine.

My hunch was that the most common instructions are used *way* more than the
majority, meaning that encoding the most common opcodes in 4 bits and the
slightly less common ones in 8 bits would be a huge gain.

And my hunch was correct -- I analyzed a bunch of Forth programs that come
with [Gforth](http://bernd-paysan.de/gforth.html), and `exit` is by far the
most common in most programs, with `jz` and `jmp` often close behind, and then
the others usually varied from program to program.

Perhaps even more importantly, is to use **Forth-like [token
threading](http://en.wikipedia.org/wiki/Threaded_code#Token_threading)** on top
of this, so it's not just primitive opcodes that can be encoded small, but any
user-defined word too. So instruction 0 might be "return", instruction 1 might
be "jump-if-zero", instruction 2 might be "user-function-1", etc. And there's
be a tiny VM interpreter that looked up these numbers in a table (of 16-bit
pointers) to get their actual address.

And your compiler would do this frequency tokenization globally on each
program, so for each program you compiled you'd get the best results for the
instructions/words it used.

On top of that, you could **combine common sequences of instructions** into
their own words (i.e., calls to a function). Pretty much like dictionary-based
compression algorithms like LZW uses -- in fact, you might use the greedy [LZW
algorithm](http://en.wikipedia.org/wiki/LZW) to find them.

C compilers do [common subexpression
elimination](http://en.wikipedia.org/wiki/Common_subexpression_elimination),
but it's only ever done within a single function, and we could do it globally,
making it much more powerful and compressive. You'd have to be careful and use
a few heuristics so you didn't actually make it bigger by factoring too much,
or factor so much it was too too slow.

Note that Forth programmers factor into tiny words in any case, so this may
not gain as much for folks who already program in a heavily-factored style
with tiny words/functions. Have you ever considered that when programmers
factor things into functions, they're basically running a [dictionary
compression](http://en.wikipedia.org/wiki/Dictionary_coder) algorithm
manually?

Also you could **inline any Forth "words" that were only used once**, as it
wouldn't help code size to have them as separate words. C compilers do this,
but only on a file-local basis.

In fact, that's a common pattern with C compilers -- they can only optimize
local to a function, or at most, local to a file. The linker can remove unused
functions, but it can't really do any further optimization.

In any case, it would be a fun project to work on at some stage. :-)

== References ==

* [Improving Code Density Using Compression Techniques]() by Lefurgy, Bird, Chen, Mudge -- this one has two similarites to my idea: compressing into nibbles, and rolling common sequences of instructions into a function call
* [Generation of Fast Interpreters for Huffman Compressed Bytecode](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.156.2546&rep=rep1&type=pdf) by Latendresse and Feeley
* [Anton Ertl's papers on Forth interpreters](http://www.complang.tuwien.ac.at/projects/interpreters.html) -- I haven't read this stuff, but some of it looks relevant and interesting
