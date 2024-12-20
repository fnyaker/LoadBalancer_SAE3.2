# Runker

Runker is a solution to be able to run code on remote servers, made for a school project.  
  
It allow multiple users to run code codes on multiples nodes, there is a central master server that serves as a proxy between users and nodes and balance the load between them.



## Compatibility

Server parts (master and nodes) are only tested on Linux based systems (fedora 41 and debian 12), they can (with some luck) run on Mac Os but, they will NOT work on windows based systems because windows is incapable of forking a process ([https://en.wikipedia.org/wiki/Fork%E2%80%93exec](<https://en.wikipedia.org/wiki/Fork%E2%80%93exec>)), or at least, it is very "sketchy".  
  
The user client gui SHOULD run on "every" system that can run base python libs and pyqt6, tested on debian, fedora, windows 11.

## Installation/Usage

Go to install.md to see detailed install instructions

## Troubleshooting

Go to troubleshoot.md to see some possible causes for some problems/crashes, if install instructions are carefully followed, it should work "out of the box"

