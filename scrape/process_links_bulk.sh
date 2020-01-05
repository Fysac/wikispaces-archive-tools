#!/bin/bash

i=0
screen -dmS 'proxy' bash -c './start-proxy.sh 8080'
sleep 2;

for file in "$@"; do
	echo "$file"
	screen -dmS "process-links-$i" bash -c "./process_links.sh process-links-$i < $file"
	((i++))
done
