name "python-pyyaml"
pypi_name = "PyYAML"
default_version "3.11"

dependency "pip"

if windows?
  pip = "#{install_dir}/embedded/Scripts/pip.exe"
  pip_global_option = "--without-libyaml"
else
  dependency "libyaml"
  pip = "#{install_dir}/embedded/bin/pip"
  pip_global_option = "--with-libyaml"
end

build do
  command "#{pip} install -I #{pypi_name}==#{default_version} --global-option=#{pip_global_option}"
end
