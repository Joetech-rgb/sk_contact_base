# contacts/views/legal.py
from django.shortcuts import render, redirect
from django.contrib import messages


def privacy_view(request):
    return render(request, "contacts/privacy.html")


def about_view(request):
    return render(request, "contacts/about.html")


def rules_view(request):
    return render(request, "contacts/rules.html")


def delete_data_view(request):
    if request.method == "POST":
        from django.core.mail import send_mail
        from django.conf import settings
        name  = request.POST.get("name",  "").strip()
        phone = request.POST.get("phone", "").strip()
        try:
            send_mail(
                subject="Data Deletion Request - " + name,
                message="Name: " + name + "\nPhone: " + phone + "\nRequests data deletion.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SK_ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(request, "Your deletion request has been received.")
        return redirect("delete-my-data")
    return render(request, "contacts/delete_data.html")

