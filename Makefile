build: clean
	# Source distribution
	python3 setup.py sdist
	# Wheel for python3
	python3 setup.py bdist_wheel

clean:
	# Clean up files of previous builds
	rm -rf dist
	rm -rf build
	rm -rf zettels.egg-info

install:
	# install locally in developer mode. Probably requires root privileges
	python3 -m pip install -e .

test-release:
	# Upload to testpypi
	twine upload -r pypitest dist/*

release:
	# Upload to pypi
	twine upload dist/*
