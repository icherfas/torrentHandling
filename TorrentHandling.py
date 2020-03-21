#!/usr/bin/env python3

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
import re

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
logger = "/home/icherfas/automated_logger.log"
# realpatt to general script folder.
general_script_folder ='/home/icherfas/generalScripts/'
# tv shows base folder
tv_shows = '/home/icherfas/shared_storage/TV-Shows/'

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

def clean_finished_seeding_torrents():
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

def download_subs_a_torrent(tr_id, name, location):
    '''
    this function will download subtitles for a given transmission id from opensubtitle
    args:
        tr_id - id as in transmission
        name - torrent name as in torrent info
        location - folder as in torront info
    '''
    os.system('{open_subs_script} -a {path_to_folder} -l eng -l heb >> {logger} '.format(open_subs_script=general_script_folder + 'OpenSubtitlesDownload.py',path_to_folder=location + name, logger=logger))

def arrange_torrent(tr_id, name, location):
    '''
    this function will move a given tr_id to the proper folder - movie or episode
    args:
        tr_id - id as in transmission
        name - torrent name as in torrent info
        location - folder as in torront info
    return:
        torrent location - might change if the torrent was an episode
    '''
    #regex pattern to catch tv episodes
    pattern = '[sS]\d{1,2}[eE]\d{1,2}'
    if re.search(pattern, name):
        #catch show name
        pt_name = '(^\D+).[sS]\d{1,2}'
        result = re.search(pt_name, name).group(1)
        # in case of delimiter between words is dot or space, replace all to '_' and put it in lower case
        result = result.replace(' ', '_').replace('.', '_').lower()
        new_location = tv_shows + result
        os.system('transmission-remote -t {tr_id} --move {new_location} >> {logger}'.format( tr_id = tr_id, logger = logger, new_location = new_location))
        os.system('transmission-remote -t {tr_id} -i | grep Name >> {logger}'.format(tr_id = tr_id, logger = logger))
        os.system('echo moved to {new_location} >> {logger}'.format(new_location = new_location, logger = logger))
        location = new_location + '/'
    else:
        os.system('echo "not a tv episode." >> {logger}'.format(logger=logger))
    return location

def get_last_torrent_id():
    '''
    this function will go over all the torrents in transmission and return its transmission id
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
    return max(tr_date_time_id.items(), key=operator.itemgetter(1))[0]

def get_torrent_name_and_folder(tr_id):
    '''
    this function will return the torrent name and containing folder for a given tr_id
    '''
    # create the info of that id and get name and location
    #example: '   Name:  The Incredibles 2 2018 1080p (10Bit) BluRay x264 DTS 5.1 MSubS - Hon3yHD'
    #example: '   Location: /home/pi/Tv-Shows/Greys-Anatomy/s16'
    os.system('transmission-remote -t {id} -i > /tmp/tr.info'.format(id=tr_id))
    f=open('/tmp/tr.info','r')
    name = ""
    location = ""
    for line in f:
        if 'Name' in line:
            name = line.split(':')[1][1:].replace(')',"\)").replace(' ',"\ ").replace('(',"\(")
        if 'Location' in line:
            location = line.split(':')[1].strip() + '/'
            break
    f.close()
    # download the proper subtitles
    name = name.strip('\n')
    return name, location

def main(args):
    os.system('echo "started running at: {time}" >>{logger}'.format(time=dt.now(),logger=logger))
    if args.debug:
        import pdb;pdb.set_trace()
    tr_id = get_last_torrent_id()
    tr_name, tr_location = get_torrent_name_and_folder(tr_id)
    tr_location = arrange_torrent(tr_id, tr_name, tr_location)
    download_subs_a_torrent(tr_id, tr_name, tr_location)
    clean_finished_seeding_torrents()
    os.system('echo "finished running at: {time}" >>{logger}'.format(time=dt.now(),logger=logger))
    #send_email()
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='TorrentHandleing.py',
                            description='Automatically move tv episodes to: {tv}\nDownload subtitles for latest torrent completed\nDelete finished seeding torrents\nSend an email with the info'.format(tv=tv_shows),
                            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--debug', help='this will ivoke pdb while running')
    args = parser.parse_args()
    main(args)
