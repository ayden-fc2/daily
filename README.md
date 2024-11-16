# 使用说明
## 放置文件
1. 多张图片（jpg/png/jpeg）放在images目录下
2. mp3文件放在music目录下，格式命名为 xxx - song_name.mp3，因为我是直接从spotifydown下载的这种格式，顺便解析歌名硬编码了。

## 安装使用
1. pip install 以下包：ffmpeg-python mutagen
2. 本机安装ffmpeg

## 运行
python3 gen_video.py即可
如果运行报错获取不到歌曲封面和歌手名，可以编辑gen_video.py文件，修改TODO的三个参数。
