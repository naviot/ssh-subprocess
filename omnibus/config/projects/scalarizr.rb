name            "scalarizr"
maintainer      "Scalr Inc"
homepage        "http://scalr.com"

_install_dir = (ENV['OMNIBUS_INSTALL_DIR'] or ENV['INSTALL_DIR'] or '/opt/scalarizr')

install_dir   File.absolute_path("#{_install_dir}")
build_version (ENV['OMNIBUS_VERSION'] or ENV['OMNIBUS_BUILD_VERSION'] or Omnibus::BuildVersion.new.semver)
build_iteration 1

if ENV['OMNIBUS_VERSION']
  _build_dir = (ENV['OMNIBUS_DATA_VOLUME'] or '/project')
else
  _build_dir = ENV['BUILD_DIR']
end

if ohai['platform_family'] == 'rhel'
    package_scripts_path "#{_build_dir}/omnibus/package-scripts/scalarizr/rpm/"
elsif linux?
    package_scripts_path "#{_build_dir}/omnibus/package-scripts/scalarizr/deb/"
end

if windows?
  install_dir File.absolute_path("#{_install_dir}/#{build_version}")
  package :msi do
    upgrade_code 'c8a28fde-f340-423f-b7db-ff1368d8bb19'
    wix_light_extension "WixUtilExtension"
  end
end

dependency "preparation"
dependency "scalarizr"
dependency "version-manifest"
conflict "scalr-upd-client"
replace "scalr-upd-client"

if ohai['platform_family'] == 'rhel'
    runtime_dependency "which"
    runtime_dependency "e2fsprogs"
    runtime_dependency "tar"
end

exclude "\.git*"
exclude "bundler\/git"
