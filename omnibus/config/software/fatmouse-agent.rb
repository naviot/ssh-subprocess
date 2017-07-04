name "fatmouse-agent"
default_version "#{project.build_version}"

if ENV['OMNIBUS_VERSION']
  data_volume = (ENV['OMNIBUS_DATA_VOLUME'] or '/project')
  source :path => "#{data_volume}/fatmouse"
else
  source :path => "#{ENV['BUILD_DIR']}/fatmouse"

end

if windows?
  python = "#{install_dir}/embedded/python.exe"
  prefix = "#{install_dir}/embedded"
  scripts = "#{install_dir}/bin"
  build do
    block do
      puts "#{source}"
    end
    command "#{windows_safe_path(python)} setup_agent.py install " \
            "--prefix=#{windows_safe_path(prefix)} --install-scripts=#{windows_safe_path(scripts)}"
  end
else
  build do
    command "#{install_dir}/embedded/bin/python setup_agent.py install " \
            "--prefix=#{install_dir}/embedded " \
            "--install-scripts #{install_dir}/bin"
  end
end
