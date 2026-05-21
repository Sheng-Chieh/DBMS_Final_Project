from django.shortcuts import redirect, render


def index(request):
    if request.session.get("user_id"):
        return redirect("homepage_logged_in")
    return render(request, "homepage/index.html")


def index_logged_in(request):
    if not request.session.get("user_id"):
        return redirect("login")
    return render(request, "homepage/index_logged_in.html")