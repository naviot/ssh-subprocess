name "setuptools"
default_version "18.0.1"

dependency "python"

version "21.2.1" do
    source md5: "b6f59b1987fe9642874448e54ee33315"
end
version "18.0.1" do
    source md5: "cecd172c9ff7fd5f2e16b2fcc88bba51"
end
version "15.2" do
    source  md5: "a9028a9794fc7ae02320d32e2d7e12ee"
end
version "5.2" do
    source md5: "ea6ed9ab1a4abe978dade73a592a229c"
end

source url: "https://storage.googleapis.com/omnibus_sources/setuptools-#{version}.tar.gz"
relative_path "setuptools-#{version}"

build do
    if windows?
        python = "#{install_dir}/embedded/python.exe"
        command "#{python} setup.py install"
    else
        python = "#{install_dir}/embedded/bin/python"
        command "#{python} setup.py install --prefix=#{install_dir}/embedded"
    end
end
