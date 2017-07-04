name "python-pycrypto"
default_version "2.5"

dependency "pip"


source :url => "https://storage.googleapis.com/omnibus_sources/pycrypto-2.5-py2.7-win-amd64.egg",
       :md5 => "a826b21029ace27d75a4abdfa5d8057d"

relative_path "pycrypto-2.5-py2.7-win-amd64.egg"
build do
    easy_install = "#{install_dir}/embedded/Scripts/easy_install.exe"
    command "#{easy_install} #{relative_path}"
end


