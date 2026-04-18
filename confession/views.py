import json

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from accounts.models import UserProfile
from confession.models import ConfessionModal, ConfessionLike, ConfessionComment
from confession.forms import ConfessionEntryForm

FEED_PAGE_SIZE = 15


def _confessions_feed_queryset():
    return (
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


def _feed_batch(qs, before_id=None):
    """
    Return up to FEED_PAGE_SIZE items (newest first) and whether more exist after this batch.
    When before_id is set, only confessions with id < before_id are included (cursor pagination).
    """
    if before_id is not None:
        qs = qs.filter(id__lt=before_id)
    chunk = list(qs[: FEED_PAGE_SIZE + 1])
    has_more = len(chunk) > FEED_PAGE_SIZE
    if has_more:
        chunk = chunk[:FEED_PAGE_SIZE]
    return chunk, has_more


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

    confessions_qs = _confessions_feed_queryset()
    confessions, feed_has_more = _feed_batch(confessions_qs)
    liked_ids = set(
        ConfessionLike.objects.filter(user=request.user)
        .values_list("confession_id", flat=True)
    )
    feed_next_before_id = confessions[-1].id if confessions and feed_has_more else None

    context = {
        "form": form,
        "confessions": confessions,
        "liked_confession_ids": liked_ids,
        "user_profile": profile,
        "feed_has_more": feed_has_more,
        "feed_next_before_id": feed_next_before_id,
    }
    return render(request, "confessionals.html", context)


@login_required
@require_http_methods(["GET"])
def confession_feed_more(request: HttpRequest):
    """JSON fragment for appending older confessions (Load more)."""
    try:
        before_id = int(request.GET.get("before", ""))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid or missing before"}, status=400)

    batch, has_more = _feed_batch(_confessions_feed_queryset(), before_id=before_id)
    liked_ids = set(
        ConfessionLike.objects.filter(user=request.user)
        .values_list("confession_id", flat=True)
    )
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    html_parts = []
    for confession in batch:
        html_parts.append(
            render_to_string(
                "confessionals/_confession_card.html",
                {
                    "confession": confession,
                    "user": request.user,
                    "liked_confession_ids": liked_ids,
                    "user_profile": profile,
                },
                request=request,
            )
        )

    next_before_id = batch[-1].id if batch else None
    return JsonResponse(
        {
            "html": "".join(html_parts),
            "has_more": has_more,
            "next_before_id": next_before_id if batch else None,
        }
    )


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
