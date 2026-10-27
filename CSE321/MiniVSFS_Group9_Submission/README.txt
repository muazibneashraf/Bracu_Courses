MiniVSFS Project Submission
============================

Files:
- mkfs_builder.c
- mkfs_adder.c

Group ID: 9

Compilation:
-------------
gcc -std=gnu11 -O2 -Wall -Wextra mkfs_builder.c -o mkfs_builder
gcc -std=gnu11 -O2 -Wall -Wextra mkfs_adder.c  -o mkfs_adder

Usage:
-------
1. Build file system image:
   ./mkfs_builder --image out.img --size-kib 180 --inodes 128

2. Add a file into the image:
   ./mkfs_adder --input out.img --output out2.img --file file_15.txt

Notes:
- Maximum size: 4096 KiB, minimum: 180 KiB (multiple of 4).
- Number of inodes: 128–512.
- Supports files up to 12 direct blocks (48 KiB max).
- Root directory always inode #1.
- Group ID is set to 9.
