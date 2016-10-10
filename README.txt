
tsh (tiny shell)
================

tsh is a tiny shell for Unix systems.
tsh is written in Python.
It's use is to give users very restricted access to a system.
One can create a user which has tsh as his/her login shell.

This small shell might serve as an example of how to write a more
elaborate shell in Python.
In practice, this shell is not really very useful since the Unix
system itself can provides good security.
Also note that most systems provide a restricted bash `rbash`.


Installation
------------

Requirement: python 2.5

Unpack the tarball, and just copy the executable `tsh` into
`/usr/local/bin` (or wherever you which to have it).


Description
-----------

`tsh` has the only the following buildtin commands:

    alias [name='value']
    unalias name
    cd [path]
    exit
    show_commands

They work in the way one would expect them to work in bash, except
the command `show_commands`, e.g.:

    /home/joe tsh> show_commands
        alias           builtin
        cat             OS
        cd              builtin
        exit            builtin
        l               aliased 'ls -l'
        ls              OS, aliased 'ls --color'
        show_commands   builtin
        unalias         builtin

The only commands imported from the OS are specified in the file
`/etc/tsh.conf`.  In the example above, only `cat` and `ls` are the
only non-builtin commands, the user is allowed to execute.
It is important not to include commands line `nice` or `time` into
this list, since they would leave a backdoor for all other commands, e.g.

    /home/joe tsh> nice rm -rf *

or even:

    /home/joe tsh> time bash

Also, `tsh` does not allow multiple commands to be executed in a call, e.g.

    /home/joe tsh> ls ; rm -rf *
    /home/joe tsh> ls || rm -rf *
    ...

does not work, because `tsh` will interpret all a words (separated with
whitespace, after the command itself as arguments to that command.
This means that `tsh` does not know anything about, pipes, IO redirecion,
combining commands and quoting.


Files
-----

  - `/etc/tsh.conf` contains the list of commands allowed for execution.
    See the example file `tsh.conf`.

  - `~/.tshrc` run-control file.   I have included an example
    Note the example file `tshrc`.

  - `~/.tsh-history` history file.
