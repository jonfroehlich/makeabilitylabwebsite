from django.core.management.base import BaseCommand, CommandError
from website.models import Person, Keyword, Talk, Project, Project_umbrella, Project_Role
import xmltodict as xd
from django.core.files import File
import requests
from django.utils import timezone
from datetime import date, datetime
import os
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from website.serializers import TalkSerializer
import shutil

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = 'https://makeabilitylab.cs.washington.edu/api/talks/?format=json'
        response = requests.get(url).content
        stream = BytesIO(response)
        data = JSONParser().parse(stream)

        temp_dir = os.path.abspath('.')
        temp_dir = os.path.join(temp_dir, 'media', 'temp')

        # Make a set of temp folders to store media files for import
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        temp_dir_image = os.path.abspath('.')
        temp_dir_image = os.path.join('media', 'person')
        if not os.path.exists(temp_dir_image):
            os.makedirs(temp_dir_image)
        temp_dir_thumbnails = os.path.join(temp_dir, 'thumbnails')
        if not os.path.exists(temp_dir_thumbnails):
            os.makedirs(temp_dir_thumbnails)

        #raw file, pdf_file
        print('preprocessing data...')
        for item in data:
            #get the url and open up a request stream
            print('Now processing ' + item['title'])
            url = item['pdf_file']
            if url is not None:
                title = url.split('/')[-1]
                print(title)
                r = requests.get(url, stream=True)
                file_path = os.path.join(temp_dir, title)
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                # open the pdf file and pass it in to the JSON
                item['pdf_file'] = File(open(os.path.join('.', 'media', 'temp', title), 'rb'))
            url = item['thumbnail']
            if url is not None:
                r_tb = requests.get(url, stream=True)
                title_tb = url.split('/')[-1]
                file_path_tb = os.path.join(temp_dir_thumbnails, title_tb)
                with open(file_path_tb, 'wb') as f:
                    f.write(r_tb.content)

            url = item['raw_file']
            if url is not None:
                title = url.split('/')[-1]
                print(title)
                r = requests.get(url, stream=True)
                file_path = os.path.join(temp_dir, title)
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                # open the pdf file and pass it in to the JSON
                item['raw_file'] = File(open(os.path.join('.', 'media', 'temp', title), 'rb'))

            for object in item['speakers']:
                #get the url and open up a request stream
                image_url = object['image']
                easter_egg_url = object['easter_egg']
                r_image = requests.get(image_url, stream=True)
                r_ee = requests.get(easter_egg_url, stream=True)

                #obtain the names of the original images from the end of each url
                image_file_name = image_url.split('/')[-1]
                ee_file_name = easter_egg_url.split('/')[-1]

                #generate the file path to write the images to
                image_file_path = os.path.join(temp_dir_image, image_file_name)
                ee_file_path = os.path.join(temp_dir_image, ee_file_name)

                #writing the online content in a stream to a local file
                with open(image_file_path, 'wb') as f:
                    f.write(r_image.content)
                with open(ee_file_path, 'wb') as f:
                    f.write(r_ee.content)
                object['image'] = File(open(image_file_path, 'rb'))
                object['easter_egg'] = File(open(ee_file_path, 'rb'))
            # initialize the serializer with many set to True to deserialize multiple objects
            serializer = TalkSerializer(data=item)
            print('saving data...')
            # must call is_valid on the serializer to verify that the data the serializer has is valid for deserialization
            # This is why the previous conversion from URLs to actual Files was necessary
            serializer.is_valid()
            # save method will be called for every object created by the data in the serializer
            serializer.save()
        # delete temp
        shutil.rmtree(temp_dir, ignore_errors=True)
