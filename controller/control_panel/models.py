# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from edx.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from controller.settings import TIME_ZONE
from libhh.mailchimp import unschedule_campaign, schedule_campaign, delete_campaign, MERGE_FIELD_DICT
from controller.settings import MAILCHIMP_DEVKEY, MAILCHIMP_URL

DAYS_OF_WEEK = (
    (0, 'MONDAY'),
    (1, 'TUESDAY'),
    (2, 'WEDNESDAY'),
    (3, 'THURSDAY'),
    (4, 'FRIDAY'),
    (5, 'SATURDAY'),
    (6, 'SUNDAY')
)

class Course(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    is_active = models.BooleanField(default=False)
    num_section = models.IntegerField(null=False, default=1)
    language = models.CharField(max_length=16, null=False, default='es', help_text="Only {0} are allowed".
                                format(', '.join(MERGE_FIELD_DICT['FNAME'].keys())))
    name = models.CharField(max_length=256, null=False)
    mailchimp_list_id = models.CharField(max_length=32, blank=True, db_column='mailchimp_list_id', null=True)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)

    def __unicode__(self):
        return self.name


class Template(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=128, null=False)

    def __unicode__(self):
        return self.name


class QualificationIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    min_percent_grade = models.FloatField(null=False, default=0)
    max_percent_grade = models.FloatField(null=False, default=1.0)
    letter_grade = models.CharField(max_length=255, null=True, blank=True)
    min_passed_timestamp = models.DateTimeField(null=True, blank=True)
    max_passed_timestamp = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Qualification Indeces"


class CertificationIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    min_percent_grade = models.FloatField(null=False, default=0)
    max_percent_grade = models.FloatField(null=False, default=1.0)
    status = models.CharField(max_length=256, null=True, verbose_name="Status")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Certification Indeces"


class ProgressIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    min_earned = models.FloatField(default=0)
    max_earned = models.FloatField(default=1)
    min_graded = models.FloatField(default=0)
    max_graded = models.FloatField(default=1)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Progress Indeces"


class EnrollmentTypeIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    mode = models.CharField(max_length=256, null=True)
    is_active = models.BooleanField(null=False, default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Enrollment Type Indeces"


class ActivityIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    enrolled_only = models.BooleanField(null=False, default=False, help_text="Users enrolled with no activity yet")
    participant = models.BooleanField(null=False, default=False, help_text="Users with course activity")
    min_inactivity_days = models.IntegerField(null=False, default=0,
                                              help_text="No recorded activity or enrolled greater than"
                                                        " this number of days")
    max_inactivity_days = models.IntegerField(null=False, default=100,
                                              help_text="No recorded activity or enrolled less than this number of days")

    def __unicode__(self):
        return self.name

    def clean_fields(self, exclude=None):
        if not self.enrolled_only and not self.participant:
            raise ValidationError("At least one enrolled_only or participant MUST be selected")

    class Meta:
        verbose_name_plural = "Activity Indeces"


class CompoundIndex(models.Model):
    name = models.CharField(max_length=128, unique=True)
    template = models.ForeignKey(Template, null=True)
    email_subject = models.CharField(max_length=256, blank=False,
                                     help_text="Merge fields (e.g. *|FNAME|*, *|LNAME|*, *|COURSE|*) are permitted")
    qualification = models.ManyToManyField(QualificationIndex, blank=True)
    certification = models.ManyToManyField(CertificationIndex, blank=True)
    enrollment = models.ManyToManyField(EnrollmentTypeIndex, blank=True)
    progress = models.ManyToManyField(ProgressIndex, blank=True)
    activity = models.ManyToManyField(ActivityIndex, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Compound Indeces"


def validate_future(value):
    if value < datetime.datetime.now(tz=value.tzinfo):
        raise ValidationError('Trigger time cannot be in the past')


class CampaignGenerator(models.Model):
    """
    Helper class to generate campaigns models
    """
    name = models.CharField(max_length=64, blank=False)
    courses = models.ManyToManyField(Course)
    is_active = models.BooleanField(null=False, default=True)
    qualification_index = models.ManyToManyField(QualificationIndex, blank=True)
    certification_index = models.ManyToManyField(CertificationIndex, blank=True)
    enrollment_index = models.ManyToManyField(EnrollmentTypeIndex, blank=True)
    progress_index = models.ManyToManyField(ProgressIndex, blank=True)
    activity_index = models.ManyToManyField(ActivityIndex, blank=True)
    compound_index = models.ManyToManyField(CompoundIndex, blank=True)
    test_emails = models.ManyToManyField(User)
    trigger_day = models.IntegerField(null=False, blank=False, default=1, choices=DAYS_OF_WEEK)
    trigger_time = models.TimeField(null=False, blank=False, default=datetime.time(hour=10, minute=0))

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    """
    Model to represent mailchimp campaign

    id: mailchimp campaign id
    """
    __original_enable = None
    __original_trigger_time = None

    def __init__(self, *args, **kwargs):
        super(Campaign, self).__init__(*args, **kwargs)
        self.__original_enable = self.enable
        self.__original_trigger_time = self.trigger_time

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.trigger_time = self.trigger_time.replace(minute=self.trigger_time.minute -
                                                             (self.trigger_time.minute % 15))

        if (self.__original_enable and not self.enable) or \
                (self.trigger_time != self.__original_trigger_time and self.__original_enable and self.enable):
            unschedule_campaign(self.id, self.name, MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)

        if (not self.__original_enable and self.enable) or \
                (self.trigger_time != self.__original_trigger_time and self.__original_enable and self.enable):
            schedule_campaign(self.id, self.name, self.trigger_time.astimezone(timezone.utc),
                              MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)

        super(Campaign, self).save(force_insert, force_update, *args, **kwargs)
        self.__original_enable = self.enable
        self.__original_trigger_time = self.trigger_time

    def delete(self, using=None, keep_parents=False):
        c_id = self.id
        c_name = self.name
        super(Campaign, self).delete(using, keep_parents)
        delete_campaign(c_id, c_name, MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)


    id = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=128, blank=False, null=False)
    course = models.ForeignKey(Course)
    enable = models.BooleanField(null=False, blank=False, default=True)
    trigger_time = models.DateTimeField(null=False, blank=False,
                                        help_text="Rounded down automatically to 15-minute multiple")
    open_rate = models.FloatField(blank=True, null=True)
    click_rate = models.FloatField(blank=True, null=True)
    num_emails = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.name


class UpdateLog(models.Model):
    last_update = models.DateTimeField(null=False)