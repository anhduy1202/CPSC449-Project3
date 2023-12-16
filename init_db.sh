fusermount -u /var/primary/fuse
fusermount -u /var/secondary/fuse
fusermount -u /var/tertiary/fuse

rm -rf var/*

mkdir ./var/primary ./var/secondary ./var/tertiary
mkdir ./var/primary/data ./var/secondary/data ./var/tertiary/data
mkdir ./var/primary/fuse ./var/secondary/fuse ./var/tertiary/fuse

