# MaxiNet

## Installation

1. `sudo sed -i '$a arthurazs ALL=(ALL) NOPASSWD:ALL' /etc/sudoers`

2. `sudo vim /etc/MaxiNet.cfg`

```conf
; place this at ~/.MaxiNet.cfg
[all]
password = HalloWelt
controller = 10.0.0.4:6633
logLevel = DEBUG       ; Either CRITICAL, ERROR, WARNING, INFO  or DEBUG
port_ns = 9090         ; Nameserver port
port_sshd = 5345       ; Port where MaxiNet will start an ssh server on each worker
runWith1500MTU = False ; Set this to True if your physical network can not handle MTUs >1500.
useMultipleIPs = 0     ; for RSS load balancing. Set to n > 0 to use multiple IP addresses per worker. More information on this feature can be found at MaxiNets github Wiki.
deactivateTSO = True   ; Deactivate TCP-Segmentation-Offloading at the emulated hosts.
sshuser = arthurazs    ; On Debian set this to root. On ubuntu set this to user which can do passwordless sudo
usesudo = True         ; If sshuser is set to something different than root set this to True.
useSTT = False         ; enables stt usage for tunnels. Only usable with OpenVSwitch. Bandwithlimitations etc do not work on STT tunnels!

[FrontendServer]
ip = 10.0.0.4
threadpool = 256       ; increase if more workers are needed (each Worker requires 2 threads on the FrontendServer)

[maq01]
ip = 10.0.0.1
share = 1

[maq02]
ip = 10.0.0.2
share = 1

[maq03]
ip = 10.0.0.3
share = 1

[maq04]
ip = 10.0.0.4
share = 1

[maq05]
ip = 10.0.0.5
share = 1
```

3. `sudo apt install mininet`

4. `pip install setuptools`

5. `wget https://raw.githubusercontent.com/MaxiNet/MaxiNet/master/installer.sh`

6. `sudo chmod +x installer.sh`

7. `./installer.sh   # only Pyro and MaxiNet`

## Running

### Leader Host

```bash
screen -dm -S front MaxiNetFrontendServer
screen -dm -S back sudo MaxiNetWorker
```

### Following Hosts
```bash
screen -dm -S back sudo MaxiNetWorker
```

<!--
screen -S front MaxiNetFrontendServer
screen -S back sudo MaxiNetWorker
 -->
