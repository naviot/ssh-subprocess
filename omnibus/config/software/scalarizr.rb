name "scalarizr"
version "#{project.build_version}"

dependency "python"
dependency "pip"
if linux?
  dependency "rsync"
end
dependency "requirements"
dependency "fatmouse-agent"
if windows?
    dependency "msi-installscripts"
end


if ENV['OMNIBUS_VERSION']
  data_volume = (ENV['OMNIBUS_DATA_VOLUME'] or '/project')
  source :path => "#{data_volume}"
  ENV['VERSION'] = ENV['MSI_VERSION'] = ENV['OMNIBUS_VERSION']
else
  source :path => "#{ENV['BUILD_DIR']}"

end

scripts = "#{install_dir}/bin"
prefix = "#{install_dir}/embedded"

if windows?
    python = "#{install_dir}/embedded/python.exe"
    build do
      # do not split this line, as it may fail silently
      command "#{windows_safe_path(python)} setup_omnibus.py install --prefix=#{windows_safe_path(prefix)} --install-scripts=#{windows_safe_path(scripts)}"
    end
else
    python = "#{install_dir}/embedded/bin/python"
    build do
      command "#{python} setup_omnibus.py install --prefix=#{prefix} --install-scripts=#{scripts}"
      command "sed -i 's/\\#\\!\\/usr\\/bin\\/python/\\#\\!\\/opt\\/scalarizr\\/embedded\\/bin\\/python/1' #{install_dir}/scripts/*"
    end
end
