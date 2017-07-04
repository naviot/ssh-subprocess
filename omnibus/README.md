# scalarizr Omnibus project

## Updating scalarizr dependencies in requirements.rb

All cases assume that embedded pip is used
which is ```/opt/scalarizr/embedded/bin/pip``` on linux and ```C:\opt\scalarizr\current\embedded\Scripts\pip```
on windows.

### Case1: adding a dependency for fatmouse-agent or scalarizr

- Build latest scalarizr package from master
- Install a package on corresponding os and do ```pip freeze```
- do ```pip install new_dependency```
- do ```pip freeze```
- compare freeze results, everything that is not in the first freeze and not a ```new_dependency``` itself
should go to ```level2``` block.


### Case2: deleting a dependency from fatmouse-agent or scalarizr
- build and install latest scalarizr package
- install pip-autoremove python package  ```pip install pip-autoremove```
- collect package list via ```pip freeze```
- do ```pip-autoremove dependency```
- compare freeze results, everything that is not in the first freeze and not a ```dependency``` itself
should go to ```level2``` block.


