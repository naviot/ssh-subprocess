#!powershell
# we expect all required fabfile's global variables to be already set

[Environment]::SetEnvironmentVariable("BUILD_DIR", "C:/$env:BUILD_DIR")
cd $PSScriptRoot
# extract
7z x $env:ARCHIVE | out-null
# sometimes 7z hangs and occupies an archive file, preventing a successful cleanup
$ProcessIsRunning = { Get-Process 7z -ErrorAction SilentlyContinue }
if($ProcessIsRunning.Invoke()) {
    stop-process -ProcessName 7z -Force
}
# bump version
echo "$env:VERSION" | out-file -encoding ASCII src\scalarizr\version
# generate changelog
# !TODO
echo "$env:CHANGELOG" > changelog
# cd to the project_root/omnibus directory
cd $env:OMNIBUS_DIR
bundle install --binstubs
[Environment]::SetEnvironmentVariable("OMNIBUS_BUILD_VERSION", "$env:VERSION")
ruby  .\bin\omnibus clean $env:PROJECT --log-level=$env:LOG_LEVEL
ruby  .\bin\omnibus build $env:PROJECT --log-level=$env:LOG_LEVEL

