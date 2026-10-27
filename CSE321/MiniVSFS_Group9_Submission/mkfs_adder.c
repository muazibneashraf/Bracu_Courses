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

static inline int bm_get(const uint8_t* bm,uint64_t idx){ return (bm[idx>>3]>>(idx&7u))&1u; }
static inline void bm_set(uint8_t* bm,uint64_t idx){ bm[idx>>3]|=(uint8_t)(1u<<(idx&7u)); }

typedef struct {
    const char* input_path;
    const char* output_path;
    const char* add_file;
} cli_t;

static int parse_cli(int argc,char** argv,cli_t* c){
    memset(c,0,sizeof(*c));
    static struct option lo[]={ {"input",1,0,'i'},{"output",1,0,'o'},{"file",1,0,'f'},{0,0,0,0} };
    int opt;
    while((opt=getopt_long(argc,argv,"i:o:f:",lo,NULL))!=-1){
        if(opt=='i') c->input_path=optarg;
        else if(opt=='o') c->output_path=optarg;
        else if(opt=='f') c->add_file=optarg;
        else return -1;
    }
    if(!c->input_path||!c->output_path||!c->add_file) return -1;
    return 0;
}

static int read_file(const char* path,uint8_t** out,size_t* out_len){
    *out=NULL; *out_len=0;
    FILE* f=fopen(path,"rb");
    if(!f) return -1;
    if(fseek(f,0,SEEK_END)!=0){ fclose(f); return -1; }
    long sz=ftell(f);
    if(sz<0){ fclose(f); return -1; }
    rewind(f);
    uint8_t* buf=(uint8_t*)malloc((size_t)sz);
    if(!buf){ fclose(f); return -1; }
    size_t rd=fread(buf,1,(size_t)sz,f);
    fclose(f);
    if(rd!=(size_t)sz){ free(buf); return -1; }
    *out=buf; *out_len=rd;
    return 0;
}

int main(int argc,char** argv){
    crc32_init();
    cli_t cli;
    if(parse_cli(argc,argv,&cli)!=0) return 1;
    uint8_t* img=NULL; size_t img_bytes=0;
    if(read_file(cli.input_path,&img,&img_bytes)!=0) return 2;
    if(img_bytes%BS!=0){ free(img); return 2; }
    superblock_t* sb=(superblock_t*)(img+0*BS);
    if(sb->block_size!=BS||sb->magic!=0x4D565346u){ free(img); return 2; }
    uint8_t* inode_bm=img+sb->inode_bitmap_start*BS;
    uint8_t* data_bm=img+sb->data_bitmap_start*BS;
    inode_t* inode_tbl=(inode_t*)(img+sb->inode_table_start*BS);
    uint8_t* data_region=img+sb->data_region_start*BS;
    uint8_t* filebuf=NULL; size_t filelen=0;
    if(read_file(cli.add_file,&filebuf,&filelen)!=0){ free(img); return 3; }
    uint64_t need_blocks=(filelen+BS-1)/BS;
    if(need_blocks>DIRECT_MAX){ free(filebuf); free(img); return 4; }
    uint64_t free_ino_idx=0; int found=0;
    for(uint64_t i=0;i<sb->inode_count;i++){ if(!bm_get(inode_bm,i)){ free_ino_idx=i; found=1; break; } }
    if(!found){ free(filebuf); free(img); return 5; }
    bm_set(inode_bm,free_ino_idx);
    uint32_t new_ino_no=(uint32_t)(free_ino_idx+1);
    uint64_t* chosen=(uint64_t*)calloc(need_blocks,sizeof(uint64_t));
    if(!chosen){ free(filebuf); free(img); return 6; }
    uint64_t got=0;
    for(uint64_t i=0;i<sb->data_region_blocks && got<need_blocks;i++){
        if(!bm_get(data_bm,i)){ bm_set(data_bm,i); chosen[got++]=i; }
    }
    if(got!=need_blocks){ free(chosen); free(filebuf); free(img); return 7; }
    for(uint64_t i=0;i<need_blocks;i++){
        uint64_t abs_blk=sb->data_region_start+chosen[i];
        uint8_t* blk=img+abs_blk*BS;
        size_t off=(size_t)(i*BS);
        size_t chunk=(off+BS<=filelen)?BS:(filelen-off);
        memset(blk,0,BS);
        memcpy(blk,filebuf+off,chunk);
    }
    inode_t* ino=&inode_tbl[free_ino_idx];
    memset(ino,0,sizeof(*ino));
    ino->mode=0100000;
    ino->links=1;
    ino->uid=0; ino->gid=0;
    ino->size_bytes=filelen;
    ino->atime=ino->mtime=ino->ctime=(uint64_t)time(NULL);
    for(int i=0;i<DIRECT_MAX;i++) ino->direct[i]=0;
    for(uint64_t i=0;i<need_blocks;i++) ino->direct[i]=(uint32_t)(sb->data_region_start+chosen[i]);
    ino->proj_id=9; ino->uid16_gid16=0; ino->xattr_ptr=0;
    inode_crc_finalize(ino);
    inode_t* root=&inode_tbl[0];
    uint32_t root_blk=root->direct[0];
    if(root_blk==0){ free(chosen); free(filebuf); free(img); return 8; }
    dirent64_t* dent=(dirent64_t*)(img+root_blk*BS);
    int slots=(int)(BS/sizeof(dirent64_t)); int slot=-1;
    for(int i=0;i<slots;i++){ if(dent[i].inode_no==0){ slot=i; break; } }
    if(slot<0){ free(chosen); free(filebuf); free(img); return 9; }
    memset(&dent[slot],0,sizeof(dirent64_t));
    dent[slot].inode_no=new_ino_no;
    dent[slot].type=1;
    const char* base=strrchr(cli.add_file,'/'); base=base?base+1:cli.add_file;
#ifdef _WIN32
    const char* b2=strrchr(cli.add_file,'\\'); if(!base||(b2&&b2>base)) base=b2+1;
#endif
    size_t nlen=strlen(base); if(nlen>58) nlen=58;
    memcpy(dent[slot].name,base,nlen);
    dirent_checksum_finalize(&dent[slot]);
    root->links+=1;
    root->mtime=root->ctime=(uint64_t)time(NULL);
    inode_crc_finalize(root);
    sb->mtime_epoch=(uint64_t)time(NULL);
    superblock_crc_finalize(sb);
    FILE* fo=fopen(cli.output_path,"wb");
    if(!fo){ free(chosen); free(filebuf); free(img); return 10; }
    size_t nw=fwrite(img,1,img_bytes,fo);
    fclose(fo);
    free(chosen); free(filebuf); free(img);
    if(nw!=img_bytes) return 11;
    return 0;
}
