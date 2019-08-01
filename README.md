# eva

This guide works on xUbuntu 18.04.

## Pre-Install

```bash
apt install mininet freeradius python3-pip
pip3 install ryu
pip3 install vakt
sed -i '$ a export PATH=$PATH:~/.local/bin' ~/.bashrc
source ~/.bashrc
```

## Configure

Download this repo and generate the certificates:

```bash
git clone https://github.com/arthurazs/eva.git
cd eva/experiment/certificates/configs
make
```

Head over to the file `/etc/freeradius/3.0/mods-enabled/eap` and **update** the following lines:

```bash
eap {
  default_eap_type = tls
  tls-config tls-common {
    home_certs = '/<WHEREVER THIS REPO IS>/eva/experiment/certificates'
    private_key_password = icuff
    private_key_file = ${home_certs}/radius/server.key
    certificate_file = ${home_certs}/radius/server.pem
    ca_file = ${home_certs}/ca.pem
    # dh_file = ${certdir}/dh
  }
}
```

## Run

Find the name of your local NIC, e.g.
```bash
$ ifconfig
enp0s3: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.2.15  netmask 255.255.255.0  broadcast 10.0.2.255
        inet6 fe80::9b29:a7dc:4a1a:eb01  prefixlen 64  scopeid 0x20<link>
        ether 08:00:27:25:46:0f  txqueuelen 1000  (Ethernet)
        RX packets 67608  bytes 32204138 (32.2 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 42403  bytes 5724044 (5.7 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 7837  bytes 762551 (762.5 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 7837  bytes 762551 (762.5 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

And use that NIC to run the experiments:

```bash
cd eva
sh run.sh enp0s3
```

<!--
openssl x509 -in client.pem -text
openssl rsa -in client.pem -text
-->
