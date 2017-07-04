name "augeas"
default_version "1.4.0"

dependency "libxml2"
dependency "readline"

source :url => "https://storage.googleapis.com/omnibus_sources/augeas-#{version}.tar.gz",
       :md5 => "a2536a9c3d744dc09d234228fe4b0c93"

relative_path "augeas-#{version}"
env = with_standard_compiler_flags(with_embedded_path)

build do
    block do
        env["LIBXML_CFLAGS"] = `#{install_dir}/embedded/bin/xml2-config --cflags`.strip
        env["LIBXML_LIBS"] = `#{install_dir}/embedded/bin/xml2-config --libs`.strip
    end
    command "./configure --prefix=#{install_dir}/embedded", :env => env
    command "make -j #{workers}", :env => env
    command "make install"
end