import os

from fabric.api import local, task


@task
def new_union(branch):
    '''
    create union branch (see #259)
    '''
    branch = 'union/{}'.format(branch)
    scalarizr_dir = os.path.abspath(os.path.dirname(__file__))
    fatmouse_dir = os.path.abspath(os.path.dirname(scalarizr_dir) + '/fatmouse')

    def git_opts(path):
        return '--git-dir={0}/.git --work-tree={0}'.format(path)

    local('git {} checkout master'.format(git_opts(scalarizr_dir)))
    local('git {} checkout -b {}'.format(git_opts(scalarizr_dir), branch))
    local('git {} checkout master'.format(git_opts(fatmouse_dir)))
    local('git {} checkout -b {}'.format(git_opts(fatmouse_dir), branch))

    print(('Created branch {!r} and switched in:\n'
           ' - scalarizr({})\n'
           ' - fatmouse({})').format(
        branch, scalarizr_dir, fatmouse_dir))
