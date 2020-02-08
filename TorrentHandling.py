#!/usr/bin/env python

'''
Created by: Itai Cherfas
this script will do the following:
1. Download subtitles for the lastest finished torrent
2. send an email with the subtitle info
3. delete torrentes that finished seeding
'''


import os
from  datetime import datetime as dt
import operator
import argparse

#dict month of number
month_dict={'Jan':1,
            'Feb':2,
            'Mar':3,
            'Apr':4,
            'May':5,
            'Jun':6,
            'Jul':7,
            'Aug':8,
            'Sep':9,
            'Oct':10,
            'Nov':11,
            'Dec':12
            }

# will be used for logging info
logger = "/home/pi/.local/bin/torrentHandling/automated_logger.log"
#realpat to OpenSubtitlesDownload.py script
open_subtitles_script_path ='/home/pi/.local/bin/OpenSubtitlesDownload.py'

def _get_torrents_id_list():
    '''
    this function will return a list of torrent ids for other functions to use
    '''
    # save transmission list data
    os.system('transmission-remote -l > /tmp/tr.tmp')
    f = open("/tmp/tr.tmp",'r')
    tr_ids =[]
    #remove the header line
    f.readline()
    for line in f:
        #handeling last line
        if (line.strip().split(' ')[0]!='Sum:'):
            tr_ids.append(line.strip().split(' ')[0])
    f.close()
    return tr_ids

def clean_finished_torrents():
    '''
    this function will search the list of torrents for the ones that finished seeding and delete them(keeping the files)
    '''
    # save trasmission data TODO: do i really need to run this???
    os.system('transmission-remote -l > /tmp/tr.tmp')
    os.system('echo "removing unneeded torrents" >>{logger}'.format(logger=logger))
    f = open("/tmp/tr.tmp",'r')
    tr_id_name_dict = {}
    for line in f:
        #search for status finished in info
        if 'Finished' in line:
            tr_id = line.strip().split(' ')[0]
            tr_name = ' '.join(line.split()).split(' ')[9]
            tr_id_name_dict[tr_id] = tr_name
    f.close()
    # remove the selected torrents
    for key in tr_id_name_dict:
        os.system('echo "removing torrent {tr}" >> {logger}'.format(tr=tr_id_name_dict[key],logger=logger))
        os.system('transmission-remote -t {id} -r >> {logger}'.format(id=key, logger=logger))

def download_subs_for_last_finished_torrent():
    '''
    this function will go over all the torrents in transmission, get the latest torrent id and download subtitles for it from opensubtitle
    '''
    tr_ids = _get_torrents_id_list()
    tr_date_time_id = {}
    for id in tr_ids:
        os.system('transmission-remote -t {id} -i > /tmp/tr.info'.format(id=id))
        f=open('/tmp/tr.info','r')
        for line in f:
            if ('Date finished' in line):
                #example for searched line: '   Date finished:    Mon Feb  3 18:42:57 2020'
                #split line to the attributs
                sp =" ".join(line.split()).split(' ')
                # line after split: '['Date', 'finished:', 'Wed', 'Feb', '5', '21:21:38', '2020']'
                year,month,day = int(sp[6]),month_dict[sp[3]],int(sp[4])
                time=sp[5].split(':')
                hour,minute,second = int(time[0]),int(time[1]),int(time[2])
                tr_date_time_id[id] = dt(year,month,day,hour,minute,second)
                break
    f.close()
    # get id of latest (biggest) date
    id_to_handle = max(tr_date_time_id.items(), key=operator.itemgetter(1))[0]

    # create the info of that id and get name and location
    #example: '   Name:  The Incredibles 2 2018 1080p BluRay x264 DTS 5.1 MSubS - Hon3yHD'
    #example: '   Location: /home/pi/Tv-Shows/Greys-Anatomy/s16'
    os.system('transmission-remote -t {id} -i > /tmp/tr.info'.format(id=id_to_handle))
    f=open('/tmp/tr.info','r')
    name = ""
    location = ""
    for line in f:
        if 'Name' in line:
            name = line.split(':')[1][1:]
            name = name.replace(' ',"\ ")
        if 'Location' in line:
            location = line.split(':')[1].strip() + '/'
            break
    f.close()
    # download the proper subtitles
    import pdb;pdb.set_trace()
    name = name.strip('\n')
    os.system('{open_subs_script} -a {path_to_folder} >> {logger} '.format(open_subs_script=open_subtitles_script_path,path_to_folder=location + name, logger=logger))


def main():
    os.system('rm {logger}'.format(logger=logger))
    os.system('echo "started running at: {time}" >>{logger}'.format(time=dt.now(),logger=logger))
    download_subs_for_last_finished_torrent()
    clean_finished_torrents()
    os.system('echo "finished running at: {time}" >>{logger}'.format(time=dt.now(),logger=logger))
    #send_email()
    exit(0)

if __name__ == '__main__':
    argparse.ArgumentParser(prog='TorrentHandleing.py',
                            description='Automatically download subtitles for latest torrent, delete finished seeding torrents and get a mail with the info!',
                            formatter_class=argparse.RawTextHelpFormatter)
    main()
