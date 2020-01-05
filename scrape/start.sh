#!/bin/bash

i=0

screen -dmS 'proxy' bash -c './start-proxy.sh 8080'
sleep 2;

for url in "$@"; do
	screen -dmS "scrape-$i" bash -c "./scrape.sh $url 8080"
	((i++))
done
