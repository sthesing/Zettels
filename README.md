# Zettels
Zettels is a command line tool implementing Niklas Luhmann's system of a 
"Zettelkasten".

It's still in alpha stage and probably very buggy.

## What does Zettels do?

Zettels is a command line tool to index markdown files (your 
zettels). It reads YAML-metadata blocks as defined by [pandoc](http://pandoc.org/MANUAL.html#extension-yaml_metadata_block) and also
parses the 
[markdown hyperlinks](https://daringfireball.net/projects/markdown/syntax#link)
in each file.
    
The resulting index contains the metadata and the targets of the hyperlinks.

Have a look at the files in `examples/Zettelkasten` and `examples/index.yaml` 
to get a better idea.

Zettels can also be used to query the index. The output can then be piped
to other tools (like grep or as arguments for the text editor of your choice).

It's intended to be used for a "Zettelkasten" like Niklas Luhmann used it.

## What the heck is a Zettelkasten?

"Zettel" is German for "note" or "slip of paper". "Kasten" is German for "box".
Think of old style library catalogues.

Obviously, this piece of software is not a box of paper sheets. However, 
[Niklas Luhmann](https://en.wikipedia.org/wiki/Niklas_Luhmann) used such a
box in a very specific way for his academic work. 

A wonderful introduction in Luhmann's system of a Zettelkasten are the slides
of a talk by Daniel Lüdecke: [Introduction to Luhmann's Zettelkasten-Thinking](https://strengejacke.wordpress.com/2015/10/07/introduction-to-luhmanns-zettelkasten-thinking-and-its-technical-implementation/)

In Luhmann's own words: [Communicating with Slip Boxes](http://luhmann.surge.sh/communicating-with-slip-boxes) (translation of 
"Kommunikation mit Zettelkästen").

If you speak German, there's more:

- Luhmann, Niklas (1981): Kommunikation mit Zettelkästen. Ein Erfahrungsbericht. 
in: H. Baier / H.M. Kepplinger / K. Reumann (Eds.), Öffentliche Meinung und sozialer
Wandel. Opladen: Westdeutscher Verlag. pp. 22-28
- Daniel Lüdecke: [Luhmanns Arbeitsweise im elektronischen Zettelkasten](https://strengejacke.wordpress.com/2015/09/08/luhmanns-arbeitsweise-im-elektronischen-zettelkasten/)
- Thomas Schlesinger: [Wissen konservieren und kuratieren mit dem Zettelkasten nach Niklas Luhmann](http://www.schlesisblog.de/2016/09/wissen-konservieren-und-kuratieren-mit.html)
- Universität Bielefeld: Video - [Einblicke in das System der Zettel - Geheimnis um Niklas Luhmanns Zettelkasten](https://youtu.be/4veq2i3teVk)

## What, no GUI?

True. A GUI for querying the index would be nice. However, as such, Zettels
doesn't provide one. It is intended to be used in a toolchain of UNIX-tools.

I myself edit my Zettelkasten in my favourite text editor and have created 
a little module that allows me to query its index from there. So, if you use
Textadept or don't care which text editor you use, have a look at 
[ta-zettels](https://github.com/sthesing/ta-zettels).

### Alternatives

If you're looking for a GUI, all-in-one approach to implementing Luhmann's idea
into software, I can recommend Daniel Lüdecke's [Zettelkasten](http://zettelkasten.danielluedecke.de/) (sjPlot/Zettelkasten).

## Installation and setup

1. Install using pip (or pip3, depending on your OS): `pip install zettels`
2. Run `zettels --setup` – follow the interactive setup process
3. Run `zettels -su` once to initially build the index.

## Usage

Run `zettels -h` for a complete list of options. Some 
examples:

### Build or update the index:
```
zettels -su
```
Shorthand for `--silentupdate`

### Querying the index
Show a list of all zettels:
```
zettels
```
Show a list of all zettels, but update the index first:
```
zettels -u
```
Show info about a specific zettel, e.g. file1.md:
```
zettels file1.md
```
Show info about two zettels, e.g. file1.md and file2.md:
```
zettels file1.md file2.md
```
Show a list of followups of a specific zettel, e.g. file1.md:
```
zettels -f file1.md
```
Show a list of zettels a specific zettel links to, e.g. file1.md:
```
zettels -l file1.md
```
Show a list of zettels linking to a specific zettel, e.g. file1.md:
```
zettels -i file1.md
```
And finally, a bit of fun with pipes:
Let's say you want to see which zettels apart from file1.md 
itself link to the followups of file1.md:
```
zettels -f file1.md | zettels -i | grep -v file1.md
```

### Try it with example data
Run e.g.
```
zettels -s examples/zettels.cfg.yaml examples/Zettelkasten/file1.md
```

## Zettel format

Zettels doesn't require your markdown files to have a metadata block. But to 
be really effective parts of your Zettelkasten, a YAML metadata block 
containing an entry for `title`, `tags` and `followups` is necessary.

```{.yaml}
---
title:  'Example Zettel'
tags: [example, question]
followups: [file.md, subdir/anotherfile.md, ../yetanotherfile.md]
...
```

Entries in `followups` should be relative to the zettel. The same is true for
hyperlinks in the zettel body.
The metadata block may contain a variety of other entries (e.g. `author`, 
`date`) – maybe for other tools, like pandoc – but those other entries are 
ignored by Zettels and do not become part of Zettels' index.

## Output format

The output can be tweaked to your needs. In the 
settings file (default: ~/.config/zettels.cfg.yaml), you'll find two settings:

- `outputformat` - standard format
- `prettyformat` - used when Zettels is called with the `--pretty` flag

These output formats are given as 
[Python Format Strings](https://docs.python.org/3.6/library/string.html#format-string-syntax).
Query output consists of two fields that these format strings can process:

    1. title - accessible by `'{0[0]}'`
    2. path (relative to the Zettelkasten directory) - accessible by `'{0[1]}'`

By default the formats are:
```
outputformat: '{0[1]}'
prettyformat: '{0[0]:<40}| {0[1]}'
```

Standard `outputformat` just outputs the path(s) of the query results, 
`prettyformat` is a pseudo-table with the title(s) of the query result in 
the first column (which is at least 40 characters wide), and the path(s) in 
the second column.

The output format can also be tweaked on a per call basis with the `-o` flag,
that takes a custom output format.

See the 
[Python Format String Syntax](https://docs.python.org/3.6/library/string.html#format-string-syntax) 
for details.

## Requirements

- Python 3.x
- [grep](https://www.gnu.org/software/grep/) – Your Python runtime must be
able to find and execute grep.
- [PyYaml](http://pyyaml.org/)
- [pathspec](https://pypi.python.org/pypi/pathspec)>=0.5.0
