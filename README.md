# eva

This guide works on xUbuntu 18.04.

## Pre-Install

```bash
apt install mininet freeradius python-pip
pip install ryu
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

```bash
cd eva/experiment
sh run.sh
```

<!--
openssl x509 -in client.pem -text
openssl rsa -in client.pem -text
-->
