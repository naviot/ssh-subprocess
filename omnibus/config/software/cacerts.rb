name "cacerts"

default_version "2016.04.20"
source  url: "https://storage.googleapis.com/omnibus_sources/cacert.pem",
        md5: "782dcde8f5d53b1b9e888fdf113c42b9"

relative_path "cacerts-#{version}"
build do
  mkdir "#{install_dir}/embedded/ssl/certs"
  copy "#{project_dir}/cacert.pem", "#{install_dir}/embedded/ssl/certs/cacert.pem"
  # Windows does not support symlinks
  unless windows?
    link "#{install_dir}/embedded/ssl/certs/cacert.pem", "#{install_dir}/embedded/ssl/cert.pem"
  end
end