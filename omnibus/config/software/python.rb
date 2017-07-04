name "python"
default_version "2.7.12"

if windows?
  source :url => "https://storage.googleapis.com/omnibus_sources/python-#{version}.amd64.msi",
         :md5 => '8fa13925db87638aa472a3e794ca4ee3'
  relative_path "Python-#{version}"

  build do
    target_dir = "#{install_dir}/embedded"
    command "msiexec /a python-#{version}.amd64.msi /qb TARGETDIR=#{windows_safe_path(target_dir)}"
  end
else
  dependency "gdbm"
  dependency "ncurses"
  dependency "zlib"
  dependency "openssl"
  dependency "bzip2"
  dependency "sqlite3"

  source url: "https://storage.googleapis.com/omnibus_sources/Python-#{version}.tgz",
         md5: '88d61f82e3616a4be952828b3694109d'
  relative_path "Python-#{version}"

  build do
    env = {
      "CFLAGS" => "-I#{install_dir}/embedded/include -O3 -g -pipe",
      "LDFLAGS" => "-Wl,-rpath,#{install_dir}/embedded/lib -L#{install_dir}/embedded/lib"
    }
    
    command "./configure" \
            " --prefix=#{install_dir}/embedded" \
            " --enable-shared" \
            " --with-dbmliborder=gdbm", env: env
    make env: env
    make "install", env: env

    # There exists no configure flag to tell Python to not compile readline
    delete "#{install_dir}/embedded/lib/python2.7/lib-dynload/readline.*"
    # Remove unused extension which is known to make healthchecks fail on CentOS 6
    delete "#{install_dir}/embedded/lib/python2.7/lib-dynload/_bsddb.*"
    delete "#{install_dir}/embedded/lib/python2.7/bsddb"
    # Remove python own testsuite (~28M)
    delete "#{install_dir}/embedded/lib/python2.7/test"
  end
end
