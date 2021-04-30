#!/usr/bin/env python3

# Converts the JSON export of Journey.Cloud diary entries into an Evernote Note Export format (ENEX) for easy import into Joplin.
# Create/update date, journal text, location, photos and tags are preserved in the resulting Evernote Note.
# Based on https://gist.github.com/mbafford/2c18f5c4d7b0dab673fddb1af2126680

import sys
import os
import json
import base64
import hashlib
import codecs
from datetime import datetime
from xml.sax.saxutils import escape

def md5sum( file ):
    m = hashlib.md5()
    m.update( file )
    return m.hexdigest()

def load_photos( journal_id, files ):
    ret = {}

    for file in files:
        try:
            with open(file, "rb") as f:
                ret[ file ] = f.read()
        except:
            print("Journal %s - Unable to find photo file %s" % ( journal_id, file ) )
            sys.exit(1)

    return ret

def get_note_xml( journal ):
    created = datetime.fromtimestamp( journal['date_journal']/1000 )
    updated = datetime.fromtimestamp( journal['date_modified']/1000 ) 

    print("%s: Converting journal from %s (modified %s)" % ( journal['id'], created.strftime("%Y-%m-%d %H:%M:%S"), updated.strftime("%Y-%m-%d %H:%M:%S") ) )

    photos = load_photos( journal['id'], journal['photos'] )
    print("%s: Loaded: %d photos" % ( journal['id'], len(photos) ) )

    resources_xml = ""
    images = ""

    for photo in photos:
        mime = ""
        if photo.lower().endswith( "jpg" ):       mime = "image/jpeg"
        elif photo.lower().endswith( "sticker" ): mime = "image/gif"
        elif photo.lower().endswith( "png" ):     mime = "image/png"
        else: 
            print("Unable to determine MIME mime from filename: %s" % photo) 
            sys.exit(1)

        resources_xml += """
            <resource><data encoding="base64">
                %(base64)s
                </data><mime>%(mime)s</mime>
                <resource-attributes>
                    <source-url>file://%(filename)s</source-url>
                    <file-name>%(filename)s</file-name>
                </resource-attributes>
            </resource>
        """ % {
            "base64": base64.b64encode(photos[photo]).decode(),
            "filename": photo,
            "mime": mime,
        }

        images += """ <div><en-media hash="%(hash)s" type="%(mime)s"/></div> """ % { "hash": md5sum( photos[photo] ), "mime": mime }

    tags = ""
    for tag in journal['tags']:
        tags += """<tag>%(tag)s</tag>""" % { "tag": tag }


    return """
<note>
    <title>%(title)s</title>
    <content>
        <![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
        <en-note>
            <div>
                %(text)s
            </div>
            %(images)s
        </en-note>
        ]]>
    </content>
    <created>%(created)s</created>
    <updated>%(updated)s</updated>
    %(tags)s
    <note-attributes>
      <latitude>%(latitude)s</latitude>
      <longitude>%(longitude)s</longitude>
    </note-attributes>
    %(resources)s
</note>""" % {
        "title": created.strftime("%Y-%m-%d %H:%M"),
        "text":  escape( journal['text'] ).replace("\n", "<br/>"),
        "created": created.strftime("%Y%m%dT%H%M%SZ"),
        "updated": updated.strftime("%Y%m%dT%H%M%SZ"),
        "latitude": journal.get('lat', ""),
        "longitude": journal.get('lon', ""),
        "resources": resources_xml,
        "images": images,
        "tags": tags,
    }
    

def find_and_convert():
    xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="%(export_date)s" application="Evernote/Windows" version="6.x">
""" % {
        "export_date": datetime.now().strftime("%Y%m%dT%H%M%SZ")
    }
  

    for fn in [fn for fn in os.listdir(".") if fn.endswith(".json")]:
        with open(fn, "r") as f:
            journal = json.loads( f.read() )

            xml += get_note_xml( journal )

    xml += "</en-export>"""

    out_file = "journey.enex"
    with codecs.getwriter("utf8")(open( out_file, "w" )) as f: 
        f.write( xml )
    
    print("Wrote %s" % ( out_file ))

find_and_convert()