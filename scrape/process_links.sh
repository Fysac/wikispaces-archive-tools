#!/bin/bash

while read link; do
	./scrape.sh "$link" 8080
	echo "$link" >> "$1"
done
