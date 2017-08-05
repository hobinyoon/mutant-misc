count=1
all=`ls traces/players_*.pcap|wc -l`

for f in `ls traces/players_*.pcap`; 
do 
	echo $f;
#	tshark -Y "memcache contains set or memcache contains get" -r $f -T fields -e memcache.key |sed -e 's/full-players://g' -e 's/,/\n/g' -e '/^$/d' >> setget.all 
	tshark -Y "memcache contains get" -r $f -T fields -e memcache.key |sed -e 's/full-players://g' -e 's/,/\n/g' -e '/^$/d' >> get.all 
	let count++;
	# echo $count;
	echo $(( $count * 100 / 480 ))% 
done
