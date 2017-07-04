# TODO: remove this condition after SA-96 is merged into master
if ENV.has_key?('OMNIBUS_INSTALL_DIR') and ENV.has_key?('OMNIBUS_VERSION')
    build_dir "/omnibus_build"
    cache_dir "/omnibus_cache"
    package_dir "/omnibus_package"
    source_dir File.join('/omnibus_cache', 'src')
    git_cache_dir File.join('/omnibus_cache', 'git_cache')
end

append_timestamp false
