from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import BlogBookmark, BlogPost


def post_list(request):
    qs = BlogPost.objects.filter(is_published=True).select_related("author")

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(body__icontains=q)
        )

    category = (request.GET.get("category") or "").strip()
    if category:
        valid = {c[0] for c in BlogPost.CATEGORY_CHOICES}
        if category in valid:
            qs = qs.filter(category=category)

    paginator = Paginator(qs, 5)
    page_num = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    category_counts = (
        BlogPost.objects.filter(is_published=True)
        .values("category")
        .annotate(count=Count("id"))
    )
    category_count_map = {row["category"]: row["count"] for row in category_counts}

    labels = dict(BlogPost.CATEGORY_CHOICES)
    category_sidebar = [
        {"key": key, "label": labels[key], "count": category_count_map.get(key, 0)}
        for key, _ in BlogPost.CATEGORY_CHOICES
        if category_count_map.get(key, 0) > 0
    ]

    query = request.GET.copy()
    query.pop("page", None)
    query_string = query.urlencode()

    return render(
        request,
        "blog/post_list.html",
        {
            "page_obj": page_obj,
            "posts": page_obj,
            "search_query": q,
            "active_category": category,
            "category_sidebar": category_sidebar,
            "category_labels": labels,
            "query_string": query_string,
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related("author"),
        slug=slug,
        is_published=True,
    )
    related = (
        BlogPost.objects.filter(
            is_published=True,
            category=post.category,
        )
        .exclude(pk=post.pk)
        .order_by("-published_at")[:3]
    )
    bookmarked = False
    if request.user.is_authenticated:
        bookmarked = BlogBookmark.objects.filter(
            user=request.user, post=post
        ).exists()
    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "related_posts": related,
            "is_bookmarked": bookmarked,
        },
    )


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def toggle_bookmark(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id, is_published=True)
    bm, created = BlogBookmark.objects.get_or_create(user=request.user, post=post)
    if not created:
        bm.delete()
        saved = False
    else:
        saved = True
    return JsonResponse({"success": True, "saved": saved})
