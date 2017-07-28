# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
### Changed

### Deprecated
### Removed
### Fixed
### Security


## [0.6.0]
### Added
### Changed
- Adjusted ignore settings in default settings file to ignore hidden 
  directories, too.
- Properly handling pandoc's specs for YAML metadata, now. Metadata block now 
  may also end with '---'.
- Reimplemented function to find updated files. Should be much faster now, 
  when dealing with a large number of Zettels. Depending on UNIX tool `find`
  now, tested against GNU find.
### Deprecated
### Removed
### Fixed
- With every run of zettels, the index was built from scratch. Now it only 
  updates it if files in the Zettelkasten directory have changed.
### Security

## [0.5.0] - 2017-06-09
### Added
- This change log
### Changed
- dropped the `query` (or `q`) subcommand. So what used to be `zettels q` is 
  now just `zettels`.
- renamed the `-t` (or `--targets`) flag to  `-l` (or `--links`)
- First column of the default `pretty` output format is now 40 spaces wide
### Fixed
- Issue with external links inside the markdown files (#9)
