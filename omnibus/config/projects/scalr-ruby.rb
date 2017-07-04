
name            "scalr-ruby"
maintainer      "Scalr Inc"
homepage        "http://scalr.com"

install_dir '/opt/scalr-ruby'


build_version (ENV['OMNIBUS_VERSION'] or ENV['OMNIBUS_BUILD_VERSION'] or Omnibus::BuildVersion.new.semver)
build_iteration 1


dependency "cacerts"

if windows?
    install_dir File.absolute_path("#{_install_dir}")
    package :msi do
        upgrade_code 'cieuvfde-f340-423f-b7db-ff1368oisnd'
        wix_light_extension "WixUtilExtension"
    end
    dependency "ruby-windows"
    override :'ruby-windows', version: "2.0.0-p648"
else
    dependency "ruby"
    override :ruby, version: "2.0.0-p648"
end


dependency "version-manifest"

if ohai['platform_family'] == 'rhel'
    runtime_dependency "which"
    runtime_dependency "e2fsprogs"
    runtime_dependency "tar"
end

exclude "\.git*"
exclude "bundler\/git"
