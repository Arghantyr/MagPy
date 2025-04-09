#!/bin/bash

# TODO
#
# Dodać sprawdzanie wartości UID, GID pod kątem wartości systemowych (<1000)
# Sprawdzać UID/GID pod kątem bycia liczbą z zakresu 1000-10000
# Sprawdzać uprawnienia użytkownika
#
# W przypadku błędu powyższych warunków opuścić środowisko
# i poinformować użytkownika o potencjalnych kolizjach i niebezpieczeństwie.

#python3 ./prepare_scripts.py

echo UID="$(id -u)" > ./.env
echo GID="$(id -g)" >> ./.env
python3 ./prepare_env.py

mkdir ./gitworker/repo
chmod u=rwx,go=rx ./gitworker/repo

cp ./gitworker/hash_reg ./gitworker/repo/hash_reg
chmod u=rw,go=r ./gitworker/repo/hash_reg

cp ./gitworker/file_index ./gitworker/repo/file_index
chmod u=rw,go=r ./gitworker/repo/file_index

docker-compose up -d
