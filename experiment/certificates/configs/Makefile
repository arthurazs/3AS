######################################################################
#
#	Make file created by freeradius
# 	Updated by Arthur Zopellaro
#
######################################################################

OPENSSL		= openssl
EXTERNAL_CA	= $(wildcard external_ca.*)

ifneq "$(EXTERNAL_CA)" ""
PARTIAL		= -partial_chain
endif

#
#  Set the passwords
#
include passwords.mk

######################################################################
#
#  Make the necessary files, but not client certificates.
#
######################################################################
.PHONY: all
all: index.txt serial server ca scada ev01

.PHONY: scada
scada: scada.pem

.PHONY: ev01
ev01: ev01.pem

.PHONY: ca
ca: ca.der

.PHONY: server
server: server.pem server.vrfy

.PHONY: verify
verify: server.vrfy scada.vrfy ev01.vrfy

passwords.mk: server.cnf ca.cnf scada.cnf ev01.cnf
	@echo "PASSWORD_SERVER	= '$(shell grep output_password server.cnf | sed 's/.*=//;s/^ *//')'"		> $@
	@echo "PASSWORD_CA	= '$(shell grep output_password ca.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
	@echo "PASSWORD_SCADA	= '$(shell grep output_password scada.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
	@echo "PASSWORD_EV01	= '$(shell grep output_password ev01.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
	@echo "CA_DEFAULT_DAYS  = '$(shell grep default_days ca.cnf | sed 's/.*=//;s/^ *//')'"			>> $@

######################################################################
#
#  Create a new self-signed CA certificate
#
######################################################################
ca.key ca.pem: ca.cnf
	@[ -f index.txt ] || $(MAKE) index.txt
	@[ -f serial ] || $(MAKE) serial
	$(OPENSSL) req -new -x509 -keyout ca.key -out ../ca.pem \
		-days $(CA_DEFAULT_DAYS) -config ./ca.cnf
	chmod g+r ca.key

ca.der: ca.pem
	$(OPENSSL) x509 -inform PEM -outform DER -in ../ca.pem -out ca.der

######################################################################
#
#  Create a new server certificate, signed by the above CA.
#
######################################################################
server.csr server.key: server.cnf
	$(OPENSSL) req -new  -out server.csr -keyout ../radius/server.key -config ./server.cnf
	chmod go+r ../radius/server.key

server.crt: server.csr ca.key ca.pem
	$(OPENSSL) ca -batch -keyfile ca.key -cert ../ca.pem -in server.csr  -key $(PASSWORD_CA) -out server.crt -config ./server.cnf

server.p12: server.crt
	$(OPENSSL) pkcs12 -export -in server.crt -inkey ../radius/server.key -out server.p12  -passin pass:$(PASSWORD_SERVER) -passout pass:$(PASSWORD_SERVER)
	chmod g+r server.p12

server.pem: server.p12
	$(OPENSSL) pkcs12 -in server.p12 -out ../radius/server.pem -passin pass:$(PASSWORD_SERVER) -passout pass:$(PASSWORD_SERVER)
	chmod go+r ../radius/server.pem

.PHONY: server.vrfy
server.vrfy: ca.pem
	@$(OPENSSL) verify $(PARTIAL) -CAfile ../ca.pem ../radius/server.pem

######################################################################
#
#  Create a new scada certificate, signed by the the above server
#  certificate.
#
######################################################################
scada.csr scada.key: scada.cnf
	$(OPENSSL) req -new  -out scada.csr -keyout ../scada/scada.key -config ./scada.cnf
	chmod go+r ../scada/scada.key

scada.crt: scada.csr ca.pem ca.key
	$(OPENSSL) ca -batch -keyfile ca.key -cert ../ca.pem -in scada.csr  -key $(PASSWORD_CA) -out scada.crt -config ./scada.cnf

scada.p12: scada.crt
	$(OPENSSL) pkcs12 -export -in scada.crt -inkey ../scada/scada.key -out scada.p12  -passin pass:$(PASSWORD_SCADA) -passout pass:$(PASSWORD_SCADA)
	chmod g+r scada.p12

scada.pem: scada.p12
	$(OPENSSL) pkcs12 -in scada.p12 -out ../scada/scada.pem -passin pass:$(PASSWORD_SCADA) -passout pass:$(PASSWORD_SCADA)
	chmod go+r ../scada/scada.pem
	# cp scada.pem $(USER_NAME).pem

.PHONY: scada.vrfy
scada.vrfy: ca.pem scada.pem
	c_rehash .
	$(OPENSSL) verify -CApath . ../scada/scada.pem

######################################################################
#
#  Create a new ev01 certificate, signed by the the above server
#  certificate.
#
######################################################################
ev01.csr ev01.key: ev01.cnf
	$(OPENSSL) req -new  -out ev01.csr -keyout ../ev01/ev01.key -config ./ev01.cnf
	chmod go+r ../ev01/ev01.key

ev01.crt: ev01.csr ca.pem ca.key
	$(OPENSSL) ca -batch -keyfile ca.key -cert ../ca.pem -in ev01.csr  -key $(PASSWORD_CA) -out ev01.crt -config ./ev01.cnf

ev01.p12: ev01.crt
	$(OPENSSL) pkcs12 -export -in ev01.crt -inkey ../ev01/ev01.key -out ev01.p12  -passin pass:$(PASSWORD_EV01) -passout pass:$(PASSWORD_EV01)
	chmod g+r ev01.p12

ev01.pem: ev01.p12
	$(OPENSSL) pkcs12 -in ev01.p12 -out ../ev01/ev01.pem -passin pass:$(PASSWORD_EV01) -passout pass:$(PASSWORD_EV01)
	chmod go+r ../ev01/ev01.pem

.PHONY: ev01.vrfy
ev01.vrfy: ca.pem ev01.pem
	c_rehash .
	$(OPENSSL) verify -CApath . ../ev01/ev01.pem

######################################################################
#
#  Miscellaneous rules.
#
######################################################################
index.txt:
	@touch index.txt

serial:
	@echo '01' > serial

print:
	$(OPENSSL) x509 -text -in server.crt

printca:
	$(OPENSSL) x509 -text -in ../ca.pem

clean:
	@rm -f *~ *old scada.csr scada.crt scada.p12 ../scada/scada.* ../radius/server.* ../ca.pem ev01.csr ev01.crt ev01.p12 ../ev01/ev*

#
#	Make a target that people won't run too often.
#
destroycerts:
	rm -f *~ passwords.mk dh *.csr *.crt *.p12 *.der *.pem *.key index.txt* \
			serial*  *\.0 *\.1
