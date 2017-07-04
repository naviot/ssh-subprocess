name "pip"
default_version "8.1.2"
dependency "setuptools"


version "8.1.2" do
    source md5: '87083c0b9867963b29f7aba3613e8f4a'
end

source url: "https://storage.googleapis.com/omnibus_sources/pip-#{version}.tar.gz"
relative_path "pip-#{version}"

if windows?
    build do
        command "#{install_dir}/embedded/python.exe setup.py install"
    end
else
    build do
        command "#{install_dir}/embedded/bin/python setup.py install --prefix=#{install_dir}/embedded"
    end
end
