name "python-pywin32"
default_version "219"


dependency "pip"
pyver_minor = "7"
pkg_name = "pywin32-#{default_version}.win-amd64-py2.#{pyver_minor}.exe"
source :url => "https://storage.googleapis.com/omnibus_sources/#{pkg_name}",
       :md5 => 'ff7e69429ef38c15088906314cb11f93'

relative_path "python-pywin32"
easy_install = "#{install_dir}/embedded/Scripts/easy_install.exe"
dll_source = "#{install_dir}\\embedded\\python2#{pyver_minor}.dll"
dll_dest = "#{install_dir}\\embedded\\lib\\site-packages\\pywin32-#{default_version}-py2.#{pyver_minor}-win-amd64.egg\\python2#{pyver_minor}.dll"

build do
    command "#{windows_safe_path(easy_install)} #{pkg_name}"
    command "cp #{windows_safe_path(dll_source)} #{windows_safe_path(dll_dest)}"
end
