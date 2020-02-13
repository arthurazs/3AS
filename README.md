# 3AS

**Authentication, Authorization and Accounting for Smart Grids**

This guide works on xUbuntu 18.04.

## Pre-Install

```bash
sudo dpkg --remove whoopsie
apt install mininet freeradius python3-pip
pip3 install ryu
pip3 install vakt
sed -i '$ a export PATH=$PATH:~/.local/bin' ~/.bashrc
source ~/.bashrc
```

## Configure

Download this repo and generate the certificates:

```bash
git clone https://github.com/arthurazs/3AS.git
cd 3AS/experiment/certificates/configs
make
```

---

Head over to the file `/etc/freeradius/3.0/mods-enabled/eap` and **update** the following lines:

```bash
eap {
  default_eap_type = tls
  tls-config tls-common {
    home_certs = '/<WHEREVER THIS REPO IS>/3AS/experiment/certificates'
    private_key_password = icuff
    private_key_file = ${home_certs}/radius/server.key
    certificate_file = ${home_certs}/radius/server.pem
    ca_file = ${home_certs}/ca.pem
    # dh_file = ${certdir}/dh
  }
}
```

**WARNING**: Do not forget to change `/<WHEREVER THIS REPO IS>/` to the full path you downloaded/cloned this repo, *e.g.*, `home_certs = '/home/arthurazs/git/3AS/experiment/certificates'`.

---

Head over to the file `/etc/freeradius/3.0/users` and add the following line to the top of the file:

```bash
ied02 Cleartext-Password := "ied02"
```

---

Head over to the folder `3AS/experiment/ieds/evs` and run the script `gen_conf.sh` script:

```bash
cd 3AS/experiment/ieds/evs
sh gen_conf.sh
```

## Run

```bash
cd 3AS
sh run.sh
```

<!--
openssl x509 -in client.pem -text
openssl rsa -in client.pem -text
-->
