name "requirements"
default_version "4.3.9" # corresponds to scalarizr version on which requirements were frozen

data_volume = (ENV['OMNIBUS_DATA_VOLUME'] or '/project')
requirements_path = "#{data_volume}/omnibus/requirements.txt"


dependency "pip"

fatmouse = "
billiard==3.5.0.2
kombu==4.0.2
git+https://github.com/Scalr/py-amqp.git@dc87d178a4a1d3095e2557cfd2a6c8d62df91846#egg=amqp-2.1.4
git+git://github.com/Scalr/celery.git@635b2be80a19859905b06217e24176a2ea0f50ba#egg=celery-4.0.2
vine==1.1.3
pytz==2016.10
git+https://github.com/Scalr/pychef@d98989989a45994566b64176a22e7ec9886facba
git+https://github.com/Scalr/libcloud.git@caa8bd3bebcda794c0835dfe30525f317d194817#egg=apache-libcloud-1.5.dev2
cryptography==1.5.3
google-api-python-client==1.4.2
mock==1.3.0
monotonic==0.5
psutil==3.4.2
pyOpenSSL==16.1.0
git+https://github.com/Scalr/python-augeas.git@5b4fe6568eca7866429180d82a7aed58ee824e37 ; sys_platform != 'win32'
requests==2.9.1
schematics==1.1.1
six==1.10.0
git+https://github.com/Scalr/python-subprocess32.git@10394b10d7c5a14e84730ba49e213f92221fcec7 ; sys_platform != 'win32'
WMI==1.4.9 ; sys_platform == 'win32'
"

scalarizr = "
boto==2.45.0
certifi
git+https://github.com/Scalr/python-cloudstack.git@269c0d842a5d138f1314c3b50834677f67dd1b81#egg=cloudstack-python-client
PyMySQL==0.5
Pygments==2.0.1
docopt==0.6.2
ipython==2.3.0
pexpect==2.4
prettytable==0.7.2
python-cinderclient==1.5.0
python-keystoneclient==1.8.1
python-novaclient==3.2.0
python-swiftclient==3.0.0
pyreadline==2.1 ; sys_platform == 'win32'
rackspace-novaclient==1.5
readline==6.2.4.1 ; sys_platform != 'win32'
"

secondlevel = "
Babel==2.2.0
git+https://github.com/Scalr/py-amqp.git@dc87d178a4a1d3095e2557cfd2a6c8d62df91846#egg=amqp-2.1.4
anyjson==0.3.3
argparse==1.4.0
billiard==3.5.0.2
cffi==1.4.2
debtcollector==1.1.0
enum34==1.1.2
funcsigs==0.4
futures==3.0.3
httplib2==0.9.2
idna==2.1 # cryptography
ip-associations-python-novaclient-ext==0.1
ipaddress==1.0.16
iso8601==0.1.11
keystoneauth1==2.1.0
kombu==4.0.2
monotonic==0.5
msgpack-python==0.4.6
netaddr==0.7.18
netifaces==0.10.4
oauth2client==1.5.2
os-diskconfig-python-novaclient-ext==0.1.3
os-networksv2-python-novaclient-ext==0.25
os-virtual-interfacesv2-python-novaclient-ext==0.19
oslo.config==3.2.0
oslo.i18n==3.1.0
oslo.serialization==2.2.0
oslo.utils==3.3.0
pbr==1.8.1
pyasn1==0.1.9
pyasn1-modules==0.0.8
pycparser==2.14
pytz==2016.10
rackspace-auth-openstack==1.3
rax-default-network-flags-python-novaclient-ext==0.3.2
rax-scheduled-images-python-novaclient-ext==0.3.1
rsa==3.2.3
simplejson==3.8.1
stevedore==1.10.0
uritemplate==0.6
wrapt==1.10.6
vine==1.1.3
"
if windows?
    dependency "python-pywin32"
    dependency "python-pycrypto-windows"
    dependency "python-lxml-windows"
    pip = "#{install_dir}/embedded/Scripts/pip.exe"
else
    dependency "augeas"
    dependency "openssl"
    dependency "libffi"
    pip = "#{install_dir}/embedded/bin/pip"
end
dependency "python-pyyaml"
dependency "python-pymongo"

build do
    if windows?
        requirements_path = "#{windows_safe_path(requirements_path)}"
    end
    [secondlevel, fatmouse, scalarizr].each { |requirements_block|
        block do
            out_file = File.new("#{requirements_path}", "w")
            out_file.puts(requirements_block)
            out_file.close
        end

    command "#{pip} install -r #{requirements_path} --no-deps"
    }
end
