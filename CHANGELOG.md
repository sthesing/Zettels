# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
