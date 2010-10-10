
################################   Titulky.com #################################


import sys
import os
import xbmc,xbmcgui

import time,calendar
import urllib2,urllib,re,cookielib
from utilities import toOpenSubtitles_two, log

_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__

"""
            <tr class="row2">
                    <td><a href="Pulp-Fiction-118518.htm" >Pulp Fiction</a></td>
          <td align="center"><a class="fixedTip" title="Pulp.Fiction.1994.720p.BluRay.x264-SiNNERS"><img src="img/ico/rel.gif" atl="release"/></a></td>        
          <td>&nbsp;</td>
          <td>1994</td>
                    <td>18.11.2008</td>        
          <td align="right">681</td>
          <td>CZ</td>
          <td>1</td>
          <td align="right">8138.46MB</td>
                    <td>
                           <a href="" onclick="UD('119203');return false;" > aAaX</a>
                      </td>
        </tr>

"""

subtitle_pattern='..<tr class=\"row[12]\">\s+?<td?[= \w\"]+><a href=\"[\w-]+-(?P<id>\d+).htm\"[ ]?>(?P<title>[\w\- ]*)</a></td>\s+?<td?[= \w\"]+>(<a?[= \w\"]+title=\"(?P<sync>[,\{\}\w.\d \(\)\]\[-]+)\"><img?[= \w\\./"]+></a>)?</td>\s+?<td?[= \w\"]+>(?P<tvshow>[\w\;\&]+)</td>\s+<td?[= \w\"]+>(?P<year>\d+)</td>\s+<td?[= \w\"]+>[\w\;\&\.\d]+</td>\s+<td?[= \w\"]+>(?P<downloads>\d+)</td>\s+<td?[= \w\"]+>(?P<lang>\w{2})</td>'

control_image_pattern='(secode.php\?[\w\d=]+)'
session_id_pattern='secode.php\?PHPSESSID=([\w\d]+)'
countdown_pattern='CountDown\((\d+)\)'

"""
<a rel="nofollow" id="downlink" href="/idown.php?id=48504441">www.titulky.com/idown.php?id=48504441</a>
"""

sublink_pattern='<a?[= \w\"]+href="([\w\.\?\d=/]+)\"'
def search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3 ): #standard input
	# need to filter titles like <Localized movie name> (<Movie name>)
	br_index = title.find('(')
	if br_index > -1:
		title = title[:br_index]
	title = title.strip()
#   print 'path '+file_original_path
#    print 'title '+title
#    print 'tvshow '+tvshow
#   print 'year '+year
#   print 'season '+season
#    print 'episode'+episode
#    print 'set_temp '+str(set_temp)
#    print 'rar '+str(rar)
#    print 'lang1 '+lang1
#    print 'lang2 '+lang2
#    print 'lang3 '+lang3
	session_id = "0"
	client = TitulkyClient()    
	subtitles_list = client.search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3 )   
	return subtitles_list, session_id, ""  #standard output



def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input

	subtitle_id =  subtitles_list[pos][ 'ID' ]
#	print pos
#	print zip_subs
#	print tmp_sub_dir
#	print sub_folder
#	print session_id
#	print subtitle_id
    
	client = TitulkyClient()
	log(__name__,'Get page with subtitle (id=%s)'%(subtitle_id))
	content = client.get_subtitle_page(subtitle_id)
	control_img = client.get_control_image(content)
	if not control_img == None:
		log(__name__,'Found control image :(, asking user for input')
		# subtitle limit was reached .. we need to ask user to rewrite image code :(
		log(__name__,'Download control image')
		img = client.get_file(control_img)
		img_file = open(os.path.join(tmp_sub_dir,'image.png'),'w')
		img_file.write(img)
		img_file.close()
		dialog = xbmcgui.Dialog()
		dialog.ok(__scriptname__,_( 757 ),_( 758 ))		
		log(__name__,'Notifying user for 10s')
		xbmc.executebuiltin("XBMC.Notification(%s,%s,10000,%s)" % (__scriptname__,'',os.path.join(tmp_sub_dir,'image.png')))		
		kb = xbmc.Keyboard('',_( 759 ),False)
		kb.doModal()
		if kb.isConfirmed():
			code = kb.getText()
			content = client.get_subtitle_page2(content,code,subtitle_id)
			control_img2 = client.get_control_image(content)
			if not control_img2 == None:
				log(__name__,'Invalid control text')
				return True,subtitles_list[pos]['language_name'], ""
		else:
			# user was not interested 
			log(__name__,'Control text not confirmed, returning in error')
			return True,subtitles_list[pos]['language_name'], ""
	wait_time = client.get_waittime(content)
	link = client.get_link(content)
	log(__name__,'Got the link, wait %i seconds before download' % (wait_time))
	delay = wait_time
	icon =  os.path.join(os.getcwd(),'icon.png')
	for i in range(wait_time+1):
		line2 = 'Download will start in %i seconds' % (delay,)
		xbmc.executebuiltin("XBMC.Notification(%s,%s,1000,%s)" % (__scriptname__,line2,icon))
		delay -= 1
		time.sleep(1)
	log(__name__,'Downloading subtitle zip')
	data = client.get_file(link)
	log(__name__,'Saving to file %s' % zip_subs)
	zip_file = open(zip_subs,'wb')
	zip_file.write(data)
	zip_file.close()
	return True,subtitles_list[pos]['language_name'], "" #standard output

def lang_titulky2xbmclang(lang):
	if lang == 'CZ': return 'Czech'
	if lang == 'SK': return 'Slovak'
	return 'English'

def lang_xbmclang2titulky(lang):
	if lang == 'Czech': return 'CZ'
	if lang == 'Slovak': return 'SK'
	return 'EN'	

def lang2_opensubtitles(lang):
	lang = lang_titulky2xbmclang(lang)
	return toOpenSubtitles_two(lang)
    
class TitulkyClient(object):
	
	def __init__(self):
		self.server_url = 'http://www.titulky.com'
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
		opener.version = 'User-Agent=Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)'
		urllib2.install_opener(opener)
	
	def search_subtitles(self, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3 ):	
		url = self.server_url+'/index.php?'+urllib.urlencode({'Fulltext':title,'FindUser':''})
		req = urllib2.Request(url)
		log(__name__,'Opening %s' % (url))
		response = urllib2.urlopen(req)
		content = response.read()
		response.close()
		log(__name__,'Done')
		subtitles_list = []
		for matches in re.finditer(subtitle_pattern, content, re.IGNORECASE | re.DOTALL):			
#			print matches.group('id') +' ' +matches.group('title')+' '+ str(matches.group('sync'))+' '+ matches.group('tvshow')+' '+ matches.group('year')+' '+ matches.group('downloads')+' '+ matches.group('lang')
			file_name = matches.group('sync')
			if file_name == None: # if no sync info is found, just use title instead of None
				file_name = matches.group('title') 
			flag_image = "flags/%s.gif" % (lang2_opensubtitles(matches.group('lang')))
			sync = False
			if file_original_path.find(matches.group('sync')) > -1:
				sync = True
			if not matches.group('year') == year:
				continue
			lang = lang_titulky2xbmclang(matches.group('lang'))
			if lang == lang1 or lang == lang2 or lang == lang3:
				subtitles_list.append( { 'title' : matches.group('title'), 'year' : matches.group('year'), "filename" : file_name, 'language_name' : lang_titulky2xbmclang(matches.group('lang')), 'ID' : matches.group('id'), "mediaType" : 'mediaType', "numberOfDiscs" : '2', "downloads" : matches.group('downloads'), "sync" : sync, "rating" :'0', "language_flag":flag_image } )
		return subtitles_list
	
	def get_waittime(self,content):
		for matches in re.finditer(countdown_pattern, content, re.IGNORECASE | re.DOTALL):
			return int(matches.group(1))

	def get_link(self,content):
		for matches in re.finditer(sublink_pattern, content, re.IGNORECASE | re.DOTALL):
			return str(matches.group(1))				

	def _get_session_id(self,content):
		for matches in re.finditer(session_id_pattern, content, re.IGNORECASE | re.DOTALL):
			return str(matches.group(1))	

	def get_control_image(self,content):
		for matches in re.finditer(control_image_pattern, content, re.IGNORECASE | re.DOTALL):
			return '/'+str(matches.group(1))
		return None

	def get_file(self,link):
		url = self.server_url+link
		log(__name__,'Downloading file %s' % (url))
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		content = response.read()
		log(__name__,'Done')
		response.close()
		return content

	def get_subtitle_page2(self,content,code,id):
		session_id = self._get_session_id(content)
		url = self.server_url+'/idown.php?'+urllib.urlencode({'PHPSESSID':session_id})
		post_data = {'downkod':code,'titulky':id,'zip':'z','securedown':'2','histstamp':''}
		req = urllib2.Request(url,urllib.urlencode(post_data))
		log(__name__,'Opening %s POST:%s' % (url,str(post_data)))
		response = urllib2.urlopen(req)
		content = response.read()
		log(__name__,'Done')
		response.close()
		return content
		
	def get_subtitle_page(self,id):
		timestamp = str(calendar.timegm(time.gmtime()))
		url = self.server_url+'/idown.php?'+urllib.urlencode({'R':timestamp,'titulky':id,'histstamp':'','zip':'z'})
		log(__name__,'Opening %s' % (url))
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		content = response.read()
		log(__name__,'Done')
		response.close()
		return content
		
