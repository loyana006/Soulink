from django.db import migrations
from django.utils import timezone


SEED_SLUGS = [
    "understanding-the-link-between-sleep-and-mood",
    "practicing-digital-minimalism-for-a-calmer-mind",
    "how-to-set-healthy-emotional-boundaries",
    "five-ways-to-manage-anxiety-in-the-workplace",
    "the-power-of-expressive-writing-why-journaling-works",
]


def seed_posts(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    User = apps.get_model("accounts", "CustomUser")

    if BlogPost.objects.exists():
        return

    author = User.objects.order_by("-is_superuser", "id").first()
    if not author:
        return

    now = timezone.now()
    posts = [
        {
            "title": "Understanding the Link Between Sleep and Mood",
            "slug": SEED_SLUGS[0],
            "excerpt": "A deep dive into how better sleep hygiene can dramatically improve your emotional stability.",
            "body": (
                "Sleep is one of the strongest levers we have for emotional regulation. When rest is short or "
                "fragmented, the same stressors feel heavier, and small problems can loom large.\n\n"
                "Building a consistent wind-down routine, limiting late caffeine, and keeping your bedroom "
                "dark and cool are simple steps that signal safety to your nervous system. Over time, better "
                "sleep supports steadier mood, clearer thinking, and more resilience in difficult moments."
            ),
            "category": "sleep",
            "author_id": author.pk,
            "is_published": True,
            "published_at": now,
        },
        {
            "title": "Practicing Digital Minimalism for a Calmer Mind",
            "slug": SEED_SLUGS[1],
            "excerpt": "Simple steps to reduce screen time and focus on real-world connections and present moments.",
            "body": (
                "Constant notifications pull attention away from what matters most. Digital minimalism is not "
                "about rejecting technology—it is about choosing what deserves your focus.\n\n"
                "Try batching checks to email and social apps, removing nonessential alerts, and carving "
                "phone-free blocks for meals, walks, or time with people you care about. Small boundaries "
                "compound into a calmer, more grounded day."
            ),
            "category": "mindfulness",
            "author_id": author.pk,
            "is_published": True,
            "published_at": now,
        },
        {
            "title": "How to Set Healthy Emotional Boundaries",
            "slug": SEED_SLUGS[2],
            "excerpt": "Learning to say no is a form of self-care. Here is a guide to establishing strong personal limits.",
            "body": (
                "Boundaries protect your energy and clarify what you can offer without burning out. They are "
                "kindest when stated clearly and early.\n\n"
                "Practice naming your limit in one sentence, offering an alternative when possible, and "
                "remembering that discomfort does not mean you are doing something wrong. Protecting your "
                "capacity allows you to show up more fully where it counts."
            ),
            "category": "relationships",
            "author_id": author.pk,
            "is_published": True,
            "published_at": now,
        },
        {
            "title": "5 Simple Ways to Manage Anxiety in the Workplace",
            "slug": SEED_SLUGS[3],
            "excerpt": "Techniques to ground yourself and reduce stress during busy days.",
            "body": (
                "Work anxiety often spikes when demands feel endless and control feels small. Short grounding "
                "practices can interrupt the spiral before it takes over your day.\n\n"
                "Try box breathing for two minutes, stand and stretch between meetings, name three objects you "
                "can see to anchor in the present, and break large tasks into the smallest next step. "
                "Consistency matters more than intensity."
            ),
            "category": "anxiety",
            "author_id": author.pk,
            "is_published": True,
            "published_at": now,
        },
        {
            "title": "The Power of Expressive Writing: Why Journaling Works",
            "slug": SEED_SLUGS[4],
            "excerpt": "Understanding the therapeutic benefits backed by research.",
            "body": (
                "Putting feelings into words changes how the brain processes them. Expressive writing can "
                "reduce rumination and help you notice patterns without judgment.\n\n"
                "You do not need perfect prose—honesty and regularity matter more. Even a few minutes of "
                "free writing after a hard day can create distance from intense emotions and make room "
                "for self-compassion."
            ),
            "category": "journaling",
            "author_id": author.pk,
            "is_published": True,
            "published_at": now,
        },
    ]

    for row in posts:
        BlogPost.objects.create(**row)


def unseed_posts(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogPost.objects.filter(slug__in=SEED_SLUGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_posts, unseed_posts),
    ]
