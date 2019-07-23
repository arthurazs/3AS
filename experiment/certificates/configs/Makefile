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
all: index.txt serial server ca scada ied01

.PHONY: scada
scada: scada.pem

.PHONY: ied01
ied01: ied01.pem

.PHONY: ca
ca: ca.der

.PHONY: server
server: server.pem server.vrfy

.PHONY: verify
verify: server.vrfy scada.vrfy ied01.vrfy

passwords.mk: server.cnf ca.cnf scada.cnf ied01.cnf
	@echo "PASSWORD_SERVER	= '$(shell grep output_password server.cnf | sed 's/.*=//;s/^ *//')'"		> $@
	@echo "PASSWORD_CA	= '$(shell grep output_password ca.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
	@echo "PASSWORD_SCADA	= '$(shell grep output_password scada.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
	@echo "PASSWORD_IED01	= '$(shell grep output_password ied01.cnf | sed 's/.*=//;s/^ *//')'"		>> $@
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
#  Create a new ied01 certificate, signed by the the above server
#  certificate.
#
######################################################################
ied01.csr ied01.key: ied01.cnf
	$(OPENSSL) req -new  -out ied01.csr -keyout ../ieds/ied01.key -config ./ied01.cnf
	chmod go+r ../ieds/ied01.key

ied01.crt: ied01.csr ca.pem ca.key
	$(OPENSSL) ca -batch -keyfile ca.key -cert ../ca.pem -in ied01.csr  -key $(PASSWORD_CA) -out ied01.crt -config ./ied01.cnf

ied01.p12: ied01.crt
	$(OPENSSL) pkcs12 -export -in ied01.crt -inkey ../ieds/ied01.key -out ied01.p12  -passin pass:$(PASSWORD_IED01) -passout pass:$(PASSWORD_IED01)
	chmod g+r ied01.p12

ied01.pem: ied01.p12
	$(OPENSSL) pkcs12 -in ied01.p12 -out ../ieds/ied01.pem -passin pass:$(PASSWORD_IED01) -passout pass:$(PASSWORD_IED01)
	chmod go+r ../ieds/ied01.pem

.PHONY: ied01.vrfy
ied01.vrfy: ca.pem ied01.pem
	c_rehash .
	$(OPENSSL) verify -CApath . ../ieds/ied01.pem

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
	@rm -f *~ *old scada.csr scada.crt scada.p12 ../scada/scada.* ../radius/server.* ../ca.pem ied01.csr ied01.crt ied01.p12 ../ieds/ied*

#
#	Make a target that people won't run too often.
#
destroycerts:
	rm -f *~ passwords.mk dh *.csr *.crt *.p12 *.der *.pem *.key index.txt* \
			serial*  *\.0 *\.1
