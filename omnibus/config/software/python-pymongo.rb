name "python-pymongo"
pypi_name = "pymongo"
default_version "2.7.2"

if windows?

  source  :url => "https://storage.googleapis.com/omnibus_sources/pymongo-#{default_version}.win-amd64-py2.7.exe",
          :md5 => "90733c584b72d1c90e783bd8683db9a3"

    easy_install = "#{install_dir}/embedded/Scripts/easy_install.exe"
    package_location = "#{install_dir}/embedded/Lib/site-packages/"
    bin_location = "#{Omnibus::Config.cache_dir}/pymongo-#{default_version}.win-amd64-py2.7.exe"
    build do
        command "#{windows_safe_path(easy_install)} --install-dir=#{package_location} #{bin_location}"
    end
else
    pip = "#{install_dir}/embedded/bin/pip"

    build do
      command "#{pip} install -I #{pypi_name}==#{default_version}"
    end
end
