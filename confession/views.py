import json

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from accounts.models import UserProfile
from confession.models import ConfessionModal, ConfessionLike, ConfessionComment
from confession.forms import ConfessionEntryForm


@login_required
def confessions(request: HttpRequest):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ConfessionEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            if entry.is_draft:
                messages.success(request, "Draft saved — finish it from your profile when you're ready.")
            else:
                messages.success(request, "Your confession was posted.")
            return redirect("confessionals")
    else:
        form = ConfessionEntryForm(
            initial={
                "is_anonymous": profile.default_confession_anonymous,
            }
        )

    context = {}
    confessions_qs = (
        ConfessionModal.objects.filter(is_draft=False)
        .select_related("user", "user__profile")
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=ConfessionComment.objects.select_related("user").order_by(
                    "created_at"
                ),
            ),
            "likes",
        )
        .order_by("-id")
    )
    # Get confession IDs the current user has liked
    liked_ids = set(
        ConfessionLike.objects.filter(user=request.user)
        .values_list("confession_id", flat=True)
    )
    context["form"] = form
    context["confessions"] = confessions_qs
    context["liked_confession_ids"] = liked_ids
    context["user_profile"] = profile
    return render(request, "confessionals.html", context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def delete_confession(request, confession_id):
    """Delete own confession only."""
    confession = get_object_or_404(ConfessionModal, id=confession_id, user=request.user)
    confession.delete()
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def toggle_like(request, confession_id):
    """Toggle like on a confession post."""
    try:
        confession = get_object_or_404(ConfessionModal, id=confession_id)
        like, created = ConfessionLike.objects.get_or_create(
            confession=confession, user=request.user
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return JsonResponse({
            "success": True,
            "liked": liked,
            "like_count": confession.like_count,
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def add_comment(request, confession_id):
    """Add a comment to a confession post."""
    try:
        confession = get_object_or_404(ConfessionModal, id=confession_id)
        data = json.loads(request.body)
        content = (data.get("content") or "").strip()
        is_anonymous = data.get("is_anonymous", True)

        if not content:
            return JsonResponse(
                {"success": False, "error": "Comment content is required"},
                status=400,
            )

        comment = ConfessionComment.objects.create(
            confession=confession,
            user=request.user,
            content=content,
            is_anonymous=is_anonymous,
        )
        return JsonResponse({
            "success": True,
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "is_anonymous": comment.is_anonymous,
                "created_at": comment.created_at.strftime("%b %d, %Y %I:%M %p"),
                "username": "Anonymous" if comment.is_anonymous else comment.user.username,
            },
            "comment_count": confession.comment_count,
        })
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def publish_confession(request, confession_id):
    confession = get_object_or_404(
        ConfessionModal, id=confession_id, user=request.user, is_draft=True
    )
    confession.is_draft = False
    confession.save(update_fields=["is_draft"])
    messages.success(request, "Your confession is now visible on the feed.")
    return redirect("my_profile")


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def toggle_confession_anonymous(request, confession_id):
    confession = get_object_or_404(ConfessionModal, id=confession_id, user=request.user)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if "is_anonymous" in data:
        confession.is_anonymous = bool(data["is_anonymous"])
    else:
        confession.is_anonymous = not confession.is_anonymous
    confession.save(update_fields=["is_anonymous"])
    return JsonResponse({"success": True, "is_anonymous": confession.is_anonymous})
