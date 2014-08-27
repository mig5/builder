#!/bin/sh

VERSION=$1

fakeroot fpm -s dir -t deb -C src --name builder \
                                  --version ${VERSION}  \
                                  --iteration 1 \
                                  --depends mysql-client \
                                  --depends mysql-server \
                                  --depends nginx \
                                  --deb-recommends fabric \
                                  --deb-recommends pv \
                                  --deb-recommends drush \
                                  --description "Builder is a suite of command line tools to simplify the creation, syncing and destruction of local Vagrant-based Drupal development environments." \
                                  --maintainer "Miguel Jacq <mig@mig5.net>" \
                                  --vendor mig5 \
                                  --url https://github.com/mig5/builder \
                                  .
