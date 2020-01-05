#!/bin/bash

cd ~/test

wget -rHp -nc -e 'robots=off' \
	-D 'wikispaces.com' \
	--exclude-domains 'session.wikispaces.com,help.wikispaces.com,helpcenter.wikispaces.com,status.wikispaces.com' \
	--regex-type 'pcre' \
	--accept-regex '/page|/user|/share|/file|(^(?!www).+wikispaces\.com)' \
	--reject-regex '((\?|&)(orderBy|orderDir|utable|f|goto)=)|/mail|/user/join|/user/remind|/page/edit|/page/microsummary|/page/pdf|/page/rss|/page/xml|/s/blank|/space/opensearch|/space/xml|/wiki/addmonitor|/wiki/xmla|/message/xml|/site/gettingstarted|/site/help|/file/rss|/file/xml|<%[^%]*%>|wikispaces\.com/user\.' \
	-e use_proxy=yes -e http_proxy=127.0.0.1:"$2" -e https_proxy=127.0.0.1:"$2" \
	--no-check-certificate \
	--content-on-error \
	-T 10 -t 10 \
	--no-http-keep-alive \
	"$1"
