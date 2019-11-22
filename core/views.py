from datetime import datetime, timedelta
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from common import constants
from core.models import ScorebotMetrics, WebhookPR, EnforcementMetrics
from core.serializers import ScorebotMetricsSerializer, WebhookPRSerializer, EnforcementMetricsSerializer
from sb_service.service.EnforcementFunctions import EnforcementFunctions
from scorebot import settings
from scorebot.forms import ExemptionForm

if constants.SSO_FLAG:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings


EnforcementFunctions = EnforcementFunctions(pull_request=None, file_extensions=None, logger=None)

framework_map = {"cpp": "CPP",
                 "java": "Java",
                 "kraken": "Kraken"}


# === SSO Integration ===


def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=settings.SAML_FOLDER)
    return auth


def prepare_django_request(request):
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        'server_port': request.META['SERVER_PORT'],
        'get_data': request.GET.copy(),
        'post_data': request.POST.copy(),
        'query_string': request.META['QUERY_STRING']
    }
    return result


def acs(request):
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    request_id = None
    if 'AuthNRequestID' in request.session:
        request_id = request.session['AuthNRequestID']
    if 'LogoutRequestID' in request.session:
        request_id = request.session['LogoutRequestID']
        request.session.flush()
    auth.process_response(request_id=request_id)
    errors = auth.get_errors()
    if len(errors) == 0:
        if 'AuthNRequestID' in request.session:
            del request.session['AuthNRequestID']
        request.session['samlNameId'] = auth.get_nameid()
        request.session['samlSessionIndex'] = auth.get_session_index()
        request.session["samlUserdata"] = auth.get_attributes()
        return HttpResponseRedirect("/scorebot/")
    return HttpResponseRedirect("/")


def attrs(request):
    paint_logout = False
    attributes = False
    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()

    return render(request, 'attrs.html',
                  {'paint_logout': paint_logout,
                   'attributes': attributes})


def metadata(request):
    saml_settings = OneLogin_Saml2_Settings(settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)
    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp


def exemptions_page(request, template_name):
    firstname = ''
    username = ''
    redirect_url = "/"
    if constants.SSO_FLAG:
        # SSO integration
        req = prepare_django_request(request)
        auth = init_saml_auth(req)

        if 'sso' in req['get_data']:
            return HttpResponseRedirect(auth.login(return_to=constants.SSO_REDIRECT))
        elif 'slo' in req['get_data']:
            name_id = None
            session_index = None
            if 'samlNameId' in request.session:
                name_id = request.session['samlNameId']
            if 'samlSessionIndex' in request.session:
                session_index = request.session['samlSessionIndex']
            slo_built_url = auth.logout(name_id=name_id, session_index=session_index)
            return HttpResponseRedirect(slo_built_url)

        if 'samlUserdata' not in request.session:
            # login
            return HttpResponseRedirect(auth.login(return_to=constants.SSO_REDIRECT))
        else:
            if len(request.session['samlUserdata']) > 0:
                attributes = request.session['samlUserdata']
                firstname = ", " + str(attributes['firstname'][0])
                username = str(attributes['username'][0])

    if request.method == "POST":
        form = ExemptionForm(request.POST)

        if form.is_valid():
            EnforcementFunctions.get_exemption(form.cleaned_data["framework"], form.cleaned_data["pull_request_url"],
                                       form.cleaned_data["commit_id"])
            form_instance = form.save(commit=False)
            form_instance.user = username
            form_instance.save()
            messages.success(request, "Exemption submitted successfully!")
            return HttpResponseRedirect("/")

        else:
            messages.info(request, '')
    else:
        form = ExemptionForm()
        form.fields["pull_request_url"].initial = request.GET.get("pr", "")
        form.fields["framework"].initial = request.GET.get("framework", "")
        form.fields["commit_id"].initial = request.GET.get("commit_id", "")
    return render(request, template_name, {"form": form, "firstname": firstname, "redirect_url": redirect_url,
                                           "nav_exemptions": "active"})


# ================= APIs to be consumed ==================


def scorebot_metrics_all(request, framework):
    """
    API to return all SCORE Bot metrics from beginning of time, filtered by framework
    :param request:
    :param framework
    :return: JSON
    """
    if request.method == "GET":
        if framework == "all":
            scorebot_metrics = ScorebotMetrics.objects.all()
        else:
            scorebot_metrics = ScorebotMetrics.objects.filter(framework=framework)
        serializer = ScorebotMetricsSerializer(scorebot_metrics, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def scorebot_metrics_start_end(request, start, end, framework):
    """
    API to return all SCORE Bot metrics from start date to end date, filtered by framework
    :param request:
    :param start: YYYY-MM-DD
    :param end: YYYY-MM-DD
    :param framework:
    :return: JSON
    """
    if request.method == "GET":
        if framework == "all":
            scorebot_metrics = ScorebotMetrics.objects.filter(
                queued_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                queued_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1))
        else:
            scorebot_metrics = ScorebotMetrics.objects.filter(
                queued_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                queued_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1),
                framework=framework)

        serializer = ScorebotMetricsSerializer(scorebot_metrics, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def enforcement_metrics_all(request, framework):
    """
    API to return list of all Enforcement metrics from beginning of time, filtered by framework
    :param request:
    :param framework:
    :return: JSON
    """

    if request.method == "GET":
        if framework == "all":
            enforcement_metrics = EnforcementMetrics.objects.all()
        else:
            enforcement_metrics = EnforcementMetrics.objects.filter(framework=framework)
        serializer = EnforcementMetricsSerializer(enforcement_metrics, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def enforcement_metrics_start_end(request, start, end, framework):
    """
    API to return all Enforcement metrics from start date to end date, filtered by framework
    :param request:
    :param start: YYYY-MM-DD
    :param end: YYYY-MM-DD
    :param framework
    :return: JSON
    """
    if request.method == "GET":
        if framework == "all":
            enforcement_metrics = EnforcementMetrics.objects.filter(
                queued_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                queued_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1))
        else:
            enforcement_metrics = EnforcementMetrics.objects.filter(
                queued_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                queued_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1),
                framework=framework)
        serializer = EnforcementMetricsSerializer(enforcement_metrics, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def pr_count_all(request, framework):
    """
    API to return list of all PRs processed from beginning of time, filtered by framework
    :param request:
    :param framework:
    :return: JSON
    """

    if request.method == "GET":
        if framework == "all":
            pr_count = WebhookPR.objects.all()
        else:
            pr_count = WebhookPR.objects.filter(framework=framework)
        serializer = WebhookPRSerializer(pr_count, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def pr_count_start_end(request, framework, start, end):
    """
    API to return all PRs processed from start date to end date, filtered by framework
    :param request:
    :param start: YYYY-MM-DD
    :param end: YYYY-MM-DD
    :param framework
    :return: JSON
    """
    if request.method == "GET":
        if framework == "all":
            pr_count = WebhookPR.objects.filter(
                completed_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                completed_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1))
        else:
            pr_count = WebhookPR.objects.filter(
                completed_time__gte=datetime.strptime(start, "%Y-%m-%d"),
                completed_time__lte=datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1),
                framework=framework)
        serializer = WebhookPRSerializer(pr_count, many=True)
        return JsonResponse(serializer.data, safe=False)
    return HttpResponse(200)


def daemon_health(request, framework):
    """
    API to check on health of server
    :param request:
    :param framework: framework checking
    :return: HTTP response
    """
    n = 5
    if request.method == "GET":
        # check to see if nth recent PR has been processed yet
        if framework == "kraken":
            framework_count = WebhookPR.objects.filter(Q(framework=framework)).count()
        else:
            framework_count = WebhookPR.objects.filter(framework=framework).count()
        if framework_count < n:
            return HttpResponse(status=200)
        if framework == "kraken":
            nth_recent_pr = WebhookPR.objects.filter(Q(framework=framework)).\
                values("processed")[framework_count-n]["processed"]
        else:
            nth_recent_pr = WebhookPR.objects.filter(framework=framework).values("processed")\
                [framework_count-n]["processed"]
        if not nth_recent_pr:
            # daemon is down
            return HttpResponse(status=500)
    return HttpResponse(status=200)
