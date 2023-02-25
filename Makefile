run:
	python3 stele/app.py

setup: requirements.txt
	pip3 install -r requirements.txt

clean:
	rm -rf __pycache__

clean-all:
	rm -rf data
	mkdir data
	touch data/.gitkeep
	echo "." >> data/.gitkeep
	mkdir data/country
	touch data/country/.gitkeep
	echo "." >> data/country/.gitkeep


.PHONY: setup run clean clean-all