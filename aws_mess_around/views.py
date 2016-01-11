from django.shortcuts import render_to_response
from django.conf import settings
from github import Github


def home(request):
    data = {
        "has_github": False
    }
    try:
        g = Github()
        org = g.get_organization("uw-it-aca")
        print "O : ", org
        repository = org.get_repos("myuw")
        print "R: ", repository
        data["has_github"] = True
    except Exception as ex:
        print ex
        pass
    return render_to_response("aws_mess_around/home.html", data)
