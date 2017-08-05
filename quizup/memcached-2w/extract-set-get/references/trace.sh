tshark -i eth0 -s 9001 "(dst host 172.16.58.122) and (port 11211)" -w /home/sveinnfannar/traces/players.pcap -b filesize:1000000 -b files:10
