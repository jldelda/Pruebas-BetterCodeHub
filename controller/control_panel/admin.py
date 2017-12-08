# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from models import *
from edx.models import *
import operator
from django.db.models import Q, Sum, F
from django.shortcuts import render
from django.utils import timezone
from django.core.exceptions import ValidationError
import pandas as pd
import datetime
import traceback
from libhh.mailchimp import *
from controller.settings import LIST_GENERIC_INFO, MAILCHIMP_DEVKEY, MAILCHIMP_URL, MAILCHIMP_BUSINESS,\
    MAILCHIMP_REPLY_TO

STATUS_CHOICES = (
    (None, ''),
    ('downloadable', 'downloadable'),
    ('audit_passing', 'audit_passing'),
    ('notpassing', 'notpassing'),
    ('audit_notpassing', 'audit_notpassing'),
)

MODE_CHOICES = (
    (None, ''),
    ('audit', 'audit'),
    ('honor', 'honor'),
    ('professional', 'professional'),
    ('verified', 'verified')
)


class CourseAdmin(admin.ModelAdmin):
    readonly_fields = ('mailchimp_list_id',)
    search_fields = ('id', 'name', 'start_date', 'end_date')
    list_display = ('id', 'name', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date', 'language')


class ActivityIndexAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'template', 'enrolled_only', 'participant', 'min_inactivity_days', 'max_inactivity_days')
    list_filter = ('enrolled_only', 'participant', 'min_inactivity_days', 'max_inactivity_days')


class QualificationIndexAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'template', 'min_percent_grade', 'max_percent_grade', 'letter_grade',
                    'min_passed_timestamp', 'max_passed_timestamp')
    list_filter = ('min_percent_grade', 'max_percent_grade', 'letter_grade', 'min_passed_timestamp',
                   'max_passed_timestamp')


class ProgressIndexAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'template', 'min_earned', 'max_earned', 'min_graded', 'max_graded')
    list_filter = ('min_earned', 'max_earned', 'min_graded', 'max_graded')


class CertificationIndexAdmin(admin.ModelAdmin):
    def get_form(self, *args, **kwargs):
        form = super(CertificationIndexAdmin, self).get_form(*args, **kwargs)
        form.base_fields['status'] = forms.MultipleChoiceField(choices=STATUS_CHOICES)
        return form

    def save_model(self, request, obj, form, change):
        obj.status = ','.join(form.cleaned_data['status'])
        obj.save()

    search_fields = ('name', 'status')
    list_display = ('name', 'template', 'status', 'min_percent_grade', 'max_percent_grade')
    list_filter = ('status', 'min_percent_grade', 'max_percent_grade')

class EnrollmentTypeIndexAdmin(admin.ModelAdmin):
    def get_form(self, *args, **kwargs):
        form = super(EnrollmentTypeIndexAdmin, self).get_form(*args, **kwargs)
        form.base_fields['mode'] = forms.MultipleChoiceField(choices=MODE_CHOICES)
        return form

    def save_model(self, request, obj, form, change):
        obj.mode = ','.join(form.cleaned_data['mode'])
        obj.save()

    search_fields = ('name', 'mode')
    list_display = ('name', 'template', 'mode', 'is_active')
    list_filter = ('mode', 'is_active')

class CompoundIndexAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'template')

class CampaignAdmin(admin.ModelAdmin):
    def campaign_report(self, modeladmin, request, campaign):
        data={}
        open = report_campaign_open_details(campaign.id, MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        click = report_campaign_email_activity(campaign.id, MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        #open = report_campaign_open_details('33aca0b765', MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        #click = report_campaign_email_activity('33aca0b765', MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        data['total_sent'] = campaign.num_emails
        data['total_opened']=open['total_opened']
        data['total_users_opened'] = open['total_users_opened']
        if len(open['members_open']) > 0:
            members_open = pd.DataFrame(open['members_open'])['email_address']
        else:
            members_open = []
        if len(click):
            click = click[['email_address', 'activity']].set_index('email_address')
            members_click = list(click[click.activity.
                                 apply(lambda x: len(filter(lambda y: y['action'] == 'click', x)) > 0)].index) #list of email addresses, future use?
        else:
            members_click = []
        campaign.click_rate = float(len(members_click))/campaign.num_emails
        campaign.open_rate = float(data['total_users_opened']) / campaign.num_emails
        campaign.save(update_fields=['click_rate', 'open_rate'])
        data['total_click'] = len(members_click)
        data['click_rate'] = campaign.click_rate
        data['open_rate'] = campaign.open_rate
        gen_admin = CampaignGeneratorAdmin(campaign, request)
        # Determine approved users
        qual_index = QualificationIndex(min_percent_grade=0.65)
        users_approved = gen_admin.qualification_index_users(qual_index, campaign.course)
        data['approved'] = len(users_approved)
        # Determine participants
        participants = CoursewareStudentmodule.objects.select_related('student_id').filter(course_id=campaign.course.id,
                                                                            student_id__is_active=True,
                                                                            modified__gte=campaign.trigger_time).\
            values_list('student_id__email', flat=True)
        data['participants'] = len(participants)
        data['campaign_participants'] = len(set(participants).intersection(members_open))
        # Determine certified users
        cert_index = CertificationIndex(status='downloadable')
        certified_users = gen_admin.certification_index_users(cert_index, campaign.course)
        data['certified'] = len(certified_users)
        data['campaign_certified'] = len(set(certified_users).intersection(members_open))
        data['campaign_approved'] = len(set(users_approved).intersection(members_open))
        data['enrolled_users'] = len(list(get_enrolled_active_users(campaign.course.id)))
        return data

    def delete_campaigns(modeladmin, request, queryset):
        results={}
        for campaign in queryset:
            results[campaign.name]={}
            try:
                campaign.delete()
                results[campaign.name][''] = (None, 'Successfully deleted')
            except Exception, e:
                results[campaign.name][''] = (e.message, 'Error while deleting campaign')

        return render(request, "campaign_results.html", {'results': results, 'total_campaigns': len(queryset)})

    def report_campaigns(modeladmin, request, queryset):
        results = []
        for campaign in queryset:
            data = {'name': campaign.name}
            data.update(modeladmin.campaign_report(modeladmin, request, campaign))
            results.append(data)

        return render(request, "campaign_report.html", {'campaigns':results})

    readonly_fields = ('open_rate', 'click_rate', 'num_emails', 'id')

    actions = [delete_campaigns, report_campaigns]
    search_fields = ('name', 'course__name')
    list_display = ('name', 'course', 'enable', 'trigger_time','open_rate', 'click_rate', 'num_emails' )
    list_filter = ('enable','open_rate', 'click_rate')


def get_enrolled_active_users(id):
    """
    Get list of active users enrolled in course id
    :param id: course id
    :return: QuerySet of StudentCourseenrollment join with AuthUser
    """

    non_students = list(StudentCourseaccessrole.objects.select_related('user_id').filter(course_id=id)
                        .values_list('user_id', flat=True))
    return StudentCourseenrollment.objects.select_related('user_id').filter(course_id=id, is_active=True,
                                                            user_id__is_active=True).exclude(user_id__in=non_students)


def update_course_list(course):
    users_info = get_enrolled_active_users(course.id).values_list('user_id__id', flat=True)
    users_info = AuthUserprofile.objects.select_related('user_id').filter(user_id__id__in=users_info)\
        .values_list('user_id__email', 'name')
    users_info = [tuple([e] + (n + ' ').split(' ', 1)) for e,n in users_info]
    course.mailchimp_list_id = update_list(course.id, course.name, course.language, LIST_GENERIC_INFO, users_info,
                                           MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
    course.save()


class CampaignGeneratorAdmin(admin.ModelAdmin):
    def create_all(self, query_grade, u_list, campaign, course, trigger_time):
        if len(u_list) == 0:
            print 'There are no users for selected filter'
            return
        non_students = list(StudentCourseaccessrole.objects.select_related('user_id').filter(course_id=course.id)
                            .values_list('user_id__email', flat=True))
        user_list = list(set(u_list) - set(non_students))
        title = course.id + '_' + query_grade.name
        segment_id = create_segment(course.mailchimp_list_id, title, user_list,
                                    MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        test_emails = list(campaign.test_emails.all().values_list('email', flat=True))
        campaign_id = create_campaign(title, course.mailchimp_list_id, segment_id, query_grade.template_id,
                                      trigger_time, query_grade.email_subject, MAILCHIMP_REPLY_TO,
                                      MAILCHIMP_BUSINESS, test_emails, MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        new_campaign = Campaign(id=campaign_id, name=title, course=course, trigger_time=trigger_time,
                                num_emails=len(user_list))
        new_campaign.save()

    def progress_index_users(self, query_grade, course):
        user_list = []
        users_with_progress = list(set(GradesPersistentsubsectiongrade.objects.all().
                                           values_list('user_id', flat=True)))
        users_with_no_progress = get_enrolled_active_users(course.id).exclude(user_id__in=users_with_progress)
        num_section = Course.objects.get(id=course.id).num_section
        q = [Q(course_id=course.id, possible_all__gt=0, possible_graded__gt=0)]
        grades = GradesPersistentsubsectiongrade.objects.select_related('user_id').filter(reduce(operator.and_, q)) \
            .annotate(earned=Sum(F('earned_all') / F('possible_all')) / num_section,
                      graded=Sum(F('earned_graded') / F('possible_graded')) / num_section) \
            .values('user_id__email', 'earned', 'graded')

        if len(grades) == 0:
            return user_list

        q1 = "earned >= {0} and earned <= {1}".format(query_grade.min_earned, query_grade.max_earned)
        q2 = "graded >= {0} and graded <= {1}".format(query_grade.min_graded, query_grade.max_graded)
        pgrades = pd.DataFrame.from_records(grades)
        # user_list[course_id] = pgrades.groupby('user_id').sum().query("{0} and {1}".format(q1,q2)).index.values
        user_list.extend(pgrades.groupby('user_id__email').sum().query("{0} and {1}".format(q1, q2)).index.values)
        if query_grade.min_earned == 0 and query_grade.min_graded == 0:
            user_list.extend(list(users_with_no_progress.values_list('user_id__email', flat=True)))
        return user_list

    def progress_index_filter(self, campaign, course, trigger_time):
        for query_grade in campaign.progress_index.all():
            user_list = self.progress_index_users(query_grade, course)
            self.create_all(query_grade, user_list, campaign, course, trigger_time)

    def qualification_index_users(self, query_grade, course):
        q = [Q(percent_grade__lte=query_grade.max_percent_grade, percent_grade__gte=query_grade.min_percent_grade,
               course_id=course.id)]
        if query_grade.letter_grade: q.append(Q(letter_grade=query_grade.letter_grade))
        if query_grade.min_passed_timestamp: q.append(Q(passed_timestamp__gte=query_grade.min_passed_timestamp))
        if query_grade.max_passed_timestamp: q.append(Q(passed_timestamp__lte=query_grade.max_passed_timestamp))
        return list(GradesPersistentcoursegrade.objects.select_related('user_id').filter(reduce(operator.and_, q))
                    .values_list('user_id__email', flat=True))

    def qualification_index_filter(self, campaign, course, trigger_time):
        for query_grade in campaign.qualification_index.all():
            user_list = self.qualification_index_users(query_grade, course)
            self.create_all(query_grade, user_list, campaign, course, trigger_time)

    def certification_index_users(self, query_grade, course):
        q = [Q(grade__lte=query_grade.max_percent_grade, grade__gte=query_grade.min_percent_grade,
               course_id=course.id)]
        if query_grade.status: q.append(Q(status__in=query_grade.status.split(',')))
        return list(CertificatesGeneratedcertificate.objects.select_related('user_id').filter(reduce(operator.and_, q))
                    .values_list('user_id__email', flat=True))

    def certification_index_filter(self, campaign, course, trigger_time):
        for query_grade in campaign.certification_index.all():
            user_list = self.certification_index_users(query_grade, course)
            self.create_all(query_grade, user_list, campaign, course, trigger_time)

    def enrollment_index_users(self, query_grade, course):
        q = [Q(is_active=query_grade.is_active, course_id=course.id, user_id__is_active=True)]
        if query_grade.mode: q.append(Q(mode__in=query_grade.mode.split(',')))
        return list(StudentCourseenrollment.objects.select_related('user_id').filter(reduce(operator.and_, q))
                    .values_list('user_id__email', flat=True))

    def enrollment_index_filter(self, campaign, course, trigger_time):
        for query_grade in campaign.enrollment_index.all():
            user_list = self.enrollment_index_users(query_grade, course)
            self.create_all(query_grade, user_list, campaign, course, trigger_time)

    def activity_index_users(self, query_grade, course):
        current_time = datetime.datetime.now(tz=timezone.utc)
        participants = CoursewareStudentmodule.objects.select_related('student_id').filter(course_id=course.id,
                                                                                           student_id__is_active=True)
        users = set()

        if query_grade.enrolled_only:
            q = [Q(course_id=course.id, is_active=True, user_id__is_active=True,
                        created__lte=current_time - datetime.timedelta(days=query_grade.min_inactivity_days))]
            if (current_time - datetime.timedelta(days=query_grade.max_inactivity_days)).date() > course.start_date:
                q.append(Q(created__gte=current_time - datetime.timedelta(days=query_grade.max_inactivity_days)))

            enrolled_users = list(StudentCourseenrollment.objects.select_related('user_id')
                                  .filter(reduce(operator.and_, q)).values_list('user_id__email', flat=True))
            all_participants = list(set(participants.values_list('student_id__email', flat=True)))
            users = users.union(set(enrolled_users) - set(all_participants))

        if query_grade.participant:
            users = users.union(set(participants.filter(modified__gte=current_time - datetime.timedelta(
                                        days=query_grade.max_inactivity_days),
                                    modified__lte=current_time - datetime.timedelta(
                                        days=query_grade.min_inactivity_days))
                            .values_list('student_id__email', flat=True)))

        return list(users)

    def activity_index_filter(self, campaign, course, trigger_time):
        for query_grade in campaign.activity_index.all():
            user_list = self.activity_index_users(query_grade, course)
            self.create_all(query_grade, user_list, campaign, course, trigger_time)

    def compound_index_filter(self, campaign, course, trigger_time):
        for query_index in campaign.compound_index.all():
            user_list = None
            for query_grade in query_index.qualification.all():
                tmp = self.qualification_index_users(query_grade, course)
                if not user_list:
                    user_list = set(tmp)
                else:
                    user_list = user_list.intersection(tmp)
            for query_grade in query_index.certification.all():
                tmp = self.certification_index_users(query_grade, course)
                if not user_list:
                    user_list = set(tmp)
                else:
                    user_list = user_list.intersection(tmp)
            for query_grade in query_index.progress.all():
                tmp = self.progress_index_users(query_grade, course)
                if not user_list:
                    user_list = set(tmp)
                else:
                    user_list = user_list.intersection(tmp)
            for query_grade in query_index.enrollment.all():
                tmp = self.enrollment_index_users(query_grade, course)
                if not user_list:
                    user_list = set(tmp)
                else:
                    user_list = user_list.intersection(tmp)
            for query_grade in query_index.activity.all():
                tmp = self.activity_index_users(query_grade, course)
                if not user_list:
                    user_list = set(tmp)
                else:
                    user_list = user_list.intersection(tmp)
            self.create_all(query_index, list(user_list), campaign, course, trigger_time)

    def generate_campaigns(modeladmin, request, queryset):
        results={}
        course_id=None
        total_campaigns=0
        for campaign in queryset:
            try:
                if not campaign.is_active:
                    continue
                results[campaign.name]={}
                for course in campaign.courses.all():
                    if course.end_date < timezone.localdate():
                        course.is_active=False
                        course.save()
                        campaign.courses.remove(course)
                        continue
                    course_id = course.id
                    update_course_list(course)

                d= timezone.localtime()
                delta = (7 - d.weekday() + campaign.trigger_day) % 7
                if delta == 0:
                    delta = 7
                d = d.replace(hour=campaign.trigger_time.hour,
                              minute=campaign.trigger_time.minute - (campaign.trigger_time.minute % 15))
                trigger_time = (d + datetime.timedelta(days=delta)).astimezone(timezone.utc)

                for course in campaign.courses.all():
                    if not course.is_active:
                        continue
                    total_campaigns += 1
                    course_id = course.id
                    if len(campaign.certification_index.all()) > 0:
                        modeladmin.certification_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id+':certification_indeces'] = (None,
                                                                    "{0} campaign(s) successfully scheduled".
                                                                    format(len(campaign.certification_index.all())))
                    if len(campaign.enrollment_index.all()) > 0:
                        modeladmin.enrollment_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id + ':enrollment_indeces'] = (None,
                                                                    "{0} campaign(s) successfully scheduled".
                                                                    format(len(campaign.enrollment_index.all())))
                    if len(campaign.qualification_index.all()) > 0:
                        modeladmin.qualification_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id + ':qualification_indeces'] = (None,
                                                                        "{0} campaign(s) successfully scheduled".
                                                                        format(len(campaign.qualification_index.all())))
                    if len(campaign.progress_index.all()) > 0:
                        modeladmin.progress_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id + ':progress_indeces'] = (None,
                                                                    "{0} campaign(s) successfully scheduled".
                                                                    format(len(campaign.progress_index.all())))
                    if len(campaign.activity_index.all()) > 0:
                        modeladmin.activity_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id + ':activity_indeces'] = (None,
                                                                    "{0} campaign(s) successfully scheduled".
                                                                    format(len(campaign.activity_index.all())))
                    if len(campaign.compound_index.all()) > 0:
                        modeladmin.compound_index_filter(campaign, course, trigger_time)
                        results[campaign.name][course_id + ':compound_indeces'] = (None,
                                                                    "{0} campaign(s) successfully scheduled".
                                                                    format(len(campaign.compound_index.all())))

            except Exception, e:
                traceback.print_stack()
                results[campaign.name][course_id] = (str(e.args), 'Error while scheduling campaign')

        return render(request, "campaign_results.html", {'results':results, 'total_campaigns':total_campaigns})

    def get_form(self, *args, **kwargs):
        form = super(CampaignGeneratorAdmin, self).get_form(*args, **kwargs)
        form.base_fields['courses'].queryset = Course.objects.filter(is_active=True)
        return form

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['last_update'] = UpdateLog.objects.last()
        return super(CampaignGeneratorAdmin, self).changelist_view(request, extra_context=extra_context)


    def save_model(self, request, obj, form, change):
        obj.save()

    actions = [generate_campaigns]
    search_fields = ('name',)
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)


admin.site.register(Course, CourseAdmin)
admin.site.register(Template)
admin.site.register(QualificationIndex, QualificationIndexAdmin)
admin.site.register(ActivityIndex, ActivityIndexAdmin)
admin.site.register(CertificationIndex, CertificationIndexAdmin)
admin.site.register(EnrollmentTypeIndex, EnrollmentTypeIndexAdmin)
admin.site.register(ProgressIndex, ProgressIndexAdmin)
admin.site.register(CompoundIndex, CompoundIndexAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(CampaignGenerator, CampaignGeneratorAdmin)
# Register your models here.
