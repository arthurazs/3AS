prefix=dataset/logs_

for evs in 1 10 300 1000
do
    for rep in $(seq 1 10)
    do
        folder="$prefix""$evs"_"$rep"/pcap
        echo
        echo Parsing "$folder" to csv...
        for file in scada sdn-hostapd freeradius openflow
        do
            echo \> Parsing $file...
            tshark -r "$folder"/$file.pcap -T fields -e frame.time_epoch -e _ws.col.Source -e _ws.col.Destination  -e _ws.col.Protocol -e _ws.col.Length -e _ws.col.Info -e eapol.type -e eth.src -E header=y -E separator=, -E quote=d > "$folder"/$file.csv
        done
    done
done
