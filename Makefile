setup: requirements.txt
	pip3 install -r requirements.txt

clean:
	rm -rf __pycache__

clean-all:
	rm -rf data
	mkdir data
	touch data/.gitkeep
	echo "." >> data/.gitkeep

run:
	python3 stele/app.py

.PHONY: setup run clean clean-all