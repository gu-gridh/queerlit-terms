# Arild 2022-02-17
for file in ~/University\ of\ Gothenburg/Olov\ Kriström\ -\ TTLs/*
do
	out=$(ttl "$file")
	if [ $? -ne 0 ]
	then
		echo $file
		echo $out
	fi
done
