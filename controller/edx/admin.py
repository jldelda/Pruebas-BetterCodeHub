# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from edx.models import *

admin.site.disable_action('delete_selected')

class GradesPersistentCourseGradeAdmin(admin.ModelAdmin):
    search_fields = ('course_id', 'user_id', 'percent_grade', 'letter_grade')
    list_display = ('course_id', 'user_id', 'percent_grade', 'letter_grade')
    list_filter = ('course_id', 'letter_grade', 'passed_timestamp')
    readonly_fields = [f.name for f in GradesPersistentcoursegrade._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]


class AuthUserAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in AuthUser._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]


class AuthUserprofileAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in AuthUserprofile._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('user_id')


class StudentCourseenrollmentAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in StudentCourseenrollment._meta.get_fields(include_parents=False) if (f.name and
                                                                                                           not f.is_relation)]
    readonly_fields.append('user_id')


class UserIdMapAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in UserIdMap._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('id')


class StudentAnonymoususeridAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in StudentAnonymoususerid._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('user_id')


class CoursewareStudentmoduleAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in CoursewareStudentmodule._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('student_id')


class GradesPersistentsubsectiongradeAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in GradesPersistentsubsectiongrade._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('user_id')


class CertificatesGeneratedcertificateAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in CertificatesGeneratedcertificate._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('user_id')
    list_display = ('course_id', 'status')
    list_filter = ('course_id', 'status')



class StudentLanguageproficiencyAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in StudentLanguageproficiency._meta.get_fields(include_parents=False) if (f.name and
                                                                                            not f.is_relation)]
    readonly_fields.append('user_profile_id')


# Register your models here.
admin.site.register(AuthUser, AuthUserAdmin)
admin.site.register(AuthUserprofile, AuthUserprofileAdmin)
admin.site.register(StudentCourseenrollment, StudentCourseenrollmentAdmin)
admin.site.register(UserIdMap, UserIdMapAdmin)
admin.site.register(StudentAnonymoususerid, StudentAnonymoususeridAdmin)
admin.site.register(CoursewareStudentmodule, CoursewareStudentmoduleAdmin)
admin.site.register(GradesPersistentcoursegrade, GradesPersistentCourseGradeAdmin)
admin.site.register(GradesPersistentsubsectiongrade, GradesPersistentsubsectiongradeAdmin)
admin.site.register(CertificatesGeneratedcertificate, CertificatesGeneratedcertificateAdmin)
admin.site.register(StudentLanguageproficiency, StudentLanguageproficiencyAdmin)