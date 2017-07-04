name "lxml"
dependency "pip"
default_version "3.3.6"
source :url => "https://storage.googleapis.com/omnibus_sources/lxml-#{default_version}.win-amd64-py2.7.exe",
       :md5 => '1b6b835a911bc6f399fcd176994cf683'
if windows?
    easy_install = "#{install_dir}/embedded/Scripts/easy_install.exe"
    package_src = "#{Omnibus::Config.source_dir}/lxml/lxml-#{default_version}.win-amd64-py2.7.exe"
    package_location = "#{install_dir}/embedded/Lib/site-packages/"
    build do
      command "#{easy_install} --install-dir=#{package_location} #{package_src}"
    end
end
