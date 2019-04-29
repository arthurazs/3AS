# eva

## Install

Running on xUbuntu 18.04:

```bash
git clone https://github.com/arthurazs/eva.git
cd eva/experiment
apt install mininet freeradius python-pip
pip install ryu
sed -i '$ a export PATH=$PATH:~/.local/bin' ~/.bashrc
source ~/.bashrc
```

Add `scada Cleartext-Password := "scada"` to the beginning of `/etc/freeradius/3.0/users`

## Run

```bash
cd eva/experiment
. run.sh
```
