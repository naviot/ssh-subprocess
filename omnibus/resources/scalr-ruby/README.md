mkdir -p /omnibus_ruby_build /omnibus_ruby_cache /omnibus_ruby_package
cd /projects/scalarizr/omnibus_ruby/
bundle install --binstubs



### Win build
```
bundle install --binstubs; ruby .\\bin\\omnibus clean {project} > NUL; ruby .\\bin\\omnibus build {project} --log-level=info
```
### Linux build

Prepare dirs
```
cache_dir=/omnibus_ruby_cache
cache_volume=/omnibus_cache

data_dir=/projects/scalarizr/omnibus_ruby
data_volume=/project

pkg_dir=/omnibus_ruby_package
pkg_volume=/omnibus_package
```
##### Ubuntu
```
docker run --rm  -e OMNIBUS_PROJECT="scalr-ruby" -e OMNIBUS_VERSION="2.0.0" -v $cache_dir:$cache_volume -v $data_dir:$data_volume -v $pkg_dir:$pkg_volume  gcr.io/scalr.com/scalr-labs/ubuntu1204-omnibus
```
##### Centos

```
docker run  --rm -e OMNIBUS_PROJECT="scalr-ruby" -e OMNIBUS_VERSION="2.0.0" -v $cache_dir:$cache_volume -v $data_dir:$data_volume -v $pkg_dir:$pkg_volume  gcr.io/scalr.com/scalr-labs/centos5-omnibus
```
