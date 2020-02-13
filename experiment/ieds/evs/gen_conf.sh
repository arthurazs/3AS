total=$1

if [ -z "$total" ]
then
    total=300
fi

echo $total

for ev in $(seq 1 1 $total)
do
    echo "ctrl_interface=/var/run/wpa_supplicant
ctrl_interface_group=0
eapol_version=2
fast_reauth=1

network={
    key_mgmt=IEEE8021X

    identity=\"ev$ev\"

    eap=TLS
    ca_cert=\"/home/arthurazs/git/3AS/experiment/certificates/ca.pem\"
    client_cert=\"/home/arthurazs/git/3AS/experiment/certificates/ieds/ied01.pem\"
    private_key=\"/home/arthurazs/git/3AS/experiment/certificates/ieds/ied01.key\"
    private_key_passwd=\"ied01\"
}" > ev$ev.conf

done
