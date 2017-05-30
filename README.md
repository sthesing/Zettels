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

1. Clone or download the repository. 
2. Run `zettels_setup.py` or `zettels.py --setup` – follow the interactive setup process
3. Run `zettels.py` once without any parameters to initially build the index.

## Usage

Run `zettels.py -h` for a complete list of options. Some examples:

Build or update the index:
```
zettels.py
```

### Querying the index

Zettels has the `query` (shorthand `q`) subcommand to query the index.

Show a list of all zettels:
```
zettels.py query
```
Show a list of all zettels, but update the index first:
```
zettels.py query -u
```
Show info about a specific zettel, e.g. file1.md:
```
zettels.py query file1.md
```
Show a list of followups of a specific zettel, e.g. file1.md:
```
zettels.py query -f file1.md
```
Show a list of zettels a specific zettel links to, e.g. file1.md:
```
zettels.py query -t file1.md
```
Show a list of zettels linking to a specific zettel, e.g. file1.md:
```
zettels.py query -i file1.md
```

### Try it with example data
Run e.g.
```
zettels.py q -s examples/zettels.cfg.yaml examples/Zettelkasten/file1.md
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
The output of the `query` subcommand can be tweaked to your needs by editing 
it in the settings file (default: ~/.config/zettels.cfg.yaml).

It's a python format string that receives the title of a zettel and its path 
as arguments. 
The default output format is:
```
'{0[0]:<50}| {0[1]}''
```

These can be accessed by `{0[0]}` (title) and `{0[1]}` (path).

If you want the output to be e.g. only the path, change the `outputformat` 
setting to
```
{0[1]}
```

See the 
[Python Format String Syntax](https://docs.python.org/3.6/library/string.html#format-string-syntax) 
for details.

## Requirements

- Python 3.x
- [grep](https://www.gnu.org/software/grep/) – Your Python runtime must be
able to find and execute grep.
- [PyYaml](http://pyyaml.org/)
