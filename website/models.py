from django.db import models
from image_cropping import ImageRatioField
from sortedm2m.fields import SortedManyToManyField
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save, m2m_changed, post_delete
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date, datetime, timedelta
from django.utils import timezone
from datetime import timedelta
import datetime
from website.utils.fileutils import UniquePathAndRename
import os
import glob
import re
from random import choice
from django.core.files import File
import shutil


#helper function to correctly capitalize a string, specify words to not capitalize in the articles list
def capitalize_title(s, exceptions):
    word_list = re.split(' ', s)       # re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)

#Standard list of words to not capitalize in a sentence
articles = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'is', 'of', 'on', 'or', 'nor', 'the', 'to', 'up', 'yet']

# Special character mappings
special_chars = {
    'ã': 'a', 'à': 'a', 'â': 'a',
    'é': 'e', 'è': 'e', 'ê': 'e',
    'ñ': 'n', 'ń': 'n',
    'ö': 'o', 'ô': 'o',
    'û': 'u', 'ü': 'u', 'ù': 'u'
}

# Simple check to seee if a file is an image. Not strictly necessary but included for safety
def isimage(filename):
    """true if the filename's extension is in the content-type lookup"""
    ext2conttype = {"jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif"}
    filename = filename.lower()
    return filename[filename.rfind(".") + 1:] in ext2conttype


# Randomly selects an image from the given directory
def get_random_starwars(direc):
    """Gets a random star wars picture to assign to new author"""
    images = [f for f in os.listdir(direc) if isimage(f)]
    return choice(images)


class Person(models.Model):
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    url_name = models.CharField(editable=False, max_length=50, default='placeholder')
    email = models.EmailField(blank=True, null=True)
    personal_website = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    next_position = models.CharField(max_length=255, blank=True, null=True)
    next_position.help_text = "This is a field to track the next position held by alumni of the lab. This field stores text information about their position and the next field stores a url for that position."
    next_position_url = models.URLField(blank=True, null=True)

    # Note: the ImageField requires the pillow library, which can be installed using pip
    # pip3 install Pillow
    # We use the get_unique_path function because otherwise if two people use the same
    # filename (something generic like picture.jpg), one will overwrite the other.
    image = models.ImageField(blank=True, upload_to="person", max_length=255)

    # image_cropped = models.ImageField(editable=False)
    image.help_text = 'You must select "Save and continue editing" at the bottom of the page after uploading a new image for cropping.'

    easter_egg = models.ImageField(blank=True, null=True, upload_to="person", max_length=255)

    # LS: Added image cropping to fixed ratio
    # See https://github.com/jonasundderwolf/django-image-cropping
    # size is "width x height"
    # TODO: update with desired aspect ratio and maximum resolution
    cropping = ImageRatioField('image', '245x245', size_warning=True)
    easter_egg_crop = ImageRatioField('easter_egg', '245x245', size_warning=True)

    # Return current title
    def get_current_title(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.title
        else:
            return None

    get_current_title.short_description = "Title"

    def get_current_title_index(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.get_title_index()
        else:
            return None

    # Return current title
    def get_current_department(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.department
        else:
            return None

    get_current_title.short_description = "Department"

    # Return current title
    def get_current_school(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.school
        else:
            return None

    get_current_school.short_description = "School"

    # Returns current role
    def get_current_role(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.role
        else:
            return None

    get_current_role.short_description = "Role"

    # Returns time in current position
    def get_time_in_current_position(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.get_time_in_this_position()
        else:
            return None

    get_time_in_current_position.short_description = "Time in Current Position"

    # Returns true if a professor
    def is_professor(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.is_professor()
        else:
            return False

    # Returns True if a grad student
    def is_grad_student(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.is_grad_student()
        else:
            return False

    # Returns True is person is current member of lab or current collaborator
    def is_active(self):
        # print(self.get_full_name() + " is active? " + str(self.is_current_member()) + " " + str(self.is_current_collaborator()))
        return self.is_current_member() or self.is_current_collaborator()

    is_active.short_description = "Is Active?"

    # Returns the total time as in the specified role across all positions
    def get_total_time_in_role(self, role):
        totalTimeInRole = timedelta(0)
        for position in self.position_set.all():
            if position.role == role:
                totalTimeInRole += position.get_time_in_this_position()
        return totalTimeInRole

    get_total_time_in_role.short_description = "Total Time In Role"

    # Returns the total time as a member across all positions
    def get_total_time_as_member(self):
        return self.get_total_time_in_role(Position.MEMBER)

    get_total_time_as_member.short_description = "Total Time As Member"

    # Returns True if person is current member of the lab. False otherwise
    def is_current_member(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.is_current_member()
        else:
            return False

    # Returns True if person is an alumni member of the lab. False otherwise
    def is_alumni_member(self):
        is_alumni_member = False
        for position in self.position_set.all():
            if position.is_member() is True:
                is_alumni_member = True

        latest_position = self.get_latest_position()
        if latest_position is not None:
            if latest_position.is_current_member():
                is_alumni_member = False

        return is_alumni_member

    # Returns True if person is current collaborator of the lab. False otherwise
    def is_current_collaborator(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            # print('Checkpoint 1: ' + str(latest_position.is_current_collaborator()))
            return latest_position.is_current_collaborator()
        else:
            return False

    def is_past_collaborator(self):
        """
        Gets whether a person is a past collaborator or not.
        :return: True if person is a past collaborator of the lab. False otherwise
        """
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.is_past_collaborator()
        else:
            return False

    def get_earliest_member_position(self):
        """
        Gets the earliest Position for this person
        :return: the earliest Position for this person
        """
        # The result of a QuerySet is a QuerySet so you can chain them together...
        return self.position_set.filter(role=Position.MEMBER).earliest('start_date')

    def get_latest_position(self):
        """
        Gets the latest Position for the person or None if none exists
        :return: latest Position for the person or None if none exists
        """
        if self.position_set.exists() is False:
            return None
        else:
            return self.position_set.latest('start_date')

    # Returns the start date of current position. Used in Admin Interface. See PersonAdmin in admin.py
    def get_start_date(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.start_date
        else:
            return None

    get_start_date.short_description = "Start Date"  # This short description is used in the admin interface

    # Returns the end date of current position. Used in Admin Interface. See PersonAdmin in admin.py
    def get_end_date(self):
        latest_position = self.get_latest_position()
        if latest_position is not None:
            return latest_position.end_date
        else:
            return None

    get_end_date.short_description = "End Date"  # This short description is used in the admin interface

    def get_full_name(self, include_middle=True):
        """
        Gets this person's full name as a string
        :param include_middle: If true, includes the middle name. Defaults to True.
        :return: the person's full name as a string
        """
        if self.middle_name and include_middle:
            return u"{0} {1} {2}".format(self.first_name, self.middle_name, self.last_name)
        else:
            return u"{0} {1}".format(self.first_name, self.last_name)

    get_full_name.short_description = "Full Name"

    def get_url_name(self):
        """
        Gets the URL name for this person. Format: firstlast
        :return: the URL name for this person. Format: firstlast
        """
        return self.url_name

    def get_projects(self):
        """
        Gets a set of all the projects this person is involved in ordered by most recent start date first
        :return: a set of all the projects this person is involved in ordered by most recent start date first
        """
        project_roles = self.project_role_set.order_by('-start_date')

        # For more on this style of list iteration (called list comprehension)
        # See: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
        #      https://www.python.org/dev/peps/pep-0202/
        projects = set([project_role.project for project_role in project_roles])
        return projects

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        dir = os.path.abspath('.')
        # requires the volume mount from docker
        image_choice = self.easter_egg
        if image_choice is None:
            dir = os.path.join('media', 'images', 'StarWarsFiguresFullSquare', 'Rebels')
            star_wars_dir = os.path.join(dir, get_random_starwars(dir))
            image_choice = File(open(star_wars_dir, 'rb'))
        # automatically set url_name field

        # Substitute any common special characters. I haven't found a better automatic way to do
        # this, so we are manually mapping 'common' special characters.
        url_name_cleaned = (self.first_name + self.last_name).lower()
        for c in url_name_cleaned:
            if bool(re.search('[^a-zA-Z]', c)) and c in special_chars:
                url_name_cleaned = url_name_cleaned.replace(c, special_chars.get(c))

        # Finally, clean remaining characters (EX: dashes, periods).
        url_name_cleaned = re.sub('[^a-zA-Z]', '', url_name_cleaned)
        self.url_name = url_name_cleaned

        if not self.image:
            self.image = image_choice
        if self.pk is None:
            self.easter_egg = image_choice
        super(Person, self).save(*args, **kwargs)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'People'


@receiver(pre_delete, sender=Person)
def person_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(False)


class Position(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    advisor = models.ForeignKey('Person', blank=True, null=True, related_name='Advisor', on_delete=models.SET_NULL)
    co_advisor = models.ForeignKey('Person', blank=True, null=True, related_name='Co_Advisor', verbose_name='Co-advisor', on_delete=models.SET_NULL)
    grad_mentor = models.ForeignKey('Person', blank=True, null=True, related_name='Grad_Mentor', on_delete=models.SET_NULL)


    # According to Django docs, best to have field choices within the primary
    # class that uses them. See https://docs.djangoproject.com/en/1.9/ref/models/fields/#choices
    MEMBER = "Member"
    COLLABORATOR = "Collaborator"

    ROLE_CHOICES = (
        (MEMBER, "Member"),
        (COLLABORATOR, "Collaborator"),
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=MEMBER)

    HIGH_SCHOOL = "High School Student"
    UGRAD = "Undergrad"
    MS_STUDENT = "MS Student"
    PHD_STUDENT = "PhD Student"
    POST_DOC = "Post doc"
    ASSISTANT_PROF = "Assistant Professor"
    ASSOCIATE_PROF = "Associate Professor"
    FULL_PROF = "Professor"
    RESEARCH_SCIENTIST = "Research Scientist"
    SOFTWARE_DEVELOPER = "Software Developer"
    UNKNOWN = "Uncategorized"

    TITLE_CHOICES = (
        (HIGH_SCHOOL, HIGH_SCHOOL),
        (UGRAD, UGRAD),
        (MS_STUDENT, MS_STUDENT),
        (PHD_STUDENT, PHD_STUDENT),
        (POST_DOC, POST_DOC),
        (ASSISTANT_PROF, ASSISTANT_PROF),
        (ASSOCIATE_PROF, ASSOCIATE_PROF),
        (FULL_PROF, FULL_PROF),
        (RESEARCH_SCIENTIST, RESEARCH_SCIENTIST),
        (SOFTWARE_DEVELOPER, SOFTWARE_DEVELOPER),
        (UNKNOWN, UNKNOWN)
    )
    title = models.CharField(max_length=50, choices=TITLE_CHOICES)

    TITLE_ORDER_MAPPING = {
        FULL_PROF: 0,
        ASSOCIATE_PROF: 1,
        ASSISTANT_PROF: 2,
        POST_DOC: 3,
        RESEARCH_SCIENTIST: 4,
        PHD_STUDENT: 5,
        MS_STUDENT: 6,
        SOFTWARE_DEVELOPER: 6,
        UGRAD: 7,
        HIGH_SCHOOL: 8,
        UNKNOWN: 9
    }

    CURRENT_MEMBER = "Current Member"
    PAST_MEMBER = "Past Member"
    CURRENT_COLLABORATOR = "Current Collaborator"
    PAST_COLLABORATOR = "Past Collaborator"

    department = models.CharField(max_length=50, blank=True, default="Computer Science")
    school = models.CharField(max_length=60, default="University of Washington")

    def get_start_date_short(self):
        if self.is_current_member():
            return self.person.get_earliest_member_position().start_date.strftime('%b %Y')
        else:
            return self.start_date.strftime('%b %Y')

    def get_end_date_short(self):
        return self.end_date.strftime('%b %Y') if self.end_date != None else "Present"

    # Returns an abbreviated version of the department field
    def get_department_abbreviated(self):
        department_keywords_normal = ["building science", "architecture", "bioengineering"]
        department_keywords_map = ["BuildSci", "Arch", "BIOE"]
        abbrv = ""
        if "computer science" in self.department.lower() and "engineering" in self.department.lower():
            abbrv += 'CSE,'
        elif "computer science" in self.department.lower():
            abbrv += 'CS,'
        elif 'computer engineering' in self.department.lower():
            abbrv += 'CprE,'

        if "information" in self.department.lower() or "ischool" in self.department.lower():
            abbrv += 'iSchool,'

        if "hcde" in self.department.lower() or "human centered design" in self.department.lower() and "engineering" in self.department.lower():
            abbrv += 'HCDE,'

        for keyword in department_keywords_normal:
            counter = 0
            if keyword in self.department.lower():
                abbrv += department_keywords_map[counter]
                counter += 1

        if abbrv.__len__() > 0:
            return abbrv[:abbrv.__len__() - 1]
        else:
            return "".join(e[0] for e in self.department.split(" "))

    def get_title_index(self):
        if self.title in self.TITLE_ORDER_MAPPING:
            return self.TITLE_ORDER_MAPPING[self.title]
        else:
            return self.TITLE_ORDER_MAPPING[self.UNKNOWN]

    # Returns a timedelta object of total time in this position
    def get_time_in_this_position(self):
        if self.end_date is not None and self.start_date is not None:
            return self.end_date - self.start_date
        elif self.end_date is None and self.start_date is not None:
            return date.today() - self.start_date
        else:
            return None

    # Returns the start and end dates as strings
    def get_date_range_as_str(self):
        if self.start_date is not None and self.end_date is None:
            return "{}-".format(self.start_date.year)
        elif self.start_date is not None and self.end_date is not None and self.start_date.year == self.end_date.year:
            return "{}".format(self.start_date.year)
        else:
            return "{}-{}".format(self.start_date.year, self.end_date.year)

    # Returns true if collaborator
    def is_collaborator(self):
        return self.role == Position.COLLABORATOR

    # Returns true if member
    def is_member(self):
        return self.role == Position.MEMBER

    # Returns true if professor
    def is_professor(self):
        return self.title == Position.FULL_PROF or self.title == Position.ASSOCIATE_PROF or self.title == Position.ASSISTANT_PROF

    # Returns true if grad student
    def is_grad_student(self):
        return self.title == Position.MS_STUDENT or self.title == Position.PHD_STUDENT

    # Returns true if high school student
    def is_high_school(self):
        return self.title == Position.HIGH_SCHOOL

    # Returns true if member is current based on end date
    def is_current_member(self):
        return self.is_member() and \
               self.start_date is not None and self.start_date <= date.today() and \
               (self.end_date is None or (self.end_date is not None and self.end_date >= date.today()))

    # Returns true if member is current based on end date
    def is_current_collaborator(self):
        return self.is_collaborator() and \
               (self.start_date is not None and self.start_date <= date.today() and \
                self.end_date is None or (self.end_date is not None and self.end_date >= date.today()))

    # Returns true if collaborator is a past collaborator (used to differentiate between future collaborators)
    def is_past_collaborator(self):
        return self.is_collaborator() and \
               self.start_date < date.today() and \
               self.end_date != None and self.end_date < date.today()

    # Returns true if member is an alumni member (used to differentiate between future members)
    def is_alumni_member(self):
        return self.is_member() and \
               self.start_date < date.today() and \
               self.end_date != None and self.end_date < date.today()

    # Automatically called by Django when saving data to validate the data
    def clean(self):
        if self.end_date is not None and self.start_date > self.end_date:
            raise ValidationError('The start date must be before the end date')

    def __str__(self):
        return "Name={}, Role={}, Title={}".format(self.person.get_full_name(), self.role, self.title)


class Keyword(models.Model):
    keyword = models.CharField(max_length=255)

    def __str__(self):
        return self.keyword


class Sponsor(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ImageField(upload_to='projects/sponsors/', blank=True, null=True, max_length=255)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


# TODO: Argh, need to change all multi-world class names to CapWords convention, see official docs: https://www.python.org/dev/peps/pep-0008/#id41
class Project_umbrella(models.Model):
    name = models.CharField(max_length=255)
    # Short name is used for urls, and should be name.lower().replace(" ", "")
    short_name = models.CharField(max_length=255)
    short_name.help_text = "This should be the same as your name but lower case with no spaces. It is used in the url of the project"
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Project Umbrella"


class Project(models.Model):
    name = models.CharField(max_length=255)

    # Short name is used for urls, and should be name.lower().replace(" ", "")
    short_name = models.CharField(max_length=255)
    short_name.help_text = "This should be the same as your name but lower case with no spaces. It is used in the url of the project"

    # Sponsors is currently a simple list of sponsors but could be updated to a many to many field if a sponsors model is desired.
    sponsors = models.ManyToManyField(Sponsor, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    project_umbrellas = models.ManyToManyField(Project_umbrella, blank=True, null=True)

    # header_visual = models.ForeignKey(Project_header, blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)

    # pis = models.ManyToOneField(Person, blank=True, null=True)
    # TODO: consider switching gallery_image var name to thumbnail
    gallery_image = models.ImageField(upload_to='projects/images', blank=True, null=True, max_length=255)
    gallery_image.help_text = "This is the image which will show up on the project gallery page. It is not displayed anywhere else. You must select 'Save and continue editing' at the bottom of the page after uploading a new image for cropping. Please note that since we are using a responsive design with fixed height banners, your selected image may appear differently on various screens."

    # Copied from person model
    # LS: Added image cropping to fixed ratio
    # See https://github.com/jonasundderwolf/django-image-cropping
    # size is "width x height"
    # TODO: update with desired aspect ratio and maximum resolution
    cropping = ImageRatioField('gallery_image', '500x400', size_warning=True)

    about = models.TextField(null=True, blank=True)

    updated = models.DateField(auto_now=True)

    def get_pi(self):
        return self.project_role_set.get(pi_member="PI").person

    def get_co_pis(self):
        copi_arr = self.project_role_set.filter(pi_member="Co-PI")
        ret = []
        for copi in copi_arr:
            ret.append(copi.person)
        return ret

    def get_most_recent_publication(self):
        if self.publication_set.exists():
            return self.publication_set.order_by('-date')[0].date
        else:
            return None

    def has_artifact(self):
        """
        Returns true if project has at least one artifact (pub, talk, or video)
        :return:
        """
        return self.get_most_recent_artifact() is not None

    def has_ended(self):
        """
        Returns true if the project has ended
        :return:
        """
        return self.end_date is not None and self.end_date < date.today()

    def get_most_recent_artifact_date(self):
        """
        Returns the most recent artifact date (if one exists); otherwise None
        :return: the most recent artifact date (if one exists); otherwise None
        """
        most_recent_artifact_tuple = self.get_most_recent_artifact()
        if most_recent_artifact_tuple is not None:
            return most_recent_artifact_tuple[0]
        else:
            return None

    get_most_recent_artifact_date.short_description = "Most Recent Artifact Date"

    def get_most_recent_artifact_type(self):
        """
        Returns either "Publication", "Talk", or "Video" or None
        :return: either "Publication", "Talk", or "Video" or None
        """
        most_recent_artifact_tuple = self.get_most_recent_artifact()
        if most_recent_artifact_tuple is not None:
            most_recent_artifact = most_recent_artifact_tuple[1]
            if type(most_recent_artifact) is Publication:
                return "Publication"
            elif type(most_recent_artifact) is Talk:
                return "Talk"
            elif type(most_recent_artifact) is Video:
                return "Video"
        else:
            return None

    get_most_recent_artifact_type.short_description = "Most Recent Artifact Type"

    def get_publication_count(self):
        """
        Returns the number of publications associated with this project
        :return: the number of publications associated with this project
        """
        return self.publication_set.count()

    get_publication_count.short_description = "Pubs"

    def get_video_count(self):
        """
        Returns the number of videos associated with this project
        :return: the number of videos associated with this project
        """
        return self.video_set.count()

    get_video_count.short_description = "Videos"

    def get_talk_count(self):
        """
        Returns the number of talks associated with this project
        :return: the number of talks associated with this project
        """
        return self.talk_set.count()

    get_talk_count.short_description = "Talks"

    def get_people_count(self):
        """
        Returns the number of people involved in the project
        :return:
        """
        project_roles = self.project_role_set.order_by('-start_date')

        # For more on this style of list iteration (called list comprehension)
        # See: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
        #      https://www.python.org/dev/peps/pep-0202/
        people = set([project_role.person for project_role in project_roles])
        return len(people)

    get_people_count.short_description = "People"

    def get_current_member_count(self):
        """
        Returns the number of current members
        :return:
        """
        project_roles = self.project_role_set.order_by('-start_date')
        current_member_cnt = 0
        for project_role in project_roles:
            if project_role.is_active():
                current_member_cnt = current_member_cnt + 1
        return current_member_cnt

    get_current_member_count.short_description = "Current Members"

    def get_past_member_count(self):
        """
        Returns the number of current members
        :return:
        """

        # TODO: could likely turn all of this code into a single query?
        project_roles = self.project_role_set.order_by('-start_date')
        past_member_cnt = 0
        for project_role in project_roles:
            if project_role.is_active():
                past_member_cnt = past_member_cnt + 1
        return past_member_cnt

    get_past_member_count.short_description = "Past Members"

    def get_most_recent_artifact(self):
        """
        Returns the most recent artifact (publication, talk, or video) as tuple of (date, artifact)
        :return: the most recent artifact, a tuple of (date, artifact)
        """
        mostRecentArtifacts = []

        if self.publication_set.exists():
            mostRecentPub = self.publication_set.order_by('-date')[0]
            mostRecentArtifacts.append((mostRecentPub.date, mostRecentPub))

        if self.talk_set.exists():
            mostRecentTalk = self.talk_set.order_by('-date')[0]
            mostRecentArtifacts.append((mostRecentTalk.date, mostRecentTalk))

        if self.video_set.exists():
            mostRecentVideo = self.video_set.order_by('-date')[0]
            mostRecentArtifacts.append((mostRecentVideo.date, mostRecentVideo))

        if len(mostRecentArtifacts) > 0:
            mostRecentArtifacts = sorted(mostRecentArtifacts, key=lambda artifact: artifact[0], reverse=True)
            return mostRecentArtifacts[0][0], mostRecentArtifacts[0][1]
        else:
            return None

    get_most_recent_artifact.short_description = "Most Recent Artifact"


    def __str__(self):
        return self.name


class Project_Role(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    PI = "PI"
    CoPI = "Co-PI"

    PIMEMBER_CHOICES = (
        (PI, "PI"),
        (CoPI, "Co-PI")
    )

    PI_MEMBER_MAPPING = {
        PI: 0,
        CoPI: 1,
        "Other": 2
    }

    pi_member = models.CharField(max_length=50, blank=True, null=True, choices=PIMEMBER_CHOICES, default=None)

    def get_start_date_short(self):
        return self.start_date.strftime('%b %Y')

    def get_end_date_short(self):
        return self.end_date.strftime('%b %Y') if self.end_date != None else "Present"

    def get_date_range_as_str(self):
        if self.start_date is not None and self.end_date is None:
            return "{}-".format(self.start_date.year)
        elif self.start_date is not None and self.end_date is not None and self.start_date.year == self.end_date.year:
            return "{}".format(self.start_date.year)
        else:
            return "{}-{}".format(self.start_date.year, self.end_date.year)

    def get_pi_status_index(self):
        if self.pi_member is not None and self.pi_member in self.PI_MEMBER_MAPPING:
            return self.PI_MEMBER_MAPPING[self.pi_member]
        else:
            return self.PI_MEMBER_MAPPING["Other"]

    def is_active(self):
        return self.start_date is not None and self.start_date <= date.today() and \
               (self.end_date is None or self.end_date >= date.today())

    # This function is used to differentiate between past and future roles
    def is_past(self):
        return self.start_date is not None and self.start_date < date.today() and \
               (self.end_date is not None and self.end_date < date.today())

    def __str__(self):
        return "Name={}, PI/Co-PI={}".format(self.person.get_full_name(), self.pi_member)


# This class contains the image or video which will appear in the top description of each project. It functions as a combination of Photo and Video, but is separated to make it simpler to have a specific video or photo as the projects header.
class Project_header(models.Model):
    title = models.CharField(max_length=255)
    title.help_text = "These fields are used as the image in the about section. To add a banner to your page go to the banners table and assign banners to your project using the project field there. This field will accept both a video and an image. If both are provided the video will be used."
    caption = models.CharField(max_length=255, blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='projects/images/', blank=True, null=True, max_length=255)
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.CASCADE)

    def get_visual(self):
        if self.video_url:
            url = self.get_embed()
            return '<iframe class=\"video-about\" src=\"' + url + '\" frameborder="0" allowfullscreen></iframe>'
        elif self.image:
            return "<img class=\"video-about\" src=\"" + self.image.url + "\">"

    def get_embed(self):
        base_url = "https://youtube.com/embed"
        unique_url = self.video_url[self.video_url.find("/", 9):]
        return base_url + unique_url

    class Meta:
        verbose_name = "Project About Visual"


class Photo(models.Model):
    picture = models.ImageField(upload_to='projects/images/', max_length=255)
    caption = models.CharField(max_length=255, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.SET_NULL)
    picture.help_text = 'You must select "Save and continue editing" at the bottom of the page after uploading a new image for cropping. Please note that since we are using a responsive design with fixed height banners, your selected image may appear differently on various screens.'

    # Copied from person model
    # LS: Added image cropping to fixed ratio
    # See https://github.com/jonasundderwolf/django-image-cropping
    # size is "width x height"
    # TODO: update with desired aspect ratio and maximum resolution
    cropping = ImageRatioField('picture', '368x245', size_warning=True)

    def admin_thumbnail(self):
        return u'<img src="%s" height="100"/>' % (self.picture.url)

    admin_thumbnail.short_description = 'Thumbnail'
    admin_thumbnail.allow_tags = True

    def __str__(self):
        return self.caption


class Video(models.Model):
    video_url = models.URLField(blank=True, null=True)
    video_preview_url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=255)
    caption = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(null=True)
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.SET_NULL)

    def get_embed(self):
        # TODO this assumes that all videos are YouTube. This is not the case.
        base_url = "https://youtube.com/embed"
        unique_url = self.video_url[self.video_url.find("/", 9):]

        # See https://developers.google.com/youtube/youtube_player_demo for details on parameterizing YouTube video
        return base_url + unique_url + "?showinfo=0&iv_load_policy=3"

    # Returns a cap case title
    def get_title(self):
        words = self.title.split()
        cap_title = ""
        first = True
        for word in words:
            if not first:
                cap_title += " "
            cap_title += word[0].upper() + word[1:].lower()
            first = False
        return cap_title

    def __str__(self):
        return self.title
# These two auto-delete files from filesystem when they are unneeded:


def repl_func(m):
    """process regular expression match groups for word upper-casing problem"""
    return m.group(1) + m.group(2).upper()


class Talk(models.Model):
    title = models.CharField(max_length=255)

    # A talk can be about more than one project
    projects = models.ManyToManyField(Project, blank=True, null=True)
    project_umbrellas = SortedManyToManyField(Project_umbrella, blank=True, null=True)

    # TODO: remove the null = True from all of the following objects
    # including forum_name, forum_url, location, speakers, date, slideshare_url
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    forum_name = models.CharField(max_length=255, null=True)
    forum_url = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, null=True)

    # Most of the time talks are given by one person, but sometimes they are given by two people
    speakers = models.ManyToManyField(Person, null=True)

    date = models.DateField(null=True)
    slideshare_url = models.URLField(blank=True, null=True)

    # The PDF and raw files (e.g., keynote, pptx) are required
    # TODO: remove null=True from these two fields
    pdf_file = models.FileField(upload_to='talks/', null=True, default=None, max_length=255)
    raw_file = models.FileField(upload_to='talks/', blank=True, null=True, default=None, max_length=255)

#test field to verify adding new fields to models
    INVITED_TALK = "Invited Talk"
    CONFERENCE_TALK = "Conference Talk"
    MS_DEFENSE = "MS Defense"
    PHD_DEFENSE = "PhD Defense"
    GUEST_LECTURE = "Guest Lecture"
    QUALS_TALK = "Quals Talk"

    TALK_TYPE_CHOICES = (
        (INVITED_TALK, INVITED_TALK),
        (CONFERENCE_TALK, CONFERENCE_TALK),
        (MS_DEFENSE, MS_DEFENSE),
        (PHD_DEFENSE, PHD_DEFENSE),
        (GUEST_LECTURE, GUEST_LECTURE),
        (QUALS_TALK, QUALS_TALK),
    )

    talk_type = models.CharField(max_length=50, choices=TALK_TYPE_CHOICES, null=True)

    # The thumbnail should have null=True because it is added automatically later by a post_save signal
    # TODO: decide if we should have this be editable=True and if user doesn't add one him/herself, then
    # auto-generate thumbnail
    thumbnail = models.ImageField(upload_to='talks/images/', editable=False, null=True, max_length=255)

    # raw_file = models.FileField(upload_to='talks/')
    # print("In talk model!")
    def get_person(self):
        return self.speakers.all()[0]

    def get_title(self):
        # Comes from here http://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
        #cap_title = ' '.join(s[0].upper() + s[1:] for s in self.title.split(' '))
        cap_title = capitalize_title(self.title, articles)
        return cap_title

    # Gets the list of speakers as a csv string
    def get_speakers_as_csv(self):
        # iterate through all of the speakers and return the csv
        is_first_speaker = True
        list_of_speakers_as_csv = ""
        for speaker in self.speakers.all():
            if is_first_speaker != True:
                # if not the first speaker, add in a comma in CSV string
                list_of_speakers_as_csv += ", "
            list_of_speakers_as_csv += speaker.get_full_name()
            is_first_speaker = False
        return list_of_speakers_as_csv

    get_speakers_as_csv.short_description = 'Speaker List'

    def __str__(self):
        return self.title

#@receiver(post_save, sender=Talk)
def update_file_name_talks(sender, instance, action, reverse, **kwargs):
    #Reverse: Indicates which side of the relation is updated (i.e., if it is the forward or reverse relation that is being modified)
    #Action: A string indicating the type of update that is done on the relation.
    #post_add: Sent after one or more objects are added to the relation

    # from: https://docs.djangoproject.com/en/2.1/ref/signals/
    if action == 'post_add' and not reverse:
        initial_path = instance.pdf_file.path
        person = instance.get_person()
        name = person.last_name
        year = instance.date.year
        title = ''.join(x for x in instance.title.title() if not x.isspace())
        title = ''.join(e for e in title if e.isalnum())

        #change the pdf_file path to point to the renamed file
        instance.pdf_file.name = os.path.join('talks', name + '_' + title + '_' + str(year) + '.pdf')
        new_path = os.path.join(settings.MEDIA_ROOT, instance.pdf_file.name)
        os.rename(initial_path, new_path)
        instance.save()

m2m_changed.connect(update_file_name_talks, sender=Talk.speakers.through)

@receiver(post_delete, sender=Talk)
def talk_delete(sender, instance, **kwargs):
    if instance.pdf_file:
        instance.pdf_file.delete(True)
    if instance.raw_file:
        instance.raw_file.delete(True)
    if instance.thumbnail:
        instance.thumbnail.delete(True)


class Publication(models.Model):
    title = models.CharField(max_length=255)
    authors = SortedManyToManyField(Person)
    # authorsOrdered = models.ManyToManyField(Person, through='PublicationAuthorThroughModel')

    # The PDF is required
    pdf_file = models.FileField(upload_to='publications', null=False, default=None, max_length=255)

    book_title = models.CharField(max_length=255, null=True)
    book_title.help_text = "This is the long-form proceedings title. For example, for UIST, this would be 'Proceedings of the 27th Annual ACM Symposium on User " \
                           "Interface Software and Technology.' For CHI, 'Proceedings of the 2017 CHI Conference on " \
                           "Human Factors in Computing Systems' "
    book_title_short = models.CharField(max_length=255, null=True)
    book_title_short.help_text = "This is a shorter version of book title. For UIST, 'Proceedings of UIST 2014' " \
                           "For CHI, 'Proceedings of CHI 2017'"

    # The thumbnail should have null=True because it is added automatically later by a post_save signal
    # TODO: decide if we should have this be editable=True and if user doesn't add one him/herself, then
    # auto-generate thumbnail
    thumbnail = models.ImageField(upload_to='publications/images/', editable=False, null=True, max_length=255)

    date = models.DateField(null=True)
    num_pages = models.IntegerField(null=True)

    # A publication can be about more than one project
    projects = SortedManyToManyField(Project, blank=True, null=True)
    project_umbrellas = SortedManyToManyField(Project_umbrella, blank=True, null=True)
    keywords = SortedManyToManyField(Keyword, blank=True, null=True)

    # TODO, see if there is an IntegerRangeField or something like that for page_num_start and end
    page_num_start = models.IntegerField(blank=True, null=True)
    page_num_end = models.IntegerField(blank=True, null=True)
    official_url = models.URLField(blank=True, null=True)
    geo_location = models.CharField(max_length=255, blank=True, null=True)
    geo_location.help_text = "The physical location of the conference, if any. For example, CHI 2017 is 'Denver, Colorado'"

    video = models.OneToOneField(Video, on_delete=models.DO_NOTHING, null=True, blank=True)
    talk = models.ForeignKey(Talk, blank=True, null=True, on_delete=models.DO_NOTHING)

    series = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=255, blank=True, null=True)
    doi = models.CharField(max_length=255, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    publisher_address = models.CharField(max_length=255, blank=True, null=True)
    acmid = models.CharField(max_length=255, blank=True, null=True)

    CONFERENCE = "Conference"
    ARTICLE = "Article"
    JOURNAL = "Journal"
    BOOK_CHAPTER = "Book Chapter"
    BOOK = "Book"
    DOCTORAL_CONSORTIUM = "Doctoral Consortium"
    MS_THESIS = "MS Thesis"
    PHD_DISSERTATION = "PhD Dissertation"
    WORKSHOP = "Workshop"
    POSTER = "Poster"
    DEMO = "Demo"
    WIP = "Work in Progress"
    LATE_BREAKING = "Late Breaking Result"
    PANEL = "Panel"
    OTHER = "Other"

    PUB_VENUE_TYPE_CHOICES = (
        (CONFERENCE, CONFERENCE),
        (ARTICLE, ARTICLE),
        (JOURNAL, JOURNAL),
        (BOOK_CHAPTER, BOOK_CHAPTER),
        (BOOK, BOOK),
        (DOCTORAL_CONSORTIUM, DOCTORAL_CONSORTIUM),
        (MS_THESIS, MS_THESIS),
        (PHD_DISSERTATION, PHD_DISSERTATION),
        (WORKSHOP, WORKSHOP),
        (POSTER, POSTER),
        (DEMO, DEMO),
        (WIP, WIP),
        (LATE_BREAKING, LATE_BREAKING),
        (PANEL, PANEL),
        (OTHER, OTHER)
    )

    # TODO: remove null=True from the following three
    pub_venue_url = models.URLField(blank=True, null=True)
    pub_venue_type = models.CharField(max_length=50, choices=PUB_VENUE_TYPE_CHOICES, null=True)
    extended_abstract = models.NullBooleanField(null=True)
    peer_reviewed = models.NullBooleanField(null=True)

    total_papers_submitted = models.IntegerField(blank=True, null=True)
    total_papers_accepted = models.IntegerField(blank=True, null=True)

    BEST_PAPER_AWARD = "Best Paper Award"
    HONORABLE_MENTION = "Honorable Mention"
    BEST_PAPER_NOMINATION = "Best Paper Nominee"
    TEN_YEAR_IMPACT_AWARD = "10-Year Impact Award"

    AWARD_CHOICES = (
        (BEST_PAPER_AWARD, BEST_PAPER_AWARD),
        (HONORABLE_MENTION, HONORABLE_MENTION),
        (BEST_PAPER_NOMINATION, BEST_PAPER_NOMINATION),
        (TEN_YEAR_IMPACT_AWARD, TEN_YEAR_IMPACT_AWARD)
    )
    award = models.CharField(max_length=50, choices=AWARD_CHOICES, blank=True, null=True)
    test = models.CharField(max_length=50, blank=True, null=True)

    def get_person(self):
        """
        Returns the first author
        :return:
        """
        return self.authors.all()[0]

    def is_extended_abstract(self):
        """
        Returns True if this publication is an extended abstract
        :return: True if this publication is an extended abstract
        """
        return (self.extended_abstract or
                self.pub_venue_type == self.POSTER or
                self.pub_venue_type == self.DEMO or
                self.pub_venue_type == self.WIP or
                self.pub_venue_type == self.DOCTORAL_CONSORTIUM)


    # Returns the title of the publication in capital case
    def get_title(self):
        # Comes from here http://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
        # TODO looks like we have similar code in class Talk--should make a common utility method for both to reduce code redundancy
        cap_title = capitalize_title(self.title, articles)
        return cap_title

    # Returns the acceptance rate as a percentage
    def get_acceptance_rate(self):
        if self.total_papers_accepted and self.total_papers_submitted:
            return 100 * (self.total_papers_accepted / self.total_papers_submitted)
        else:
            return -1

    # Returns true if the publication date happens in the future (e.g., tomorrow or later)
    def to_appear(self):
        return self.date and self.date > date.today()

    def __str__(self):
        return self.title


def update_file_name_publication(sender, instance, action, reverse, **kwargs):
    # Reverse: Indicates which side of the relation is updated (i.e., if it is the forward or reverse relation that is being modified)
    # Action: A string indicating the type of update that is done on the relation.
    # post_add: Sent after one or more objects are added to the relation
    if action == 'post_add' and not reverse:
        initial_path = instance.pdf_file.path
        person = instance.get_person()
        name = person.last_name
        year = instance.date.year
        title = ''.join(x for x in instance.title.title() if not x.isspace())
        title = ''.join(e for e in title if e.isalnum())


        #change the path of the pdf file to point to the new file name
        instance.pdf_file.name = os.path.join('publications', name + '_' + title + '_' + str(year) + '.pdf')
        new_path = os.path.join(settings.MEDIA_ROOT, instance.pdf_file.name)
        os.rename(initial_path, new_path)
        instance.save()

m2m_changed.connect(update_file_name_publication , sender=Publication.authors.through)

@receiver(pre_delete, sender=Publication)
def publication_delete(sender, instance, **kwards):
    if instance.thumbnail:
        instance.thumbnail.delete(True)
    if instance.pdf_file:
        instance.pdf_file.delete(True)
    if instance.thumbnail:
        instance.thumbnail.delete(True)


class Poster(models.Model):
    publication = models.ForeignKey(Publication, blank=True, null=True, on_delete=models.DO_NOTHING)

    # If publication is set, then these fields will be drawn from Publication
    # and ignored here.
    title = models.CharField(max_length=255, blank=True, null=True)
    authors = models.ManyToManyField(Person, blank=True, null=True)

    # The PDF and raw files (e.g., illustrator, powerpoint)
    pdf_file = models.FileField(upload_to='posters/', null=True, default=None, max_length=255)
    raw_file = models.FileField(upload_to='posters/', null=True, default=None, max_length=255)

    # The thumbnail should have null=True because it is added automatically later by a post_save signal
    # TODO: decide if we should have this be editable=True and if user doesn't add one him/herself, then
    # auto-generate thumbnail
    thumbnail = models.ImageField(upload_to='posters/images/', editable=False, null=True, max_length=255)

    def __str__(self):
        if self.publication:
            return self.publication.title
        else:
            return self.title


@receiver(pre_delete, sender=Poster)
def poster_delete(sender, instance, **kwargs):
    if instance.pdf_file:
        instance.pdf_file.delete(False)
    if instance.raw_file:
        instance.raw_file.delete(False)


class News(models.Model):
    title = models.CharField(max_length=255)
    #date = models.DateTimeField(default=timezone.now)
    date = models.DateField(default=date.today)  # check this line, might be diff
    author = models.ForeignKey(Person, null=True, on_delete=models.SET_NULL)
    content = models.TextField(blank=True)
    # Following the scheme of above thumbnails in other models
    image = models.ImageField(blank=True, upload_to=UniquePathAndRename("news", True), max_length=255)
    image.help_text = 'You must select "Save and continue editing" at the bottom of the page after uploading a new image for cropping. Please note that since we are using a responsive design with fixed height banners, your selected image may appear differently on various screens.'

    # Copied from person model
    # LS: Added image cropping to fixed ratio
    # See https://github.com/jonasundderwolf/django-image-cropping
    # size is "width x height"
    # TODO: update with desired aspect ratio and maximum resolution
    cropping = ImageRatioField('image', '245x245', size_warning=True)

    # Optional caption and alt_text for the imate
    caption = models.CharField(max_length=1024, blank=True, null=True)
    alt_text = models.CharField(max_length=1024, blank=True, null=True)

    project = models.ManyToManyField(Project, blank=True, null=True)

    # def time_now(self):
    #    d = self.date.date() - datetime.timedelta(seconds=0)
    #    if d > timezone.now() - datetime.timedelta(hours=24):
    #        return str(int(timezone.now().hour) - int(self.date.hour)) + ' hours ago'
    #    else:
    #        return self.short_date()

    def short_date(self):
        month = self.date.strftime('%b')
        day = self.date.strftime('%d')
        year = self.date.strftime('%Y')
        return month + " " + day + ", " + year

    def __str__(self):
        return self.title

    class Meta:
        # These names are used in the admin display, see https://docs.djangoproject.com/en/1.9/ref/models/options/#verbose-name
        ordering = ['-date', 'title']
        verbose_name = 'News Item'
        verbose_name_plural = 'News'


@receiver(pre_delete, sender=News)
def news_delete(sender, instance, **kwards):
    if instance.image:
        instance.image.delete(False)


class Banner(models.Model):
    FRONTPAGE = "FRONTPAGE"
    PEOPLE = "PEOPLE"
    PUBLICATIONS = "PUBLICATIONS"
    TALKS = "TALKS"
    PROJECTS = "PROJECTS"
    INDPROJECT = "INDPROJECT"
    NEWSLISTING = "NEWSLISTING"
    VIDEOS = "VIDEOS"
    PAGE_CHOICES = (
        (FRONTPAGE, "Front Page"),
        (NEWSLISTING, "News Listings"),
        (PEOPLE, "People"),
        (PUBLICATIONS, "Publications"),
        (TALKS, "Talks"),
        (PROJECTS, "Projects"),
        (INDPROJECT, "Ind_Project"),
        (VIDEOS, "Videos")
    )    
    page = models.CharField(max_length=50, choices=PAGE_CHOICES, default=FRONTPAGE)
    image = models.ImageField(blank=True, upload_to=UniquePathAndRename("banner", True), max_length=255)
    # This field is only needed if the banner has been assigned to a specific project. The field is used by project_ind to select project specific banners so we don't have to add each project to the PAGE_CHOICES dictionary.
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.CASCADE)
    project.help_text = "If this banner is for a specific project, set the page to Ind_Project. You must also set this field to the desired project for your banner to be displayed on that projects page."
    # def image_preview(self):
    #     if self.image:
    #         return u'<img src="%s" style="width:100%%"/>' % self.image.url
    #     else:
    #         return '(Please upload an image)'
    # image_preview.short_description = 'Image Preview'
    # image_preview.allow_tags = True
    cropping = ImageRatioField('image', '2000x500', free_crop=True)
    image.help_text = 'You must select "Save and continue editing" at the bottom of the page after uploading a new image for cropping. Please note that since we are using a responsive design with fixed height banners, your selected image may appear differently on various screens.'
    title = models.CharField(max_length=50, blank=True, null=True)
    caption = models.CharField(max_length=1024, blank=True, null=True)
    alt_text = models.CharField(max_length=1024, blank=True, null=True)
    link = models.CharField(max_length=1024, blank=True, null=True)
    favorite = models.BooleanField(default=False)
    favorite.help_text = 'Check this box if this image should appear before other (non-favorite) banner images on the same page.'
    date_added = models.DateField(auto_now=True)

    def admin_thumbnail(self):
        if self.image:
            return u'<img src="%s" height="100"/>' % (self.image.url)
        else:
            return "No image found"

    admin_thumbnail.short_description = 'Thumbnail'
    admin_thumbnail.allow_tags = True

    def __str__(self):
        if self.title and self.page:
            return self.title + ' (' + self.get_page_display() + ')'
        else:
            return "Banner object for " + self.get_page_display()


@receiver(pre_delete, sender=Banner)
def banner_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(False)
