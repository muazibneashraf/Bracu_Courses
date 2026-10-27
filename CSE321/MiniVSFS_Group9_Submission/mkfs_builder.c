#define _FILE_OFFSET_BITS 64
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
#include <errno.h>
#include <time.h>
#include <getopt.h>

#define BS 4096u
#define INODE_SIZE 128u
#define ROOT_INO 1u
#define DIRECT_MAX 12

#pragma pack(push,1)
typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t block_size;
    uint64_t total_blocks;
    uint64_t inode_count;
    uint64_t inode_bitmap_start;
    uint64_t inode_bitmap_blocks;
    uint64_t data_bitmap_start;
    uint64_t data_bitmap_blocks;
    uint64_t inode_table_start;
    uint64_t inode_table_blocks;
    uint64_t data_region_start;
    uint64_t data_region_blocks;
    uint64_t root_inode;
    uint64_t mtime_epoch;
    uint32_t flags;
    uint32_t checksum;
} superblock_t;
#pragma pack(pop)
_Static_assert(sizeof(superblock_t)==116,"superblock must fit in one block");

#pragma pack(push,1)
typedef struct {
    uint16_t mode;
    uint16_t links;
    uint32_t uid;
    uint32_t gid;
    uint64_t size_bytes;
    uint64_t atime;
    uint64_t mtime;
    uint64_t ctime;
    uint32_t direct[12];
    uint32_t reserved_0;
    uint32_t reserved_1;
    uint32_t reserved_2;
    uint32_t proj_id;
    uint32_t uid16_gid16;
    uint64_t xattr_ptr;
    uint64_t inode_crc;
} inode_t;
#pragma pack(pop)
_Static_assert(sizeof(inode_t)==INODE_SIZE,"inode size mismatch");

#pragma pack(push,1)
typedef struct {
    uint32_t inode_no;
    uint8_t type;
    char name[58];
    uint8_t checksum;
} dirent64_t;
#pragma pack(pop)
_Static_assert(sizeof(dirent64_t)==64,"dirent size mismatch");

uint32_t CRC32_TAB[256];
void crc32_init(void){
    for(uint32_t i=0;i<256;i++){
        uint32_t c=i;
        for(int j=0;j<8;j++) c=(c&1)?(0xEDB88320u^(c>>1)):(c>>1);
        CRC32_TAB[i]=c;
    }
}
uint32_t crc32(const void* data,size_t n){
    const uint8_t* p=(const uint8_t*)data; uint32_t c=0xFFFFFFFFu;
    for(size_t i=0;i<n;i++) c=CRC32_TAB[(c^p[i])&0xFF]^(c>>8);
    return c^0xFFFFFFFFu;
}
static uint32_t superblock_crc_finalize(superblock_t* sb){
    sb->checksum=0;
    uint32_t s=crc32((void*)sb,BS-4);
    sb->checksum=s;
    return s;
}
void inode_crc_finalize(inode_t* ino){
    uint8_t tmp[INODE_SIZE]; memcpy(tmp,ino,INODE_SIZE);
    memset(&tmp[120],0,8);
    uint32_t c=crc32(tmp,120);
    ino->inode_crc=(uint64_t)c;
}
void dirent_checksum_finalize(dirent64_t* de){
    const uint8_t* p=(const uint8_t*)de; uint8_t x=0;
    for(int i=0;i<63;i++) x^=p[i];
    de->checksum=x;
}

static inline void bm_set(uint8_t* bm,uint64_t idx){ bm[idx>>3]|=(uint8_t)(1u<<(idx&7u)); }
static inline int bm_get(const uint8_t* bm,uint64_t idx){ return (bm[idx>>3]>>(idx&7u))&1u; }

typedef struct {
    const char* image_path;
    uint32_t size_kib;
    uint32_t inodes;
} cli_t;

static int parse_cli(int argc,char** argv,cli_t* c){
    memset(c,0,sizeof(*c));
    static struct option lo[]={ {"image",1,0,'i'},{"size-kib",1,0,'s'},{"inodes",1,0,'n'},{0,0,0,0} };
    int opt;
    while((opt=getopt_long(argc,argv,"i:s:n:",lo,NULL))!=-1){
        if(opt=='i') c->image_path=optarg;
        else if(opt=='s') c->size_kib=(uint32_t)strtoul(optarg,NULL,10);
        else if(opt=='n') c->inodes=(uint32_t)strtoul(optarg,NULL,10);
        else return -1;
    }
    if(!c->image_path) return -1;
    if(c->size_kib<180||c->size_kib>4096||(c->size_kib%4)!=0) return -1;
    if(c->inodes<128||c->inodes>512) return -1;
    return 0;
}

int main(int argc,char** argv){
    crc32_init();
    cli_t cli;
    if(parse_cli(argc,argv,&cli)!=0) return 1;
    uint64_t total_blocks=(cli.size_kib*1024ull)/BS;
    uint64_t inode_tbl_bytes=(uint64_t)cli.inodes*INODE_SIZE;
    uint64_t inode_tbl_blocks=(inode_tbl_bytes+BS-1)/BS;
    uint64_t superblock_start=0;
    uint64_t inode_bm_start=superblock_start+1;
    uint64_t data_bm_start=inode_bm_start+1;
    uint64_t inode_tbl_start=data_bm_start+1;
    uint64_t data_start=inode_tbl_start+inode_tbl_blocks;
    if(total_blocks<=data_start) return 2;
    uint64_t data_blocks=total_blocks-data_start;
    if(data_blocks==0) return 2;
    uint64_t img_bytes=total_blocks*BS;
    uint8_t* img=(uint8_t*)calloc(1,img_bytes);
    if(!img) return 3;
    superblock_t* sb=(superblock_t*)(img+superblock_start*BS);
    uint8_t* inode_bm=img+inode_bm_start*BS;
    uint8_t* data_bm=img+data_bm_start*BS;
    inode_t* inode_tbl=(inode_t*)(img+inode_tbl_start*BS);
    uint8_t* data_region=img+data_start*BS;
    memset(sb,0,sizeof(*sb));
    sb->magic=0x4D565346u;
    sb->version=1;
    sb->block_size=BS;
    sb->total_blocks=total_blocks;
    sb->inode_count=cli.inodes;
    sb->inode_bitmap_start=inode_bm_start;
    sb->inode_bitmap_blocks=1;
    sb->data_bitmap_start=data_bm_start;
    sb->data_bitmap_blocks=1;
    sb->inode_table_start=inode_tbl_start;
    sb->inode_table_blocks=inode_tbl_blocks;
    sb->data_region_start=data_start;
    sb->data_region_blocks=data_blocks;
    sb->root_inode=ROOT_INO;
    sb->mtime_epoch=(uint64_t)time(NULL);
    sb->flags=0;
    bm_set(inode_bm,0);
    bm_set(data_bm,0);
    inode_t* root=&inode_tbl[0];
    memset(root,0,sizeof(*root));
    root->mode=040000;
    root->links=2;
    root->uid=0;
    root->gid=0;
    root->size_bytes=2*sizeof(dirent64_t);
    root->atime=root->mtime=root->ctime=(uint64_t)time(NULL);
    for(int i=0;i<DIRECT_MAX;i++) root->direct[i]=0;
    root->direct[0]=(uint32_t)(data_start+0);
    root->proj_id=9;
    root->uid16_gid16=0;
    root->xattr_ptr=0;
    inode_crc_finalize(root);
    dirent64_t* dent=(dirent64_t*)(data_region+0*BS);
    memset(dent,0,BS);
    dent[0].inode_no=ROOT_INO; dent[0].type=2; memset(dent[0].name,0,sizeof(dent[0].name)); dent[0].name[0]='.'; dirent_checksum_finalize(&dent[0]);
    dent[1].inode_no=ROOT_INO; dent[1].type=2; memset(dent[1].name,0,sizeof(dent[1].name)); dent[1].name[0]='.'; dent[1].name[1]='.'; dirent_checksum_finalize(&dent[1]);
    superblock_crc_finalize(sb);
    FILE* f=fopen(cli.image_path,"wb");
    if(!f){ free(img); return 4; }
    size_t nw=fwrite(img,1,img_bytes,f);
    fclose(f);
    free(img);
    if(nw!=img_bytes) return 5;
    return 0;
}
