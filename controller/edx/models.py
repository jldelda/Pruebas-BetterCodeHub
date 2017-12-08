# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True, null=False)
    username = models.CharField(max_length=30L, null=False, unique=True)
    first_name = models.CharField(max_length=30L, null=False)
    last_name = models.CharField(max_length=30L, null=False)
    email = models.CharField(max_length=75L, null=False, unique=True)
    password = models.CharField(max_length=128L, null=False)
    is_staff = models.IntegerField(null=False)
    is_active = models.IntegerField(null=False)
    is_superuser = models.IntegerField(null=False)
    last_login = models.DateTimeField(null=False)
    date_joined = models.DateTimeField(null=False)

    def __unicode__(self):
        return "{0}".format(self.username)

    class Meta:
        db_table = 'auth_user'


class AuthUserprofile(models.Model):
    id = models.IntegerField(primary_key=True, null=False)
    user_id = models.ForeignKey(AuthUser, db_column='user_id')
    name = models.CharField(max_length=255L, null=False, db_index=True)
    meta = models.TextField(null=False)
    gender = models.CharField(max_length=6L, null=True, db_index=True)
    year_of_birth = models.IntegerField(null=True, db_index=True)
    level_of_education = models.CharField(max_length=6L, null=True, db_index=True)
    goals = models.TextField(null=True)
    allow_certificate = models.SmallIntegerField(null=False)
    country = models.CharField(max_length=2L, null=False)
    city = models.TextField()
    bio = models.CharField(max_length=3000L, null=True)
    profile_image_uploaded_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "{0}".format(self.name)

    class Meta:
        db_table = 'auth_userprofile'


class StudentCourseenrollment(models.Model):
    id = models.IntegerField(primary_key=True, null=False)
    user_id = models.ForeignKey(AuthUser, db_index=True, db_column='user_id')
    course_id = models.CharField(max_length=255, null=False, db_index=True)
    created = models.DateTimeField(null=True, db_index=True)
    is_active = models.SmallIntegerField(null=False)
    mode = models.CharField(max_length=100, null=False)

    def __unicode__(self):
        return "{0} : {1}".format(self.course_id, self.user_id)

    class Meta:
        db_table = 'student_courseenrollment'


class UserIdMap(models.Model):
    hash_id = models.CharField(max_length=40, null=False, primary_key=True)
    id = models.ForeignKey(AuthUser, to_field='id', related_name='+', db_column='id')
    username = models.ForeignKey(AuthUser, to_field= 'username', related_name='+', db_column='username')

    def __unicode__(self):
        return "{0}".format(self.username)

    class Meta:
        db_table = 'user_id_map'


class StudentAnonymoususerid(models.Model):
    id = models.IntegerField(primary_key=True, null=False)
    user_id = models.ForeignKey(AuthUser, db_column='user_id')
    anonymous_user_id = models.CharField(max_length=32, null=False, unique=True)
    course_id = models.CharField(max_length=255, null=False, db_index=True)

    def __unicode__(self):
        return "{0}".format(self.user_id)

    class Meta:
        db_table = 'student_anonymoususerid'


class StudentLanguageproficiency(models.Model):
    id = models.IntegerField(null=False, primary_key=True)
    user_profile_id	= models.ForeignKey(AuthUserprofile, db_column='user_profile_id')
    code = models.CharField(max_length=16, null=False, db_index=True)

    def __unicode__(self):
        return "{0}".format(self.user_profile_id)

    class Meta:
        db_table = 'student_languageproficiency'


class CoursewareStudentmodule(models.Model):
    id = models.IntegerField(null=False, primary_key=True)
    module_type = models.CharField(max_length=32, null=False, db_index=True, default='problem')
    module_id = models.CharField(max_length=255, null=False, db_index=True)
    student_id = models.ForeignKey(AuthUser, db_column='student_id')
    state = models.TextField(null=True)
    grade = models.FloatField(null=True, db_index=True)
    created = models.DateTimeField(null=False, db_index=True)
    modified = models.DateTimeField(null=True, db_index=True)
    max_grade = models.FloatField(null=True)
    done = models.CharField(max_length=8, null=False)
    course_id = models.CharField(max_length=255, null=False, db_index=True)

    def __unicode__(self):
        return "{0} : {1}".format(self.student_id, self.module_id)

    class Meta:
        db_table = 'courseware_studentmodule'


class GradesPersistentcoursegrade(models.Model):
    course_id = models.CharField(max_length=255, null=False, db_index=True)
    user_id = models.ForeignKey(AuthUser, db_column='user_id')
    grading_policy_hash = models.CharField(max_length=255, null=False)
    percent_grade = models.FloatField(null=False, db_index=True)
    letter_grade = models.CharField(max_length=255)
    passed_timestamp = models.DateTimeField(null=True, db_index=True)
    created	= models.DateTimeField(null=False, db_index=True)
    modified = models.DateTimeField(null=False, db_index=True)

    def __unicode__(self):
        return "{0}: {1} got {2}".format(self.course_id, self.user_id, self.percent_grade)

    class Meta:
        db_table = 'grades_persistentcoursegrade'


class GradesPersistentsubsectiongrade(models.Model):
    course_id = models.CharField(max_length=255, null=False, db_index=True)
    user_id = models.ForeignKey(AuthUser, db_column='user_id')
    usage_key= models.CharField(max_length=255, null=False, db_index=True)
    earned_all = models.FloatField(null=False, db_index=True)
    possible_all = models.FloatField(null=False, db_index=True)
    earned_graded = models.FloatField(null=False, db_index=True)
    possible_graded	= models.FloatField(null=False, db_index=True)
    first_attempted	= models.DateTimeField(null=False, db_index=True)
    created	= models.DateTimeField(null=False)
    modified = models.DateTimeField(null=False, db_index=True)

    def __unicode__(self):
        return "{0} : {1}".format(self.course_id, self.user_id)

    class Meta:
        db_table = 'grades_persistentsubsectiongrade'


class CertificatesGeneratedcertificate(models.Model):
    id = models.IntegerField(primary_key=True, null=False)
    user_id	= models.ForeignKey(AuthUser, db_column='user_id')
    download_url = models.CharField(max_length=128, null=False)
    grade = models.FloatField(null=False)
    course_id = models.CharField(max_length=255, null=False, db_index=True)
    key	= models.CharField(max_length=32, null=False)
    status = models.CharField(max_length=32, null=False)
    verify_uuid = models.CharField(max_length=32, null=False)
    download_uuid = models.CharField(max_length=32, null=False)
    name = models.CharField(max_length=255, null=False)
    created_date = models.DateTimeField(null=False)
    modified_date = models.DateTimeField(null=False)
    error_reason = models.CharField(max_length=512, null=False)
    mode = models.CharField(max_length=32, null=False)

    def __unicode__(self):
        return "{0} : {1}".format(self.user_id, self.course_id)

    class Meta:
        db_table = 'certificates_generatedcertificate'


class StudentCourseaccessrole(models.Model):
    user_id = models.ForeignKey(AuthUser, db_column='user_id')
    course_id = models.CharField(max_length=255, null=False, db_index=True, db_column='course_id')
    role = models.CharField(max_length=255, null=False)

    def __unicode__(self):
        return "{0}:{1}".format(self.user_id, self.role)

    class Meta:
        db_table = 'student_courseaccessrole'