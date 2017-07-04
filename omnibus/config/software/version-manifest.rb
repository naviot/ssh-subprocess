name "version-manifest"
description "generates a version manifest file"
default_version "0.0.1"

build do
  block do
    if windows?
        version = ENV['MSI_VERSION'] or ENV['OMNIBUS_VERSION']
    else
        version = project.build_version
    end
    File.open("#{install_dir}/version-manifest.txt", "w") do |f|
      f.puts "#{project.name} #{version}"
      f.puts ""
      f.puts Omnibus::Reports.pretty_version_map(project)
    end
  end
end