# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from controller.settings import MAILCHIMP_DEVKEY, MAILCHIMP_URL
from control_panel.models import Template, CampaignGenerator
from libhh.mailchimp import get_templates
from control_panel.admin import CampaignGeneratorAdmin
from django.shortcuts import render


def fetch_templates(request):
    try:
        templates = get_templates(MAILCHIMP_URL, headers=MAILCHIMP_DEVKEY)
        for index, row in templates.iterrows():
            Template.objects.update_or_create(id=row['id'], name=row['name'])
        return HttpResponse("{0} templates updated".format(len(templates)))

    except Exception, e:
        return HttpResponse("Error trying to import and update templates </br>{0}".format(e.message))


def trigger_campaigns(request):
    campaigns = CampaignGenerator.objects.all()
    return CampaignGeneratorAdmin.generate_campaigns(CampaignGeneratorAdmin(CampaignGenerator, request), request, campaigns)
