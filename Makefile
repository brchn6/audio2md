.PHONY: all setup clean dist

all: setup

# One-time setup on cluster
setup:
	./audio2md setup

# Full pipeline on an audio file
run:
	./audio2md $(AUDIO)

# Fetch results
fetch:
	./audio2md fetch $(OUTPUT)

# Clean up cluster working directory
clean:
	ssh $(CLUSTER) "rm -rf ~/dev/audio2md/input.* ~/dev/audio2md/*.md ~/dev/audio2md/*.out ~/dev/audio2md/*.err"
	rm -f meeting-summary.md

# Check status
status:
	./audio2md status

# Remove conda env (full reset)
reset:
	ssh $(CLUSTER) "conda remove -y -n audio2md --all 2>/dev/null || true"
	ssh $(CLUSTER) "rm -rf ~/dev/audio2md"
