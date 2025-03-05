#!/bin/bash

# TODO
#
# Dodać sprawdzanie wartości UID, GID pod kątem wartości systemowych (<1000)
# Sprawdzać UID/GID pod kątem bycia liczbą z zakresu 1000-10000
# Sprawdzać uprawnienia użytkownika
#
# W przypadku błędu powyższych warunków opuścić środowisko
# i poinformować użytkownika o potencjalnych kolizjach i niebezpieczeństwie.
echo UID="$(id -u)" > ./.env
echo GID="$(id -g)" >> ./.env
echo USERNAME=test_user >> ./.env
cat ./.env

mkdir ./gitworker/repo
chmod u=rwx,go=rx ./gitworker/repo

docker-compose up --force-recreate -d
