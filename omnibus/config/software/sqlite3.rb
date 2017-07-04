name "sqlite3"
default_version "3080401"

dependency "readline"

source :url => "https://storage.googleapis.com/omnibus_sources/sqlite-autoconf-#{default_version}.tar.gz",
       :md5 => "6b8cb7b9063a1d97f7b5dc517e8ee0c4"

relative_path "sqlite-autoconf-#{default_version}"

env = {
  "LDFLAGS" => "-L#{install_dir}/embedded/lib -I#{install_dir}/embedded/include",
  "CFLAGS" => "-L#{install_dir}/embedded/lib -I#{install_dir}/embedded/include",
  "LD_RUN_PATH" => "#{install_dir}/embedded/lib"
}

build do
  command "./configure --prefix=#{install_dir}/embedded", :env => env
  command "make -j #{workers}", :env => env
  command "make install"
end
