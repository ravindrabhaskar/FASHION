"""Realistic development/demo seed data (PRD §54).

Run: python manage.py seed_demo
Idempotent — safe to re-run.
"""
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from accounts.models import UserRole
from fashion.registry import OCCASIONS
from profiles.models import StyleProfile
from subscriptions.models import SubscriptionPlan

User = get_user_model()

PLANS = [
    {
        "code": "style-monthly", "name": "Style", "tier": SubscriptionPlan.Tier.STYLE,
        "price_inr": 99, "ai_text_daily_limit": 8, "ai_image_monthly_limit": 5,
        "max_saved_looks": 25, "wardrobe_item_limit": 40,
        "features": ["Photo analysis", "Occasion styling", "Color recommendations",
                     "Accessories & footwear guidance", "Limited AI generations"],
    },
    {
        "code": "discover-monthly", "name": "Discover", "tier": SubscriptionPlan.Tier.DISCOVER,
        "price_inr": 199, "ai_text_daily_limit": 15, "ai_image_monthly_limit": 10,
        "max_saved_looks": 75, "wardrobe_item_limit": 100,
        "features": ["Everything in Style", "Personalized fashion feed", "Creator & brand discovery",
                     "Similar outfit recommendations", "Fashion boards & saved looks"],
    },
    {
        "code": "designer-monthly", "name": "AI Personal Designer", "tier": SubscriptionPlan.Tier.AI_DESIGNER,
        "price_inr": 499, "ai_text_daily_limit": 60, "ai_image_monthly_limit": 30,
        "max_saved_looks": 500, "wardrobe_item_limit": 300,
        "designer_chat_enabled": True, "customization_requests_enabled": True,
        "features": ["Everything in Discover", "Conversational AI stylist",
                     "Advanced outfit generation", "Digital wardrobe intelligence",
                     "AI customization + designer matching"],
    },
]

DEMO_PASSWORD = "demo-pass-123"

# (email, name, category, color, hex, fabric, formality, occasions)
WARDROBE_ITEMS = {
    "aisha@demo.com": [
        ("Emerald silk kurta set", "ethnic", "emerald-green", "#0B6E4F", "cotton-silk", 4,
         ["wedding", "festival", "cultural"]),
        ("Ivory chikankari dupatta", "accessories", "ivory", "#FFFFF0", "cotton", 3,
         ["wedding", "festival"]),
        ("Gold embroidered mojaris", "footwear", "gold", "#D4AF37", "leather", 4,
         ["wedding", "festival", "party"]),
        ("Blush pink georgette saree", "ethnic", "blush-pink", "#E8B4BC", "georgette", 5,
         ["reception", "engagement"]),
        ("White cotton kurti", "tops", "white", "#FAFAFA", "cotton", 2,
         ["casual", "college"]),
        ("Palazzo pants - olive", "bottoms", "olive", "#708238", "rayon", 2,
         ["casual", "travel"]),
    ],
    "rohit@demo.com": [
        ("Navy oxford shirt", "tops", "navy", "#1B2A4A", "oxford-cotton", 3,
         ["office", "dinner", "date"]),
        ("Charcoal tapered trousers", "bottoms", "charcoal", "#3B3B3B", "wool-blend", 4,
         ["office", "business-meeting"]),
        ("Olive relaxed chinos", "bottoms", "olive", "#6B8E23", "cotton-twill", 2,
         ["casual", "college", "travel"]),
        ("White leather sneakers", "footwear", "white", "#FAFAFA", "leather", 2,
         ["casual", "college", "travel"]),
        ("Denim trucker jacket", "outerwear", "denim-blue", "#283593", "denim", 2,
         ["casual", "party"]),
    ],
}

PEOPLE = [
    {"email": "aisha@demo.com", "full_name": "Aisha Verma", "role": UserRole.CREATOR,
     "city": "Hyderabad", "styles": ["ethnic-traditional", "fusion", "minimal"],
     "colors": ["emerald-green", "gold", "ivory"], "occasions": ["wedding", "festival", "party"]},
    {"email": "rohit@demo.com", "full_name": "Rohit Sharma", "role": UserRole.USER,
     "city": "Bengaluru", "styles": ["smart-casual", "streetwear"],
     "colors": ["navy", "olive", "white"], "occasions": ["office", "casual", "college"]},
    {"email": "meera@demo.com", "full_name": "Meera Iyer", "role": UserRole.DESIGNER,
     "city": "Chennai", "styles": ["ethnic-traditional", "romantic"],
     "colors": ["temple-red", "gold"], "occasions": ["wedding", "cultural", "engagement"]},
    {"email": "arjun@demo.com", "full_name": "Arjun Rao", "role": UserRole.USER,
     "city": "Mumbai", "styles": ["minimal", "formal-business"],
     "colors": ["charcoal", "sky-blue", "white"], "occasions": ["business-meeting", "dinner", "travel"]},
]


class Command(BaseCommand):
    help = "Seed realistic demo data: plans, occasions, users, style profiles."

    def handle(self, *args, **options):
        self._seed_plans()
        self._seed_occasions()
        self._seed_users()
        self._seed_wardrobe()
        self._seed_badges()
        self._seed_challenge()
        self._seed_rewards()
        self._seed_designer()
        self._seed_products()
        self._seed_posts()
        self._seed_admin()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_badges(self):
        from fashionxp.models import Badge

        BADGES = [
            ("first-post", "First Post", "Published your first look", "✦",
             {"metric": "posts_published", "threshold": 1}, 25),
            ("wardrobe-starter", "Closet Curator", "Added 5 wardrobe pieces", "▤",
             {"metric": "wardrobe_items", "threshold": 5}, 40),
            ("look-collector", "Look Collector", "Saved 5 looks", "♥",
             {"metric": "saved_looks", "threshold": 5}, 40),
            ("social-star", "Social Star", "Reached 10 followers", "★",
             {"metric": "followers", "threshold": 10}, 75),
        ]
        for code, name, desc, icon, criteria, bonus in BADGES:
            Badge.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc, "icon": icon,
                          "criteria": criteria, "xp_bonus": bonus},
            )
        self.stdout.write(f"badges ensured ({len(BADGES)})")

    def _seed_challenge(self):
        from datetime import timedelta

        from django.utils import timezone

        from fashionxp.models import Challenge

        Challenge.objects.update_or_create(
            slug="festive-flair",
            defaults={
                "title": "Festive Flair",
                "description": "Style your best festive look using pieces you already own.",
                "occasion_slug": "festival",
                "hashtag": "#FestiveFlair",
                "starts_at": timezone.now() - timedelta(days=1),
                "ends_at": timezone.now() + timedelta(days=14),
                "xp_reward": 150,
                "status": Challenge.Status.LIVE,
            },
        )
        self.stdout.write("challenge ensured (festive-flair)")

    def _seed_rewards(self):
        from fashionxp.models import Reward

        REWARDS = [
            ("style-credit-500", "₹500 Style Credit", "Off your next designer order", 400, None),
            ("priority-slot", "Priority Custom Slot", "Skip the queue with any designer", 250, 50),
            ("free-custom-quote", "Free Premium Quote", "Detailed quote from a top studio", 600, None),
        ]
        for code, name, desc, cost, stock in REWARDS:
            Reward.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc, "cost_xp": cost, "stock": stock},
            )
        self.stdout.write(f"rewards ensured ({len(REWARDS)})")

    def _seed_designer(self):
        from django.utils import timezone

        from designers.models import DesignerProfile

        try:
            meera = User.objects.get(email="meera@demo.com")
        except User.DoesNotExist:
            return
        profile, _ = DesignerProfile.objects.update_or_create(
            user=meera,
            defaults={
                "slug": "meera-atelier",
                "studio_name": "Meera Atelier",
                "tagline": "Hand-finished ethnic wear for modern celebrations",
                "bio": "Chennai-based studio specializing in bridal handwork, "
                       "sustainable silks and made-to-measure festive sets.",
                "city": "Chennai",
                "specialities": ["bridal-wear", "handloom", "made-to-measure"],
                "experience_years": 8,
                "instagram": "@meera.atelier",
                "verified": True,
                "verified_at": timezone.now(),
            },
        )
        self.stdout.write(f"designer ensured ({profile.slug})")

    def _seed_products(self):
        from designers.models import DesignerProfile
        from marketplace.models import Product

        try:
            profile = DesignerProfile.objects.get(slug="meera-atelier")
        except DesignerProfile.DoesNotExist:
            return
        PRODUCTS = [
            ("Emerald Bridal Lehenga Set", "ethnic", 24999, True,
             ["bridal", "emerald", "wedding", "zardozi"]),
            ("Ivory Handloom Silk Kurta Set", "ethnic", 7499, False,
             ["handloom", "ivory", "festival"]),
            ("Blush Organza Anarkali", "fusion", 9999, True,
             ["organza", "blush-pink", "reception"]),
        ]
        for title, category, price, customizable, tags in PRODUCTS:
            product, created = Product.objects.update_or_create(
                title=title,
                defaults={
                    "seller_user": profile.user, "designer": profile,
                    "description": f"{title} by Meera Atelier — made to measure.",
                    "category": category, "price_inr": price, "city": "Chennai",
                    "fabric": "cotton-silk" if "Kurta" in title else "raw-silk",
                    "colors": [t for t in tags if "-" in t] or ["emerald-green"],
                    "tags": tags, "is_customizable": customizable,
                    "ready_to_ship": not customizable, "stock": 5 if not customizable else 0,
                },
            )
            from marketplace.services import CatalogService

            CatalogService.ensure_embedding(product)
        self.stdout.write(f"products ensured ({len(PRODUCTS)})")

    def _seed_posts(self):
        import io

        from PIL import Image

        from social.models import Post

        PALETTES = {
            "aisha@demo.com": [
                ("Sangeet-ready in emerald silk ✦ #FestiveFlair", "wedding", (11, 110, 79)),
                ("Everyday ivory & gold layering", "casual", (255, 248, 231)),
            ],
            "rohit@demo.com": [
                ("Monday uniform: navy oxford, charcoal trousers", "office", (27, 42, 74)),
            ],
        }
        created = 0
        for email, specs in PALETTES.items():
            try:
                person = User.objects.get(email=email)
            except User.DoesNotExist:
                continue
            if Post.objects.filter(user=person).exists():
                continue
            for caption, occasion, color in specs:
                buf = io.BytesIO()
                Image.new("RGB", (320, 320), color=color).save(buf, format="JPEG")
                post = Post(user=person, caption=caption, occasion=occasion,
                            city_snapshot=person.profile.city)
                post.image.save(f"posts/{abs(hash(caption)) % 10**8}.jpg",
                                ContentFile(buf.getvalue()))
                post.save()
                created += 1
        self.stdout.write(f"social posts ensured (+{created})")

    def _seed_plans(self):
        for spec in PLANS:
            plan, created = SubscriptionPlan.objects.update_or_create(
                code=spec["code"],
                defaults={k: v for k, v in spec.items() if k != "code"},
            )
            tag = "created" if created else "updated"
            self.stdout.write(f"plan {plan.code}: {tag}")

    def _seed_occasions(self):
        for spec in OCCASIONS.values():
            from fashion.models import Occasion

            Occasion.objects.update_or_create(
                slug=spec.slug,
                defaults={
                    "label": spec.label,
                    "description": spec.description,
                    "formality": spec.formality,
                    "palette_bias": list(spec.palette_bias),
                },
            )
        self.stdout.write(f"occasions ensured ({len(OCCASIONS)})")

    def _seed_users(self):
        for person in PEOPLE:
            user, created = User.objects.get_or_create(
                email=person["email"],
                defaults={"full_name": person["full_name"], "role": person["role"]},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.onboarding_completed_at = user.created_at
                user.save(update_fields=["password", "onboarding_completed_at"])

            profile = user.profile
            profile.city = person["city"]
            profile.display_name = person["full_name"].split()[0]
            profile.save(update_fields=["city", "display_name", "updated_at"])

            sp = user.style_profile
            sp.preferred_styles = person["styles"]
            sp.favorite_colors = person["colors"]
            sp.common_occasions = person["occasions"]
            sp.fit_preference = StyleProfile.FitPreference.REGULAR
            sp.budget_min, sp.budget_max = (1500, 6000) if person["role"] == UserRole.USER else (3000, 25000)
            sp.traditional_modern_balance = random.randint(35, 70)
            sp.completion_cache = sp.compute_completion()
            sp.save()
            self.stdout.write(f"user {user.email}: {'created' if created else 'exists'}")

    def _seed_wardrobe(self):
        from wardrobe.models import WardrobeItem

        created_count = 0
        for email, items in WARDROBE_ITEMS.items():
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                continue
            existing = {i.name for i in WardrobeItem.objects.filter(user=user)}
            for (name, category, color, color_hex, fabric, formality, occasions) in items:
                if name in existing:
                    continue
                WardrobeItem.objects.create(
                    user=user,
                    name=name,
                    category=category,
                    status=WardrobeItem.Status.READY,
                    color_primary=color,
                    color_hex=color_hex,
                    fabric=fabric,
                    formality=formality,
                    occasion_slugs=list(occasions),
                    seasons=["all-season"],
                    style_tags=["seeded"],
                )
                created_count += 1
        self.stdout.write(f"wardrobe items ensured (+{created_count})")

    def _seed_admin(self):
        email = settings.DJANGO_ADMIN_EMAIL if hasattr(settings, "DJANGO_ADMIN_EMAIL") else "admin@fashionxp.local"
        password = getattr(settings, "DJANGO_ADMIN_PASSWORD", "") or "admin-demo-123"
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(f"superuser {email} created")
        else:
            self.stdout.write(f"superuser {email} exists")
