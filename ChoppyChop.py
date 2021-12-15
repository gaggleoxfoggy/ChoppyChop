#!./.env/bin/python
# codng: utf-8

'''Video Trimmer

Cut down h.264 videos without transcoding.

'''

import shutil
import os
import sys
import re
import datetime
import time
import subprocess
import argparse
import json
import logging
from tqdm import tqdm


FORMAT = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log_file_only = logging.getLogger()
log.setLevel(logging.DEBUG)
log_file_only.setLevel(logging.DEBUG)
path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'choppy.log')
fh = logging.FileHandler(path)
fh.setFormatter(FORMAT)
ch = logging.StreamHandler()
log.addHandler(fh)
log.addHandler(ch)
log_file_only.addHandler(fh)

# Set paths
OUTPUT_LOCATION = os.path.expanduser('~/Desktop/ChoppyChop/')
ENCODING = os.path.join(OUTPUT_LOCATION, '.encoding/')

# Encoding options
FFMPEG_CHOP = ['ffmpeg -y',
                '-ss', '{startpoint}',
                '-to', '{runtime}',
                '-i', '{inpath}',
                '-c copy',
                '-bsf:v h264_mp4toannexb',
                '{outpath}']
FFMPEG_IMAGE = ['ffmpeg -y',
                '-f lavfi -i anullsrc -loop 1',
                '-i', '{inpath}',
                '-c:v libx264',
                '-b:v 10M',
                '-c:a aac',
                '-ar', '{sample_rate}',
                '-t 3',
                '-r', '{framerate}',
                '-pix_fmt', '{pix_fmt}',
                '-vf scale={width}:{height}',
                '{outpath}']
FFMPEG_VIDEO_MOS = ['ffmpeg -y',
                '-f lavfi -i anullsrc',
                '-i', '{inpath}',
                '-c:v libx264', #h264_videotoolbox',
                '-b:v 10M',
                '-c:a aac',
                '-ar', '{sample_rate}',
                '-r', '{framerate}',
                '-pix_fmt', '{pix_fmt}',
                '-vf scale={width}:{height}',
                '{outpath}']
FFMPEG_VIDEO = ['ffmpeg -y',
                '-i', '{inpath}',
                '-c:v libx264', #h264_videotoolbox',
                '-b:v 10M',
                '-c:a', '{audio_format}',
                '-ar', '{sample_rate}',
                '-t 3',
                '-r', '{framerate}',
                '-pix_fmt', '{pix_fmt}',
                '-vf scale={width}:{height}',
                '{outpath}']
FFMPEG_WATERMARK = ['ffmpeg -y',
                '-i', '{inpath}',
                '-i', '{watermark}',
                '-c:v libx264', #h264_videotoolbox',
                '-b:v 10M',
                '-filter_complex overlay',
                '{outpath}']
                
def clear():
    #Clear terminal window
    p = subprocess.Popen(['clear'])
    p.communicate()

def quotes(bs):
    #return string in quotes
    bs = "'" + bs + "'"
    return bs

def intro_message():
    log.info('-------------------------------------------------------------------------')
    log.info('Follow instructions to trim h.264 video files')
    log.info('Files will be exported to: {path}'.format(path=OUTPUT_LOCATION))
    log.info('-------------------------------------------------------------------------\n')


def make_dirs():
    #Create necessary directories
    for folder in [OUTPUT_LOCATION, ENCODING]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def clean_leftovers():
    #clear leftovers from previous run
    files = os.path.join(OUTPUT_LOCATION, 'listfile.txt')
    if os.path.exists(files):
                os.remove(files)
    files = os.path.join(OUTPUT_LOCATION, 'intro.ts')
    if os.path.exists(files):
                os.remove(files)
    files = os.path.join(OUTPUT_LOCATION, 'outro.ts')
    if os.path.exists(files):
                os.remove(files)

def get_url():
    "Prompt user for local file path"
    while True:
        url = input('Drag and drop local file: ')
        #path = re.sub("'", '', url).strip()
        path = re.sub('\\\\', '', url).strip()
        if check_path(path):
            return path
        log.warning('Something went wrong, please ensure you entered a valid file path.')

def get_addvideo(watermark):
    "Prompt user for additional local file path"
    while True:
        addwm = ''
        url = input('Drag and drop additional versions (Leave blank for none): ')
        #path = re.sub("'", '', url).strip()
        path = re.sub('\\\\', '', url).strip()
        if check_path(path):
            if watermark:
                addwm = input('Would you like this version watermarked? (y/n): ') or 'n'
                if addwm[0].lower() == 'y':
                    addwm = watermark
                else:
                    addwm = ''
            return path, addwm
        if not path:
            return path, addwm
        log.warning('Something went wrong, please ensure you entered a valid file path.')

def check_path(path):
    return os.path.exists(path)

def get_metadata(video_path):
    '''Get video metadata using ffprobe'''
    proc = ['ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path]
    log_file_only.info('subprocess call: {}'.format(proc))
    p = subprocess.Popen(proc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = p.communicate()
    metadata = json.loads(result[0])
    return metadata


def read_metadata(metadata):
    streams = metadata.get('streams')
    formats = metadata.get('format')

    duration = float(formats.get('duration'))
    filetype = formats.get('format_name')

    for stream in streams:
        if stream.get('codec_type') == 'video':
            width = int(stream['width'])
            height = int(stream['height'])
            vid_codec = stream['codec_name']
            pix_fmt = stream['pix_fmt']
            framerate = stream['r_frame_rate']
            #bitrate = stream['bit_rate'] zzzfails on image source
        else:
            if stream.get('codec_type') == 'audio':
                audio_codec = stream['codec_name']
                sample_rate = stream['sample_rate']
        continue
    try:
        tmp = audio_codec
    except:
        audio_codec = ''
        sample_rate = ''

    return (width, height, vid_codec, pix_fmt, framerate, audio_codec, sample_rate, duration, filetype)

def get_trim():
    # Get trim points for video
    inpoint = get_time('in')
    outpoint = get_time('out')
    return inpoint, outpoint

def get_time(mode):
    # prompt for in and out points
    while True:
        bs = input('What %s point do you want? (hh:mm:ss.ms, leave blank for default): ' % mode)
        return bs

def get_ends(mode, video):
    # prompt for intro or outro
    while True:
        bs = input('Drag & drop %s file (leave blank for none): ' % mode)
        if not bs:
            return bs
        else:
            #path = re.sub("'", '', bs).strip()
            path = re.sub('\\\\', '', bs).strip()
            if check_path(path):
                #filename, ext = os.path.splitext(video)
                encode(path, '', '', mode, video, '', '')
                return path
        log.warning('Something went wrong, please ensure you entered a valid file path.')

def get_watermark():
    # prompt for watermark
    while True:
        bs = input('Drag & drop watermark file (leave blank for none): ')
        if not bs:
            return bs
        else:
            #path = re.sub("'", '', bs).strip()
            path = re.sub('\\\\', '', bs).strip()
            if check_path(path):
                return path
        log.warning('Something went wrong, please ensure you entered a valid file path.')

def get_subclip():
    # prompt for additional name extensions
    bs = input('Enter additional filename options (leave blank for none): ')
    return bs

def process(proc, duration):
    log_file_only.info('subprocess call: {}'.format(proc))
    p = subprocess.Popen(proc, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    seconds_encoded = float()
    with tqdm(total=duration, desc='Encoding') as pbar:
        for line in iter(p.stdout.readline, ''):
            log_file_only.info(line.rstrip())

            re1='.*?'	# Non-greedy match on filler
            re2='(time)'	# Word 1
            re3='(=)'	# Any Single Character 1
            re4='(\\d+)'	# Integer Number 1
            re5='(:)'	# Any Single Character 2
            re6='(\\d+)'	# Integer Number 2
            re7='(:)'	# Any Single Character 3
            re8='(\\d+)'	# Integer Number 3
            re9='(\\.)'	# Any Single Character 4
            re10='(\\d+)'	# Integer Number 4

            rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10,re.IGNORECASE|re.DOTALL)
            m = rg.search(line)
            if m:
                int1=m.group(3)
                c2=m.group(4)
                int2=m.group(5)
                c3=m.group(6)
                int3=m.group(7)
                c4=m.group(8)
                int4=m.group(9)

                time_progress = int1+c2+int2+c3+int3+c4+int4
                t = datetime.datetime.strptime(time_progress, '%H:%M:%S.%f')
                total_seconds = (t - datetime.datetime(1900, 1, 1)).total_seconds()
                pbar.update(total_seconds - seconds_encoded)
                seconds_encoded = total_seconds
    p.communicate()

def encode(video, inpoint, outpoint, opt1, opt2, opt3, watermark):
    # output video files
    metadata = get_metadata(video)
    width, height, vid_codec, pix_fmt, framerate, audio_codec, sample_rate, duration, filetype = read_metadata(metadata)
    filename, ext = os.path.splitext(video)
    filename = os.path.splitext(os.path.basename(filename))[0]
    videopath = quotes(video)
    if opt3:
        opt3 = '_' + opt3

    if opt1 == 'intro' or opt1 == 'outro': #match intro/outro to destination format
        metadata = get_metadata(opt2)
        width, height, null, pix_fmt, framerate, null, sample_rate, duration, null = read_metadata(metadata)
        filename, ext = os.path.splitext(opt2)
        filename = os.path.splitext(os.path.basename(filename))[0]
        outpath = os.path.join("'" + OUTPUT_LOCATION, opt1 + ".ts'")
        if os.path.exists(outpath): #skip encode if file already exist
            return
        else:
            if not audio_codec: # if source doesn't have audio, add null audio track
                if filetype == 'image2':
                    proc = ' '.join(FFMPEG_IMAGE).format(inpath=videopath, sample_rate=sample_rate, framerate=framerate, pix_fmt=pix_fmt, width=width, height=height, outpath=outpath)
                else:
                    proc = ' '.join(FFMPEG_VIDEO_MOS).format(inpath=videopath, sample_rate=sample_rate, framerate=framerate, pix_fmt=pix_fmt, width=width, height=height, outpath=outpath)
            else:
                proc = ' '.join(FFMPEG_VIDEO).format(inpath=videopath, audio_format=audio_codec, sample_rate=sample_rate, framerate=framerate, pix_fmt=pix_fmt, width=width, height=height, outpath=outpath)
        process(proc, duration)

    else: # process as normal if not intro/outro
        if not inpoint:
            inpoint = '00:00:00'
        if not outpoint:
            outpoint = time.strftime('%H:%M:%S', time.gmtime(duration + 1))
        if opt1 or opt2:
            tmpoutpath = os.path.join("'" + OUTPUT_LOCATION, filename + opt3 + "_TEMP.ts'")
            proc = ' '.join(FFMPEG_CHOP).format(inpath=videopath, startpoint=inpoint, outpath=tmpoutpath, runtime=outpoint)
            process(proc, duration)
            listfile = os.path.join(OUTPUT_LOCATION, 'listfile.txt')
            outpath = os.path.join(OUTPUT_LOCATION, filename + opt3 + ext) 
            if os.path.exists(listfile):
                os.remove(listfile)
            with open(listfile, 'w+') as f:
                if opt1:
                    f.write("file '" + OUTPUT_LOCATION + "intro.ts'")
                    f.write('\n')
                f.write('file ' + tmpoutpath)
                f.write('\n')
                if opt2:
                    f.write("file '" + OUTPUT_LOCATION + "outro.ts'")
                    f.write('\n')
            proc = 'ffmpeg -y -safe 0 -f concat -i ' + listfile + ' -c copy ' + quotes(outpath)
            process(proc, duration)
            if os.path.exists(listfile):
                os.remove(listfile)
            tmpoutpath = os.path.join(OUTPUT_LOCATION, filename + opt3 + "_TEMP.ts")
            if os.path.exists(tmpoutpath):
                os.remove(tmpoutpath)

        else:
            outpath = os.path.join("'" + OUTPUT_LOCATION, filename + opt3 + ext + "'")
            proc = ' '.join(FFMPEG_CHOP).format(inpath=videopath, startpoint=inpoint, outpath=outpath, runtime=outpoint)
            process(proc, duration)

        if watermark:
            wmfilename, wmext = os.path.splitext(watermark)
            tmpwatermark = os.path.join(OUTPUT_LOCATION, 'WATERMARK' + wmext)
            proc = 'ffmpeg -y -i ' + watermark + ' -vf scale=' + str(width) + ':' + str(height) + ' ' + quotes(tmpwatermark)
            process(proc, duration)
            wmpath = os.path.join("'" + OUTPUT_LOCATION, filename + opt3 +'_WATERMARK' + ext + "'")
            proc = ' '.join(FFMPEG_WATERMARK).format(inpath=quotes(outpath), watermark=quotes(tmpwatermark), outpath=wmpath)
            process(proc, duration)
            if os.path.exists(tmpwatermark):
                os.remove(tmpwatermark)


def main():
    clean_leftovers()
    
    while True:
        make_dirs()
        clear()
        intro_message()

        video = get_url()
        inpoint, outpoint = get_trim()        
        watermark = get_watermark()
        intro = get_ends('intro', video)
        outro = get_ends('outro', video)
        subclip = get_subclip()
        addvideo, addwm = get_addvideo(watermark)

        encode(video, inpoint, outpoint, intro, outro, subclip, watermark)
        if addvideo:
            encode(addvideo, inpoint, outpoint, intro, outro, subclip, addwm)

if __name__ == '__main__':
    main()
