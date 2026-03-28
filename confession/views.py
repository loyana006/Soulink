import json
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from confession.models import ConfessionModal, ConfessionLike, ConfessionComment
from confession.forms import ConfessionEntryForm


@login_required
def confessions(request: HttpRequest):
    context = {}
    form = ConfessionEntryForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()

    confessions_qs = ConfessionModal.objects.all().prefetch_related(
        "likes", "likes__user", "comments"
    )
    # Get confession IDs the current user has liked
    liked_ids = set(
        ConfessionLike.objects.filter(user=request.user)
        .values_list("confession_id", flat=True)
    )
    context["form"] = form
    context["confessions"] = confessions_qs
    context["liked_confession_ids"] = liked_ids
    return render(request, "confessionals.html", context)


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
            "like_count": confession.like_count(),
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
            "comment_count": confession.comment_count(),
        })
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
